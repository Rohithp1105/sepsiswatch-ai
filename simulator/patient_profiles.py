# patient_profiles.py
# Extended patient profiles with age and comorbidities
# Used by the simulator and risk engine for context-aware scoring

PATIENTS = {
    101: {
        "name": "Rahul",
        "age": 28,
        "condition": "Healthy",
        "severity": 0,
        "comorbidities": {
            "diabetes": False,
            "hypertension": False,
            "immunocompromised": False,
            "chronic_kidney_disease": False,
            "copd": False,
        }
    },

    102: {
        "name": "Priya",
        "age": 45,
        "condition": "Recovering",
        "severity": 1,
        "comorbidities": {
            "diabetes": True,
            "hypertension": False,
            "immunocompromised": False,
            "chronic_kidney_disease": False,
            "copd": False,
        }
    },

    103: {
        "name": "Arjun",
        "age": 62,
        "condition": "Developing Sepsis",
        "severity": 3,
        "comorbidities": {
            "diabetes": True,
            "hypertension": True,
            "immunocompromised": False,
            "chronic_kidney_disease": True,
            "copd": False,
        }
    },

    104: {
        "name": "Meera",
        "age": 55,
        "condition": "Stable",
        "severity": 1,
        "comorbidities": {
            "diabetes": False,
            "hypertension": True,
            "immunocompromised": False,
            "chronic_kidney_disease": False,
            "copd": False,
        }
    },

    105: {
        "name": "Kiran",
        "age": 70,
        "condition": "Moderate Risk",
        "severity": 2,
        "comorbidities": {
            "diabetes": True,
            "hypertension": True,
            "immunocompromised": True,
            "chronic_kidney_disease": False,
            "copd": True,
        }
    }
}