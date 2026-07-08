import joblib
import pandas as pd

# Load trained model
model = joblib.load("ml/model.pkl")


def predict_sepsis(patient):

    features = pd.DataFrame([{
        "heart_rate": patient["heart_rate"],
        "temperature": patient["temperature"],
        "spo2": patient["spo2"],
        "resp_rate": patient["resp_rate"],
        "systolic": patient["systolic"],
        "diastolic": patient["diastolic"]
    }])

    prediction = model.predict(features)[0]

    probabilities = model.predict_proba(features)[0]

    confidence = round(max(probabilities) * 100, 2)
    probability = round(probabilities[prediction] * 100, 2)

    risk_labels = {
        0: "Low",
        1: "Low-Medium",
        2: "Medium",
        3: "High"
    }

    risk = risk_labels[prediction]

    return risk, probability, confidence