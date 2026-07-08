import random


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def update_vitals(state, severity):
    """
    Updates the patient's current vitals slightly instead of
    generating completely new random values.
    """

    # Small natural fluctuations
    state["heart_rate"] += random.randint(-2, 3)
    state["temperature"] += round(random.uniform(-0.1, 0.1), 1)
    state["spo2"] += random.randint(-1, 1)
    state["resp_rate"] += random.randint(-1, 1)
    state["systolic"] += random.randint(-2, 2)
    state["diastolic"] += random.randint(-2, 2)

    # Patient slowly deteriorates based on severity
    if severity == 1:
        state["heart_rate"] += random.choice([0, 1])
        state["temperature"] += random.choice([0, 0.1])

    elif severity == 2:
        state["heart_rate"] += random.randint(1, 2)
        state["temperature"] += 0.1
        state["spo2"] -= random.choice([0, 1])

    elif severity == 3:
        state["heart_rate"] += random.randint(2, 4)
        state["temperature"] += 0.2
        state["spo2"] -= random.randint(0, 2)
        state["resp_rate"] += random.randint(0, 2)
        state["systolic"] -= random.randint(0, 2)

    # Keep values realistic
    state["heart_rate"] = clamp(state["heart_rate"], 55, 150)
    state["temperature"] = round(clamp(state["temperature"], 35.5, 41.5), 1)
    state["spo2"] = clamp(state["spo2"], 80, 100)
    state["resp_rate"] = clamp(state["resp_rate"], 8, 35)
    state["systolic"] = clamp(state["systolic"], 70, 150)
    state["diastolic"] = clamp(state["diastolic"], 40, 100)

    return state