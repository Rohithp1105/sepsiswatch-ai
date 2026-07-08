from collections import defaultdict

MAX_POINTS = 20

history = defaultdict(lambda: {
    "heart_rate": [],
    "temperature": [],
    "spo2": []
})


def update_history(patient):

    pid = patient["patient_id"]

    history[pid]["heart_rate"].append(patient["heart_rate"])
    history[pid]["temperature"].append(patient["temperature"])
    history[pid]["spo2"].append(patient["spo2"])

    if len(history[pid]["heart_rate"]) > MAX_POINTS:
        history[pid]["heart_rate"].pop(0)

    if len(history[pid]["temperature"]) > MAX_POINTS:
        history[pid]["temperature"].pop(0)

    if len(history[pid]["spo2"]) > MAX_POINTS:
        history[pid]["spo2"].pop(0)


def get_history(patient_id):
    return history[patient_id]