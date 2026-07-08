from datetime import datetime
import time

from patient_profiles import PATIENTS
from patient_state import PATIENT_STATE
from vitals_generator import update_vitals


def get_live_data():
    """
    Update every patient's vitals and return
    the latest state.
    """

    patients = []

    for patient_id, profile in PATIENTS.items():

        # Current persistent state
        state = PATIENT_STATE[patient_id]

        # Update smoothly
        state = update_vitals(state, profile["severity"])

        # Save updated state
        PATIENT_STATE[patient_id] = state

        patients.append({
            "patient_id": patient_id,
            "name": profile["name"],
            "condition": profile["condition"],

            "heart_rate": state["heart_rate"],
            "temperature": state["temperature"],
            "spo2": state["spo2"],
            "resp_rate": state["resp_rate"],
            "systolic": state["systolic"],
            "diastolic": state["diastolic"],
        })

    return patients


def main():

    while True:

        print("=" * 80)

        patients = get_live_data()

        for p in patients:

            print(f"""
Time : {datetime.now().strftime('%H:%M:%S')}

Patient : {p['name']}
Bed     : {p['patient_id']}
Status  : {p['condition']}

Heart Rate      : {p['heart_rate']} bpm
Temperature     : {p['temperature']} °C
SpO₂            : {p['spo2']} %
Resp Rate       : {p['resp_rate']}
Blood Pressure  : {p['systolic']}/{p['diastolic']}
""")

        time.sleep(2)


if __name__ == "__main__":
    main()