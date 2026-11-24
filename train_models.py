"""Train the two ML risk models and save them to ./models.

Run once:  python train_models.py

Models (Logistic Regression inside a scikit-learn Pipeline that imputes
missing values, so a patient may leave any field empty):
  1. diabetes  - Pima Indians Diabetes Database (768 patients)
  2. heart     - Cleveland Heart Disease dataset, 'lite' version that only uses
                 values a normal check-up gives (age, sex, BP, cholesterol, fasting sugar)
"""
import urllib.request
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, recall_score, precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).parent
DATA, MODELS = BASE / "data", BASE / "models"
DATA.mkdir(exist_ok=True); MODELS.mkdir(exist_ok=True)

SOURCES = {
    "diabetes.csv": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
    "heart.csv": "https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv",
}


def fetch(name):
    path = DATA / name
    if not path.exists():
        print(f"Downloading {name} ...")
        urllib.request.urlretrieve(SOURCES[name], path)
    return path


def build(X, y, features, name):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000)),
    ]).fit(Xtr, ytr)
    pred, prob = pipe.predict(Xte), pipe.predict_proba(Xte)[:, 1]
    metrics = {
        "accuracy": round(accuracy_score(yte, pred), 3),
        "recall": round(recall_score(yte, pred), 3),
        "precision": round(precision_score(yte, pred), 3),
        "auc": round(roc_auc_score(yte, prob), 3),
        "train_size": len(Xtr), "test_size": len(Xte),
    }
    joblib.dump({"pipeline": pipe, "features": features, "metrics": metrics}, MODELS / f"{name}.joblib")
    print(f"[{name}] {metrics}")


# ---- Diabetes -----------------------------------------------------------
cols = ["pregnancies", "glucose", "bp", "skin", "insulin", "bmi", "dpf", "age", "outcome"]
d = pd.read_csv(fetch("diabetes.csv"), names=cols)
for c in ["glucose", "bp", "skin", "insulin", "bmi"]:      # 0 means "not recorded" here
    d[c] = d[c].replace(0, np.nan)
feats = cols[:-1]
build(d[feats].values, d["outcome"].values, feats, "diabetes")

# ---- Heart disease (lite) -------------------------------------------------
h = pd.read_csv(fetch("heart.csv"), encoding="utf-8-sig")
h.columns = [c.strip() for c in h.columns]
# IMPORTANT: in this popular Kaggle copy, target==1 means "NO disease" (labels are
# inverted compared with the original UCI data). We flip it so 1 = disease present.
h["disease"] = 1 - h["target"]
feats = ["age", "sex", "trestbps", "chol", "fbs"]
build(h[feats].values, h["disease"].values, feats, "heart")
print("Done. Models saved in ./models")
