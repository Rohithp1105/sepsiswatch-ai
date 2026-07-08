import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# -------------------------
# Load Dataset
# -------------------------

df = pd.read_csv("ml/generated_dataset.csv")

print("Dataset Loaded Successfully!")
print(df.head())

# -------------------------
# Features & Labels
# -------------------------

X = df.drop("risk", axis=1)

y = df["risk"]

# -------------------------
# Train Test Split
# -------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# -------------------------
# Train Model
# -------------------------

print("\nTraining Random Forest...")

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# -------------------------
# Evaluate
# -------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nAccuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report\n")
print(classification_report(y_test, predictions))

# -------------------------
# Save Model
# -------------------------

joblib.dump(model, "ml/model.pkl")

print("\nModel saved successfully!")