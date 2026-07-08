"""
SepsisWatch AI - Patient Vitals Simulator with AWS IoT Core
------------------------------------------------------------
Streams live patient vitals to AWS IoT Core via MQTT.
"""

import json
import random
import time
from datetime import datetime, timezone
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# ============================================================
# CONFIGURATION — fill in your cert filenames below
# ============================================================

ENDPOINT   = "a14ijcld81hg3m-ats.iot.ap-south-1.amazonaws.com"
CLIENT_ID  = "sepsiswatch-simulator"
TOPIC      = "sepsiswatch/vitals"
REGION     = "ap-south-1"

# Path to your certs folder
CERTS_DIR  = "certs/"

# Fill these in with your actual filenames (run: dir certs\ to see them)
CERT_FILE  = CERTS_DIR + "8920317a1f483b66322a5dcceb6dc3e246f2589f63ac944b614352ef9ae4651c-certificate.pem.crt"
KEY_FILE   = CERTS_DIR + "8920317a1f483b66322a5dcceb6dc3e246f2589f63ac944b614352ef9ae4651c-private.pem.key"
ROOT_CA    = CERTS_DIR + "AmazonRootCA1.pem"

# ============================================================
# PATIENT PROFILES
# ============================================================

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
            "patient_id": patient_id,
            "name": profile["name"],
            "condition": profile["condition"],
            "heart_rate": state["heart_rate"],
            "temperature": state["temperature"],
            "spo2": state["spo2"],
            "resp_rate": state["resp_rate"],
            "systolic": state["systolic"],
            "diastolic": state["diastolic"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    return patients


# ============================================================
# MQTT CONNECTION
# ============================================================

def build_mqtt_connection():
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT_FILE,
        pri_key_filepath=KEY_FILE,
        ca_filepath=ROOT_CA,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )
    return mqtt_connection


def send_to_aws(mqtt_connection, payload: dict):
    mqtt_connection.publish(
        topic=TOPIC,
        payload=json.dumps(payload),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )


# ============================================================
# MAIN LOOP
# ============================================================

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
                print(f"Published: {patient['name']} | "
                      f"HR:{patient['heart_rate']} "
                      f"BP:{patient['systolic']}/{patient['diastolic']} "
                      f"SpO2:{patient['spo2']} "
                      f"Temp:{patient['temperature']}")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nStopping simulator...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected from AWS IoT Core.")


if __name__ == "__main__":
    run_simulation()