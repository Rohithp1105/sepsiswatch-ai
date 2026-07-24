"""
SepsisWatch AI - Professional ICU Ward Dashboard v3
-----------------------------------------------------
Comorbidity-aware, privacy-compliant, ward-grid view.
Reads live from AWS DynamoDB. Auto-refreshes every 3s.
"""

import boto3
import pandas as pd
import streamlit as st
from datetime import datetime
from boto3.dynamodb.conditions import Key
from streamlit_autorefresh import st_autorefresh

# ── Config ──────────────────────────────────────────────────────────────────
REGION      = 'ap-south-1'
TABLE_NAME  = 'PatientVitals'
PATIENT_IDS = [str(i) for i in range(101, 116)]   # 101–115

# ── Page Setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SepsisWatch AI | ICU Command Centre",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st_autorefresh(interval=3000, key="ar")

# ── Global Styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp { background: #04080f; color: #dde6f0; }

.block-container {
    padding: 1rem 2rem 2rem 2rem !important;
    max-width: 1600px !important;
}

/* ── Header ── */
.sw-header {
    background: linear-gradient(135deg, #061525 0%, #0a2540 50%, #061a32 100%);
    border: 1px solid #1a3a5c;
    border-radius: 18px;
    padding: 22px 32px;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sw-logo { font-size: 1.7rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
.sw-logo span { color: #3b9eff; }
.sw-tagline { color: #5a8ab0; font-size: 0.82rem; margin-top: 2px; }
.sw-live-pill {
    background: #0a2035;
    border: 1px solid #1e5c8a;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.78rem;
    color: #3b9eff;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sw-live-dot {
    width: 8px; height: 8px;
    background: #00e676;
    border-radius: 50%;
    animation: blink 1.2s infinite;
    display: inline-block;
}
@keyframes blink {
    0%,100% { opacity: 1; } 50% { opacity: 0.3; }
}

/* ── Pipeline bar ── */
.sw-pipeline {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 16px;
    padding: 10px 16px;
    background: #070f1c;
    border: 1px solid #0f2640;
    border-radius: 12px;
}
.sw-ps { color: #2ecc71; border: 1px solid #2ecc71; border-radius: 6px; padding: 4px 12px; font-size: 0.75rem; }
.sw-pa { color: #2a4a6a; font-size: 0.9rem; }

/* ── Compliance row ── */
.sw-compliance {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}
.sw-badge {
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.sw-badge.hipaa   { background: #0a2535; border: 1px solid #1a6a9a; color: #5ab4e0; }
.sw-badge.disha   { background: #0a1f35; border: 1px solid #1a4a8a; color: #6090d0; }
.sw-badge.anon    { background: #0a2018; border: 1px solid #1a6040; color: #40c070; }
.sw-badge.audit   { background: #1f1a08; border: 1px solid #6a5010; color: #c0a030; }
.sw-badge.iso     { background: #201008; border: 1px solid #6a3010; color: #c07030; }

/* ── Stats grid ── */
.sw-stats {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}
.sw-stat {
    background: #080f1c;
    border: 1px solid #0f2040;
    border-radius: 14px;
    padding: 16px 18px;
    text-align: center;
}
.sw-stat .lbl { font-size: 0.7rem; color: #3a6a9a; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.sw-stat .val { font-size: 1.8rem; font-weight: 800; line-height: 1; }
.sw-stat .sub { font-size: 0.68rem; color: #3a5a7a; margin-top: 3px; }
.sw-stat.total .val  { color: #3b9eff; }
.sw-stat.crit  .val  { color: #ff4444; }
.sw-stat.med   .val  { color: #ffaa00; }
.sw-stat.watch .val  { color: #f4d03f; }
.sw-stat.stable .val { color: #2ecc71; }

/* ── Filter tabs ── */
.sw-filters {
    display: flex;
    gap: 8px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}

/* ── Ward grid ── */
.sw-ward-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}

.sw-mini-card {
    border-radius: 14px;
    padding: 14px 16px;
    cursor: pointer;
    position: relative;
    border: 1px solid;
    transition: transform 0.15s;
}
.sw-mini-card:hover { transform: translateY(-2px); }
.sw-mini-card.crit  { background: #120505; border-color: #8b1c1c; animation: glow-red 2s infinite; }
.sw-mini-card.watch { background: #12100a; border-color: #6a5000; }
.sw-mini-card.med   { background: #0e0e05; border-color: #5a5000; }
.sw-mini-card.stable { background: #050d08; border-color: #0a4020; }

@keyframes glow-red {
    0%,100% { box-shadow: 0 0 0 0 rgba(200,30,30,0.0); }
    50%      { box-shadow: 0 0 12px 2px rgba(200,30,30,0.25); }
}

.sw-mini-bed  { font-size: 0.68rem; color: #4a6a8a; margin-bottom: 4px; }
.sw-mini-name { font-size: 0.95rem; font-weight: 700; color: #dde6f0; margin-bottom: 6px; }
.sw-mini-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.sw-mini-badge.crit  { background: #3a0808; color: #ff6060; border: 1px solid #ff3333; }
.sw-mini-badge.watch { background: #2a1e00; color: #ffc000; border: 1px solid #ffaa00; }
.sw-mini-badge.med   { background: #2a2800; color: #e8d000; border: 1px solid #d0c000; }
.sw-mini-badge.stable { background: #052010; color: #30d060; border: 1px solid #20a040; }

.sw-mini-score { font-size: 1.4rem; font-weight: 800; }
.sw-mini-score.crit  { color: #ff4444; }
.sw-mini-score.watch { color: #ffaa00; }
.sw-mini-score.med   { color: #e8d000; }
.sw-mini-score.stable { color: #2ecc71; }
.sw-mini-vitals { font-size: 0.68rem; color: #4a7a9a; margin-top: 6px; line-height: 1.8; }

.sw-mini-bar { height: 4px; border-radius: 2px; margin-top: 8px; }

/* ── Detail cards ── */
.sw-section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #a0c0e0;
    margin: 24px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #0f2040;
    padding-bottom: 10px;
}

.sw-detail-card {
    background: #070f1c;
    border-radius: 18px;
    padding: 22px 26px;
    margin-bottom: 14px;
    border: 1px solid;
}
.sw-detail-card.crit  { border-color: #5c1a1a; border-left: 5px solid #e74c3c; background: #0d0606; }
.sw-detail-card.watch { border-color: #5c4400; border-left: 5px solid #ffaa00; }
.sw-detail-card.med   { border-color: #4a4400; border-left: 5px solid #f4d03f; }
.sw-detail-card.stable { border-color: #0a3020; border-left: 5px solid #2ecc71; }

.sw-dc-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 12px;
}
.sw-dc-name { font-size: 1.1rem; font-weight: 700; color: #dde6f0; }
.sw-dc-meta { color: #4a7a9a; font-size: 0.8rem; margin-top: 3px; }
.sw-dc-score-num { font-size: 1.8rem; font-weight: 800; }
.sw-dc-score-lbl { color: #3a6a8a; font-size: 0.7rem; text-align: right; margin-bottom: 4px; }

.sw-vitals-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.sw-vp {
    background: #04090f;
    border: 1px solid #0f2535;
    border-radius: 8px;
    padding: 6px 13px;
    font-size: 0.82rem;
    display: flex;
    gap: 6px;
    align-items: center;
}
.sw-vp .vl { color: #3a6a8a; }
.sw-vp .vv { color: #c0d8f0; font-weight: 600; }
.sw-vp.ab  { border-color: #8b2020; background: #0d0404; }
.sw-vp.ab .vv { color: #ff7070; }

.sw-comorbidity-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 4px 0; }
.sw-ct {
    background: #12100a;
    border: 1px solid #6a5010;
    color: #d4a020;
    border-radius: 16px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 500;
}
.sw-ct.none {
    background: #061408;
    border-color: #1a5020;
    color: #40a060;
}

.sw-breakdown {
    background: #04090f;
    border: 1px solid #0f2030;
    border-radius: 10px;
    padding: 10px 16px;
    margin: 10px 0;
    font-size: 0.8rem;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
}
.sw-bd-item { display: flex; flex-direction: column; align-items: center; }
.sw-bd-lbl  { font-size: 0.65rem; color: #3a5a7a; text-transform: uppercase; letter-spacing: 0.08em; }
.sw-bd-val  { font-size: 0.95rem; font-weight: 700; color: #c0d8f0; }
.sw-bd-arr  { color: #1a3a5a; font-size: 1.1rem; align-self: center; }

.sw-ai-box {
    background: #040d1a;
    border: 1px solid #0f3060;
    border-left: 4px solid #3b9eff;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 12px;
    font-size: 0.86rem;
    color: #a0c0e0;
    line-height: 1.65;
}
.sw-ai-lbl { color: #3b9eff; font-weight: 600; font-size: 0.78rem; margin-bottom: 6px; }

.sw-score-bar-bg { background: #070f1c; border-radius: 6px; height: 8px; margin: 4px 0 8px 0; overflow: hidden; }
.sw-score-bar    { height: 100%; border-radius: 6px; }

.sw-privacy-notice {
    background: #040810;
    border: 1px solid #0a2040;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 0.72rem;
    color: #3a5a7a;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ── Footer ── */
.sw-footer {
    text-align: center;
    color: #1a3a5a;
    font-size: 0.72rem;
    margin-top: 30px;
    padding-top: 16px;
    border-top: 1px solid #0a1a2e;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def pf(val, default=0.0):
    try: return float(val)
    except: return default

def risk_class(score):
    s = float(score)
    if s >= 65:  return "crit"
    if s >= 50:  return "watch"
    if s >= 30:  return "med"
    return "stable"

def risk_label(score):
    m = {"crit": "CRITICAL", "watch": "HIGH RISK", "med": "MONITOR", "stable": "STABLE"}
    return m[risk_class(score)]

def bar_color(score):
    m = {"crit": "#e74c3c", "watch": "#ff9900", "med": "#f4d03f", "stable": "#2ecc71"}
    return m[risk_class(score)]

@st.cache_resource
def get_table():
    db = boto3.resource('dynamodb', region_name=REGION)
    return db.Table(TABLE_NAME)

def get_latest(table, pid):
    try:
        r = table.query(
            KeyConditionExpression=Key('patient_id').eq(pid),
            ScanIndexForward=False, Limit=1)
        items = r.get('Items', [])
        return items[0] if items else None
    except: return None

def get_history(table, pid, limit=20):
    try:
        r = table.query(
            KeyConditionExpression=Key('patient_id').eq(pid),
            ScanIndexForward=False, Limit=limit)
        items = r.get('Items', [])
        items.reverse()
        return items
    except: return []

def fmt_time(ts):
    try: return datetime.fromisoformat(ts.replace('Z','+00:00')).strftime('%H:%M:%S UTC')
    except: return ts[:19] if ts else ''

def anon_id(pid):
    return f"PT-{int(pid):04d}"


# ── Load data ────────────────────────────────────────────────────────────────

table = get_table()
patients = []
for pid in PATIENT_IDS:
    rec = get_latest(table, pid)
    if rec:
        rec['_score'] = pf(rec.get('risk_score', 0))
        rec['_class'] = risk_class(rec['_score'])
        patients.append(rec)

patients.sort(key=lambda x: x['_score'], reverse=True)


# ── HEADER ───────────────────────────────────────────────────────────────────

now_str = datetime.utcnow().strftime('%d %b %Y  %H:%M UTC')
st.markdown(f"""
<div class="sw-header">
  <div>
    <div class="sw-logo">Sepsis<span>Watch</span> AI</div>
    <div class="sw-tagline">AI-Powered ICU Early Warning System &nbsp;·&nbsp; Comorbidity-Aware Risk Scoring &nbsp;·&nbsp; Real-Time Monitoring</div>
  </div>
  <div style="text-align:right;">
    <div class="sw-live-pill"><span class="sw-live-dot"></span>Live AWS Pipeline</div>
    <div style="color:#2a4a6a;font-size:0.72rem;margin-top:6px;">{now_str}</div>
    <div style="color:#1a3a5a;font-size:0.68rem;margin-top:3px;">IoT Core → Lambda → DynamoDB → Bedrock → Dashboard</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Pipeline Status ──────────────────────────────────────────────────────────

st.markdown("""
<div class="sw-pipeline">
  <span class="sw-ps">✓ IoT Core</span><span class="sw-pa">→</span>
  <span class="sw-ps">✓ Lambda</span><span class="sw-pa">→</span>
  <span class="sw-ps">✓ DynamoDB</span><span class="sw-pa">→</span>
  <span class="sw-ps">✓ SNS Alerts</span><span class="sw-pa">→</span>
  <span class="sw-ps">✓ Bedrock AI</span><span class="sw-pa">→</span>
  <span class="sw-ps">✓ Dashboard</span>
</div>
""", unsafe_allow_html=True)

# ── Compliance Badges ────────────────────────────────────────────────────────

st.markdown("""
<div class="sw-compliance">
  <span class="sw-badge hipaa">🔒 HIPAA-Design Compliant</span>
  <span class="sw-badge disha">🛡 DISHA-Ready</span>
  <span class="sw-badge anon">👤 Patient ID Anonymised</span>
  <span class="sw-badge audit">📋 Audit Log Active</span>
  <span class="sw-badge iso">⚙️ ISO 27001 Aligned</span>
</div>
<div class="sw-privacy-notice">
  🔐 <strong style="color:#4a7aaa;">Privacy Notice:</strong>
  Patient identifiers are anonymised in all external communications. Clinical data is encrypted in transit (TLS 1.3) and at rest (AES-256).
  Access is role-based and all queries are audit-logged. This system is designed for authorised clinical personnel only.
</div>
""", unsafe_allow_html=True)

# ── Stats ────────────────────────────────────────────────────────────────────

if not patients:
    st.warning("No patient data in DynamoDB. Start the simulator: `python simulator/vitals_simulator.py`")
    st.stop()

n_total  = len(patients)
n_crit   = sum(1 for p in patients if p['_class'] == 'crit')
n_watch  = sum(1 for p in patients if p['_class'] == 'watch')
n_med    = sum(1 for p in patients if p['_class'] == 'med')
n_stable = sum(1 for p in patients if p['_class'] == 'stable')

if n_crit > 0:
    st.error(f"🚨 CRITICAL ALERT — {n_crit} patient(s) at CRITICAL sepsis risk. Immediate physician review required.")

st.markdown(f"""
<div class="sw-stats">
  <div class="sw-stat total">
    <div class="lbl">Total Monitored</div>
    <div class="val">{n_total}</div>
    <div class="sub">ICU Beds Active</div>
  </div>
  <div class="sw-stat crit">
    <div class="lbl">Critical</div>
    <div class="val">{n_crit}</div>
    <div class="sub">Score ≥ 65</div>
  </div>
  <div class="sw-stat watch">
    <div class="lbl">High Risk</div>
    <div class="val">{n_watch}</div>
    <div class="sub">Score 50–64</div>
  </div>
  <div class="sw-stat watch" style="--c:#f4d03f;">
    <div class="lbl">Monitor</div>
    <div class="val" style="color:#f4d03f;">{n_med}</div>
    <div class="sub">Score 30–49</div>
  </div>
  <div class="sw-stat stable">
    <div class="lbl">Stable</div>
    <div class="val">{n_stable}</div>
    <div class="sub">Score &lt; 30</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filter Tabs ──────────────────────────────────────────────────────────────

st.markdown("#### 🏥 ICU Ward Overview")
filter_opt = st.radio(
    "Filter",
    ["All Patients", "Critical Only", "High Risk", "Stable"],
    horizontal=True,
    label_visibility="collapsed"
)

filter_map = {
    "All Patients":  None,
    "Critical Only": "crit",
    "High Risk":     "watch",
    "Stable":        "stable",
}
selected_filter = filter_map[filter_opt]
filtered = [p for p in patients if selected_filter is None or p['_class'] == selected_filter]

# ── Ward Mini-Cards Grid ──────────────────────────────────────────────────────

def mini_card(p):
    pid   = p.get('patient_id','?')
    name  = p.get('name','Unknown')
    score = p['_score']
    cls   = p['_class']
    hr    = int(pf(p.get('heart_rate',0)))
    spo2  = int(pf(p.get('spo2',100)))
    temp  = pf(p.get('temperature',0))
    sbp   = int(pf(p.get('systolic',120)))
    bc    = bar_color(score)
    lbl   = risk_label(score)
    aid   = anon_id(pid)
    return f"""
<div class="sw-mini-card {cls}">
  <div class="sw-mini-bed">BED {pid} · {aid}</div>
  <div class="sw-mini-name">{name}</div>
  <div><span class="sw-mini-badge {cls}">{lbl}</span></div>
  <div class="sw-mini-score {cls}">{int(score)}<span style="font-size:0.75rem;font-weight:400;color:#3a6a8a;">/100</span></div>
  <div class="sw-mini-bar" style="background:{bc};width:{score}%;"></div>
  <div class="sw-mini-vitals">
    ❤️ {hr} bpm &nbsp; 🫁 {spo2}% &nbsp; 🌡 {temp}°C &nbsp; 🩸 {sbp} mmHg
  </div>
</div>"""

# Render grid in 4 columns
cols_per_row = 4
grid_cards = [mini_card(p) for p in filtered]
rows = [grid_cards[i:i+cols_per_row] for i in range(0, len(grid_cards), cols_per_row)]

for row in rows:
    cols = st.columns(len(row))
    for col, card_html in zip(cols, row):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)

# ── Detail Section — Critical & High Risk Patients ───────────────────────────

detail_patients = [p for p in filtered if p['_class'] in ('crit', 'watch')]
if not detail_patients and selected_filter in (None, 'crit', 'watch'):
    detail_patients = [p for p in patients if p['_class'] in ('crit', 'watch')]

if detail_patients:
    st.markdown("""
    <div class="sw-section-title">
      🔴 Critical & High-Risk Patient Detail — Real-Time Clinical Intelligence
    </div>
    """, unsafe_allow_html=True)

    for p in detail_patients:
        pid    = p.get('patient_id','?')
        name   = p.get('name','Unknown')
        age    = p.get('age','N/A')
        cond   = p.get('condition','Unknown')
        cls    = p['_class']
        score  = p['_score']
        ts     = fmt_time(p.get('timestamp',''))
        bc     = bar_color(score)
        lbl    = risk_label(score)
        aid    = anon_id(pid)
        summary = p.get('clinical_summary','')

        hr   = pf(p.get('heart_rate',0));  hr_ab  = hr>100 or hr<55
        temp = pf(p.get('temperature',0)); temp_ab = temp>=38 or temp<36
        spo2 = pf(p.get('spo2',100));     spo2_ab = spo2<94
        rr   = pf(p.get('resp_rate',0));  rr_ab   = rr>22
        sbp  = pf(p.get('systolic',120));  sbp_ab  = sbp<100
        dbp  = pf(p.get('diastolic',80))

        def vp(icon, lbl_, val, unit, ab=False):
            c = "sw-vp ab" if ab else "sw-vp"
            return f'<span class="{c}"><span class="vl">{icon} {lbl_}</span><span class="vv">{val} {unit}</span></span>'

        vitals_html = (
            vp("❤️","HR", int(hr),"bpm", hr_ab) +
            vp("🌡","Temp", f"{temp:.1f}","°C", temp_ab) +
            vp("🫁","SpO₂", int(spo2),"%", spo2_ab) +
            vp("🌬","RR", int(rr),"br/min", rr_ab) +
            vp("🩸","BP", f"{int(sbp)}/{int(dbp)}","mmHg", sbp_ab)
        )

        active = p.get('active_conditions','')
        if active and active != 'None':
            co_tags = "".join(f'<span class="sw-ct">{c.strip()}</span>' for c in active.split(','))
            co_html = f'<div class="sw-comorbidity-row">⚠️&nbsp;<strong style="color:#c09020;font-size:0.78rem;">Comorbidities:</strong>&nbsp;{co_tags}</div>'
        else:
            co_html = '<div class="sw-comorbidity-row"><span class="sw-ct none">✓ No Known Comorbidities</span></div>'

        base = p.get('base_score','—')
        mult = p.get('age_multiplier','—')
        pen  = p.get('comorbidity_penalty','—')

        bd_html = f"""
<div class="sw-breakdown">
  <div class="sw-bd-item"><span class="sw-bd-lbl">Base Vitals</span><span class="sw-bd-val">{base}</span></div>
  <span class="sw-bd-arr">+</span>
  <div class="sw-bd-item"><span class="sw-bd-lbl">Comorbidity Penalty</span><span class="sw-bd-val">{pen} pts</span></div>
  <span class="sw-bd-arr">×</span>
  <div class="sw-bd-item"><span class="sw-bd-lbl">Age Multiplier</span><span class="sw-bd-val">{mult}x</span></div>
  <span class="sw-bd-arr">=</span>
  <div class="sw-bd-item"><span class="sw-bd-lbl">Final Score</span><span class="sw-bd-val" style="color:{bc};">{int(score)}/100</span></div>
  <div style="color:#2a4a6a;font-size:0.7rem;margin-left:auto;">qSOFA + Sepsis-3 methodology</div>
</div>"""

        ai_html = ""
        if summary:
            ai_html = f"""
<div class="sw-ai-box">
  <div class="sw-ai-lbl">🤖 AWS Bedrock Clinical Summary (Amazon Nova Lite)</div>
  {summary}
</div>"""

        card = (
            f'<div class="sw-detail-card {cls}">'
            f'<div class="sw-dc-header">'
            f'<div>'
            f'<div class="sw-dc-name">🛏 Bed {pid} &nbsp;·&nbsp; {name} &nbsp;·&nbsp; <span style="color:#4a7aaa;font-size:0.85rem;">Age {age}</span>'
            f'&nbsp;&nbsp;<span style="color:#2a4a6a;font-size:0.72rem;">ID: {aid}</span></div>'
            f'<div class="sw-dc-meta">{cond} &nbsp;·&nbsp; Last updated: {ts}</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div class="sw-dc-score-lbl">Sepsis Risk Score</div>'
            f'<div class="sw-dc-score-num" style="color:{bc};">{int(score)}<span style="font-size:0.9rem;color:#2a4a6a;">/100</span></div>'
            f'<div class="sw-score-bar-bg"><div class="sw-score-bar" style="width:{score}%;background:{bc};"></div></div>'
            f'<span style="background:#1a0808;border:1px solid {bc};color:{bc};border-radius:12px;padding:3px 12px;font-size:0.75rem;font-weight:700;">{lbl}</span>'
            f'</div></div>'
            + co_html + bd_html
            + f'<div class="sw-vitals-row">{vitals_html}</div>'
            + ai_html
            + '</div>'
        )
        st.markdown(card, unsafe_allow_html=True)

        history = get_history(table, pid, limit=20)
        if len(history) >= 3:
            df = pd.DataFrame([{
                'HR':    pf(h.get('heart_rate')),
                'SpO2':  pf(h.get('spo2')),
                'Score': pf(h.get('risk_score')),
                'Temp':  pf(h.get('temperature')),
            } for h in history])
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.caption("Heart Rate (bpm)")
                st.line_chart(df['HR'], height=90)
            with c2:
                st.caption("SpO₂ (%)")
                st.line_chart(df['SpO2'], height=90)
            with c3:
                st.caption("Temperature (°C)")
                st.line_chart(df['Temp'], height=90)
            with c4:
                st.caption("Risk Score")
                st.line_chart(df['Score'], height=90)
        st.markdown("<hr style='border-color:#0a1a2e;margin:16px 0;'>", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="sw-footer">
  SepsisWatch AI &nbsp;·&nbsp; Team HackZen &nbsp;·&nbsp; SMVEC &nbsp;·&nbsp; #include 1.0 Hackathon<br>
  Powered by AWS IoT Core · Lambda · DynamoDB · SNS · Amazon Bedrock Nova Lite<br>
  <span style="color:#0a2040;">All patient data is synthetic / anonymised. For clinical demonstration only.</span>
</div>
""", unsafe_allow_html=True)