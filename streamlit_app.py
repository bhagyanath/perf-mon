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
    "File Inbox (Off)": {"url": f"{BASE_URL}/file-management-services/v2/inbox-homepage?currentPostId=ce83ea76-ddf5-4d00-9076-f51990f8a480&excludeServiceCode=BFIF01&fileStatus=RUNNING&isForDisposal=false&officeId=10132101210&page=0&size=100&sortDirection=desc", "method": "POST", "auth_type": "official", "payload": {}},
    "Finance Ward (Off)": {"url": f"{BASE_URL}/fin-voucher-services/voucher/ward-search", "method": "POST", "auth_type": "official", "payload": {"voucherNo": "R-M130500-25052181", "officeCode": "10132100221"}},
    "CR Birth (Cit)": {"url": f"{BASE_URL}/birth-services/cr/new-birth/save-child-details", "method": "PUT", "auth_type": "citizen", "payload": {"dateOfBirth": "18-03-2026", "gender": "MALE", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfBirthType": "HOSPITAL", "additionalBirthInformation": {"natureOfMedicalAttention": "DELIVERY_ATTENTION_PRIVATE", "durationOfPregnancy": 32, "deliveryMethod": "DELIVERY_NATURAL", "weightAt": 2}, "firstName": "adadsa", "firstNameInLcl": "എസ്‌എഫ്‌എസ്‌എഫ്‌എസ്", "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, "birthApplicationId": "4750c4aa-d67a-4b9e-b095-3fc85aa08654", "id": "09fd56f1-39ba-4467-bcba-0acbd678cc52"}},
    "CR Death (Cit)": {"url": f"{BASE_URL}/death-services/cr/new-death/save-death-information", "method": "PUT", "auth_type": "citizen", "payload": {"aadhaar": "836412654427", "dateOfDeathFrom": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfDeathType": "HOSPITAL", "firstName": "adadss", "firstNameInLcl": "അഡ്സ്", "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, "id": "c032fae6-2db9-46ac-a3da-4d34412c2c2d"}},
    "CR Marriage (Cit)": {"url": f"{BASE_URL}/marriage-services/cr/marriage-registration/information", "method": "POST", "auth_type": "citizen", "payload": {"dateOfMarriage": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfMarriageType": "RELIGIOUS_INSTITUTION", "registrationType": "C"}},
    "Property Tax (Cit)": {"url": f"{BASE_URL}/property-services/v1/tax-assessment-requests/building-address", "method": "PATCH", "auth_type": "citizen", "payload": {"id": "bc796b13-0479-471d-86fa-41bf64ed2c41", "applicationId": "9f33935f-200d-489c-be06-f69d91c59994", "houseName": "Sfsfs", "streetName": "Adad", "localPlaceName": "Asdad", "mainPlaceName": "Adasd", "postOfficeCode": "10232100578", "pincode": "695605", "houseNameLocal": "അടട", "streetNameLocal": "അടട", "requestId": "e91a0662-1264-469b-b24d-28411f202f6f"}},
    "License Create (Cit)": {
        "url": f"{BASE_URL}/bf-ifteos-services/application/create",
        "method": "POST", "auth_type": "citizen",
        "payload": {
            "license": {
                "id": "f73b080a-1ed0-420e-9631-e0ae8133148b", "officeCode": "10132100266", "applicationType": "NEW", "status": "INITIATED", "financialYear": 2025,
                "licenseUnit": {"id": "1fcd4f62-1879-4f85-8bd5-555e0536d59d", "officeCode": "10132100266", "structurePlaceType": "BUILDING", "wardId": "16332106080", "wardNo": 1},
                "buildings": [{
                    "id": "0cee33c4-4737-4612-999b-47feaab77ebb", "officeCode": 10132100266, "isOwned": True, "ptaxBuildingId": 50266010002901, "usageId": 1, "buildingArea": 141.22,
                    "owner": [{"ownerName": "KRISHNAN KUTTY NADAR P", "mobileNo": "******9201", "pincode": "695028"}]
                }],
                "location": {"locality": "sfsfs", "streetRoad": "sfsfs", "pincode": 695028, "officeCode": "10132100266", "id": "2fe5b3e8-d740-4e21-b1e4-010779547dd9"},
                "application": {"officeCode": "10132100266", "userType": "CITIZEN", "userName": "Bhagyanath V V", "userMobileNo": "9947788325"}
            }
        }
    },
    "Inbox (Cit)": {"url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR", "method": "POST", "auth_type": "citizen", "payload": {}}
}

# --- 2. INTELLIGENT OFFSETS ---
INTELLIGENT_OFFSETS = {
    "File Inbox (Off)": 1062, "Finance Ward (Off)": 738, "CR Birth (Cit)": 500, "CR Death (Cit)": 760,
    "CR Marriage (Cit)": 475, "Property Tax (Cit)": 519, "License Create (Cit)": 440, "Inbox (Cit)": 940
}

st.set_page_config(page_title="K-SMART Hub", layout="centered")

# --- 3. TELEGRAM ALERT ---
def send_telegram(msg):
    if "TELEGRAM_TOKEN" in st.secrets:
        token, chat_id = st.secrets["TELEGRAM_TOKEN"], st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 4. SESSION STATE INIT ---
for key in ['log_data', 'monitoring_active', 'citizen_token', 'official_token']:
    if key not in st.session_state:
        if key == 'log_data': st.session_state[key] = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError"])
        elif key == 'monitoring_active': st.session_state[key] = False
        else: st.session_state[key] = None
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now() - timedelta(days=1)

st.title("🛡️ K-SMART Hub")

# --- 5. VERIFIED STATUS UI ---
c_ver = "✅ VERIFIED" if st.session_state.citizen_token else "❌ NOT VERIFIED"
o_ver = "✅ VERIFIED" if st.session_state.official_token else "❌ NOT VERIFIED"

st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 15px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid #1f77b4;">
    <p style="margin:0; font-weight: bold; font-size: 0.85em; color: #555;">SESSION TRACKER</p>
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <span style="color: {'#008000' if st.session_state.citizen_token else '#FF0000'}; font-weight: bold;">👤 Citizen: {c_ver}</span>
        <span style="color: {'#008000' if st.session_state.official_token else '#FF0000'}; font-weight: bold;">🏢 Official: {o_ver}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. AUTH SECTIONS ---
with st.expander("🔑 Login & OTP Verification", expanded=not st.session_state.monitoring_active):
    t1, t2 = st.tabs(["Citizen", "Official"])
    with t1:
        c_phone = st.text_input("Mobile", value="9947788325")
        if st.button("Request Citizen OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("Enter Cit OTP", type="password")
        if st.button("Verify Citizen Session"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN"}).json()
            st.session_state.citizen_token = res['data']['token']
            st.rerun()
    with t2:
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Request Official OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}").json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("Enter Off OTP", type="password")
        if st.button("Verify Official Session"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']
            st.rerun()

# --- 7. ENGINE ---
st.sidebar.header("⚙️ Intelligent Config")
interval_min = st.sidebar.slider("Interval (Min)", 1, 60, 5)
alert_limit = st.sidebar.slider("Alert Threshold (ms)", 200, 2000, 500)

if st.session_state.citizen_token and st.session_state.official_token:
    if st.sidebar.button("▶️ START 24h MONITORING", type="primary"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.rerun()

    if st.session_state.monitoring_active:
        now = datetime.now()
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
                    raw_ms = (time.time() - s_time) * 1000
                    lat = round(max(0, raw_ms - INTELLIGENT_OFFSETS.get(name, 500)), 2)
                    err = 1 if (lat > alert_limit or r.status_code not in [200, 201]) else 0
                    if err: send_telegram(f"🚨 *K-SMART LAG*\n{name}: {lat}ms")
                    new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": r.status_code, "IsError": err}
                    st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)
                except: pass

        if not st.session_state.log_data.empty:
            st.subheader("Calibrated Latency")
            latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
            for _, row in latest.iterrows():
                st.write(f"{'🔴' if row['IsError'] else '🟢'} **{row['Module']}**: {row['Latency(ms)']}ms")
            st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=380), use_container_width=True)

        time.sleep(5)
        st.rerun()
else:
    st.warning("Please complete both Citizen and Official logins to enable monitoring.")