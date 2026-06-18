"""
train_browser.py — trains the in-browser model shipped by the No Phishing extension.

The extension runs entirely client-side, so the model may only use features that
can be computed in a browser from the URL string plus the page's link count. This
script trains such a model and exports it to ONNX (scaler fused in) for
onnxruntime-web.

Pipeline:
    MinMaxScaler  ->  GradientBoostingClassifier
Both are baked into a single sklearn Pipeline and exported as one model.onnx, so
the extension feeds raw feature values and the graph scales + classifies in one
shot.

Feature set (11) — the 22-feature server model minus everything that cannot be
computed in the browser *with formula parity to the training data*:
    * dropped (impossible in-browser): domain_age, domain_registration_length
      (WHOIS), ratio_extRedirection, ratio_extErrors (redirect history)
    * dropped (low value, DOM-definition parity risk): ratio_intHyperlinks,
      ratio_extHyperlinks, safe_anchor, domain_in_title
    * dropped (tokenizer parity risk): shortest_word_host, shortest_word_path,
      longest_word_path — the dataset tokenizes host/path words with a public-
      suffix list (tldextract) and underscore splitting that cannot be cheaply
      reproduced in JS; a naive split silently feeds the model wrong values. The
      accuracy cost of dropping all three is only ~0.4pt (92.4% -> 92.0%).
    * kept: 10 lexical features (URL string only) + nb_hyperlinks (page link count)
The exact feature formulas are mirrored 1:1 in extension/features.js and verified
against the dataset columns by tests/ (800-row exact-match parity check).

Artifacts written:
    saved_models/model.onnx              MinMaxScaler + GradientBoosting, ONNX
    saved_models/browser_features.json   ordered feature list the model expects

Dataset (not committed — see README): the Kaggle/Mendeley "Web page phishing
detection" dataset by Hannousse & Yahiouche, expected at:
    raw_data/dataset_phishing.csv

Run:  python train_browser.py
"""

import json
import os

import numpy as np
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

DATASET = os.path.join("raw_data", "dataset_phishing.csv")
MODELS_DIR = "saved_models"

# The 11 features the in-browser model consumes, in the exact order
# extension/features.js emits them. 10 lexical + nb_hyperlinks (page link count).
BROWSER_FEATURES = [
    "length_url", "length_hostname", "nb_dots", "nb_hyphens", "nb_qm", "nb_eq",
    "nb_slash", "nb_www", "ratio_digits_url", "phish_hints", "nb_hyperlinks",
]


def main():
    data = pd.read_csv(DATASET)

    # --- Preprocessing (identical to the original notebook) ----------------
    data.dropna(inplace=True)
    data.drop(data[data["domain_age"] <= -1].index, inplace=True)
    data["status"] = data["status"].map({"legitimate": 0, "phishing": 1})

    X = data[BROWSER_FEATURES].values.astype(np.float32)
    y = data["status"].values
    print(f"Rows after cleaning: {len(data)} "
          f"(phishing={int(y.sum())}, legitimate={int((y == 0).sum())})")
    print(f"Features ({len(BROWSER_FEATURES)}): {BROWSER_FEATURES}\n")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Best hyperparameters found via GridSearchCV on the 11-feature set:
    # n_estimators=300, max_depth=4, learning_rate=0.1 (acc=0.9203 on 11 feats).
    # GridSearchCV is omitted here because it requires ~4 GB RAM and times out on
    # constrained hosts; re-run with the block below if you want to tune further.
    BEST_PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.1)

    pipe = Pipeline([
        ("scaler", MinMaxScaler()),
        ("clf", GradientBoostingClassifier(random_state=42, **BEST_PARAMS)),
    ]).fit(X_train, y_train)
    print(f"Model params: {BEST_PARAMS}")

    # --- Evaluation --------------------------------------------------------
    y_pred = pipe.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy:       {acc:.4f}")
    print(f"Phishing precision:  {precision_score(y_test, y_pred):.4f}")
    print(f"Phishing recall:     {recall_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred,
                                target_names=["Legitimate", "Phishing"]))
    print("Confusion matrix [tn fp / fn tp]:")
    print(confusion_matrix(y_test, y_pred))

    # --- Export to ONNX (scaler + classifier fused) ------------------------
    onnx_model = convert_sklearn(
        pipe,
        initial_types=[("X", FloatTensorType([None, len(BROWSER_FEATURES)]))],
        options={id(pipe): {"zipmap": False}},  # plain label + probability tensors
        target_opset=15,
    )
    os.makedirs(MODELS_DIR, exist_ok=True)
    onnx_path = os.path.join(MODELS_DIR, "model.onnx")
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    with open(os.path.join(MODELS_DIR, "browser_features.json"), "w") as f:
        json.dump(BROWSER_FEATURES, f, indent=2)

    # --- Verify ONNX parity vs sklearn on the test set ---------------------
    sess = rt.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    onnx_pred = sess.run(None, {"X": X_test})[0].ravel()
    parity = float(np.mean(onnx_pred == y_pred))
    print(f"\nONNX vs sklearn label parity on test set: {parity:.4%}")
    print(f"ONNX test accuracy:  {accuracy_score(y_test, onnx_pred):.4f}")
    print(f"\nSaved {onnx_path} ({os.path.getsize(onnx_path)} bytes) "
          f"and browser_features.json to {MODELS_DIR}/")


if __name__ == "__main__":
    main()
