import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- Configuration & Fixed Payloads ---
BASE_URL = "https://api.ksmart.lsgkerala.gov.in"
API_ENDPOINTS = {
    "File Inbox": {"url": f"{BASE_URL}/file-management-services/v2/inbox-homepage?currentPostId=ce83ea76-ddf5-4d00-9076-f51990f8a480&excludeServiceCode=BFIF01&fileStatus=RUNNING&isForDisposal=false&officeId=10132101210&page=0&size=100&sortDirection=desc", "method": "POST", "auth_type": "official", "payload": {}},
    "CR Birth": {"url": f"{BASE_URL}/birth-services/cr/new-birth/save-child-details", "method": "PUT", "auth_type": "citizen", "payload": {"dateOfBirth": "18-03-2026", "gender": "MALE", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfBirthType": "HOSPITAL", "additionalBirthInformation": {"natureOfMedicalAttention": "DELIVERY_ATTENTION_PRIVATE", "durationOfPregnancy": 32, "deliveryMethod": "DELIVERY_NATURAL", "weightAt": 2}, "firstName": "adadsa", "firstNameInLcl": "എസ്‌എഫ്‌എസ്‌എഫ്‌എസ്", "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, "birthApplicationId": "4750c4aa-d67a-4b9e-b095-3fc85aa08654", "id": "09fd56f1-39ba-4467-bcba-0acbd678cc52"}},
    "Inbox (Cit)": {"url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR", "method": "POST", "auth_type": "citizen", "payload": {}}
}

# --- UI Mobile Setup ---
st.set_page_config(page_title="Mobile Health Hub", layout="centered") # Centered is better for mobile

# Custom CSS for mobile-friendly buttons and spacing
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; height: 3em; margin-bottom: 10px; }
    .metric-container { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError"])
if 'monitoring_active' not in st.session_state: st.session_state.monitoring_active = False

st.title("📱 K-SMART Monitor")

# --- Simplified Auth (Accordion for mobile space) ---
with st.expander("🔑 Session Authentication", expanded=not st.session_state.monitoring_active):
    tab1, tab2 = st.tabs(["Citizen", "Official"])
    
    with tab1:
        c_phone = st.text_input("Mobile", value="9947788325")
        if st.button("Get OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("OTP", type="password", key="cit_otp")
        if st.button("Verify Citizen"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN", "organizationId": 0}).json()
            st.session_state.citizen_token = res['data']['token']
            st.success("Citizen OK")

    with tab2:
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Request OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}", json={}).json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("OTP", type="password", key="off_otp")
        if st.button("Verify Official"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']
            st.success("Official OK")

# --- Monitoring Dashboard ---
if st.session_state.get('citizen_token') and st.session_state.get('official_token'):
    if not st.session_state.monitoring_active:
        if st.button("▶️ START MONITORING", type="primary"):
            st.session_state.monitoring_active = True
            st.session_state.last_run = datetime.now() - timedelta(minutes=10)
            st.rerun()
    else:
        if st.button("⏹️ STOP"):
            st.session_state.monitoring_active = False
            st.rerun()

        # Mobile-optimized Metrics Grid
        now = datetime.now()
        
        # Check if it's time to pulse
        if (now - st.session_state.get('last_run', now)).total_seconds() > 300: # 5 min interval
            st.session_state.last_run = now
            for name, cfg in API_ENDPOINTS.items():
                token = st.session_state.official_token if cfg["auth_type"] == "official" else st.session_state.citizen_token
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-STATE-CODE": "kl"}
                
                s_time = time.time()
                try:
                    r = requests.request(cfg["method"], cfg["url"], headers=headers, json=cfg["payload"], timeout=15)
                    lat, stat = round((time.time() - s_time) * 1000, 2), r.status_code
                except: lat, stat = 0, "ERR"

                err = 1 if (lat > 2000 or stat != 200) else 0
                new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": stat, "IsError": err}
                st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)

        # Show status
        if not st.session_state.log_data.empty:
            latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
            for _, row in latest.iterrows():
                color = "🔴" if row['IsError'] else "🟢"
                st.markdown(f"**{color} {row['Module']}**: {row['Latency(ms)']}ms (Code: {row['Status']})")
            
            st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=300), use_container_width=True)

        st.caption(f"Last update: {now.strftime('%H:%M:%S')}")
        time.sleep(5)
        st.rerun()