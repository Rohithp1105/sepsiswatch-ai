"""
SepsisWatch AI - Dataset Generator v3 (Clinically Accurate)
------------------------------------------------------------
Key improvements over v2:
1. Comorbidities STRONGLY affect vitals — not just small shifts
2. Sepsis presentation differs by comorbidity (diabetic sepsis looks different)
3. Overlap zones between classes — real ICU data is messy, not perfectly separated
4. Age affects BOTH vitals AND which risk class a patient ends up in
5. Hypothermia in sepsis (temp < 36) — often missed, clinically important
6. 100k records for better model generalization
"""

import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

NUM_SAMPLES = 100000

# ── Comorbidity prevalence in real ICU populations ─────────────────────────
# Source: APACHE III (Zimmerman 2006), Angus et al. (2001)
COMORBIDITY_PREVALENCE = {
    "diabetes":               0.30,
    "hypertension":           0.45,
    "immunocompromised":      0.12,
    "chronic_kidney_disease": 0.20,
    "copd":                   0.18,
}

def random_comorbidities():
    c = {k: random.random() < v for k, v in COMORBIDITY_PREVALENCE.items()}
    # Correlation: diabetes + hypertension often co-occur
    if c["diabetes"] and random.random() < 0.45:
        c["hypertension"] = True
    # CKD often follows diabetes
    if c["diabetes"] and random.random() < 0.25:
        c["chronic_kidney_disease"] = True
    return c

def comorbidity_count(c):
    return sum(1 for v in c.values() if v)


def generate_patient(severity, age, c):
    """
    severity: 0=healthy, 1=mild, 2=moderate, 3=sepsis
    c: comorbidities dict

    Vitals are generated with STRONG comorbidity effects so the
    ML model can actually learn from those features.
    """
    n = np.random.normal  # shorthand

    # ── Base vitals by severity ────────────────────────────────────────────
    # These ranges are deliberately overlapping to match real ICU data messiness

    if severity == 0:   # Healthy / normal ICU admission
        hr   = n(72,  10)
        temp = n(36.8, 0.4)
        spo2 = n(98.5, 1.0)
        rr   = n(14,   2)
        sbp  = n(122,  12)
        dbp  = n(78,   8)

    elif severity == 1:  # Mild infection / early warning
        hr   = n(90,  14)
        temp = n(37.8, 0.5)
        spo2 = n(96.0, 1.5)
        rr   = n(19,   3)
        sbp  = n(112,  14)
        dbp  = n(72,   9)

    elif severity == 2:  # Moderate / suspected sepsis
        hr   = n(108, 16)
        temp = n(38.8, 0.7)
        spo2 = n(92.5, 2.5)
        rr   = n(24,   4)
        sbp  = n(100,  14)
        dbp  = n(64,   9)

    else:               # Severe sepsis / septic shock
        # Key: ~15% of sepsis patients present with HYPOTHERMIA (temp < 36)
        # This is a dangerous pattern often missed — immunocompromised especially
        if c.get("immunocompromised") or (age > 65 and random.random() < 0.2):
            temp = n(35.5, 0.6)   # hypothermic sepsis
        else:
            temp = n(39.5, 0.8)   # classic febrile sepsis

        hr   = n(126, 18)
        spo2 = n(86.0, 3.5)
        rr   = n(30,   5)
        sbp  = n(84,   14)
        dbp  = n(52,   10)

    # ── STRONG comorbidity effects on vitals ───────────────────────────────
    # These are large enough for the ML model to learn from

    # Diabetes: autonomic neuropathy → blunted HR response + higher glucose-driven temp
    if c.get("diabetes"):
        hr   += n(6,  3)    # resting tachycardia
        temp += n(0.3, 0.1) # slight temp elevation tendency
        if severity >= 2:
            # Diabetics in sepsis: worse BP control
            sbp -= n(8, 4)
            hr  += n(8, 4)

    # Hypertension: chronically elevated BP — paradoxically BP DROP is more alarming
    if c.get("hypertension"):
        sbp += n(18, 6)   # higher baseline
        dbp += n(10, 4)
        if severity >= 2:
            # For hypertensives, a "normal" BP of 100 is actually severe hypotension
            sbp -= n(5, 3)   # net: BP still higher than non-hypertensive sepsis

    # COPD: chronically low SpO2, high RR, airway limitation
    if c.get("copd"):
        spo2 -= n(5,  2)   # baseline low SpO2
        rr   += n(5,  2)   # elevated baseline RR
        hr   += n(7,  3)   # chronic hypoxia → tachycardia
        if severity >= 2:
            spo2 -= n(4, 2)  # drops much lower in sepsis
            rr   += n(4, 2)

    # Immunocompromised: blunted fever response, faster deterioration
    if c.get("immunocompromised"):
        if severity >= 1:
            temp -= n(0.5, 0.2)  # fever suppressed by immunosuppressants
        if severity >= 2:
            hr   += n(10, 4)
            spo2 -= n(4,  2)

    # CKD: fluid retention → elevated BP, compensatory tachycardia
    if c.get("chronic_kidney_disease"):
        hr   += n(8,  3)
        sbp  += n(8,  4)
        if severity >= 2:
            # CKD worsens acidosis in sepsis → more tachycardia
            hr   += n(8,  4)
            rr   += n(3,  2)

    # ── Age effects ────────────────────────────────────────────────────────
    # Strong age effects so model learns this feature
    age_factor = (age - 40) / 40.0   # -0.5 to +1.375 range
    hr   += age_factor * 8
    spo2 -= age_factor * 3
    rr   += age_factor * 2
    sbp  += age_factor * 10   # elderly have higher baseline BP

    # ── Correlated HR from physiology ─────────────────────────────────────
    # Fever, low BP, low SpO2 all drive HR up
    temp_effect = max(0, float(temp) - 37.0) * 7
    bp_effect   = max(0, 100 - float(sbp)) * 0.5
    spo2_effect = max(0, 94 - float(spo2)) * 0.6
    hr += temp_effect + bp_effect + spo2_effect

    # ── Clamp to physiological limits ─────────────────────────────────────
    hr   = int(np.clip(hr,   25,  220))
    temp = round(float(np.clip(temp, 33.0, 42.5)), 1)
    spo2 = int(np.clip(spo2, 60,  100))
    rr   = int(np.clip(rr,    4,   50))
    sbp  = int(np.clip(sbp,  55,  220))
    dbp  = int(np.clip(dbp,  25,  130))

    # ── Risk label with comorbidity + age uplift ───────────────────────────
    risk = severity
    n_comorbidities = comorbidity_count(c)

    # Elderly + multiple comorbidities → higher true clinical risk
    if age >= 60 and n_comorbidities >= 2 and risk < 3:
        if random.random() < 0.30:
            risk = min(risk + 1, 3)
    if age >= 75 and n_comorbidities >= 1 and risk < 3:
        if random.random() < 0.20:
            risk = min(risk + 1, 3)
    # Immunocompromised + any infection → worse outcome
    if c.get("immunocompromised") and risk >= 1 and risk < 3:
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
        "diabetes":               int(c.get("diabetes", False)),
        "hypertension":           int(c.get("hypertension", False)),
        "immunocompromised":      int(c.get("immunocompromised", False)),
        "chronic_kidney_disease": int(c.get("chronic_kidney_disease", False)),
        "copd":                   int(c.get("copd", False)),
        "comorbidity_count":      n_comorbidities,
        "risk":                   risk
    }


# ── ICU population distribution ────────────────────────────────────────────
SEVERITY_WEIGHTS = [0.38, 0.25, 0.22, 0.15]
AGE_MEAN, AGE_STD = 58, 16

print(f"Generating {NUM_SAMPLES:,} records with strong comorbidity effects...")

data = []
for _ in range(NUM_SAMPLES):
    severity = np.random.choice([0,1,2,3], p=SEVERITY_WEIGHTS)
    age      = int(np.clip(np.random.normal(AGE_MEAN, AGE_STD), 18, 95))
    c        = random_comorbidities()
    data.append(generate_patient(severity, age, c))

df = pd.DataFrame(data)
df.to_csv("ml/generated_dataset.csv", index=False)

print(f"Saved: {len(df):,} records\n")
print("Risk distribution:")
for risk, label in [(0,"Low"),(1,"Mild"),(2,"Moderate"),(3,"Sepsis")]:
    n = (df['risk']==risk).sum()
    print(f"  {label:10s}: {n:6,} ({n/len(df)*100:.1f}%)")

print(f"\nAge: mean={df['age'].mean():.1f}, std={df['age'].std():.1f}")

print("\nFeature correlations with risk:")
feats = ["heart_rate","temperature","spo2","resp_rate","systolic",
         "age","diabetes","hypertension","immunocompromised",
         "chronic_kidney_disease","copd","comorbidity_count"]
for f in feats:
    r = df[f].corr(df['risk'])
    bar = "█" * int(abs(r) * 30)
    print(f"  {f:30s}: r={r:+.3f}  {bar}")
print("\nDone!")