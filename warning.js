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
    if (actualURL) {
      // Inform the background script to skip the next check for this URL
      chrome.runtime.sendMessage({ action: "proceedToURL", url: actualURL });

      // Redirect the user to the actual URL
      window.location.href = actualURL;
    } else {
      console.error('URL parameter is missing');
      // Handle the case where the URL parameter is missing
    }
  }

  function goBack() {
    window.history.back();
  }
});
