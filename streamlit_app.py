import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- 1. Configuration & COMPLETE Original Payloads ---
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
                "licenseUnit": {"id": "1fcd4f62-1879-4f85-8bd5-555e0536d59d", "officeCode": "10132100266", "wardNo": 1}
            }
        }
    },
    "Inbox (Cit)": {
        "url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR",
        "method": "POST", "auth_type": "citizen", "payload": {}
    }
}

# --- 2. Responsive UI Setup ---
st.set_page_config(page_title="Performance Hub", layout="centered")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
    .status-card { padding: 10px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Telegram Logic ---
def send_telegram_alert(mod, lat, stat):
    if "TELEGRAM_TOKEN" in st.secrets:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        msg = f"🚨 *K-SMART ALERT*\n\n*Module:* {mod}\n*Latency:* {lat}ms\n*Status:* {stat}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 4. Session State ---
if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "Hour", "IsError"])
if 'monitoring_active' not in st.session_state: st.session_state.monitoring_active = False
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now() - timedelta(days=1)

st.title("🛡️ K-SMART Hub")

# --- 5. Mobile Auth Section ---
with st.expander("🔑 Session Authentication", expanded=not st.session_state.monitoring_active):
    tab1, tab2 = st.tabs(["Citizen", "Official"])
    with tab1:
        c_phone = st.text_input("Citizen Mobile", value="9947788325")
        if st.button("Get Cit OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("Cit OTP", type="password", key="cit_otp_in")
        if st.button("Verify Citizen"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN", "organizationId": 0}).json()
            st.session_state.citizen_token = res['data']['token']
            st.success("Citizen OK ✅")
    with tab2:
        e_pen = st.text_input("Official PEN", value="M10021")
        if st.button("Get Off OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}", json={}).json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("Off OTP", type="password", key="off_otp_in")
        if st.button("Verify Official"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']
            st.success("Official OK ✅")

# --- 6. Execution ---
if st.session_state.get('citizen_token') and st.session_state.get('official_token'):
    st.sidebar.header("⚙️ Settings")
    interval_min = st.sidebar.slider("Pulse (Min)", 1, 60, 5)
    lag_limit = st.sidebar.slider("Limit (ms)", 500, 5000, 2000)

    if st.sidebar.button("▶️ START 24h" if not st.session_state.monitoring_active else "⏹️ STOP"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.session_state.start_time = datetime.now()
        st.rerun()

    if st.sidebar.button("🧪 Test Telegram"):
        send_telegram_alert("TEST", 0, "SUCCESS")
        st.sidebar.toast("Test Sent!")

    if st.session_state.monitoring_active:
        now = datetime.now()
        next_pulse = st.session_state.last_run + timedelta(minutes=interval_min)
        time_left = (next_pulse - now).total_seconds()
        
        st.metric("Next Update In", f"{int(max(0, time_left)//60)}m {int(max(0, time_left)%60)}s")

        if time_left <= 0:
            st.session_state.last_run = now
            for name, cfg in API_ENDPOINTS.items():
                token = st.session_state.official_token if cfg["auth_type"] == "official" else st.session_state.citizen_token
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-STATE-CODE": "kl"}
                
                s_time = time.time()
                try:
                    r = requests.request(cfg["method"], cfg["url"], headers=headers, json=cfg["payload"], timeout=20)
                    lat, stat = round((time.time() - s_time) * 1000, 2), r.status_code
                except: lat, stat = 0, "TIMEOUT"

                err = 1 if (lat > lag_limit or stat not in [200, 201]) else 0
                if err: send_telegram_alert(name, lat, stat)
                
                new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": stat, "Hour": now.hour, "IsError": err}
                st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)

        # Dashboard View
        if not st.session_state.log_data.empty:
            st.subheader("Live Status")
            latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
            for _, row in latest.iterrows():
                icon = "🔴" if row['IsError'] else "🟢"
                st.markdown(f"**{icon} {row['Module']}**: {row['Latency(ms)']}ms")
            
            st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=300), use_container_width=True)

            with st.expander("📊 Detailed Stats"):
                stats = st.session_state.log_data.groupby("Module")["Latency(ms)"].agg(['mean', 'max']).reset_index()
                st.dataframe(stats, use_container_width=True)
                st.download_button("Export CSV", st.session_state.log_data.to_csv(index=False).encode('utf-8'), "audit.csv")

        time.sleep(2)
        st.rerun()
else:
    st.info("Please login to both sessions to start monitoring.")