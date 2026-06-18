/*
 * features.js — runtime feature extraction for the No Phishing extension (browser build).
 *
 * Produces the 11-feature vector the bundled ONNX model expects, in the exact
 * order of saved_models/browser_features.json:
 *
 *   10 lexical features  — computed here from the URL string alone.
 *    1 content feature   — nb_hyperlinks — passed in by the caller (counted from
 *                          the live page DOM: document.querySelectorAll('a').length).
 *
 * Train/inference parity is guaranteed by construction: the model is retrained on
 * exactly these formulas, and tests verify each one reproduces the training
 * dataset's column values byte-for-byte on an 800-row sample (npm test / Node).
 *
 * Features deliberately NOT computed here, and why:
 *   - domain_age, domain_registration_length (WHOIS) and ratio_extRedirection,
 *     ratio_extErrors (redirect history): impossible client-side.
 *   - ratio_intHyperlinks, ratio_extHyperlinks, safe_anchor, domain_in_title:
 *     low value (~1pt) and carry DOM-definition parity risk.
 *   - shortest_word_host, shortest_word_path, longest_word_path: the dataset
 *     tokenizes words with a public-suffix list (tldextract) + underscore
 *     splitting that JS cannot cheaply match; a naive split feeds the model
 *     wrong values. Dropping all three costs ~0.4pt accuracy — see train_browser.py.
 *
 * Works both as a service-worker global (importScripts) and as a Node module
 * (module.exports) so it can be unit-tested against the Python golden vectors.
 */
(function (root) {
  "use strict";

  // Suspicious tokens commonly found in phishing URLs (Hannousse & Yahiouche).
  var PHISH_HINTS = [
    "wp", "login", "includes", "admin", "content", "site", "images", "js",
    "alibaba", "css", "myaccount", "dropbox", "themes", "plugins", "signin",
    "view",
  ];

  // Ordered list of every feature the model consumes (must match browser_features.json).
  var FEATURE_ORDER = [
    "length_url", "length_hostname", "nb_dots", "nb_hyphens", "nb_qm", "nb_eq",
    "nb_slash", "nb_www", "ratio_digits_url", "phish_hints", "nb_hyperlinks",
  ];

  // Non-overlapping substring count, identical to Python str.count(sub).
  function countSub(s, sub) {
    if (sub.length === 0) return 0;
    return s.split(sub).length - 1;
  }

  function parseParts(url) {
    // Mirror Python urlparse(url).hostname: lower-cased, port stripped, null -> "".
    try {
      var u = new URL(url);
      return { hostname: u.hostname || "" };
    } catch (e) {
      return { hostname: "" };
    }
  }

  // Compute the 10 lexical features from the URL string, in FEATURE_ORDER order.
  function extractLexical(url) {
    url = url || "";
    var p = parseParts(url);
    var low = url.toLowerCase();

    var digits = (url.match(/[0-9]/g) || []).length;
    var hintTotal = 0;
    for (var i = 0; i < PHISH_HINTS.length; i++) hintTotal += countSub(low, PHISH_HINTS[i]);

    return [
      url.length,                                   // length_url
      p.hostname.length,                            // length_hostname
      countSub(url, "."),                           // nb_dots
      countSub(url, "-"),                           // nb_hyphens
      countSub(url, "?"),                           // nb_qm
      countSub(url, "="),                           // nb_eq
      countSub(url, "/"),                           // nb_slash
      countSub(url, "www"),                         // nb_www
      url.length ? digits / url.length : 0,         // ratio_digits_url
      hintTotal,                                    // phish_hints
    ];
  }

  // Full 11-feature vector: 10 lexical + nb_hyperlinks (counted from the page DOM).
  function extractFeatures(url, nbHyperlinks) {
    var v = extractLexical(url);
    v.push(typeof nbHyperlinks === "number" && isFinite(nbHyperlinks) ? nbHyperlinks : 0);
    return v;
  }

  var api = {
    FEATURE_ORDER: FEATURE_ORDER,
    PHISH_HINTS: PHISH_HINTS,
    extractLexical: extractLexical,
    extractFeatures: extractFeatures,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;          // Node (tests)
  } else {
    root.NoPhishingFeatures = api; // service worker / browser global
  }
})(typeof self !== "undefined" ? self : this);
