/*
 * knn.js — K-Nearest-Neighbours inference in pure JavaScript.
 *
 * Mirrors sklearn's KNeighborsClassifier(n_neighbors=3, metric="manhattan") and
 * MinMaxScaler.transform. KNN is instance-based: classification is a majority
 * vote of the nearest seed points, so user-feedback points added in the browser
 * change predictions immediately — no offline retraining, no WASM, no server.
 *
 * Works as a service-worker global (importScripts) and a Node module (tests).
 */
(function (root) {
  "use strict";

  // sklearn MinMaxScaler.transform(x) == x * scale_ + min_  (frozen params).
  function scale(features, scaler) {
    var out = new Array(features.length);
    for (var i = 0; i < features.length; i++) {
      out[i] = features[i] * scaler.scale[i] + scaler.min[i];
    }
    return out;
  }

  function manhattan(a, b) {
    var d = 0;
    for (var i = 0; i < a.length; i++) {
      var diff = a[i] - b[i];
      d += diff < 0 ? -diff : diff;
    }
    return d;
  }

  // Majority vote of the k nearest points. X is an array of scaled vectors,
  // y the parallel array of 0/1 labels. Returns { label, votes, k, ratio }
  // where ratio = votes / k is the fraction of neighbours voting PHISHING —
  // i.e. the model's confidence that the page is phishing (0..1).
  // Ties in distance are broken by original order (stable), matching the
  // "first k after a stable sort by distance" behaviour.
  function predict(queryScaled, X, y, k) {
    var n = X.length;
    var dists = new Array(n);
    for (var i = 0; i < n; i++) {
      dists[i] = { d: manhattan(queryScaled, X[i]), label: y[i], idx: i };
    }
    dists.sort(function (a, b) {
      return a.d - b.d || a.idx - b.idx;
    });
    var kk = Math.min(k, n);
    var phishing = 0;
    for (var j = 0; j < kk; j++) phishing += dists[j].label === 1 ? 1 : 0;
    var label = phishing * 2 > kk ? 1 : 0; // majority for binary labels
    var ratio = kk > 0 ? phishing / kk : 0; // confidence: share voting PHISHING
    return { label: label, votes: phishing, k: kk, ratio: ratio };
  }

  var api = { scale: scale, manhattan: manhattan, predict: predict };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.NoPhishingKNN = api;
  }
})(typeof self !== "undefined" ? self : this);
