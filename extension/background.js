/*
 * background.js — service worker for No Phishing (self-contained, pure-JS KNN).
 *
 * Pages are reported by content.js and scored locally with a K-Nearest-Neighbours
 * classifier implemented in JavaScript (knn.js). The seed dataset ships with the
 * extension (saved_models/seed_model.json); user-feedback points accumulate in
 * chrome.storage.local and are merged into the vote at inference time, so the
 * model "retrains" in the browser. No server, no ONNX, no WebAssembly.
 *
 * Trusted domains: "Proceed" on a warning trusts that hostname so future visits
 * skip scoring. In the OSS build, "Proceed" also adds a legitimate feedback
 * point and the popup can add a phishing one.
 */
importScripts("config.js");   // self.IS_OSS_BUILD
importScripts("features.js");  // self.NoPhishingFeatures
importScripts("knn.js");       // self.NoPhishingKNN
importScripts("storage.js");   // self.NoPhishingStore

function hostnameOf(url) {
  try {
    return new URL(url).hostname;
  } catch (e) {
    return "";
  }
}

// --- Trusted domains -------------------------------------------------------

async function getTrustedDomains() {
  const { trusted_domains } = await chrome.storage.local.get("trusted_domains");
  return Array.isArray(trusted_domains) ? trusted_domains : [];
}

async function trustDomain(url) {
  const host = hostnameOf(url);
  if (!host) return;
  const domains = await getTrustedDomains();
  if (!domains.includes(host)) {
    domains.push(host);
    await chrome.storage.local.set({ trusted_domains: domains });
  }
}

// --- Feedback points (in-browser retraining, OSS build only) ---------------

// Add a scaled feedback point with the given label (0 legitimate, 1 phishing).
async function addPoint(scaledFeatures, label) {
  if (!IS_OSS_BUILD) return;
  await NoPhishingStore.addFeedbackPoint(scaledFeatures, label);
}

// "Proceed" past a warning: the scaled features were cached at detection time.
async function addLegitimateFromPending(url) {
  if (!IS_OSS_BUILD || !url) return;
  const key = "pending:" + url;
  const data = await chrome.storage.session.get(key);
  const scaled = data[key];
  if (Array.isArray(scaled)) {
    await addPoint(scaled, 0);
    await chrome.storage.session.remove(key);
  }
}

// "Mark as phishing" from the popup: score the active tab's URL live.
async function markActiveTabPhishing() {
  if (!IS_OSS_BUILD) return { ok: false };
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab && tab.url;
  if (!url || url.startsWith("chrome") || url.startsWith(chrome.runtime.getURL(""))) {
    return { ok: false };
  }
  let nb = 0;
  try {
    const resp = await chrome.tabs.sendMessage(tab.id, { action: "getLinkCount" });
    if (resp && typeof resp.nbHyperlinks === "number") nb = resp.nbHyperlinks;
  } catch (e) {
    // No content script (e.g. a page that wasn't injected) — fall back to 0.
  }
  const ds = await NoPhishingStore.buildDataset();
  const feats = NoPhishingFeatures.extractFeatures(url, nb);
  const scaled = NoPhishingKNN.scale(feats, ds.scaler);
  await addPoint(scaled, 1);
  return { ok: true };
}

// --- Model stats (self-learning transparency) ------------------------------

// Summarise the in-browser model so the popup can show that it is improving:
// how many feedback points exist, when the last one was added, and a leave-one-
// out accuracy over the feedback points (each predicted against seed + the
// *other* feedback, so a point never votes for itself — an honest estimate of
// how well the current model classifies the user's own corrections).
async function computeStats() {
  const fb = await NoPhishingStore.getFeedbackPoints();
  const ds = await NoPhishingStore.buildDataset();
  const seedLen = ds.X.length - fb.length; // feedback occupies the tail of ds

  let lastUpdated = null;
  for (const p of fb) {
    if (p.ts && (lastUpdated === null || p.ts > lastUpdated)) lastUpdated = p.ts;
  }

  let correct = 0;
  for (let i = 0; i < fb.length; i++) {
    const gi = seedLen + i; // this point's index in the merged dataset
    const X = ds.X.slice(0, gi).concat(ds.X.slice(gi + 1));
    const y = ds.y.slice(0, gi).concat(ds.y.slice(gi + 1));
    const { label } = NoPhishingKNN.predict(ds.X[gi], X, y, ds.k);
    if (label === fb[i].y) correct++;
  }

  return {
    feedbackCount: fb.length,
    lastUpdated: lastUpdated, // ISO string or null
    accuracy: fb.length ? correct / fb.length : null, // 0..1 or null
  };
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ isEnabled: false });
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "updateState") {
    chrome.storage.sync.set({ isEnabled: msg.state });
    return;
  }
  if (msg.action === "trustDomain") {
    trustDomain(msg.url).then(() => sendResponse({ ok: true }));
    return true;
  }
  if (msg.action === "addLegitimate") {
    addLegitimateFromPending(msg.url).then(() => sendResponse({ ok: true }));
    return true;
  }
  if (msg.action === "markPhishing") {
    markActiveTabPhishing().then(sendResponse);
    return true;
  }
  if (msg.action === "getStats") {
    computeStats().then(sendResponse);
    return true;
  }
  if (msg.type === "NP_PAGE" && sender.tab) {
    handlePage(msg, sender.tab.id);
  }
});

async function handlePage(msg, tabId) {
  const { isEnabled } = await chrome.storage.sync.get("isEnabled");
  if (!isEnabled) return;

  const url = msg.url;
  if (!url || url.startsWith("chrome") || url.startsWith(chrome.runtime.getURL(""))) {
    return; // skip chrome:// and our own pages (incl. the warning page)
  }

  const host = hostnameOf(url);
  const trusted = await getTrustedDomains();
  if (host && trusted.includes(host)) return;

  try {
    const ds = await NoPhishingStore.buildDataset();
    const feats = NoPhishingFeatures.extractFeatures(url, msg.nbHyperlinks);
    const scaled = NoPhishingKNN.scale(feats, ds.scaler);
    const { label, ratio } = NoPhishingKNN.predict(scaled, ds.X, ds.y, ds.k);
    if (label === 1) {
      // Cache the scaled vector so "Proceed" can log it as a legitimate point.
      await chrome.storage.session.set({ ["pending:" + url]: scaled });
      // Pass the phishing confidence (share of neighbours voting phishing,
      // 0..100) so the warning page can show how likely the verdict is.
      const conf = Math.round(ratio * 100);
      const warningUrl =
        chrome.runtime.getURL("extension/warning.html") +
        "?url=" + encodeURIComponent(url) +
        "&conf=" + conf;
      chrome.tabs.update(tabId, { url: warningUrl });
    }
  } catch (e) {
    console.error("No Phishing:", e);
  }
}
