/*
 * content.js — runs on every http/https page (document_idle).
 *
 * Reports the page URL and its hyperlink count to the service worker, which
 * scores the page locally with the in-browser KNN model. Also answers
 * getLinkCount requests so the popup's "Mark as phishing" can score the live
 * page. Nothing is sent off the device.
 */
(function () {
  function linkCount() {
    return document.querySelectorAll("a").length;
  }

  try {
    chrome.runtime.sendMessage({
      type: "NP_PAGE",
      url: location.href,
      nbHyperlinks: linkCount(),
    });
  } catch (e) {
    // Extension context can be invalidated during reloads/updates — ignore.
  }

  chrome.runtime.onMessage.addListener(function (msg, sender, sendResponse) {
    if (msg && msg.action === "getLinkCount") {
      sendResponse({ nbHyperlinks: linkCount() });
    }
  });
})();
