"""
train.py — reproduces the model used by the No Phishing extension.

This is a script port of cyberguard_phishing_detection.ipynb. It performs the
same feature screening, trains the same two classifiers (KNN, Logistic
Regression) and writes the artifacts the Flask server (app.py) loads at runtime:

    saved_models/knn_model.pkl     winning classifier (KNN)
    saved_models/lr_model.pkl      runner-up, kept for comparison
    saved_models/scaler.pkl        the MinMaxScaler fitted on the training features
    saved_models/feature_names.json  ordered feature list the model expects

Dataset (not committed — see README): the Kaggle/Mendeley "Web page phishing
detection" dataset by Hannousse & Yahiouche, expected at:

    raw_data/dataset_phishing.csv

Run:  python train.py
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler

DATASET = os.path.join("raw_data", "dataset_phishing.csv")
MODELS_DIR = "saved_models"

# Features dropped at the end because they cannot be recomputed at inference time
# without third-party APIs (the extension only has the URL to work with).
RUNTIME_UNAVAILABLE = ["web_traffic", "google_index", "page_rank"]


def main():
    data = pd.read_csv(DATASET)

    # --- Preprocessing -----------------------------------------------------
    data.dropna(inplace=True)
    data.drop(data[data["domain_age"] <= -1].index, inplace=True)
    data["status"] = data["status"].map({"legitimate": 0, "phishing": 1})

    X = data.drop(columns=["url", "status"])
    y = data["status"]

    # --- Feature screening -------------------------------------------------
    # 1) Multicollinearity: for any pair with |corr| > 0.75, drop the feature
    #    that is less correlated with the target.
    corr = X.corr()
    target_corr = data.drop(columns=["url"]).corr()["status"].drop("status")
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    pairs = upper.stack().reset_index()
    pairs.columns = ["f1", "f2", "pair_corr"]
    pairs["f1_t"] = pairs["f1"].map(target_corr)
    pairs["f2_t"] = pairs["f2"].map(target_corr)
    redundant = pairs[pairs["pair_corr"].abs() > 0.75].copy()
    redundant["drop"] = redundant.apply(
        lambda r: r["f1"] if abs(r["f1_t"]) < abs(r["f2_t"]) else r["f2"], axis=1
    )
    all_drops = set(redundant["drop"].tolist())

    # 2) Near-zero variance features carry almost no information.
    selector = VarianceThreshold(threshold=0.005).fit(X)
    low_variance = X.columns[~selector.get_support()].tolist()
    all_drops.update(low_variance)

    # 3) Weak linear correlation with the target.
    weak = target_corr[target_corr.abs() < 0.023].index.tolist()
    all_drops.update(weak)

    # 4) Low Random-Forest importance (captures non-linear relationships).
    rf = RandomForestClassifier(n_estimators=100, random_state=42).fit(X, y)
    importances = pd.Series(rf.feature_importances_, index=X.columns)
    low_importance = importances[importances < 0.005].index.tolist()
    all_drops.update(low_importance)

    print(f"Dropped {len(all_drops)} of {X.shape[1]} features via screening.")

    data_filtered = data.drop(columns=list(all_drops))
    X_filtered = data_filtered.drop(columns=["url", "status"])
    X_filtered = X_filtered.drop(columns=RUNTIME_UNAVAILABLE)
    feature_names = list(X_filtered.columns)
    print(f"Final feature count: {len(feature_names)}")
    print("Features:", feature_names)

    # --- Scaling -----------------------------------------------------------
    # Fit on raw arrays (no column names) so the server can feed plain numpy
    # vectors at inference time without sklearn feature-name warnings. The
    # column order is preserved separately in feature_names.json.
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_filtered.values)
    y = y.values

    # --- Train / test split ------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- Hyper-parameter search -------------------------------------------
    knn_grid = GridSearchCV(
        KNeighborsClassifier(),
        {"n_neighbors": list(range(3, 12)), "metric": ["euclidean", "manhattan"]},
        cv=5, scoring="accuracy", n_jobs=-1,
    ).fit(X_train, y_train)
    print(f"KNN best params: {knn_grid.best_params_}")

    lr_grid = GridSearchCV(
        LogisticRegression(max_iter=1000, random_state=42),
        {"C": [0.01, 0.1, 1, 10, 100], "solver": ["liblinear", "lbfgs"]},
        cv=5, scoring="accuracy", n_jobs=-1,
    ).fit(X_train, y_train)
    print(f"LogReg best params: {lr_grid.best_params_}")

    def evaluate(name, model):
        y_pred = model.predict(X_test)
        cv = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        print(f"\n{name}")
        print(f"  Test accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print(f"  CV accuracy:   {cv.mean():.4f} (+/- {cv.std():.4f})")
        print(classification_report(y_test, y_pred,
                                    target_names=["Legitimate", "Phishing"]))
        print(confusion_matrix(y_test, y_pred))

    knn = knn_grid.best_estimator_
    lr = lr_grid.best_estimator_
    evaluate("KNN", knn)
    evaluate("Logistic Regression", lr)

    # --- Persist artifacts -------------------------------------------------
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(knn, os.path.join(MODELS_DIR, "knn_model.pkl"))
    joblib.dump(lr, os.path.join(MODELS_DIR, "lr_model.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))
    with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
        json.dump(feature_names, f, indent=2)
    print(f"\nSaved KNN, LogReg, scaler and feature_names.json to {MODELS_DIR}/")


if __name__ == "__main__":
    main()
