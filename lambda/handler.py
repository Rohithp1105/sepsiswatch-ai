import json
import boto3
import os
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
sns = boto3.client('sns', region_name='ap-south-1')

TABLE_NAME = 'PatientVitals'
SNS_TOPIC_ARN = 'REPLACE_WITH_YOUR_SNS_TOPIC_ARN'
RISK_THRESHOLD = 65


def calculate_risk_score(vitals):
    score = 0

    hr = vitals.get('heart_rate', 0)
    if hr > 120:
        score += 25
    elif hr > 100:
        score += 15
    elif hr < 55:
        score += 10

    temp = vitals.get('temperature', 0)
    if temp >= 39.0:
        score += 20
    elif temp >= 38.0:
        score += 12
    elif temp < 36.0:
        score += 15

    spo2 = vitals.get('spo2', 100)
    if spo2 < 90:
        score += 30
    elif spo2 < 94:
        score += 20
    elif spo2 < 96:
        score += 8

    rr = vitals.get('resp_rate', 0)
    if rr > 28:
        score += 20
    elif rr > 22:
        score += 12
    elif rr < 8:
        score += 10

    sbp = vitals.get('systolic', 120)
    if sbp < 85:
        score += 25
    elif sbp < 100:
        score += 15

    score = min(score, 100)

    if score < 30:
        risk_level = 'Low'
    elif score < 60:
        risk_level = 'Medium'
    else:
        risk_level = 'High'

    return score, risk_level


def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        patient_id = str(event.get('patient_id', 'UNKNOWN'))
        name = event.get('name', 'Unknown')
        condition = event.get('condition', 'Unknown')
        timestamp = event.get('timestamp', datetime.now(timezone.utc).isoformat())

        vitals = {
            'heart_rate': float(event.get('heart_rate', 0)),
            'temperature': float(event.get('temperature', 0)),
            'spo2': float(event.get('spo2', 100)),
            'resp_rate': float(event.get('resp_rate', 0)),
            'systolic': float(event.get('systolic', 120)),
            'diastolic': float(event.get('diastolic', 80)),
        }

        risk_score, risk_level = calculate_risk_score(vitals)

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'patient_id': patient_id,
            'timestamp': timestamp,
            'name': name,
            'condition': condition,
            'heart_rate': str(vitals['heart_rate']),
            'temperature': str(vitals['temperature']),
            'spo2': str(vitals['spo2']),
            'resp_rate': str(vitals['resp_rate']),
            'systolic': str(vitals['systolic']),
            'diastolic': str(vitals['diastolic']),
            'risk_score': str(risk_score),
            'risk_level': risk_level,
        })

        print(f"Saved to DynamoDB: {patient_id} | Score: {risk_score} | Risk: {risk_level}")

        if risk_score >= RISK_THRESHOLD:
            alert_message = f"""
SEPSISWATCH AI ALERT
====================
Patient  : {name} (ID: {patient_id})
Condition: {condition}
Time     : {timestamp}

VITALS
------
Heart Rate     : {vitals['heart_rate']} bpm
Temperature    : {vitals['temperature']} C
SpO2           : {vitals['spo2']} %
Resp Rate      : {vitals['resp_rate']} breaths/min
Blood Pressure : {vitals['systolic']}/{vitals['diastolic']} mmHg

RISK ASSESSMENT
---------------
Risk Score : {risk_score}/100
Risk Level : {risk_level}

ACTION REQUIRED: Immediate physician review recommended.
"""
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=alert_message,
                Subject=f"SEPSIS ALERT - {name} (Bed {patient_id}) - Score {risk_score}/100"
            )
            print(f"SNS alert sent for {name} with score {risk_score}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'patient_id': patient_id,
                'risk_score': risk_score,
                'risk_level': risk_level
            })
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise e
