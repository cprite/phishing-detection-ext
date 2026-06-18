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
    const status = document.getElementById('feedbackStatus');
    ossSection.style.display = 'block';

    function setStatus(text) {
      status.textContent = text;
      if (text) setTimeout(function() { status.textContent = ''; }, 4000);
    }

    // Model stats: show the user that the in-browser model is improving.
    function renderStats() {
      chrome.runtime.sendMessage({ action: 'getStats' }, function(s) {
        if (!s) return;
        document.getElementById('statUpdated').textContent =
          s.lastUpdated ? new Date(s.lastUpdated).toLocaleString() : '—';
        document.getElementById('statCount').textContent = s.feedbackCount + ' added';
        document.getElementById('statAcc').textContent =
          s.accuracy === null ? '—' : Math.round(s.accuracy * 100) + '%';
      });
    }
    renderStats();

    // Mark the active tab as phishing (a missed detection). The service worker
    // scores the live page and adds a phishing point to the KNN dataset.
    markBtn.addEventListener('click', function() {
      markBtn.disabled = true;
      chrome.runtime.sendMessage({ action: 'markPhishing' }, function(resp) {
        markBtn.disabled = false;
        setStatus(resp && resp.ok ? 'Marked as phishing. Thanks!' : 'Cannot mark this page.');
        if (resp && resp.ok) renderStats(); // refresh after a new point
      });
    });
  }
});
