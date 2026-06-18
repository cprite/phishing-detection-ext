document.addEventListener('DOMContentLoaded', function() {
  const proceedBtn = document.getElementById('proceedBtn');
  const goBackBtn = document.getElementById('goBackBtn');

  proceedBtn.addEventListener('click', proceedToURL);
  goBackBtn.addEventListener('click', goBack);

  function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }

  function proceedToURL() {
    const actualURL = getQueryParam('url');
    if (!actualURL) {
      console.error('URL parameter is missing');
      return;
    }
    // Proceeding means the user judges this page legitimate (a false positive).
    // Trust the domain so future visits aren't re-checked, and — in the OSS
    // build — record a "legitimate" correction for offline retraining. Navigate
    // only after the writes are acked so the next load sees the updated list.
    chrome.runtime.sendMessage({ action: "trustDomain", url: actualURL }, function () {
      if (typeof IS_OSS_BUILD !== "undefined" && IS_OSS_BUILD) {
        chrome.runtime.sendMessage(
          { action: "recordFeedback", url: actualURL, label: "legitimate" },
          function () { window.location.href = actualURL; }
        );
      } else {
        window.location.href = actualURL;
      }
    });
  }

  function goBack() {
    window.history.back();
  }
});
