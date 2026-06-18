document.addEventListener('DOMContentLoaded', function() {
  const proceedBtn = document.getElementById('proceedBtn');
  const goBackBtn = document.getElementById('goBackBtn');

  proceedBtn.addEventListener('click', proceedToURL);
  goBackBtn.addEventListener('click', goBack);

  function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }

  // Show the KNN confidence (share of nearest neighbours voting phishing).
  // Higher percentage = more dangerous.
  function showConfidence() {
    const el = document.getElementById('confidence');
    if (!el) return;
    const raw = getQueryParam('conf');
    if (raw === null) return;
    const pct = Math.max(0, Math.min(100, Math.round(Number(raw))));
    if (!Number.isFinite(pct)) return;
    el.textContent = '⚠️ This site is likely phishing (confidence: ' + pct + '%)';
    el.hidden = false;
  }
  showConfidence();

  function proceedToURL() {
    const actualURL = getQueryParam('url');
    if (!actualURL) {
      console.error('URL parameter is missing');
      return;
    }
    // Proceeding means the user judges this page legitimate (a false positive).
    // Trust the domain so future visits aren't re-checked, and — in the OSS
    // build — add a legitimate feedback point so the in-browser KNN learns from
    // it. Navigate only after the writes are acked so the next load sees them.
    chrome.runtime.sendMessage({ action: "trustDomain", url: actualURL }, function () {
      if (typeof IS_OSS_BUILD !== "undefined" && IS_OSS_BUILD) {
        chrome.runtime.sendMessage(
          { action: "addLegitimate", url: actualURL },
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
