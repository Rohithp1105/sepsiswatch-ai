from collections import defaultdict

MAX_HISTORY = 20

patient_history = defaultdict(list)


def update_history(patient):
    """
    Store one complete snapshot of a patient's vitals.
    Keeps only the most recent MAX_HISTORY records.
    """

    patient_history[patient["patient_id"]].append({
        "heart_rate": patient["heart_rate"],
        "temperature": patient["temperature"],
        "spo2": patient["spo2"],
        "resp_rate": patient["resp_rate"],
        "systolic": patient["systolic"],
        "diastolic": patient["diastolic"],
        "probability": patient.get("probability", 0)
    })

    if len(patient_history[patient["patient_id"]]) > MAX_HISTORY:
        patient_history[patient["patient_id"]].pop(0)


def get_history(patient_id):
    return patient_history[patient_id]