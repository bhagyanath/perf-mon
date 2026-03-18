import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- Configuration & All API Modules ---
BASE_URL = "https://api.ksmart.lsgkerala.gov.in"
API_ENDPOINTS = {
    "File Inbox (Off)": {
        "url": f"{BASE_URL}/file-management-services/v2/inbox-homepage?currentPostId=ce83ea76-ddf5-4d00-9076-f51990f8a480&excludeServiceCode=BFIF01&fileStatus=RUNNING&isForDisposal=false&officeId=10132101210&page=0&size=100&sortDirection=desc",
        "method": "POST", "auth_type": "official", "payload": {}
    },
    "Finance Ward (Off)": {
        "url": f"{BASE_URL}/fin-voucher-services/voucher/ward-search",
        "method": "POST", "auth_type": "official",
        "payload": {"voucherNo": "R-M130500-25052181", "officeCode": "10132100221"}
    },
    "CR Birth (Cit)": {
        "url": f"{BASE_URL}/birth-services/cr/new-birth/save-child-details",
        "method": "PUT", "auth_type": "citizen",
        "payload": {
            "dateOfBirth": "18-03-2026", "gender": "MALE", "districtId": 503001, "lbTypeId": 3, 
            "lbOfficeCode": 10132100173, "placeOfBirthType": "HOSPITAL",
            "additionalBirthInformation": {"natureOfMedicalAttention": "DELIVERY_ATTENTION_PRIVATE", "durationOfPregnancy": 32, "deliveryMethod": "DELIVERY_NATURAL", "weightAt": 2},
            "firstName": "adadsa", "firstNameInLcl": "എസ്‌എഫ്‌എസ്‌എഫ്‌എസ്", 
            "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2},
            "birthApplicationId": "4750c4aa-d67a-4b9e-b095-3fc85aa08654", "id": "09fd56f1-39ba-4467-bcba-0acbd678cc52"
        }
    },
    "CR Death (Cit)": {
        "url": f"{BASE_URL}/death-services/cr/new-death/save-death-information",
        "method": "PUT", "auth_type": "citizen",
        "payload": {
            "aadhaar": "836412654427", "dateOfDeathFrom": "18-03-2026", "districtId": 503001, 
            "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfDeathType": "HOSPITAL", 
            "firstName": "adadss", "firstNameInLcl": "അഡ്സ്",
            "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, 
            "id": "c032fae6-2db9-46ac-a3da-4d34412c2c2d"
        }
    },
    "CR Marriage (Cit)": {
        "url": f"{BASE_URL}/marriage-services/cr/marriage-registration/information",
        "method": "POST", "auth_type": "citizen",
        "payload": {"dateOfMarriage": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfMarriageType": "RELIGIOUS_INSTITUTION", "registrationType": "C"}
    },
    "Property Tax (Cit)": {
        "url": f"{BASE_URL}/property-services/v1/tax-assessment-requests/building-address",
        "method": "PATCH", "auth_type": "citizen",
        "payload": {"id": "bc796b13-0479-471d-86fa-41bf64ed2c41", "houseName": "MobileTest", "pincode": "695605"}
    },
    "License Create (Cit)": {
        "url": f"{BASE_URL}/bf-ifteos-services/application/create",
        "method": "POST", "auth_type": "citizen",
        "payload": {"license": {"officeCode": "10132100266", "applicationType": "NEW", "status": "INITIATED"}}
    },
    "Inbox (Cit)": {
        "url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR",
        "method": "POST", "auth_type": "citizen", "payload": {}
    }
}

st.set_page_config(page_title="K-SMART Mobile Hub", layout="centered")

# --- Telegram Alert Function ---
def send_telegram_alert(mod, lat, stat):
    if "TELEGRAM_TOKEN" in st.secrets:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        msg = f"🚨 *K-SMART ALERT*\n*Module:* {mod}\n*Latency:* {lat}ms\n*Status:* {stat}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- State Management ---
if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError"])
if 'monitoring_active' not in st.session_state: st.session_state.monitoring_active = False

st.title("🛡️ K-SMART Health Hub")

# --- Mobile Auth Section ---
with st.expander("🔑 Verify Sessions", expanded=not st.session_state.monitoring_active):
    c_col, e_col = st.columns(2)
    with c_col:
        st.caption("Citizen Login")
        c_phone = st.text_input("Phone", value="9947788325")
        if st.button("Send OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("Cit OTP", type="password")
        if st.button("Verify Cit"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN"}).json()
            st.session_state.citizen_token = res['data']['token']
    
    with e_col:
        st.caption("Official Login")
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Req OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}", json={}).json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("Off OTP", type="password")
        if st.button("Verify Off"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']

# --- Monitoring Loop ---
if st.session_state.get('citizen_token') and st.session_state.get('official_token'):
    st.sidebar.header("Settings")
    interval = st.sidebar.slider("Pulse (Min)", 1, 30, 5)
    limit = st.sidebar.slider("Limit (ms)", 500, 5000, 2000)

    if st.sidebar.button("▶️ START" if not st.session_state.monitoring_active else "⏹️ STOP"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.session_state.last_run = datetime.now() - timedelta(minutes=interval)
        st.rerun()

    if st.session_state.monitoring_active:
        now = datetime.now()
        if (now - st.session_state.get('last_run', now)).total_seconds() >= (interval * 60):
            st.session_state.last_run = now
            for name, cfg in API_ENDPOINTS.items():
                token = st.session_state.official_token if cfg["auth_type"] == "official" else st.session_state.citizen_token
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-STATE-CODE": "kl"}
                
                start = time.time()
                try:
                    r = requests.request(cfg["method"], cfg["url"], headers=headers, json=cfg["payload"], timeout=20)
                    lat, stat = round((time.time() - start) * 1000, 2), r.status_code
                except: lat, stat = 0, "TIMEOUT"

                err = 1 if (lat > limit or stat not in [200, 201]) else 0
                if err: send_telegram_alert(name, lat, stat)
                
                new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": stat, "IsError": err}
                st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)

        # UI Display
        st.subheader("Current Status")
        latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
        for _, row in latest.iterrows():
            col = "🔴" if row['IsError'] else "🟢"
            st.write(f"{col} **{row['Module']}**: {row['Latency(ms)']}ms")
        
        st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=350), use_container_width=True)
        
        st.caption(f"Last updated: {now.strftime('%H:%M:%S')}")
        time.sleep(5)
        st.rerun()