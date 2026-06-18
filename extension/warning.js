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
    // Trust this domain so future visits aren't re-checked, then navigate.
    // Navigation waits for the ack so the next page load sees the updated list.
    chrome.runtime.sendMessage({ action: "trustDomain", url: actualURL }, function () {
      window.location.href = actualURL;
    });
  }

  function goBack() {
    window.history.back();
  }
});
