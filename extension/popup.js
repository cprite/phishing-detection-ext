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

  // --- Self-learning feedback (OSS build only) -----------------------------
  if (typeof IS_OSS_BUILD !== 'undefined' && IS_OSS_BUILD) {
    const ossSection = document.getElementById('ossSection');
    const markBtn = document.getElementById('markPhishingBtn');
    const exportBtn = document.getElementById('exportBtn');
    const status = document.getElementById('feedbackStatus');
    ossSection.style.display = 'block';

    function setStatus(text) {
      status.textContent = text;
      if (text) setTimeout(function() { status.textContent = ''; }, 4000);
    }

    // Mark the active tab's URL as phishing (a missed detection).
    markBtn.addEventListener('click', function() {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const url = tabs && tabs[0] && tabs[0].url;
        if (!url || /^chrome/.test(url) || url.startsWith(chrome.runtime.getURL(''))) {
          setStatus('Cannot mark this page.');
          return;
        }
        chrome.runtime.sendMessage(
          { action: 'recordFeedback', url: url, label: 'phishing' },
          function() { setStatus('Marked as phishing. Thanks!'); }
        );
      });
    });

    // Export accumulated feedback to a JSON file for retrain_from_feedback.py.
    exportBtn.addEventListener('click', function() {
      chrome.storage.local.get('feedback', function(data) {
        const fb = Array.isArray(data.feedback) ? data.feedback : [];
        if (!fb.length) { setStatus('No feedback collected yet.'); return; }
        const blob = new Blob([JSON.stringify(fb, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'phishing-feedback.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        setStatus(fb.length + ' item(s) exported.');
      });
    });
  }
});
