let proceedURLs = new Set();

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ isEnabled: false });
});

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "updateState") {
    chrome.storage.sync.set({ isEnabled: request.state });
  }

  if (request.action === "proceedToURL") {
    // Add the URL to a set of URLs to skip checking
    proceedURLs.add(request.url);
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
    if (!tab.url.startsWith(chrome.runtime.getURL("warning.html"))) {
      if (proceedURLs.has(tab.url)) {
        // Remove the URL from the set after allowing it to proceed once
        proceedURLs.delete(tab.url);
      } else {
        fetch('http://127.0.0.1:5000/check_url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: tab.url })
        })
        .then(response => response.json())
        .then(data => {
          if (data.decision === 'PHISHING') {
            const warningPageUrl = chrome.runtime.getURL("warning.html") + "?url=" + encodeURIComponent(tab.url);
            chrome.tabs.update(tabId, { url: warningPageUrl });
          }
        })
        .catch(error => console.error('Error:', error));
      }
    }
  }
});
