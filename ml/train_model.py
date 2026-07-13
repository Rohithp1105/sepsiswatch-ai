"""
SepsisWatch AI - Model Training v3
------------------------------------
100k records | 12 features | 86.89% accuracy
Comorbidities now meaningfully contribute to predictions
"""
import pandas as pd
import joblib
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

df = pd.read_csv("ml/generated_dataset.csv")
print(f"Dataset loaded: {len(df):,} records")

FEATURES = [
    "heart_rate", "temperature", "spo2", "resp_rate", "systolic", "diastolic",
    "age",
    "diabetes", "hypertension", "immunocompromised", "chronic_kidney_disease", "copd"
]

X = df[FEATURES]
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

print("\nTraining Random Forest (300 trees)...")
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=15,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"\nAccuracy: {acc*100:.2f}%")
print(classification_report(y_test, preds, target_names=["Low","Mild","Moderate","Sepsis"]))

print("\nFeature Importances:")
for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: x[1], reverse=True):
    bar = "█" * int(imp * 60)
    print(f"  {feat:30s}: {imp:.4f}  {bar}")

joblib.dump(model, "ml/model.pkl")
with open("ml/features.json", "w") as f:
    json.dump(FEATURES, f)
print("\nModel saved to ml/model.pkl")
print("Feature list saved to ml/features.json")