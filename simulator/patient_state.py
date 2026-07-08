from patient_profiles import PATIENTS

# Initial state of every patient
PATIENT_STATE = {}

for patient_id, patient in PATIENTS.items():

    severity = patient["severity"]

    if severity == 0:  # Healthy
        PATIENT_STATE[patient_id] = {
            "heart_rate": 72,
            "temperature": 36.8,
            "spo2": 99,
            "resp_rate": 15,
            "systolic": 120,
            "diastolic": 80
        }

    elif severity == 1:  # Mild
        PATIENT_STATE[patient_id] = {
            "heart_rate": 88,
            "temperature": 37.4,
            "spo2": 97,
            "resp_rate": 17,
            "systolic": 118,
            "diastolic": 78
        }

    elif severity == 2:  # Moderate
        PATIENT_STATE[patient_id] = {
            "heart_rate": 102,
            "temperature": 38.2,
            "spo2": 94,
            "resp_rate": 21,
            "systolic": 108,
            "diastolic": 72
        }

    else:  # Developing Sepsis
        PATIENT_STATE[patient_id] = {
            "heart_rate": 112,
            "temperature": 38.8,
            "spo2": 92,
            "resp_rate": 25,
            "systolic": 96,
            "diastolic": 66
        }