/*
 * background.js — service worker for No Phishing (self-contained build).
 *
 * Pages are reported by content.js, scored locally by the ONNX model running in
 * an offscreen document, and redirected to the warning page when flagged. There
 * is no companion server: the old http://127.0.0.1:5030 dependency is gone.
 *
 * Trusted domains: when the user clicks "Proceed" on the warning page, that
 * page's hostname is saved to chrome.storage.local (trusted_domains). Future
 * visits to any URL on that hostname skip the model entirely.
 */
importScripts("config.js");   // provides self.IS_OSS_BUILD
importScripts("features.js");  // provides self.NoPhishingFeatures

const OFFSCREEN_PATH = "extension/offscreen.html";
let creatingOffscreen = null;

async function hasOffscreen() {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
  });
  return contexts.length > 0;
}

async function ensureOffscreen() {
  if (await hasOffscreen()) return;
  if (creatingOffscreen) return creatingOffscreen; // collapse concurrent creates
  creatingOffscreen = chrome.offscreen.createDocument({
    url: OFFSCREEN_PATH,
    reasons: ["WORKERS"],
    justification:
      "Run the bundled ONNX phishing-detection model with onnxruntime-web (WebAssembly).",
  });
  try {
    await creatingOffscreen;
  } finally {
    creatingOffscreen = null;
  }
}

async function classify(features) {
  await ensureOffscreen();
  return chrome.runtime.sendMessage({ target: "offscreen", action: "classify", features });
}

// --- Trusted domains (user-approved via the warning page) ------------------

function hostnameOf(url) {
  try {
    return new URL(url).hostname;
  } catch (e) {
    return "";
  }
}

async function getTrustedDomains() {
  const { trusted_domains } = await chrome.storage.local.get("trusted_domains");
  return Array.isArray(trusted_domains) ? trusted_domains : [];
}

// Add a URL's hostname to the trusted list (no-op if already present).
async function trustDomain(url) {
  const host = hostnameOf(url);
  if (!host) return;
  const domains = await getTrustedDomains();
  if (!domains.includes(host)) {
    domains.push(host);
    await chrome.storage.local.set({ trusted_domains: domains });
  }
}

// --- Self-learning feedback (OSS build only) -------------------------------
// ONNX models cannot be retrained in the browser, so feedback is accumulated
// here and folded back into the model offline by retrain_from_feedback.py.

async function getFeedback() {
  const { feedback } = await chrome.storage.local.get("feedback");
  return Array.isArray(feedback) ? feedback : [];
}

// Append a {url, label, ts} feedback example. No-op outside the OSS build.
async function recordFeedback(url, label) {
  if (!IS_OSS_BUILD) return;
  if (!url || (label !== "phishing" && label !== "legitimate")) return;
  const feedback = await getFeedback();
  feedback.push({ url, label, ts: new Date().toISOString() });
  await chrome.storage.local.set({ feedback });
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ isEnabled: false });
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target === "offscreen") return; // handled by the offscreen document
  if (msg.action === "updateState") {
    chrome.storage.sync.set({ isEnabled: msg.state });
    return;
  }
  if (msg.action === "trustDomain") {
    // Persist the domain, then ack so the warning page navigates only after the
    // write lands (the next page load must see the updated trusted list).
    trustDomain(msg.url).then(() => sendResponse({ ok: true }));
    return true; // keep the channel open for the async response
  }
  if (msg.action === "recordFeedback") {
    recordFeedback(msg.url, msg.label).then(() => sendResponse({ ok: true }));
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

  // Skip any page on a hostname the user has explicitly trusted.
  const host = hostnameOf(url);
  const trusted = await getTrustedDomains();
  if (host && trusted.includes(host)) return;

  try {
    const features = NoPhishingFeatures.extractFeatures(url, msg.nbHyperlinks);
    const result = await classify(features);
    if (result && result.decision === "PHISHING") {
      const warningUrl =
        chrome.runtime.getURL("extension/warning.html") + "?url=" + encodeURIComponent(url);
      chrome.tabs.update(tabId, { url: warningUrl });
    }
  } catch (e) {
    console.error("No Phishing:", e);
  }
}
