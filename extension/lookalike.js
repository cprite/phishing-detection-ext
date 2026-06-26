/*
 * lookalike.js — heuristic detector for brand-impersonation phishing hosted on
 * Vercel deploy domains.
 *
 * The KNN classifier (knn.js) is lexical + DOM and has a documented blind spot:
 * short, clean-looking URLs on reputable free hosting score as LEGITIMATE even
 * when the subdomain impersonates a brand. Vercel's preview/production deploys
 * (`<project>.vercel.app`, `<project>-<hash>-<scope>.vercel.app`, and the legacy
 * `*.now.sh`) are abused for phishing and typosquatting because anyone can ship
 * a page on a *.vercel.app host in seconds — e.g.
 *   messenger-clone-delta-two.vercel.app, toki-gov-tr-17.vercel.app,
 *   talk-messenger.vercel.app, en-startrezor (trezor) lookalikes.
 *
 * A genuine company serves its product on its own custom domain, not on a
 * *.vercel.app subdomain that carries a well-known brand name or a login/verify
 * keyword. So "Vercel deploy host whose label impersonates a brand" is a strong
 * phishing signal the lexical model misses. This module returns that signal so
 * background.js can override a LEGITIMATE verdict to PHISHING for these hosts.
 *
 * Works as a service-worker global (importScripts) and a Node module (tests).
 */
(function (root) {
  "use strict";

  // Vercel-branded deploy domains. A custom domain (e.g. acme.com) is NOT here:
  // we only treat the free, self-service *.vercel.app / *.now.sh hosts as risky,
  // since those are what phishers spin up. Match is on a label boundary so
  // `notvercel.app` or `myvercel.app.evil.com` do not count.
  var VERCEL_SUFFIXES = ["vercel.app", "now.sh"];

  // Brands commonly impersonated in phishing. Brands >= 5 chars are matched as a
  // substring of the (de-hyphenated) subdomain so typosquats like "startrezor"
  // (trezor) and "talk-messenger" (messenger) are caught; shorter, ambiguous
  // brands are matched only as a whole hyphen/dot-delimited label to avoid false
  // hits (e.g. "ups" inside "startups", "gov" inside "governance").
  var BRANDS = [
    "paypal", "microsoft", "office365", "outlook", "apple", "icloud", "google",
    "gmail", "amazon", "netflix", "facebook", "instagram", "whatsapp",
    "messenger", "roblox", "steam", "discord", "telegram", "twitter", "linkedin",
    "coinbase", "binance", "kraken", "metamask", "trezor", "ledger", "blockchain",
    "dropbox", "docusign", "ebay", "dhl", "fedex", "usps", "hmrc", "irs",
    "santander", "barclays", "lloyds", "revolut", "monzo", "wise", "vodafone",
    "bankofamerica", "wellsfargo", "chase", "natwest", "halifax", "nubank",
    "ups", "gov", "bank",
  ];

  // Impersonation / credential-harvest keywords. A legit Vercel preview is rarely
  // named "secure-login-verify"; on a Vercel host these strongly imply phishing.
  // "giris" (tr), "connexion" (fr), "anmelden" (de) cover non-English login pages.
  var HINTS = [
    "login", "signin", "log-in", "sign-in", "verify", "verification", "secure",
    "account", "update", "recover", "unlock", "wallet", "support", "billing",
    "confirm", "webscr", "giris", "connexion", "anmelden", "clone",
  ];

  function hostnameOf(url) {
    try {
      return (new URL(url).hostname || "").toLowerCase();
    } catch (e) {
      return "";
    }
  }

  // If host is on a Vercel deploy domain, return the subdomain part (everything
  // before the matched suffix); otherwise null. "msg.vercel.app" -> "msg",
  // "vercel.app" (apex) -> "" (no subdomain, not a deploy), "x.now.sh" -> "x".
  function vercelSubdomain(host) {
    for (var i = 0; i < VERCEL_SUFFIXES.length; i++) {
      var suf = VERCEL_SUFFIXES[i];
      if (host === suf) return ""; // apex, no project label
      if (host.length > suf.length + 1 && host.slice(-(suf.length + 1)) === "." + suf) {
        return host.slice(0, host.length - suf.length - 1);
      }
    }
    return null;
  }

  // Returns { hit, host, brand, keyword, reason }.
  function check(url) {
    var host = hostnameOf(url);
    var miss = { hit: false, host: host, brand: null, keyword: null, reason: "" };
    if (!host) return miss;

    var sub = vercelSubdomain(host);
    if (!sub) return miss; // not a Vercel deploy host (or bare apex)

    var labels = sub.split(/[-_.]/).filter(Boolean);
    var flat = labels.join(""); // de-hyphenated, for substring brand match

    // Brand impersonation.
    for (var i = 0; i < BRANDS.length; i++) {
      var b = BRANDS[i];
      var matched =
        b.length >= 5 ? flat.indexOf(b) !== -1 : labels.indexOf(b) !== -1;
      if (matched) {
        return {
          hit: true, host: host, brand: b, keyword: null,
          reason: "Vercel deploy host impersonating “" + b + "”",
        };
      }
    }

    // Credential-harvest keyword on a Vercel host.
    for (var j = 0; j < HINTS.length; j++) {
      var h = HINTS[j];
      if (flat.indexOf(h.replace(/-/g, "")) !== -1 || labels.indexOf(h) !== -1) {
        return {
          hit: true, host: host, brand: null, keyword: h,
          reason: "Vercel deploy host with phishing keyword “" + h + "”",
        };
      }
    }

    return miss;
  }

  var api = {
    VERCEL_SUFFIXES: VERCEL_SUFFIXES,
    BRANDS: BRANDS,
    HINTS: HINTS,
    vercelSubdomain: vercelSubdomain,
    check: check,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.NoPhishingLookalike = api;
  }
})(typeof self !== "undefined" ? self : this);
