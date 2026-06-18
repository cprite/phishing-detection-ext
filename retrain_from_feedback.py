"""
retrain_from_feedback.py — fold in-browser feedback into the model (OSS build).

This is step 2 of the self-learning loop. The extension's open-source build
collects user corrections in chrome.storage.local and exports them to JSON via
the popup's "Export feedback" button:

    [{"url": "...", "label": "phishing" | "legitimate", "ts": "..."}, ...]

This script computes the 11 browser features for each feedback URL, appends the
examples to the training data (up-weighted so a handful of corrections actually
move the model), retrains the Gradient Boosting pipeline and re-exports
saved_models/model.onnx. Reload the unpacked extension afterwards.

The 10 lexical features are computed here with the exact formulas used in
extension/features.js. nb_hyperlinks is fetched from the live page (best effort;
falls back to 0 if the page can't be retrieved or BeautifulSoup isn't installed).

Usage:
    python retrain_from_feedback.py phishing-feedback.json [--weight 50]
"""

import argparse
import json
import os
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

from train_browser import BROWSER_FEATURES, DATASET, MODELS_DIR

# Same suspicious tokens as extension/features.js (Hannousse & Yahiouche).
PHISH_HINTS = [
    "wp", "login", "includes", "admin", "content", "site", "images", "js",
    "alibaba", "css", "myaccount", "dropbox", "themes", "plugins", "signin",
    "view",
]


def lexical_features(url):
    """The 10 lexical features, mirroring extension/features.js exactly."""
    host = urlparse(url).hostname or ""
    low = url.lower()
    digits = sum(c.isdigit() for c in url)
    hints = sum(low.count(h) for h in PHISH_HINTS)
    return {
        "length_url": len(url),
        "length_hostname": len(host),
        "nb_dots": url.count("."),
        "nb_hyphens": url.count("-"),
        "nb_qm": url.count("?"),
        "nb_eq": url.count("="),
        "nb_slash": url.count("/"),
        "nb_www": url.count("www"),
        "ratio_digits_url": digits / len(url) if url else 0,
        "phish_hints": hints,
    }


def fetch_nb_hyperlinks(url):
    """Count <a> tags on the live page. Best effort: 0 on any failure."""
    try:
        import requests
        from bs4 import BeautifulSoup
        html = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"}).text
        return len(BeautifulSoup(html, "html.parser").find_all("a"))
    except Exception:
        return 0


def feature_row(url):
    feat = lexical_features(url)
    feat["nb_hyperlinks"] = fetch_nb_hyperlinks(url)
    return [feat[c] for c in BROWSER_FEATURES]


def load_base():
    data = pd.read_csv(DATASET)
    data.dropna(inplace=True)
    data.drop(data[data["domain_age"] <= -1].index, inplace=True)
    data["status"] = data["status"].map({"legitimate": 0, "phishing": 1})
    X = data[BROWSER_FEATURES].values.astype(np.float32)
    y = data["status"].values
    return X, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("feedback", help="feedback JSON exported from the extension popup")
    ap.add_argument("--weight", type=float, default=50.0,
                    help="weight of each feedback example vs a base row (default 50)")
    args = ap.parse_args()

    with open(args.feedback) as f:
        feedback = json.load(f)

    X_base, y_base = load_base()

    # Honest accuracy estimate: hold out a base test split, train on the rest +
    # all feedback, evaluate on the untouched base test split.
    Xb_tr, Xb_te, yb_tr, yb_te = train_test_split(
        X_base, y_base, test_size=0.2, random_state=42, stratify=y_base
    )

    rows, labels = [], []
    skipped = 0
    for fb in feedback:
        url, label = fb.get("url"), fb.get("label")
        if not url or label not in ("phishing", "legitimate"):
            skipped += 1
            continue
        rows.append(feature_row(url))
        labels.append(1 if label == "phishing" else 0)

    n_fb = len(rows)
    print(f"Feedback examples folded in: {n_fb} (skipped {skipped} malformed)")
    if n_fb == 0:
        print("Nothing to fold in — aborting without touching the model.")
        return

    X_fb = np.array(rows, dtype=np.float32)
    y_fb = np.array(labels)

    X_train = np.vstack([Xb_tr, X_fb])
    y_train = np.concatenate([yb_tr, y_fb])
    weights = np.concatenate([np.ones(len(Xb_tr)), np.full(n_fb, args.weight)])

    # Same pipeline/params as train_browser.py.
    pipe = Pipeline([
        ("scaler", MinMaxScaler()),
        ("clf", GradientBoostingClassifier(
            random_state=42, n_estimators=300, max_depth=4, learning_rate=0.1)),
    ]).fit(X_train, y_train, clf__sample_weight=weights)

    acc = accuracy_score(yb_te, pipe.predict(Xb_te))
    print(f"Accuracy on held-out base test set: {acc:.4f} "
          f"(feedback up-weighted x{args.weight:g})")

    # --- Export to ONNX (scaler + classifier fused) ------------------------
    onnx_model = convert_sklearn(
        pipe,
        initial_types=[("X", FloatTensorType([None, len(BROWSER_FEATURES)]))],
        options={id(pipe): {"zipmap": False}},
        target_opset=15,
    )
    os.makedirs(MODELS_DIR, exist_ok=True)
    onnx_path = os.path.join(MODELS_DIR, "model.onnx")
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    sess = rt.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    onnx_pred = sess.run(None, {"X": Xb_te})[0].ravel()
    parity = float(np.mean(onnx_pred == pipe.predict(Xb_te)))
    print(f"ONNX vs sklearn parity: {parity:.4%}")
    print(f"\nWrote {onnx_path} ({os.path.getsize(onnx_path)} bytes). "
          f"Reload the unpacked extension to use the updated model.")


if __name__ == "__main__":
    main()
