"""
SepsisWatch AI - ICU Dashboard
--------------------------------
Reads live patient data from AWS DynamoDB.
Full pipeline visible: IoT Core -> Lambda -> DynamoDB -> Dashboard
"""

import sys
import boto3
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from boto3.dynamodb.conditions import Key
from streamlit_autorefresh import st_autorefresh

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

REGION     = 'ap-south-1'
TABLE_NAME = 'PatientVitals'
PATIENT_IDS = ['101', '102', '103', '104', '105']

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="SepsisWatch AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st_autorefresh(interval=3000, key="autorefresh")

# ──────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #060f1e;
    color: #e8edf5;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 1400px;
}

.header-bar {
    background: linear-gradient(135deg, #0a2540 0%, #0f4c81 100%);
    border: 1px solid #1a4a7a;
    padding: 20px 28px;
    border-radius: 16px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}

.metric-box {
    background: #0d1f35;
    border: 1px solid #1a3a5c;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
}

.metric-box .label {
    font-size: 0.78rem;
    color: #7a9bbf;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}

.metric-box .value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}

.metric-box.total  .value { color: #4a9eff; }
.metric-box.low    .value { color: #2ecc71; }
.metric-box.medium .value { color: #f4d03f; }
.metric-box.high   .value { color: #e74c3c; }

.patient-card {
    background: #0d1f35;
    border: 1px solid #1a3a5c;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border-left: 5px solid #1a3a5c;
}

.patient-card.low    { border-left-color: #2ecc71; }
.patient-card.medium { border-left-color: #f4d03f; }
.patient-card.high   {
    border-left-color: #e74c3c;
    background: #150a0a;
    border-color: #5c1a1a;
    animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.3); }
    70%  { box-shadow: 0 0 0 8px rgba(231, 76, 60, 0); }
    100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }
}

.vital-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 12px 0;
}

.vital-pill {
    background: #0a1a2e;
    border: 1px solid #1e3d5a;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 0.85rem;
    display: flex;
    gap: 6px;
    align-items: center;
}

.vital-pill .label { color: #7a9bbf; }
.vital-pill .value { color: #e8edf5; font-weight: 600; }
.vital-pill.abnormal { border-color: #e74c3c; background: #1a0808; }

.risk-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}

.risk-badge.low    { background: #0d3320; color: #2ecc71; border: 1px solid #2ecc71; }
.risk-badge.medium { background: #332d00; color: #f4d03f; border: 1px solid #f4d03f; }
.risk-badge.high   { background: #330d0d; color: #e74c3c; border: 1px solid #e74c3c; }

.score-bar-bg {
    background: #0a1a2e;
    border-radius: 8px;
    height: 10px;
    margin: 6px 0 10px 0;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

.summary-box {
    background: #0a1e33;
    border: 1px solid #1e4a6e;
    border-left: 4px solid #4a9eff;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 12px;
    font-size: 0.88rem;
    color: #c8d8ea;
    line-height: 1.6;
}

.aws-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0a2035;
    border: 1px solid #1a4a6e;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #7ab8e8;
}

.pipeline-status {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.pipeline-step {
    background: #0d1f35;
    border: 1px solid #1a3a5c;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.78rem;
    color: #7a9bbf;
}

.pipeline-step.active { color: #2ecc71; border-color: #2ecc71; }
.pipeline-arrow { color: #2a4a6a; font-size: 1rem; }

.stDivider { border-color: #1a3a5c; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# DATA LAYER — DynamoDB
# ──────────────────────────────────────────────

@st.cache_resource
def get_dynamodb():
    return boto3.resource('dynamodb', region_name=REGION)


def get_latest_vitals(table, patient_id: str) -> dict | None:
    """Get the most recent record for a patient from DynamoDB."""
    try:
        response = table.query(
            KeyConditionExpression=Key('patient_id').eq(patient_id),
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"DynamoDB query error for {patient_id}: {e}")
        return None


def get_vital_history(table, patient_id: str, limit: int = 20) -> list:
    """Get last N records for trend charts."""
    try:
        response = table.query(
            KeyConditionExpression=Key('patient_id').eq(patient_id),
            ScanIndexForward=False,
            Limit=limit
        )
        items = response.get('Items', [])
        items.reverse()
        return items
    except Exception:
        return []


def parse_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

st.markdown("""
<div class="header-bar">
    <div>
        <h2 style="margin:0; color:#e8edf5;">🏥 SepsisWatch AI</h2>
        <p style="margin:4px 0 0 0; color:#7a9bbf; font-size:0.9rem;">
            AI-Powered ICU Early Warning System
        </p>
    </div>
    <div style="text-align:right;">
        <div class="aws-badge">☁ Live AWS Pipeline</div>
        <p style="margin:6px 0 0 0; color:#4a6a8a; font-size:0.75rem;">
            IoT Core → Lambda → DynamoDB → Dashboard
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Pipeline status bar
st.markdown("""
<div class="pipeline-status">
    <span class="pipeline-step active">✓ IoT Core</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step active">✓ Lambda</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step active">✓ DynamoDB</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step active">✓ SNS Alerts</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step active">✓ Bedrock AI</span>
    <span class="pipeline-arrow">→</span>
    <span class="pipeline-step active">✓ Dashboard</span>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────

db    = get_dynamodb()
table = db.Table(TABLE_NAME)

all_patients = []
for pid in PATIENT_IDS:
    record = get_latest_vitals(table, pid)
    if record:
        all_patients.append(record)

if not all_patients:
    st.warning("No data in DynamoDB yet. Start the simulator: `python simulator/vitals_simulator.py`")
    st.stop()

# Sort by risk score descending (highest risk first)
all_patients.sort(key=lambda x: parse_float(x.get('risk_score', 0)), reverse=True)

# ──────────────────────────────────────────────
# SUMMARY METRICS
# ──────────────────────────────────────────────

low_count    = sum(1 for p in all_patients if p.get('risk_level') == 'Low')
medium_count = sum(1 for p in all_patients if p.get('risk_level') == 'Medium')
high_count   = sum(1 for p in all_patients if p.get('risk_level') == 'High')

if high_count > 0:
    st.error(f"🚨 CRITICAL ALERT: {high_count} patient(s) at HIGH sepsis risk — immediate action required")

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-box total">
        <div class="label">Total Patients</div>
        <div class="value">{len(all_patients)}</div>
    </div>
    <div class="metric-box low">
        <div class="label">Low Risk</div>
        <div class="value">{low_count}</div>
    </div>
    <div class="metric-box medium">
        <div class="label">Medium Risk</div>
        <div class="value">{medium_count}</div>
    </div>
    <div class="metric-box high">
        <div class="label">High Risk</div>
        <div class="value">{high_count}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🏥 Live ICU Patient Monitor")

# ──────────────────────────────────────────────
# PATIENT CARDS
# ──────────────────────────────────────────────

for patient in all_patients:
    pid         = patient.get('patient_id', '?')
    name        = patient.get('name', 'Unknown')
    condition   = patient.get('condition', 'Unknown')
    risk_level  = patient.get('risk_level', 'Low')
    risk_score  = parse_float(patient.get('risk_score', 0))
    summary     = patient.get('clinical_summary', '')
    timestamp   = patient.get('timestamp', '')

    hr   = parse_float(patient.get('heart_rate',  0))
    temp = parse_float(patient.get('temperature', 0))
    spo2 = parse_float(patient.get('spo2',        100))
    rr   = parse_float(patient.get('resp_rate',   0))
    sbp  = parse_float(patient.get('systolic',    120))
    dbp  = parse_float(patient.get('diastolic',   80))

    css_class = risk_level.lower()

    # Bar colour
    if risk_score < 30:    bar_colour = "#2ecc71"
    elif risk_score < 65:  bar_colour = "#f4d03f"
    else:                  bar_colour = "#e74c3c"

    # Abnormal flags
    hr_ab   = hr > 100 or hr < 55
    temp_ab = temp >= 38 or temp < 36
    spo2_ab = spo2 < 94
    rr_ab   = rr > 22
    sbp_ab  = sbp < 100

    def pill(icon, label, val, unit, abnormal=False):
        cls = "vital-pill abnormal" if abnormal else "vital-pill"
        return f'<span class="{cls}"><span class="label">{icon} {label}</span><span class="value">{val} {unit}</span></span>'

    vitals_html = (
        pill("❤️", "HR",    int(hr),   "bpm",          hr_ab)   +
        pill("🌡",  "Temp",  temp,      "°C",           temp_ab) +
        pill("🫁", "SpO₂",  int(spo2), "%",            spo2_ab) +
        pill("🌬", "RR",    int(rr),   "br/min",       rr_ab)   +
        pill("🩸", "BP",    f"{int(sbp)}/{int(dbp)}", "mmHg",  sbp_ab)
    )

    try:
        ts_fmt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S UTC')
    except Exception:
        ts_fmt = timestamp[:19] if timestamp else ''

    badge_cls = css_class

    st.markdown(f"""
<div class="patient-card {css_class}">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <h3 style="margin:0; color:#e8edf5;">🛏 Bed {pid} &nbsp;·&nbsp; {name}</h3>
            <p style="margin:4px 0 0 0; color:#7a9bbf; font-size:0.82rem;">{condition} &nbsp;·&nbsp; Last updated: {ts_fmt}</p>
        </div>
        <div style="text-align:right;">
            <span class="risk-badge {badge_cls}">{risk_level.upper()} RISK</span>
            <p style="margin:6px 0 2px 0; color:#7a9bbf; font-size:0.78rem;">Sepsis Risk Score</p>
            <p style="margin:0; font-size:1.6rem; font-weight:700; color:{bar_colour};">{int(risk_score)}<span style="font-size:0.9rem; color:#7a9bbf;">/100</span></p>
            <div class="score-bar-bg">
                <div class="score-bar-fill" style="width:{risk_score}%; background:{bar_colour};"></div>
            </div>
        </div>
    </div>
    <div class="vital-row">{vitals_html}</div>
</div>
""", unsafe_allow_html=True)

    # Bedrock clinical summary
    if summary:
        st.markdown(f"""
<div class="summary-box">
    <strong style="color:#4a9eff;">🤖 AWS Bedrock Clinical Summary</strong><br><br>
    {summary}
</div>
""", unsafe_allow_html=True)

    # Trend charts
    history = get_vital_history(table, pid, limit=20)
    if len(history) >= 3:
        df = pd.DataFrame([{
            'HR':    parse_float(h.get('heart_rate')),
            'SpO2':  parse_float(h.get('spo2')),
            'Score': parse_float(h.get('risk_score')),
            'Temp':  parse_float(h.get('temperature')),
        } for h in history])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.caption("Heart Rate (bpm)")
            st.line_chart(df['HR'], height=100, use_container_width=True)
        with c2:
            st.caption("SpO2 (%)")
            st.line_chart(df['SpO2'], height=100, use_container_width=True)
        with c3:
            st.caption("Temperature (°C)")
            st.line_chart(df['Temp'], height=100, use_container_width=True)
        with c4:
            st.caption("Risk Score")
            st.line_chart(df['Score'], height=100, use_container_width=True)

    st.markdown("<hr style='border-color:#1a3a5c; margin: 16px 0;'>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown("""
<p style='text-align:center; color:#2a4a6a; font-size:0.78rem; margin-top:20px;'>
SepsisWatch AI &nbsp;·&nbsp; Team HackZen &nbsp;·&nbsp; SMVEC &nbsp;·&nbsp; #include 1.0 &nbsp;·&nbsp;
AWS IoT Core · Lambda · DynamoDB · SNS · Bedrock
</p>
""", unsafe_allow_html=True)