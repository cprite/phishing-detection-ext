/*
 * content.js — runs on every http/https page (document_idle).
 *
 * Reports the page URL and its hyperlink count to the service worker, which
 * scores the page locally with the bundled ONNX model. Nothing is sent off the
 * device. The hyperlink count is the only signal read from the page DOM;
 * everything else is derived from the URL string in the worker.
 */
(function () {
  try {
    chrome.runtime.sendMessage({
      type: "NP_PAGE",
      url: location.href,
      nbHyperlinks: document.querySelectorAll("a").length,
    });
  } catch (e) {
    // Extension context can be invalidated during reloads/updates — ignore.
  }
})();
