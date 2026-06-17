"""
app.py — local inference server for the No Phishing browser extension.

The extension POSTs a URL to /check_url; this server extracts the 22 features
the model expects, scales them with the fitted MinMaxScaler and returns a
PHISHING / LEGITIMATE decision from the KNN classifier.

Artifacts are produced by train.py:
    saved_models/knn_model.pkl
    saved_models/scaler.pkl
    saved_models/feature_names.json
"""

import json
import os

import joblib
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

from libs import features_comp

MODELS_DIR = "saved_models"

with open(os.path.join(MODELS_DIR, "feature_names.json")) as f:
    FEATURE_NAMES = json.load(f)

scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
model = joblib.load(os.path.join(MODELS_DIR, "knn_model.pkl"))

app = Flask(__name__)
CORS(app)


def extract_features(url):
    """Compute the model's feature vector, in the exact training order."""
    values = []
    for name in FEATURE_NAMES:
        result = getattr(features_comp, name)(url)
        if result is True:
            result = 1
        elif result is False or result is None:
            result = 0
        values.append(float(result))
    return np.array(values).reshape(1, -1)


def classify(url):
    features = extract_features(url)
    scaled = scaler.transform(features)
    prediction = int(model.predict(scaled)[0])
    return "PHISHING" if prediction == 1 else "LEGITIMATE"


@app.route("/check_url", methods=["POST"])
def check_url():
    url = request.json["url"]

    # Browser-internal pages have no meaningful features to score.
    if url.startswith("chrome://") or url == "about:blank":
        return jsonify({"decision": "LEGITIMATE"})

    return jsonify({"decision": classify(url)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5030))
    app.run(host="0.0.0.0", port=port)
