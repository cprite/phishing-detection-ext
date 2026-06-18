document.addEventListener('DOMContentLoaded', function() {
  const toggleSwitch = document.getElementById('toggleSwitch');

  // --- Enable/disable toggle -----------------------------------------------
  chrome.storage.sync.get('isEnabled', function(data) {
    toggleSwitch.checked = data.isEnabled !== undefined ? data.isEnabled : false;
  });

  toggleSwitch.addEventListener('change', function() {
    chrome.runtime.sendMessage({ action: "updateState", state: this.checked });
  });

  // --- Trusted sites list --------------------------------------------------
  const list = document.getElementById('trustedList');
  const empty = document.getElementById('trustedEmpty');

  function renderTrusted() {
    chrome.storage.local.get('trusted_domains', function(data) {
      const domains = Array.isArray(data.trusted_domains) ? data.trusted_domains : [];
      list.innerHTML = '';
      empty.style.display = domains.length ? 'none' : 'block';

      domains.forEach(function(host) {
        const li = document.createElement('li');

        const span = document.createElement('span');
        span.className = 'host';
        span.textContent = host;
        span.title = host;

        const btn = document.createElement('button');
        btn.className = 'remove';
        btn.textContent = '✕'; // ✕
        btn.title = 'Remove ' + host;
        btn.addEventListener('click', function() { removeTrusted(host); });

        li.appendChild(span);
        li.appendChild(btn);
        list.appendChild(li);
      });
    });
  }

  function removeTrusted(host) {
    chrome.storage.local.get('trusted_domains', function(data) {
      const domains = (Array.isArray(data.trusted_domains) ? data.trusted_domains : [])
        .filter(function(d) { return d !== host; });
      chrome.storage.local.set({ trusted_domains: domains }, renderTrusted);
    });
  }

  renderTrusted();
});
