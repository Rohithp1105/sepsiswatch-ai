"""
SepsisWatch AI - Inference Wrapper v3
"""
import joblib
import json
import pandas as pd

model    = joblib.load("ml/model.pkl")
FEATURES = json.load(open("ml/features.json"))
RISK_LABELS = {0: "Low", 1: "Low-Medium", 2: "Medium", 3: "High"}

def predict_sepsis(patient: dict) -> tuple:
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
    features_df   = pd.DataFrame([row])[FEATURES]
    prediction    = model.predict(features_df)[0]
    probabilities = model.predict_proba(features_df)[0]
    risk          = RISK_LABELS[prediction]
    probability   = round(probabilities[prediction] * 100, 2)
    confidence    = round(max(probabilities) * 100, 2)
    return risk, probability, confidence

if __name__ == "__main__":
    tests = [
        {"label": "Young healthy (28)",
         "data": {"heart_rate":72,"temperature":36.8,"spo2":99,"resp_rate":14,
                  "systolic":120,"diastolic":80,"age":28,"comorbidities":{}}},
        {"label": "Elderly diabetic + CKD + HTN (67)",
         "data": {"heart_rate":118,"temperature":38.9,"spo2":91,"resp_rate":24,
                  "systolic":92,"diastolic":60,"age":67,
                  "comorbidities":{"diabetes":True,"hypertension":True,"chronic_kidney_disease":True}}},
        {"label": "COPD patient mild infection (70)",
         "data": {"heart_rate":96,"temperature":37.9,"spo2":88,"resp_rate":26,
                  "systolic":108,"diastolic":68,"age":70,
                  "comorbidities":{"copd":True,"hypertension":True}}},
        {"label": "Immunocompromised hypothermic sepsis (55)",
         "data": {"heart_rate":130,"temperature":35.2,"spo2":84,"resp_rate":32,
                  "systolic":82,"diastolic":50,"age":55,
                  "comorbidities":{"immunocompromised":True}}},
    ]
    for t in tests:
        risk, prob, conf = predict_sepsis(t["data"])
        print(f"{t['label']:45s}: {risk:12s} | {prob}%")