chrome.runtime.onInstalled.addListener(() => {
  // Initialize the extension state
  chrome.storage.sync.set({ isEnabled: false });
});

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
      if (request.action === "updateState") {
          // Update the extension state when a message is received
          chrome.storage.sync.set({ isEnabled: request.state });
      }
  }
);

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Existing URL checking functionality
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
      fetch('http://127.0.0.1:5000/check_url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: tab.url })
      })
      .then(response => response.json())
      .then(data => {
          if (data.decision === 'PHISHING') {
              chrome.tabs.update(tabId, { url: "warning.html" });
          }
      })
      .catch(error => console.error('Error:', error));
  }
});
