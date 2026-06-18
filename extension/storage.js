/*
 * storage.js — seed dataset + user-feedback merge for the in-browser KNN.
 *
 * The seed dataset (saved_models/seed_model.json) ships with the extension and
 * is loaded once. User-feedback points accumulate separately in
 * chrome.storage.local ("feedback_points"); at inference time the two are merged
 * so feedback participates in the vote. The frozen scaler from the seed is used
 * to scale both live queries and new feedback points — it is never recomputed.
 *
 * Service-worker global (importScripts). Provides self.NoPhishingStore.
 */
(function (root) {
  "use strict";

  var seedPromise = null;

  // Load + cache the bundled seed model (feature_names, k, scaler, X, y).
  function loadSeed() {
    if (!seedPromise) {
      seedPromise = fetch(chrome.runtime.getURL("saved_models/seed_model.json"))
        .then(function (r) { return r.json(); });
    }
    return seedPromise;
  }

  async function getFeedbackPoints() {
    var data = await chrome.storage.local.get("feedback_points");
    return Array.isArray(data.feedback_points) ? data.feedback_points : [];
  }

  // Append a scaled feedback point {x:[...], y:0|1, ts}. Caller scales with the
  // seed scaler so seed and feedback live in the same space.
  async function addFeedbackPoint(scaledFeatures, label) {
    if (label !== 0 && label !== 1) return;
    var points = await getFeedbackPoints();
    points.push({ x: scaledFeatures, y: label, ts: new Date().toISOString() });
    await chrome.storage.local.set({ feedback_points: points });
  }

  // Merge seed + feedback into parallel X / y arrays for knn.predict.
  async function buildDataset() {
    var seed = await loadSeed();
    var fb = await getFeedbackPoints();
    var X = seed.X.slice();
    var y = seed.y.slice();
    for (var i = 0; i < fb.length; i++) {
      X.push(fb[i].x);
      y.push(fb[i].y);
    }
    return { X: X, y: y, k: seed.k, scaler: seed.scaler, featureNames: seed.feature_names };
  }

  root.NoPhishingStore = {
    loadSeed: loadSeed,
    getFeedbackPoints: getFeedbackPoints,
    addFeedbackPoint: addFeedbackPoint,
    buildDataset: buildDataset,
  };
})(typeof self !== "undefined" ? self : this);
