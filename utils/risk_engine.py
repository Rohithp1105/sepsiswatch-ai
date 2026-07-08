def calculate_risk(vitals):

    score = 0

    # Heart Rate
    if vitals["heart_rate"] > 100:
        score += 20

    # Temperature
    if vitals["temperature"] >= 38:
        score += 20

    # SpO2
    if vitals["spo2"] < 94:
        score += 25

    # Respiratory Rate
    if vitals["resp_rate"] > 22:
        score += 15

    # Blood Pressure
    if vitals["systolic"] < 100:
        score += 20

    score = min(score, 100)

    if score < 30:
        risk_level = "Low"
        condition = "Stable"
        alert = "No Action Required"

    elif score < 60:
        risk_level = "Medium"
        condition = "Observation"
        alert = "Monitor Closely"

    else:
        risk_level = "High"
        condition = "Critical"
        alert = "Possible Early Sepsis"

    return {
        "score": score,
        "risk": risk_level,
        "condition": condition,
        "alert": alert
    }