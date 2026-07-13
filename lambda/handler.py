"""
SepsisWatch AI - Lambda Handler (v2 - Comorbidity Aware)
---------------------------------------------------------
Triggered by AWS IoT Core rule on topic: sepsiswatch/vitals
Pipeline: IoT Core -> Lambda -> DynamoDB + SNS + Bedrock

Risk scoring now accounts for:
  - Patient age (elderly patients have higher sepsis mortality risk)
  - Comorbidities: diabetes, hypertension, immunocompromised, CKD, COPD
"""

import json
import boto3
from datetime import datetime, timezone

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
sns      = boto3.client('sns',        region_name='ap-south-1')
bedrock  = boto3.client('bedrock-runtime', region_name='us-east-1')

TABLE_NAME     = 'PatientVitals'
SNS_TOPIC_ARN  = 'arn:aws:sns:ap-south-1:818783923830:SepsisAlert'
RISK_THRESHOLD = 65


# ── Age multiplier ─────────────────────────────────────────────────────────

def get_age_multiplier(age: int) -> float:
    if age < 40:   return 1.0
    elif age < 55: return 1.1
    elif age < 65: return 1.2
    elif age < 75: return 1.35
    else:          return 1.5


# ── Comorbidity weights ────────────────────────────────────────────────────

COMORBIDITY_WEIGHTS = {
    "diabetes":               8,
    "hypertension":           5,
    "immunocompromised":     12,
    "chronic_kidney_disease": 8,
    "copd":                   7,
}

def get_comorbidity_penalty(comorbidities: dict) -> tuple:
    penalty = 0
    active = []
    for condition, present in comorbidities.items():
        if present:
            penalty += COMORBIDITY_WEIGHTS.get(condition, 0)
            active.append(condition.replace("_", " ").title())
    return penalty, active


# ── Base vitals scoring ────────────────────────────────────────────────────

def calculate_base_score(vitals: dict) -> int:
    score = 0

    hr = vitals.get('heart_rate', 0)
    if hr > 120:   score += 25
    elif hr > 100: score += 15
    elif hr < 55:  score += 10

    temp = vitals.get('temperature', 0)
    if temp >= 39.0:   score += 20
    elif temp >= 38.0: score += 12
    elif temp < 36.0:  score += 15

    spo2 = vitals.get('spo2', 100)
    if spo2 < 90:   score += 30
    elif spo2 < 94: score += 20
    elif spo2 < 96: score += 8

    rr = vitals.get('resp_rate', 0)
    if rr > 28:   score += 20
    elif rr > 22: score += 12
    elif rr < 8:  score += 10

    sbp = vitals.get('systolic', 120)
    if sbp < 85:    score += 25
    elif sbp < 100: score += 15

    return score


# ── Full risk scoring ──────────────────────────────────────────────────────

def calculate_risk_score(vitals: dict, age: int = 40, comorbidities: dict = None):
    if comorbidities is None:
        comorbidities = {}

    base_score = calculate_base_score(vitals)
    comorbidity_penalty, active_conditions = get_comorbidity_penalty(comorbidities)
    age_multiplier = get_age_multiplier(age)

    adjusted_score = int((base_score + comorbidity_penalty) * age_multiplier)
    adjusted_score = min(adjusted_score, 100)

    if adjusted_score < 30:   risk_level = 'Low'
    elif adjusted_score < 50: risk_level = 'Low-Medium'
    elif adjusted_score < 65: risk_level = 'Medium'
    else:                     risk_level = 'High'

    return adjusted_score, risk_level, base_score, age_multiplier, comorbidity_penalty, active_conditions


# ── Bedrock clinical summary ───────────────────────────────────────────────

def generate_clinical_summary(patient_name, age, vitals, risk_score, risk_level,
                               active_conditions, base_score, age_multiplier, comorbidity_penalty):
    conditions_str = ", ".join(active_conditions) if active_conditions else "none reported"
    prompt = f"""You are a clinical decision support AI in an ICU.
A patient's vitals have triggered a sepsis early warning alert.

Patient: {patient_name}, Age: {age}
Known Comorbidities: {conditions_str}

Heart Rate: {vitals['heart_rate']} bpm (normal: 60-100)
Blood Pressure: {vitals['systolic']}/{vitals['diastolic']} mmHg (normal systolic: 90-120)
SpO2: {vitals['spo2']}% (normal: 95-100)
Respiratory Rate: {vitals['resp_rate']} breaths/min (normal: 12-20)
Temperature: {vitals['temperature']}°C (normal: 36.1-37.2)

Risk Scoring Breakdown:
  Base vitals score   : {base_score}/100
  Comorbidity penalty : +{comorbidity_penalty} points
  Age adjustment      : x{age_multiplier} (age {age})
  Final risk score    : {risk_score}/100 ({risk_level} Risk)

Write a 3-sentence clinical summary for the nurse.
Sentence 1: Which vitals are abnormal and how the patient's comorbidities increase their sepsis risk.
Sentence 2: What this pattern likely indicates clinically.
Sentence 3: The single most important immediate action to take.
Keep it clear, direct, and free of jargon."""

    try:
        body = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "inferenceConfig": {"maxTokens": 220, "temperature": 0.3}
        })
        response = bedrock.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text'].strip()

    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        abnormal = []
        if vitals['heart_rate'] > 100: abnormal.append(f"elevated HR ({vitals['heart_rate']} bpm)")
        if vitals['spo2'] < 94:        abnormal.append(f"low SpO2 ({vitals['spo2']}%)")
        if vitals['systolic'] < 100:   abnormal.append(f"low BP ({vitals['systolic']} mmHg)")
        if vitals['temperature'] > 38: abnormal.append(f"fever ({vitals['temperature']}°C)")
        abnormal_str = ", ".join(abnormal) if abnormal else "multiple parameters"
        conditions_note = f" with known {conditions_str}" if active_conditions else ""
        return (
            f"Patient {patient_name} (age {age}{conditions_note}) shows {abnormal_str}. "
            f"Risk score {risk_score}/100 ({risk_level}) is adjusted for age and comorbidities — "
            f"base vitals score was {base_score} before adjustment. "
            f"Immediate physician review and blood culture recommended."
        )


# ── Lambda handler ─────────────────────────────────────────────────────────

def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")

    try:
        patient_id    = str(event.get('patient_id', 'UNKNOWN'))
        name          = event.get('name', 'Unknown')
        age           = int(event.get('age', 40))
        condition     = event.get('condition', 'Unknown')
        comorbidities = event.get('comorbidities', {})
        timestamp     = event.get('timestamp', datetime.now(timezone.utc).isoformat())

        vitals = {
            'heart_rate':  float(event.get('heart_rate', 0)),
            'temperature': float(event.get('temperature', 0)),
            'spo2':        float(event.get('spo2', 100)),
            'resp_rate':   float(event.get('resp_rate', 0)),
            'systolic':    float(event.get('systolic', 120)),
            'diastolic':   float(event.get('diastolic', 80)),
        }

        # ── Risk scoring ──
        risk_score, risk_level, base_score, age_multiplier, comorbidity_penalty, active_conditions = \
            calculate_risk_score(vitals, age, comorbidities)

        # ── Bedrock summary ──
        clinical_summary = ""
        if risk_score >= 40:
            clinical_summary = generate_clinical_summary(
                name, age, vitals, risk_score, risk_level,
                active_conditions, base_score, age_multiplier, comorbidity_penalty
            )
            print(f"Bedrock summary: {clinical_summary}")

        # ── DynamoDB write ──
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'patient_id':          patient_id,
            'timestamp':           timestamp,
            'name':                name,
            'age':                 str(age),
            'condition':           condition,
            'heart_rate':          str(vitals['heart_rate']),
            'temperature':         str(vitals['temperature']),
            'spo2':                str(vitals['spo2']),
            'resp_rate':           str(vitals['resp_rate']),
            'systolic':            str(vitals['systolic']),
            'diastolic':           str(vitals['diastolic']),
            'risk_score':          str(risk_score),
            'risk_level':          risk_level,
            'base_score':          str(base_score),
            'age_multiplier':      str(age_multiplier),
            'comorbidity_penalty': str(comorbidity_penalty),
            'active_conditions':   ", ".join(active_conditions) if active_conditions else "None",
            'clinical_summary':    clinical_summary,
        })
        print(f"DynamoDB write: {patient_id} | Age: {age} | Base: {base_score} | "
              f"Comorbidity: +{comorbidity_penalty} | Multiplier: x{age_multiplier} | "
              f"Final Score: {risk_score} | Risk: {risk_level}")

        # ── SNS alert ──
        if risk_score >= RISK_THRESHOLD:
            conditions_str = ", ".join(active_conditions) if active_conditions else "None"
            alert_message = f"""
SEPSISWATCH AI — CRITICAL ALERT
=================================
Patient  : {name}  (ID: {patient_id})
Age      : {age} years
Condition: {condition}
Time     : {timestamp}

KNOWN COMORBIDITIES
-------------------
{conditions_str}

VITALS
------
Heart Rate     : {vitals['heart_rate']} bpm
Temperature    : {vitals['temperature']} C
SpO2           : {vitals['spo2']} %
Resp Rate      : {vitals['resp_rate']} breaths/min
Blood Pressure : {vitals['systolic']}/{vitals['diastolic']} mmHg

RISK ASSESSMENT (Comorbidity-Adjusted)
---------------------------------------
Base Vitals Score   : {base_score}/100
Comorbidity Penalty : +{comorbidity_penalty} points
Age Adjustment      : x{age_multiplier} (age {age})
Final Risk Score    : {risk_score}/100
Risk Level          : {risk_level}

AI CLINICAL SUMMARY
-------------------
{clinical_summary}

ACTION: Immediate physician review required.
"""
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=alert_message,
                Subject=f"SEPSIS ALERT — {name} (Age {age}) — Score {risk_score}/100"
            )
            print(f"SNS alert sent: {name} age={age} score={risk_score}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'patient_id':   patient_id,
                'risk_score':   risk_score,
                'risk_level':   risk_level,
                'base_score':   base_score,
                'age_multiplier': age_multiplier,
                'comorbidity_penalty': comorbidity_penalty,
            })
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise e