"""
SepsisWatch AI - Inference Wrapper (v2)
-----------------------------------------
Loads trained model and predicts sepsis risk.
Now accepts age and comorbidities as input features.
"""

import joblib
import json
import pandas as pd

model    = joblib.load("ml/model.pkl")
FEATURES = json.load(open("ml/features.json"))

RISK_LABELS = {0: "Low", 1: "Low-Medium", 2: "Medium", 3: "High"}


def predict_sepsis(patient: dict) -> tuple:
    """
    Predict sepsis risk for a patient.

    Args:
        patient: dict with keys:
            vitals   — heart_rate, temperature, spo2, resp_rate, systolic, diastolic
            context  — age (int)
            flags    — diabetes, hypertension, immunocompromised,
                       chronic_kidney_disease, copd (all bool/int)

    Returns:
        (risk_label, probability_pct, confidence_pct)
    """
    comorbidities = patient.get("comorbidities", {})

    row = {
        "heart_rate":             float(patient.get("heart_rate", 0)),
        "temperature":            float(patient.get("temperature", 37.0)),
        "spo2":                   float(patient.get("spo2", 98)),
        "resp_rate":              float(patient.get("resp_rate", 16)),
        "systolic":               float(patient.get("systolic", 120)),
        "diastolic":              float(patient.get("diastolic", 80)),
        "age":                    float(patient.get("age", 40)),
        "diabetes":               int(comorbidities.get("diabetes", False)),
        "hypertension":           int(comorbidities.get("hypertension", False)),
        "immunocompromised":      int(comorbidities.get("immunocompromised", False)),
        "chronic_kidney_disease": int(comorbidities.get("chronic_kidney_disease", False)),
        "copd":                   int(comorbidities.get("copd", False)),
    }

    features_df  = pd.DataFrame([row])[FEATURES]
    prediction   = model.predict(features_df)[0]
    probabilities = model.predict_proba(features_df)[0]

    risk        = RISK_LABELS[prediction]
    probability = round(probabilities[prediction] * 100, 2)
    confidence  = round(max(probabilities) * 100, 2)

    return risk, probability, confidence


# ── Quick test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test 1 — Healthy young patient
    test1 = {
        "heart_rate": 72, "temperature": 36.8, "spo2": 99,
        "resp_rate": 14, "systolic": 120, "diastolic": 80,
        "age": 28, "comorbidities": {}
    }

    # Test 2 — Elderly diabetic with elevated vitals
    test2 = {
        "heart_rate": 118, "temperature": 38.9, "spo2": 91,
        "resp_rate": 24, "systolic": 92, "diastolic": 60,
        "age": 67,
        "comorbidities": {
            "diabetes": True, "hypertension": True,
            "chronic_kidney_disease": True
        }
    }

    for i, patient in enumerate([test1, test2], 1):
        risk, prob, conf = predict_sepsis(patient)
        print(f"Test {i} (Age {patient['age']}): {risk} risk | "
              f"Probability: {prob}% | Confidence: {conf}%")