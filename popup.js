document.addEventListener('DOMContentLoaded', function() {
  const toggleSwitch = document.getElementById('toggleSwitch');

  // Update switch appearance based on the extension state
  function updateSwitch(isEnabled) {
    toggleSwitch.checked = isEnabled;
  }

  // Retrieve the current state of the extension from Chrome storage
  chrome.storage.sync.get('isEnabled', function(data) {
    const isEnabled = data.isEnabled !== undefined ? data.isEnabled : false;
    updateSwitch(isEnabled);
  });

  // Send the updated state to the background script
  toggleSwitch.addEventListener('change', function() {
    const isEnabled = this.checked;
    // Send message to background script to update the state
    chrome.runtime.sendMessage({ action: "updateState", state: isEnabled });
  });
});
