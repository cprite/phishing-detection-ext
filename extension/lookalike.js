/*
 * lookalike.js — heuristic brand-impersonation / lookalike-domain detector.
 *
 * Runs alongside the lexical KNN (knn.js), which has a documented blind spot on
 * short, clean-looking phishing that impersonates a brand. This module adds four
 * deterministic detectors and returns a verdict background.js can act on:
 *
 *   1. Subdomain / hyphen brand injection — a brand name as a token of the
 *      subdomain or registrable label of an UNRELATED domain:
 *      apple.account-secure.com, paypal.login-now.net, secure-paypal.example.com,
 *      and (legacy) brand-bearing *.vercel.app / *.now.sh preview deploys.
 *   2. Homoglyph swaps — 0↔o, 1↔l/i, rn↔m, vv↔w: paypa1.com, m1crosoft.com,
 *      rnicrosoft.com, vvhatsapp.com.
 *   3. Typosquat — Damerau-Levenshtein distance 1..2 between the registrable
 *      label and a brand: paypai.com, microsfot.com.
 *   4. TLD spoofing — exact brand label on a non-official TLD: paypal.net,
 *      netflix.org (official: paypal.com, netflix.com).
 *
 * Confidence / action:
 *   - subdomain brand injection ...... 95%  → force PHISHING
 *   - homoglyph or typosquat (1 edit) . 90%  → force PHISHING
 *   - typosquat (2 edits) ............. 80%  → suspect only (may be legit, no block)
 *   - TLD spoofing .................... 80%  → suspect only (ccTLD ambiguity)
 *
 * False-positive guards: a whitelist of legitimate registrable domains (the real
 * brand sites and their common ccTLD variants) short-circuits to "no hit", so the
 * genuine sites and their subdomains are never flagged; brand tokens are matched
 * on label/hyphen boundaries (not raw substrings), so "startups" never matches
 * "ups"; typosquat only runs for brands >= 5 chars with a comparable length.
 *
 * NOTE: registrable-domain parsing uses a small built-in multi-part-suffix list,
 * not the full Public Suffix List — good enough for a heuristic, may mis-split
 * rare ccTLDs. Works as a service-worker global (importScripts) and a Node module.
 */
(function (root) {
  "use strict";

  // Vercel-branded deploy domains (kept for the original Vercel-specific rule).
  var VERCEL_SUFFIXES = ["vercel.app", "now.sh"];

  // Brands worth typosquat/homoglyph/TLD matching, each with its legitimate
  // registrable domain(s). Generic short words (gov, bank, ups) are deliberately
  // excluded from this set — too collision-prone for fuzzy matching.
  var BRANDS = [
    { sld: "paypal", domains: ["paypal.com"] },
    { sld: "microsoft", domains: ["microsoft.com"] },
    { sld: "office365", domains: ["office365.com", "office.com"] },
    { sld: "outlook", domains: ["outlook.com", "live.com"] },
    { sld: "apple", domains: ["apple.com"] },
    { sld: "icloud", domains: ["icloud.com"] },
    { sld: "google", domains: ["google.com", "google.co.uk"] },
    { sld: "gmail", domains: ["gmail.com"] },
    { sld: "amazon", domains: ["amazon.com", "amazon.co.uk", "amazon.de"] },
    { sld: "netflix", domains: ["netflix.com"] },
    { sld: "facebook", domains: ["facebook.com"] },
    { sld: "instagram", domains: ["instagram.com"] },
    { sld: "whatsapp", domains: ["whatsapp.com"] },
    { sld: "messenger", domains: ["messenger.com"] },
    { sld: "roblox", domains: ["roblox.com"] },
    { sld: "steam", domains: ["steampowered.com", "steamcommunity.com"] },
    { sld: "discord", domains: ["discord.com", "discord.gg"] },
    { sld: "telegram", domains: ["telegram.org"] },
    { sld: "twitter", domains: ["twitter.com", "x.com"] },
    { sld: "linkedin", domains: ["linkedin.com"] },
    { sld: "coinbase", domains: ["coinbase.com"] },
    { sld: "binance", domains: ["binance.com"] },
    { sld: "kraken", domains: ["kraken.com"] },
    { sld: "metamask", domains: ["metamask.io"] },
    { sld: "trezor", domains: ["trezor.io"] },
    { sld: "ledger", domains: ["ledger.com"] },
    { sld: "blockchain", domains: ["blockchain.com"] },
    { sld: "dropbox", domains: ["dropbox.com"] },
    { sld: "docusign", domains: ["docusign.com"] },
    { sld: "ebay", domains: ["ebay.com", "ebay.co.uk"] },
    { sld: "dhl", domains: ["dhl.com"] },
    { sld: "fedex", domains: ["fedex.com"] },
    { sld: "usps", domains: ["usps.com"] },
    { sld: "hmrc", domains: ["hmrc.gov.uk"] },
    { sld: "santander", domains: ["santander.com", "santander.co.uk"] },
    { sld: "barclays", domains: ["barclays.co.uk"] },
    { sld: "lloyds", domains: ["lloydsbank.com"] },
    { sld: "revolut", domains: ["revolut.com"] },
    { sld: "monzo", domains: ["monzo.com"] },
    { sld: "wise", domains: ["wise.com"] },
    { sld: "vodafone", domains: ["vodafone.com", "vodafone.co.uk"] },
    { sld: "natwest", domains: ["natwest.com"] },
    { sld: "halifax", domains: ["halifax.co.uk"] },
    { sld: "nubank", domains: ["nubank.com.br"] },
    { sld: "chase", domains: ["chase.com"] },
    { sld: "wellsfargo", domains: ["wellsfargo.com"] },
    { sld: "bankofamerica", domains: ["bankofamerica.com"] },
  ];

  // Fast lookups derived from BRANDS.
  var BRAND_SLDS = {};       // sld -> brand
  var LEGIT_DOMAINS = {};    // registrable domain -> true (never flag these)
  for (var bi = 0; bi < BRANDS.length; bi++) {
    BRAND_SLDS[BRANDS[bi].sld] = BRANDS[bi];
    for (var di = 0; di < BRANDS[bi].domains.length; di++) {
      LEGIT_DOMAINS[BRANDS[bi].domains[di]] = true;
    }
  }
  // A few popular non-brand domains that visit often, kept off the radar so a
  // coincidental fuzzy match never warns on them.
  ["github.com", "gov.uk", "wikipedia.org", "cloudflare.com", "bbc.co.uk",
   "stackoverflow.com"].forEach(function (d) { LEGIT_DOMAINS[d] = true; });

  // Generic government / finance tokens that are too collision-prone for the
  // GENERAL detector (would flag gov.uk) but safe in the Vercel-host rule, since
  // gov.uk etc. are never *.vercel.app deploys. Used only by checkVercel().
  var VERCEL_EXTRA_TOKENS = ["gov", "bank", "irs", "hmrc", "ups", "dpd", "post"];

  // Credential-harvest keywords (used only for the Vercel-host rule, where a
  // generic keyword is meaningful; firing on any domain would over-trigger).
  var HINTS = [
    "login", "signin", "verify", "verification", "secure", "account", "update",
    "recover", "unlock", "wallet", "support", "billing", "confirm", "webscr",
    "giris", "connexion", "anmelden", "clone",
  ];

  // Common multi-part public suffixes (subset of the PSL — heuristic).
  var MULTI_SUFFIX = {
    "co.uk": 1, "org.uk": 1, "gov.uk": 1, "ac.uk": 1, "me.uk": 1, "co.jp": 1,
    "com.au": 1, "net.au": 1, "org.au": 1, "com.br": 1, "com.mx": 1, "com.tr": 1,
    "co.nz": 1, "co.za": 1, "co.in": 1, "com.sg": 1, "com.hk": 1, "com.cn": 1,
  };

  function hostnameOf(url) {
    try {
      return (new URL(url).hostname || "").toLowerCase();
    } catch (e) {
      return "";
    }
  }

  // Split host into { sub: [labels...], registrable: "sld.suffix", sld: "sld" }.
  function parseHost(host) {
    var parts = host.split(".").filter(Boolean);
    if (parts.length < 2) return { sub: [], registrable: host, sld: host };
    var lastTwo = parts.slice(-2).join(".");
    var suffixLen = MULTI_SUFFIX[lastTwo] && parts.length >= 3 ? 3 : 2;
    var regParts = parts.slice(-suffixLen);
    return {
      sub: parts.slice(0, parts.length - suffixLen),
      registrable: regParts.join("."),
      sld: regParts[0],
    };
  }

  // Confusable skeleton: collapse homoglyph classes so paypa1 -> paypal, etc.
  function skeleton(s) {
    s = s.replace(/rn/g, "m").replace(/vv/g, "w");
    var out = "";
    for (var i = 0; i < s.length; i++) {
      var c = s[i];
      if (c === "0") c = "o";
      else if (c === "1" || c === "i") c = "l";
      else if (c === "5") c = "s";
      out += c;
    }
    return out;
  }

  // Optimal String Alignment distance (Damerau-Levenshtein with adjacent
  // transpositions). Returns an int; caller compares against a threshold.
  function osaDistance(a, b) {
    var n = a.length, m = b.length;
    if (!n) return m;
    if (!m) return n;
    var prev = new Array(m + 1), cur = new Array(m + 1), tmp;
    var prevPrev = new Array(m + 1);
    for (var j = 0; j <= m; j++) prev[j] = j;
    for (var i = 1; i <= n; i++) {
      cur[0] = i;
      for (var k = 1; k <= m; k++) {
        var cost = a[i - 1] === b[k - 1] ? 0 : 1;
        cur[k] = Math.min(prev[k] + 1, cur[k - 1] + 1, prev[k - 1] + cost);
        if (i > 1 && k > 1 && a[i - 1] === b[k - 2] && a[i - 2] === b[k - 1]) {
          cur[k] = Math.min(cur[k], prevPrev[k - 2] + 1);
        }
      }
      tmp = prevPrev; prevPrev = prev; prev = cur; cur = tmp;
    }
    return prev[m];
  }

  // The original Vercel-specific rule: brand substring OR keyword on a Vercel
  // deploy host. Kept verbatim in behaviour so the shipped 92% sample doesn't
  // regress. Returns a verdict or null.
  function checkVercel(host) {
    var sub = null;
    for (var i = 0; i < VERCEL_SUFFIXES.length; i++) {
      var suf = VERCEL_SUFFIXES[i];
      if (host === suf) return null;
      if (host.length > suf.length + 1 && host.slice(-(suf.length + 1)) === "." + suf) {
        sub = host.slice(0, host.length - suf.length - 1);
        break;
      }
    }
    if (sub === null) return null;
    var labels = sub.split(/[-_.]/).filter(Boolean);
    var flat = labels.join("");
    for (var b = 0; b < BRANDS.length; b++) {
      var name = BRANDS[b].sld;
      var hit = name.length >= 5 ? flat.indexOf(name) !== -1 : labels.indexOf(name) !== -1;
      if (hit) {
        return verdict(true, false, 95, name, "injection",
          "Vercel deploy host impersonating “" + name + "”");
      }
    }
    for (var e = 0; e < VERCEL_EXTRA_TOKENS.length; e++) {
      if (labels.indexOf(VERCEL_EXTRA_TOKENS[e]) !== -1) {
        return verdict(true, false, 95, VERCEL_EXTRA_TOKENS[e], "injection",
          "Vercel deploy host impersonating “" + VERCEL_EXTRA_TOKENS[e] + "”");
      }
    }
    for (var h = 0; h < HINTS.length; h++) {
      if (flat.indexOf(HINTS[h]) !== -1 || labels.indexOf(HINTS[h]) !== -1) {
        return verdict(true, false, 95, null, "keyword",
          "Vercel deploy host with phishing keyword “" + HINTS[h] + "”");
      }
    }
    return null;
  }

  function verdict(hit, suspect, confidence, brand, kind, reason) {
    return { hit: hit, suspect: suspect, confidence: confidence,
             brand: brand, kind: kind, reason: reason };
  }
  function miss(host) {
    return { hit: false, suspect: false, confidence: 0, brand: null,
             kind: null, reason: "", host: host };
  }

  function check(url) {
    var host = hostnameOf(url);
    if (!host) return miss(host);

    // 1) Original Vercel rule first (most specific).
    var v = checkVercel(host);
    if (v) { v.host = host; return v; }

    var p = parseHost(host);

    // Never flag the genuine brand sites or known-popular domains (any subdomain).
    if (LEGIT_DOMAINS[p.registrable]) return miss(host);

    // 2) Brand injection — a brand as a whole hyphen/dot-delimited token of the
    //    subdomain, OR one token among several in the registrable label
    //    (paypal-login.com). A registrable label that is EXACTLY the brand
    //    (paypal.net) is NOT injection — that is TLD spoofing, handled below as
    //    a softer "suspect" signal.
    var tokens = [];
    for (var s = 0; s < p.sub.length; s++) {
      if (p.sub[s] === "www") continue;
      tokens = tokens.concat(p.sub[s].split(/[-_]/));
    }
    var sldTokens = p.sld.split(/[-_]/);
    if (sldTokens.length > 1) tokens = tokens.concat(sldTokens); // "secure-paypal" -> [secure, paypal]
    for (var t = 0; t < tokens.length; t++) {
      if (BRAND_SLDS[tokens[t]]) {
        var nm = tokens[t];
        var r = verdict(true, false, 95, nm, "injection",
          "Brand “" + nm + "” injected into unrelated domain “" + p.registrable + "”");
        r.host = host; return r;
      }
    }

    // The remaining detectors compare the registrable label (sld) to each brand.
    var skel = skeleton(p.sld);
    var bestSuspect = null;
    for (var bb = 0; bb < BRANDS.length; bb++) {
      var brand = BRANDS[bb];
      if (brand.sld.length < 5) continue;            // fuzzy match long brands only
      if (p.sld === brand.sld) {
        // 4) TLD spoofing — exact brand label, but registrable not official.
        var rt = verdict(false, true, 80, brand.sld, "tld-spoof",
          "Domain “" + p.registrable + "” uses the brand “" + brand.sld +
          "” on a non-official TLD (official: " + brand.domains[0] + ")");
        rt.host = host; return rt;
      }
      // 3a) Homoglyph — same confusable skeleton, different raw label.
      if (skel === skeleton(brand.sld)) {
        var rh = verdict(true, false, 90, brand.sld, "homoglyph",
          "Domain “" + p.registrable + "” appears to be a homoglyph of “" +
          brand.domains[0] + "”");
        rh.host = host; return rh;
      }
      // 3b) Typosquat — Damerau-Levenshtein 1..2, comparable length.
      if (Math.abs(p.sld.length - brand.sld.length) <= 2) {
        var d = osaDistance(p.sld, brand.sld);
        if (d === 1) {
          var r1 = verdict(true, false, 90, brand.sld, "typosquat",
            "Domain “" + p.registrable + "” appears to be a typosquat of “" +
            brand.domains[0] + "”");
          r1.host = host; return r1;
        }
        if (d === 2 && !bestSuspect) {
          bestSuspect = verdict(false, true, 80, brand.sld, "typosquat",
            "Domain “" + p.registrable + "” may be a typosquat of “" +
            brand.domains[0] + "”");
        }
      }
    }
    if (bestSuspect) { bestSuspect.host = host; return bestSuspect; }
    return miss(host);
  }

  var api = {
    VERCEL_SUFFIXES: VERCEL_SUFFIXES,
    BRANDS: BRANDS,
    HINTS: HINTS,
    parseHost: parseHost,
    skeleton: skeleton,
    osaDistance: osaDistance,
    check: check,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.NoPhishingLookalike = api;
  }
})(typeof self !== "undefined" ? self : this);
