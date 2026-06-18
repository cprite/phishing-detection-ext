/*
 * background.js — service worker for No Phishing (self-contained build).
 *
 * Pages are reported by content.js, scored locally by the ONNX model running in
 * an offscreen document, and redirected to the warning page when flagged. There
 * is no companion server: the old http://127.0.0.1:5030 dependency is gone.
 */
importScripts("features.js"); // provides self.NoPhishingFeatures

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

// URLs the user chose to proceed to from the warning page (skip one check).
const proceedURLs = new Set();

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ isEnabled: false });
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.target === "offscreen") return; // handled by the offscreen document
  if (msg.action === "updateState") {
    chrome.storage.sync.set({ isEnabled: msg.state });
    return;
  }
  if (msg.action === "proceedToURL") {
    proceedURLs.add(msg.url);
    return;
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
  if (proceedURLs.has(url)) {
    proceedURLs.delete(url);
    return;
  }

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
