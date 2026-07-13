"""
SepsisWatch AI - Model Training (v2)
--------------------------------------
Trains Random Forest on 80k realistic ICU records.
Features now include: vitals + age + 5 comorbidity flags
"""

import pandas as pd
import joblib
import json

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# ── Load dataset ───────────────────────────────────────────────────────────

df = pd.read_csv("ml/generated_dataset.csv")
print(f"Dataset loaded: {len(df):,} records")
print(f"Features: {list(df.columns)}\n")

# ── Features & labels ──────────────────────────────────────────────────────

FEATURES = [
    "heart_rate", "temperature", "spo2", "resp_rate", "systolic", "diastolic",
    "age",
    "diabetes", "hypertension", "immunocompromised", "chronic_kidney_disease", "copd"
]

X = df[FEATURES]
y = df["risk"]

# ── Train/test split ───────────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── Train Random Forest ────────────────────────────────────────────────────

print("\nTraining Random Forest (200 trees)...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ── Evaluate ───────────────────────────────────────────────────────────────

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"\nAccuracy: {round(accuracy * 100, 2)}%")
print("\nClassification Report:")
print(classification_report(
    y_test, predictions,
    target_names=["Low", "Mild", "Moderate", "Sepsis"]
))

# ── Feature importance ─────────────────────────────────────────────────────

print("\nFeature Importances:")
importances = sorted(
    zip(FEATURES, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
)
for feat, imp in importances:
    bar = "█" * int(imp * 50)
    print(f"  {feat:30s}: {imp:.4f} {bar}")

# ── Save model and feature list ────────────────────────────────────────────

joblib.dump(model, "ml/model.pkl")

with open("ml/features.json", "w") as f:
    json.dump(FEATURES, f)

print(f"\nModel saved to ml/model.pkl")
print(f"Feature list saved to ml/features.json")
print("Done!")