"""
export_model.py — export the KNN seed dataset for the in-browser classifier.

The extension runs K-Nearest-Neighbours entirely in JavaScript (knn.js). KNN is
instance-based, so "the model" is just the scaled training points plus their
labels and the frozen scaler parameters. This script fits the MinMaxScaler on
the training split, scales the training points and writes everything the browser
needs to saved_models/seed_model.json:

    {
      "feature_names": [...11...],
      "k": 3, "metric": "manhattan",
      "scaler": { "min": [...11...], "scale": [...11...] },   # x*scale + min
      "X": [[...11 scaled...], ...],                          # seed points
      "y": [0|1, ...]                                         # labels
    }

It also writes a separate hold-out test set to saved_models/seed_test.json
({"X": [...scaled...], "y": [...]}). Those points are NEVER added to the KNN
dataset — the extension scores them after every feedback addition to report an
unbiased "Accuracy (on held-out test set)" in the popup. The test set is a
stratified sample capped at TEST_SAMPLE_SIZE so the bundle stays small and the
in-browser scoring stays fast.

Because KNN classifies by majority vote of the nearest points, new user-feedback
points added in the browser participate immediately — that is the in-browser
"retraining". The scaler is frozen here and never recomputed.

Feature set (11): the parity-safe browser features — see train history / README.
The 10 lexical features mirror extension/features.js exactly; nb_hyperlinks is
the page link count.

Dataset (not committed — see README): Hannousse & Yahiouche, expected at
    raw_data/dataset_phishing.csv

Run:  python export_model.py
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler

DATASET = os.path.join("raw_data", "dataset_phishing.csv")
MODELS_DIR = "saved_models"

# Parity-safe browser features (10 lexical + nb_hyperlinks), in features.js order.
BROWSER_FEATURES = [
    "length_url", "length_hostname", "nb_dots", "nb_hyphens", "nb_qm", "nb_eq",
    "nb_slash", "nb_www", "ratio_digits_url", "phish_hints", "nb_hyperlinks",
]

K = 3
METRIC = "manhattan"

# The held-out test set ships in the bundle and is scored in-browser on every
# feedback addition, so cap it: a stratified sample keeps the bundle small and
# KNN scoring fast while staying a statistically sound accuracy estimate.
TEST_SAMPLE_SIZE = 1000


def main():
    data = pd.read_csv(DATASET)
    data.dropna(inplace=True)
    data.drop(data[data["domain_age"] <= -1].index, inplace=True)
    data["status"] = data["status"].map({"legitimate": 0, "phishing": 1})

    X = data[BROWSER_FEATURES].values.astype(np.float64)
    y = data["status"].values
    print(f"Rows after cleaning: {len(data)} "
          f"(phishing={int(y.sum())}, legitimate={int((y == 0).sum())})")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = MinMaxScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Honest accuracy estimate for the exact JS algorithm (k=3, manhattan).
    knn = KNeighborsClassifier(n_neighbors=K, metric=METRIC).fit(X_train_s, y_train)
    pred = knn.predict(X_test_s)
    print(f"KNN(k={K}, {METRIC}) on {len(BROWSER_FEATURES)} features:")
    print(f"  test accuracy:  {accuracy_score(y_test, pred):.4f}")
    print(f"  precision (ph): {precision_score(y_test, pred):.4f}")
    print(f"  recall (ph):    {recall_score(y_test, pred):.4f}")

    # Stratified sample of the hold-out set to ship + score in-browser.
    if len(X_test_s) > TEST_SAMPLE_SIZE:
        X_test_s, _, y_test, _ = train_test_split(
            X_test_s, y_test, train_size=TEST_SAMPLE_SIZE,
            random_state=42, stratify=y_test,
        )
    sample_pred = knn.predict(X_test_s)
    print(f"  held-out sample: {len(X_test_s)} points, "
          f"accuracy {accuracy_score(y_test, sample_pred):.4f} "
          f"(== popup value at 0 feedback)")

    seed = {
        "feature_names": BROWSER_FEATURES,
        "k": K,
        "metric": METRIC,
        # sklearn MinMaxScaler.transform(x) == x * scale_ + min_
        "scaler": {
            "min": scaler.min_.tolist(),
            "scale": scaler.scale_.tolist(),
        },
        "X": [[round(v, 6) for v in row] for row in X_train_s.tolist()],
        "y": [int(v) for v in y_train.tolist()],
    }

    test = {
        "X": [[round(v, 6) for v in row] for row in X_test_s.tolist()],
        "y": [int(v) for v in y_test.tolist()],
    }

    os.makedirs(MODELS_DIR, exist_ok=True)
    out = os.path.join(MODELS_DIR, "seed_model.json")
    with open(out, "w") as f:
        json.dump(seed, f, separators=(",", ":"))
    print(f"\nWrote {out} "
          f"({os.path.getsize(out)} bytes, {len(seed['X'])} seed points).")

    out_test = os.path.join(MODELS_DIR, "seed_test.json")
    with open(out_test, "w") as f:
        json.dump(test, f, separators=(",", ":"))
    print(f"Wrote {out_test} "
          f"({os.path.getsize(out_test)} bytes, {len(test['X'])} held-out points).")


if __name__ == "__main__":
    main()
