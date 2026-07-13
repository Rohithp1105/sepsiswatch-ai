"""
SepsisWatch AI - Patient Vitals Simulator with AWS IoT Core (v2)
-----------------------------------------------------------------
Now publishes age and comorbidities alongside vitals so Lambda
can perform comorbidity-aware risk scoring.
"""

import json
import time
from datetime import datetime, timezone
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# ── Configuration ──────────────────────────────────────────────────────────

ENDPOINT   = "a14ijcld81hg3m-ats.iot.ap-south-1.amazonaws.com"
CLIENT_ID  = "sepsiswatch-simulator"
TOPIC      = "sepsiswatch/vitals"

CERTS_DIR  = "certs/"
CERT_FILE  = CERTS_DIR + "8920317a1f483b66322a5dcceb6dc3e246f2589f63ac944b614352ef9ae4651c-certificate.pem.crt"
KEY_FILE   = CERTS_DIR + "8920317a1f483b66322a5dcceb6dc3e246f2589f63ac944b614352ef9ae4651c-private.pem.key"
ROOT_CA    = CERTS_DIR + "AmazonRootCA1.pem"

# ── Patient data ───────────────────────────────────────────────────────────

from patient_profiles import PATIENTS
from patient_state import PATIENT_STATE
from vitals_generator import update_vitals


def get_live_data():
    patients = []
    for patient_id, profile in PATIENTS.items():
        state = PATIENT_STATE[patient_id]
        state = update_vitals(state, profile["severity"])
        PATIENT_STATE[patient_id] = state

        patients.append({
            # Identity
            "patient_id":    patient_id,
            "name":          profile["name"],
            "age":           profile["age"],               # ← NEW
            "condition":     profile["condition"],
            "comorbidities": profile["comorbidities"],     # ← NEW

            # Vitals
            "heart_rate":    state["heart_rate"],
            "temperature":   state["temperature"],
            "spo2":          state["spo2"],
            "resp_rate":     state["resp_rate"],
            "systolic":      state["systolic"],
            "diastolic":     state["diastolic"],
            "timestamp":     datetime.now(timezone.utc).isoformat()
        })
    return patients


# ── MQTT ───────────────────────────────────────────────────────────────────

def build_mqtt_connection():
    return mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT_FILE,
        pri_key_filepath=KEY_FILE,
        ca_filepath=ROOT_CA,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )


def send_to_aws(mqtt_connection, payload: dict):
    mqtt_connection.publish(
        topic=TOPIC,
        payload=json.dumps(payload),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )


# ── Main loop ──────────────────────────────────────────────────────────────

def run_simulation(interval_seconds: float = 2.0):
    print("Connecting to AWS IoT Core...")
    mqtt_connection = build_mqtt_connection()
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print(f"Connected to {ENDPOINT}")
    print(f"Publishing to topic: {TOPIC}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            patients = get_live_data()
            for patient in patients:
                send_to_aws(mqtt_connection, patient)
                conditions = [k.replace("_", " ") for k, v in patient["comorbidities"].items() if v]
                conditions_str = ", ".join(conditions) if conditions else "none"
                print(f"Published: {patient['name']} (Age {patient['age']}) | "
                      f"HR:{patient['heart_rate']} "
                      f"BP:{patient['systolic']}/{patient['diastolic']} "
                      f"SpO2:{patient['spo2']} "
                      f"Temp:{patient['temperature']} | "
                      f"Comorbidities: {conditions_str}")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nStopping simulator...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected from AWS IoT Core.")


if __name__ == "__main__":
    run_simulation()