"""
SepsisWatch AI - Clinically Realistic Dataset Generator (v2)
-------------------------------------------------------------
Generates 80,000 synthetic ICU records with:
  - Correlated vitals (fever raises HR, low BP raises HR etc.)
  - Age-based baseline adjustments
  - Comorbidity effects on vitals and sepsis risk
  - Realistic noise and measurement variation
  - Label distribution matching real ICU populations

Based on feature definitions from:
  PhysioNet Computing in Cardiology Challenge 2019
  Sepsis-3 definition (Singer et al., JAMA 2016)
  qSOFA criteria (Seymour et al., JAMA 2016)
"""

import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

NUM_SAMPLES = 80000

def age_baseline_shift(age):
    if age < 40:
        return {"heart_rate": 0, "spo2": 0, "systolic": 0, "resp_rate": 0}
    elif age < 55:
        return {"heart_rate": 3, "spo2": -1, "systolic": 5, "resp_rate": 1}
    elif age < 65:
        return {"heart_rate": 5, "spo2": -2, "systolic": 8, "resp_rate": 1}
    elif age < 75:
        return {"heart_rate": 7, "spo2": -3, "systolic": 12, "resp_rate": 2}
    else:
        return {"heart_rate": 10, "spo2": -4, "systolic": 15, "resp_rate": 2}


def comorbidity_vital_shift(comorbidities):
    shift = {"heart_rate": 0, "spo2": 0, "resp_rate": 0, "systolic": 0}
    if comorbidities.get("diabetes"):
        shift["heart_rate"] += 3
    if comorbidities.get("hypertension"):
        shift["systolic"] += 15
    if comorbidities.get("copd"):
        shift["spo2"] -= 4
        shift["resp_rate"] += 3
    if comorbidities.get("immunocompromised"):
        shift["heart_rate"] += 2
    if comorbidities.get("chronic_kidney_disease"):
        shift["heart_rate"] += 3
    return shift


def generate_patient(severity, age, comorbidities):
    age_shift  = age_baseline_shift(age)
    como_shift = comorbidity_vital_shift(comorbidities)

    if severity == 0:
        temp = round(np.random.normal(36.7, 0.3), 1)
        spo2 = int(np.random.normal(98.5, 0.8))
        rr   = int(np.random.normal(14, 1.5))
        sbp  = int(np.random.normal(118, 8))
        dbp  = int(np.random.normal(76, 6))
        risk = 0
    elif severity == 1:
        temp = round(np.random.normal(37.6, 0.4), 1)
        spo2 = int(np.random.normal(96.5, 1.2))
        rr   = int(np.random.normal(18, 2))
        sbp  = int(np.random.normal(112, 9))
        dbp  = int(np.random.normal(73, 7))
        risk = 1
    elif severity == 2:
        temp = round(np.random.normal(38.6, 0.5), 1)
        spo2 = int(np.random.normal(93.0, 1.8))
        rr   = int(np.random.normal(23, 2.5))
        sbp  = int(np.random.normal(103, 10))
        dbp  = int(np.random.normal(66, 8))
        risk = 2
    else:
        temp = round(np.random.normal(39.4, 0.7), 1)
        spo2 = int(np.random.normal(88.0, 2.5))
        rr   = int(np.random.normal(29, 3))
        sbp  = int(np.random.normal(88, 10))
        dbp  = int(np.random.normal(54, 8))
        risk = 3

    base_hr = {0: 72, 1: 88, 2: 104, 3: 122}[severity]
    temp_effect  = max(0, (temp - 37.0)) * 8
    bp_effect    = max(0, (100 - sbp)) * 0.4
    spo2_effect  = max(0, (94 - spo2)) * 0.5
    hr = int(np.random.normal(base_hr + temp_effect + bp_effect + spo2_effect, 6))

    hr   += age_shift["heart_rate"] + como_shift["heart_rate"]
    spo2 += age_shift["spo2"]       + como_shift["spo2"]
    rr   += age_shift["resp_rate"]  + como_shift["resp_rate"]
    sbp  += age_shift["systolic"]   + como_shift["systolic"]

    hr   = int(np.clip(hr,   30,  200))
    temp = round(np.clip(temp, 34.0, 42.0), 1)
    spo2 = int(np.clip(spo2, 70,  100))
    rr   = int(np.clip(rr,    6,   45))
    sbp  = int(np.clip(sbp,  60,  200))
    dbp  = int(np.clip(dbp,  30,  120))

    comorbidity_count = sum(1 for v in comorbidities.values() if v)
    if age >= 65 and comorbidity_count >= 2 and risk < 3:
        if random.random() < 0.25:
            risk = min(risk + 1, 3)

    return {
        "heart_rate":             hr,
        "temperature":            temp,
        "spo2":                   spo2,
        "resp_rate":              rr,
        "systolic":               sbp,
        "diastolic":              dbp,
        "age":                    age,
        "diabetes":               int(comorbidities.get("diabetes", False)),
        "hypertension":           int(comorbidities.get("hypertension", False)),
        "immunocompromised":      int(comorbidities.get("immunocompromised", False)),
        "chronic_kidney_disease": int(comorbidities.get("chronic_kidney_disease", False)),
        "copd":                   int(comorbidities.get("copd", False)),
        "risk":                   risk
    }


SEVERITY_WEIGHTS = [0.40, 0.25, 0.20, 0.15]
AGE_MEAN, AGE_STD = 58, 16

COMORBIDITY_PREVALENCE = {
    "diabetes":               0.30,
    "hypertension":           0.45,
    "immunocompromised":      0.12,
    "chronic_kidney_disease": 0.20,
    "copd":                   0.18,
}

def random_comorbidities():
    return {k: random.random() < v for k, v in COMORBIDITY_PREVALENCE.items()}


print(f"Generating {NUM_SAMPLES:,} clinically realistic ICU records...")

data = []
for i in range(NUM_SAMPLES):
    severity      = np.random.choice([0, 1, 2, 3], p=SEVERITY_WEIGHTS)
    age           = int(np.clip(np.random.normal(AGE_MEAN, AGE_STD), 18, 95))
    comorbidities = random_comorbidities()
    data.append(generate_patient(severity, age, comorbidities))

df = pd.DataFrame(data)
df.to_csv("ml/generated_dataset.csv", index=False)

print(f"Saved to ml/generated_dataset.csv")
print(f"Total records : {len(df):,}")
print(f"\nRisk class distribution:")
for risk, label in [(0,"Low"), (1,"Mild"), (2,"Moderate"), (3,"Sepsis")]:
    count = (df['risk'] == risk).sum()
    print(f"  Class {risk} ({label:8s}): {count:6,} ({count/len(df)*100:.1f}%)")
print(f"\nAge:  mean={df['age'].mean():.1f}, std={df['age'].std():.1f}")
print(f"\nVital correlations with risk label:")
for col in ["heart_rate","temperature","spo2","resp_rate","systolic"]:
    r = df[col].corr(df['risk'])
    print(f"  {col:25s}: r = {r:+.3f}")
print("\nDone!")