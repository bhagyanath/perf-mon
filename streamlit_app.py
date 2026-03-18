import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & FULL MODULE RECOVERY ---
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
        "payload": {
            "dateOfMarriage": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173,
            "placeOfMarriageType": "RELIGIOUS_INSTITUTION", 
            "religiousInstitutionInformation": {"religiousInstitutionOfficeCode": 10532107556, "id": None},
            "registrationType": "C"
        }
    },
    "Property Tax (Cit)": {
        "url": f"{BASE_URL}/property-services/v1/tax-assessment-requests/building-address",
        "method": "PATCH", "auth_type": "citizen",
        "payload": {
            "id": "bc796b13-0479-471d-86fa-41bf64ed2c41", "applicationId": "9f33935f-200d-489c-be06-f69d91c59994",
            "houseName": "Sfsfs", "streetName": "Adad", "localPlaceName": "Asdad", "mainPlaceName": "Adasd",
            "postOfficeCode": "10232100578", "pincode": "695605", "houseNameLocal": "അടട", "streetNameLocal": "അടട",
            "requestId": "e91a0662-1264-469b-b24d-28411f202f6f"
        }
    },
    "License Create (Cit)": {
        "url": f"{BASE_URL}/bf-ifteos-services/application/create",
        "method": "POST", "auth_type": "citizen",
        "payload": {
            "license": {
                "id": "f73b080a-1ed0-420e-9631-e0ae8133148b", "officeCode": "10132100266", "applicationType": "NEW",
                "applicationDate": datetime.now().strftime("%Y-%m-%d"), "status": "INITIATED", "financialYear": 2025,
                "licenseUnit": {"id": "1fcd4f62-1879-4f85-8bd5-555e0536d59d", "officeCode": "10132100266", "wardNo": 1},
                "buildings": [{"ptaxBuildingId": 50266010002901, "usageId": 1, "buildingArea": 141.22}]
            }
        }
    },
    "Inbox (Cit)": {
        "url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR",
        "method": "POST", "auth_type": "citizen", "payload": {}
    }
}

# --- 2. UI SETUP ---
st.set_page_config(page_title="K-SMART Monitor", layout="centered")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; color: #1f77b4; }
    .status-box { padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NOTIFICATION LOGIC ---
def send_telegram(msg):
    if "TELEGRAM_TOKEN" in st.secrets:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 4. SESSION STATE ---
if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError"])
if 'monitoring_active' not in st.session_state: st.session_state.monitoring_active = False
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now() - timedelta(days=1)
if 'last_summary_date' not in st.session_state: st.session_state.last_summary_date = datetime.now().date()

st.title("🛡️ K-SMART Hub")

# --- 5. AUTH SECTION (Mobile Tabs) ---
with st.expander("🔑 Verify Access Tokens", expanded=not st.session_state.monitoring_active):
    c_tab, o_tab = st.tabs(["Citizen", "Official"])
    with c_tab:
        c_phone = st.text_input("Mobile", value="9947788325")
        if st.button("Get OTP (Citizen)"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("OTP", type="password", key="c_otp")
        if st.button("Login Citizen"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN", "organizationId": 0}).json()
            st.session_state.citizen_token = res['data']['token']
    with o_tab:
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Get OTP (Official)"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}").json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("OTP", type="password", key="o_otp")
        if st.button("Login Official"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']

# --- 6. SIDEBAR CONTROLS ---
st.sidebar.header("📊 Controls")
interval_min = st.sidebar.slider("Interval (Min)", 1, 60, 5)
lag_limit = st.sidebar.slider("Alert Limit (ms)", 500, 5000, 2000)
offset = st.sidebar.slider("Network Offset (ms)", 0, 500, 200, help="Subtract travel time between US and India")

if st.sidebar.button("🧪 Test Telegram"):
    send_telegram("✅ *K-SMART Bot Connected!*")
    st.sidebar.toast("Test Message Sent!")

# --- 7. MAIN ENGINE ---
if st.session_state.get('citizen_token') and st.session_state.get('official_token'):
    if st.sidebar.button("▶️ START MONITORING", type="primary"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.rerun()

    if st.session_state.monitoring_active:
        now = datetime.now()
        
        # Daily Summary Logic (11:55 PM)
        if now.hour == 23 and now.minute >= 55 and st.session_state.last_summary_date != now.date():
            if not st.session_state.log_data.empty:
                max_lat = st.session_state.log_data.loc[st.session_state.log_data['Latency(ms)'].idxmax()]
                send_telegram(f"📋 *K-SMART DAILY SUMMARY*\nWorst: {max_lat['Module']} at {max_lat['Latency(ms)']}ms")
                st.session_state.last_summary_date = now.date()
                st.session_state.log_data = st.session_state.log_data.tail(0) # Clear for new day

        # Pulse Check
        next_pulse = st.session_state.last_run + timedelta(minutes=interval_min)
        time_left = (next_pulse - now).total_seconds()
        st.info(f"Next pulse in {int(max(0, time_left)//60)}m {int(max(0, time_left)%60)}s")

        if time_left <= 0:
            st.session_state.last_run = now
            for name, cfg in API_ENDPOINTS.items():
                token = st.session_state.official_token if cfg["auth_type"] == "official" else st.session_state.citizen_token
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-STATE-CODE": "kl"}
                
                s_time = time.time()
                try:
                    r = requests.request(cfg["method"], cfg["url"], headers=headers, json=cfg["payload"], timeout=20)
                    lat = round(max(0, ((time.time() - s_time) * 1000) - offset), 2)
                    stat = r.status_code
                except: lat, stat = 0, "TIMEOUT"

                err = 1 if (lat > lag_limit or stat not in [200, 201]) else 0
                if err: send_telegram(f"🚨 *LAG ALERT*\n{name}: {lat}ms (Code: {stat})")
                
                new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": stat, "IsError": err}
                st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)

        # Display Stats
        if not st.session_state.log_data.empty:
            st.subheader("Live Latency (Calibrated)")
            latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
            for _, row in latest.iterrows():
                icon = "🔴" if row['IsError'] else "🟢"
                st.write(f"{icon} **{row['Module']}**: {row['Latency(ms)']}ms")
            st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=350), use_container_width=True)

        time.sleep(5)
        st.rerun()
else:
    st.info("Log in above to activate 24/7 monitoring.")