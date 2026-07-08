import random
import pandas as pd

NUM_SAMPLES = 50000

data = []

for _ in range(NUM_SAMPLES):

    severity = random.choice([0, 1, 2, 3])

    if severity == 0:
        hr = random.randint(60, 85)
        temp = round(random.uniform(36.3, 37.2), 1)
        spo2 = random.randint(97, 100)
        rr = random.randint(12, 16)
        sbp = random.randint(115, 130)
        dbp = random.randint(75, 85)
        risk = 0

    elif severity == 1:
        hr = random.randint(80, 95)
        temp = round(random.uniform(37.1, 38.0), 1)
        spo2 = random.randint(95, 98)
        rr = random.randint(15, 20)
        sbp = random.randint(108, 122)
        dbp = random.randint(70, 82)
        risk = 1

    elif severity == 2:
        hr = random.randint(95, 115)
        temp = round(random.uniform(38.0, 38.8), 1)
        spo2 = random.randint(91, 95)
        rr = random.randint(20, 25)
        sbp = random.randint(95, 110)
        dbp = random.randint(65, 78)
        risk = 2

    else:
        hr = random.randint(115, 140)
        temp = round(random.uniform(38.8, 40.2), 1)
        spo2 = random.randint(85, 92)
        rr = random.randint(25, 32)
        sbp = random.randint(80, 95)
        dbp = random.randint(50, 65)
        risk = 3

    data.append({
        "heart_rate": hr,
        "temperature": temp,
        "spo2": spo2,
        "resp_rate": rr,
        "systolic": sbp,
        "diastolic": dbp,
        "risk": risk
    })

df = pd.DataFrame(data)

df.to_csv("ml/generated_dataset.csv", index=False)

print(df.head())
print(f"\nGenerated {len(df)} patient records.")