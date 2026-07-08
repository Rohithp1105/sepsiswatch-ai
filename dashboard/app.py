
# ============================
# SepsisWatch AI - app.py
# Version 1 UI Refresh
# ============================

import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "simulator"))
sys.path.append(str(ROOT / "ml"))
sys.path.append(str(ROOT / "utils"))

from vitals_simulator import get_live_data
from predict import predict_sepsis
from history import update_history, get_history

st.set_page_config(page_title="SepsisWatch AI",
                   page_icon="🏥",
                   layout="wide")

st_autorefresh(interval=2000, key="refresh")

st.markdown("""
<style>
.stApp{
 background:#07111f;
 color:#F5F7FA;
}
.block-container{
 padding-top:1.2rem;
}
.metric-card{
 background:#12263A;
 padding:16px;
 border-radius:14px;
 border-left:6px solid #1f77ff;
 margin-bottom:12px;
}
.patient-card{
 background:#12263A;
 padding:16px;
 border-radius:14px;
 margin-bottom:18px;
}
.low{border-left:8px solid #2ECC71;}
.medium{border-left:8px solid #F4D03F;}
.high{border-left:8px solid #E74C3C;}
.header{
 background:linear-gradient(90deg,#10345f,#0f4c81);
 padding:18px;
 border-radius:14px;
}
.small{
 color:#c8d2dc;
 font-size:0.9rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='header'>
<h1>🏥 SepsisWatch AI</h1>
<h4>AI-Powered ICU Command Center</h4>
</div>
""", unsafe_allow_html=True)

patients = sorted(get_live_data(), key=lambda x: x["patient_id"])

results=[]
low=medium=high=0

for patient in patients:
    risk, probability, confidence = predict_sepsis(patient)
    patient["probability"]=probability
    update_history(patient)
    results.append((patient,risk,probability,confidence))

    if risk=="Low":
        low+=1
    elif risk in ("Low-Medium","Medium"):
        medium+=1
    else:
        high+=1

if high:
    st.error(f"🚨 ALERT: {high} High-Risk Patient(s) Require Immediate Attention")
else:
    st.success("🟢 No Critical Patients Detected")

c1,c2,c3,c4=st.columns(4)
vals=[("Patients",len(results)),("Low",low),("Medium",medium),("High",high)]
for col,(title,val) in zip((c1,c2,c3,c4),vals):
    with col:
        st.markdown(f"<div class='metric-card'><h4>{title}</h4><h2>{val}</h2></div>",unsafe_allow_html=True)

st.markdown("## 🏥 Live ICU Dashboard")

for patient,risk,probability,confidence in results:

    css="low" if risk=="Low" else "medium" if risk in ("Low-Medium","Medium") else "high"
    history=get_history(patient["patient_id"])

    st.markdown(f"<div class='patient-card {css}'>",unsafe_allow_html=True)

    left,mid,right=st.columns([2,2,1])

    with left:
        st.subheader(f"🛏 Bed {patient['patient_id']} • {patient['name']}")
        st.write(f"❤️ Heart Rate: **{patient['heart_rate']} bpm**")
        st.write(f"🌡 Temperature: **{patient['temperature']} °C**")
        st.write(f"🫁 SpO₂: **{patient['spo2']} %**")

    with mid:
        st.write(f"🩸 Blood Pressure: **{patient['systolic']}/{patient['diastolic']} mmHg**")
        st.write(f"🌬 Respiratory Rate: **{patient['resp_rate']} breaths/min**")
        st.write(f"🤖 AI Prediction: **{risk}**")

    with right:
        st.metric("Risk",f"{probability:.1f}%")
        st.caption(f"Confidence {confidence:.1f}%")

        if risk=="Low":
            st.success("LOW")
        elif risk in ("Low-Medium","Medium"):
            st.warning("MEDIUM")
        else:
            st.error("HIGH")

    if risk=="Low":
        st.success("✅ Continue routine monitoring.")
    elif risk in ("Low-Medium","Medium"):
        st.warning("⚠ Observe closely and repeat vitals.")
    else:
        st.error("🚑 Immediate physician review recommended.")

    # Simple explainability
    reasons=[]
    if patient["temperature"]>=38:
        reasons.append("High temperature")
    if patient["spo2"]<=94:
        reasons.append("Low oxygen saturation")
    if patient["heart_rate"]>=100:
        reasons.append("Tachycardia")
    if patient["systolic"]<=100:
        reasons.append("Hypotension")
    if reasons:
        st.info("**AI Reasons:** " + ", ".join(reasons))

    if len(history)>=2:
        df=pd.DataFrame(history)
        a,b,c=st.columns(3)
        with a:
            st.caption("Heart Rate")
            st.line_chart(df["heart_rate"])
        with b:
            st.caption("Temperature")
            st.line_chart(df["temperature"])
        with c:
            st.caption("AI Probability")
            st.line_chart(df["probability"])

    st.markdown("</div>",unsafe_allow_html=True)

st.divider()
st.caption("SepsisWatch AI • Version 1 ICU Dashboard UI Refresh")
