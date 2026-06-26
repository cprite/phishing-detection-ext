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
 * are never blocked. In the OSS build they are still scored silently in the
 * background, and a PHISHING verdict on a trusted host is treated as a model
 * error and fed back as a LEGITIMATE point (the trusted list is ground truth).
 * "Proceed" also adds a legitimate feedback point and the popup can add a
 * phishing one.
 */
importScripts("config.js");   // self.IS_OSS_BUILD
importScripts("features.js");  // self.NoPhishingFeatures
importScripts("knn.js");       // self.NoPhishingKNN
importScripts("storage.js");   // self.NoPhishingStore
importScripts("lookalike.js"); // self.NoPhishingLookalike

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

// "Proceed" past a warning records the page as a LEGITIMATE feedback point so
// the in-browser KNN learns the correction. This path is mandatory, not best-
// effort: a legitimate point is ALWAYS added.
//
// Preferred source is the scaled vector cached at detection time — it carries
// nb_hyperlinks, a live-DOM feature that cannot be recovered once the warning
// page has replaced the original page. If that cache is gone (e.g. the browser
// session was cleared between detection and proceed), recompute from the full
// URL: the 10 lexical features are exact, nb_hyperlinks falls back to 0.
async function addLegitimateForUrl(url) {
  if (!IS_OSS_BUILD || !url) return;
  const key = "pending:" + url;
  const data = await chrome.storage.session.get(key);
  let scaled = data[key];
  if (!Array.isArray(scaled)) {
    const ds = await NoPhishingStore.buildDataset();
    const feats = NoPhishingFeatures.extractFeatures(url, 0); // lexical-only fallback
    scaled = NoPhishingKNN.scale(feats, ds.scaler);
    console.warn("No Phishing: pending vector missing, recomputed legit point from URL");
  }
  await addPoint(scaled, 0);
  await chrome.storage.session.remove(key);
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
// how many feedback points exist, when the last one was added, and the accuracy
// on a fixed HELD-OUT test set (saved_models/seed_test.json) that is never added
// to the KNN dataset — an unbiased estimate, unlike scoring the user's own
// feedback. Each test point is classified against the live dataset (seed +
// feedback), so the number moves as feedback accumulates.
//
// Scoring the whole test set is O(test * dataset), so it is cached keyed on the
// feedback count (the test set and seed are immutable): it recomputes once per
// new feedback point, and re-opening the popup is instant.
async function computeStats() {
  const fb = await NoPhishingStore.getFeedbackPoints();
  const count = fb.length;

  let lastUpdated = null;
  for (const p of fb) {
    if (p.ts && (lastUpdated === null || p.ts > lastUpdated)) lastUpdated = p.ts;
  }

  let accuracy = null;
  const cached = (await chrome.storage.local.get("stats_cache")).stats_cache;
  if (cached && cached.count === count && typeof cached.accuracy === "number") {
    accuracy = cached.accuracy;
  } else {
    const ds = await NoPhishingStore.buildDataset();
    const test = await NoPhishingStore.loadTest();
    if (test && Array.isArray(test.X) && test.X.length) {
      let correct = 0;
      for (let i = 0; i < test.X.length; i++) {
        const { label } = NoPhishingKNN.predict(test.X[i], ds.X, ds.y, ds.k);
        if (label === test.y[i]) correct++;
      }
      accuracy = correct / test.X.length;
      await chrome.storage.local.set({ stats_cache: { count: count, accuracy: accuracy } });
    }
  }

  return {
    feedbackCount: count,
    lastUpdated: lastUpdated, // ISO string or null
    accuracy: accuracy, // 0..1 on held-out test set, or null
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
    addLegitimateForUrl(msg.url).then(() => sendResponse({ ok: true }));
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
  const isTrusted = !!(host && trusted.includes(host));

  try {
    const ds = await NoPhishingStore.buildDataset();
    const feats = NoPhishingFeatures.extractFeatures(url, msg.nbHyperlinks);
    const scaled = NoPhishingKNN.scale(feats, ds.scaler);
    const { label, ratio } = NoPhishingKNN.predict(scaled, ds.X, ds.y, ds.k);

    // Lookalike override: the lexical KNN misses brand-impersonation phishing on
    // Vercel deploy hosts (clean-looking *.vercel.app subdomains). When the
    // detector fires, force a PHISHING verdict regardless of the KNN label, with
    // high confidence — this is a deterministic rule, not a vote.
    const look = NoPhishingLookalike.check(url);
    const phishing = label === 1 || look.hit;
    if (!phishing) return;
    const conf = look.hit ? Math.max(Math.round(ratio * 100), 95) : Math.round(ratio * 100);

    if (isTrusted) {
      // Trusted host = ground truth: the user has vouched for it, so we never
      // block it. But a PHISHING verdict here means the model is wrong on a
      // domain we know is good — feed that back SILENTLY as a legitimate point
      // (the same dataset effect as "Proceed past the warning"), reusing the
      // vector we just scored (it carries the live nb_hyperlinks feature).
      // No warning page, no navigation, no user-facing notification.
      await addPoint(scaled, 0);
      return;
    }

    // Untrusted phishing verdict: warn the user and let them decide.
    // Cache the scaled vector so "Proceed" can log it as a legitimate point.
    await chrome.storage.session.set({ ["pending:" + url]: scaled });
    // Pass the phishing confidence (0..100) so the warning page can show how
    // likely the verdict is, plus the lookalike reason when the override fired.
    let warningUrl =
      chrome.runtime.getURL("extension/warning.html") +
      "?url=" + encodeURIComponent(url) +
      "&conf=" + conf;
    if (look.hit) warningUrl += "&reason=" + encodeURIComponent(look.reason);
    chrome.tabs.update(tabId, { url: warningUrl });
  } catch (e) {
    console.error("No Phishing:", e);
  }
}
