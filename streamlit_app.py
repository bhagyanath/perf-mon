import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import uuid # Add this at the top of your script

# --- 1. FULL MODULE RECOVERY ---
BASE_URL = "https://api.ksmart.lsgkerala.gov.in"
API_ENDPOINTS = {
    "File Inbox (Off)": {"url": f"{BASE_URL}/file-management-services/v2/inbox-homepage?currentPostId=ce83ea76-ddf5-4d00-9076-f51990f8a480&excludeServiceCode=BFIF01&fileStatus=RUNNING&isForDisposal=false&officeId=10132101210&page=0&size=100&sortDirection=desc", "method": "POST", "auth_type": "official", "payload": {}},
    "Finance Ward (Off)": {"url": f"{BASE_URL}/fin-voucher-services/voucher/ward-search", "method": "POST", "auth_type": "official", "payload": {"voucherNo": "R-M130500-25052181", "officeCode": "10132100221"}},
    "CR Birth (Cit)": {"url": f"{BASE_URL}/birth-services/cr/new-birth/save-child-details", "method": "PUT", "auth_type": "citizen", "payload": {"dateOfBirth": "18-03-2026", "gender": "MALE", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfBirthType": "HOSPITAL", "additionalBirthInformation": {"natureOfMedicalAttention": "DELIVERY_ATTENTION_PRIVATE", "durationOfPregnancy": 32, "deliveryMethod": "DELIVERY_NATURAL", "weightAt": 2}, "firstName": "adadsa", "firstNameInLcl": "എസ്‌എഫ്‌എസ്‌എഫ്‌എസ്", "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, "birthApplicationId": "4750c4aa-d67a-4b9e-b095-3fc85aa08654", "id": "09fd56f1-39ba-4467-bcba-0acbd678cc52"}},
    "CR Death (Cit)": {"url": f"{BASE_URL}/death-services/cr/new-death/save-death-information", "method": "PUT", "auth_type": "citizen", "payload": {"aadhaar": "836412654427", "dateOfDeathFrom": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173, "placeOfDeathType": "HOSPITAL", "firstName": "adadss", "firstNameInLcl": "അഡ്സ്", "hospitalInformation": {"hospitalOfficeCode": 10332100606, "hospitalTypeId": 2}, "id": "c032fae6-2db9-46ac-a3da-4d34412c2c2d"}},
    "CR Marriage (Cit)": {
        "url": f"{BASE_URL}/marriage-services/cr/marriage-registration/information",
        "method": "POST", "auth_type": "citizen",
        "payload": {
            "dateOfMarriage": "18-03-2026", "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173,
            "placeOfMarriageType": "RELIGIOUS_INSTITUTION", 
            "religiousInstitutionInformation": {"religiousInstitutionOfficeCode": 10532107556, "id": None},
            "registrationType": "C"
    }},
    "Property Tax - PTX (Citizen)": {
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
                "id": "f73b080a-1ed0-420e-9631-e0ae8133148b",
                "officeCode": "10132100266",
                "applicationType": "NEW",
                "applicationDate": datetime.now().strftime("%Y-%m-%d"),
                "status": "INITIATED",
                "financialYear": 2025,
                "businessSector": "NOTSET",
                "active": True,
                "licenseUnit": {
                    "id": "1fcd4f62-1879-4f85-8bd5-555e0536d59d",
                    "officeCode": "10132100266",
                    "structurePlaceType": "BUILDING",
                    "structurePlaceSubtype": "PERMANENT",
                    "zonalId": "10132100266",
                    "wardYear": "2013",
                    "wardId": "16332106080",
                    "wardNo": 1,
                    "unitType": "NOTSET",
                    "active": True,
                    "empty": True
                },
                "buildings": [
                    {
                        "id": "0cee33c4-4737-4612-999b-47feaab77ebb",
                        "officeCode": 10132100266,
                        "isOwned": True,
                        "ownershipType": "OWN",
                        "doorNo": 1,
                        "doorNoSub": "",
                        "ptaxBuildingId": 50266010002901,
                        "mainUsageId": None,
                        "usageId": 1,
                        "functionalityMaster": {
                            "id": 1,
                            "code": "Residential",
                            "name": "Residential",
                            "nameInLocal": "പാര്‍പ്പിടാവശ്യം",
                            "active": False
                        },
                        "subUsageId": 1,
                        "functionalitySubMaster": {
                            "id": 1,
                            "code": "Houses",
                            "name": "Houses",
                            "nameInLocal": "വീടുകള്‍",
                            "active": False
                        },
                        "buildingArea": 141.22,
                        "permissionValidFrom": None,
                        "permissionValidTo": None,
                        "ptaxTotal": None,
                        "penalInterest": 0,
                        "active": True,
                        "isSingleAgreement": True,
                        "wardId": 16332106080,
                        "lbownAgreementNo": None,
                        "lbownValidFrom": None,
                        "lbownValidTo": None,
                        "isCancelled": False,
                        "owner": [
                            {
                                "id": "a6c8e54c-e98e-43d4-adc4-e326f2f28e9c",
                                "officeCode": 10132100266,
                                "aadharNo": None,
                                "ownerName": "KRISHNAN KUTTY NADAR  P",
                                "ownerNameLocal": "ക്യഷ്ണന്‍കുട്ടി നാടാര്‍ പി",
                                "salutation": None,
                                "careOfName": None,
                                "houseNo": None,
                                "houseName": "PXXXA VXXXXXM BXXXXXXU",
                                "locality": None,
                                "streetRoad": None,
                                "postOffice": None,
                                "pincode": "695028",
                                "state": 502032,
                                "country": 501077,
                                "mobileNo": "******9201",
                                "contactNo": "******9201",
                                "email": None,
                                "agreementNo": None,
                                "validFrom": None,
                                "validTo": None,
                                "active": True,
                                "buildingId": None,
                                "landId": None,
                                "postOfficeId": 10232100749,
                                "district": None,
                                "isAadhar": None,
                                "isPassport": None,
                                "passportNo": None,
                                "slId": "1xg78m_mmvmhz9b_c3hqm3"
                            }
                        ],
                        "isAutherised": True,
                        "wardYear": 2013,
                        "slId": "vzj6ee_mmvmhz9b_losrwg"
                    }
                ],
                "stall": [],
                "bunk": [],
                "vehicle": None,
                "land": [],
                "vessel": None,
                "location": {
                    "locality": "sfsfs",
                    "streetRoad": "sfsfs",
                    "postOfficeId": 10232100255,
                    "pincode": 695028,
                    "landmark": "adada",
                    "officeCode": "10132100266",
                    "buildingName": "sss",
                    "id": "2fe5b3e8-d740-4e21-b1e4-010779547dd9"
                },
                "application": {
                    "officeCode": "10132100266",
                    "createdBy": "cca5abd0-c82a-4942-99fa-9b57deee8670",
                    "userType": "CITIZEN",
                    "userName": "Bhagyanath V V",
                    "userMobileNo": "9947788325"
                }
            }
        }
    },
    "Inbox (Cit)": {"url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?pageNumber=0&pageSize=8&category=CR", "method": "POST", "auth_type": "citizen", "payload": {}}
}

# --- 2. INTELLIGENT OFFSETS ---
INTELLIGENT_OFFSETS = {
    "File Inbox (Off)": 233, "Finance Ward (Off)": 735, "CR Birth (Cit)": 186, "CR Death (Cit)": 830,
    "CR Marriage (Cit)": 373, "Property Tax (Cit)": 490, "License Create (Cit)": 222, "Inbox (Cit)": 112
}

st.set_page_config(page_title="K-SMART Hub", layout="centered")

# --- 3. TELEGRAM ALERT ---
def send_telegram(msg):
    if "TELEGRAM_TOKEN" in st.secrets:
        token, chat_id = st.secrets["TELEGRAM_TOKEN"], st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- 4. SESSION STATE ---
for key in ['log_data', 'monitoring_active', 'citizen_token', 'official_token', 'alert_log']:
    if key not in st.session_state:
        if key in ['log_data', 'alert_log']: st.session_state[key] = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError", "Details"])
        elif key == 'monitoring_active': st.session_state[key] = False
        else: st.session_state[key] = None
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now() - timedelta(days=1)

# --- 5. UI & VERIFIED STATUS ---
st.title("🛡️ K-SMART Hub")

c_ver = "✅ VERIFIED" if st.session_state.citizen_token else "❌ NOT VERIFIED"
o_ver = "✅ VERIFIED" if st.session_state.official_token else "❌ NOT VERIFIED"

st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 15px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid #1f77b4;">
    <div style="display: flex; justify-content: space-between; font-family: sans-serif;">
        <span style="color: {'#008000' if st.session_state.citizen_token else '#FF0000'}; font-weight: bold;">👤 Citizen: {c_ver}</span>
        <span style="color: {'#008000' if st.session_state.official_token else '#FF0000'}; font-weight: bold;">🏢 Official: {o_ver}</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("🔑 Login & Verify OTP", expanded=not st.session_state.monitoring_active):
    t1, t2 = st.tabs(["Citizen", "Official"])
    with t1:
        c_phone = st.text_input("Mobile", value="9947788325")
        if st.button("Request Citizen OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("Cit OTP", type="password")
        if st.button("Verify Citizen"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN"}).json()
            st.session_state.citizen_token = res['data']['token']
            st.rerun()
    with t2:
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Request Official OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}").json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("Off OTP", type="password")
        if st.button("Verify Official"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']
            st.rerun()

# --- 6. SIDEBAR CONTROLS ---
st.sidebar.header("📊 Controls")
interval_min = st.sidebar.slider("Interval (Min)", 1, 60, 5)
spike_sensitivity = st.sidebar.slider("Spike Sensitivity (%)", 10, 100, 30)

if st.sidebar.button("⏹️ Reset System Logs"):
    st.session_state.log_data = st.session_state.log_data.tail(0)
    st.session_state.alert_log = st.session_state.alert_log.tail(0)
    st.rerun()

# --- 7. MONITORING ENGINE ---
if st.session_state.citizen_token and st.session_state.official_token:
    if st.sidebar.button("▶️ START MONITORING", type="primary"):
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
                    
                    is_spike, alert_type = False, ""
                    if not st.session_state.log_data.empty:
                        mod_history = st.session_state.log_data[st.session_state.log_data['Module'] == name]
                        if len(mod_history) >= 3:
                            avg_lat = mod_history['Latency(ms)'].tail(5).mean()
                            if lat > (avg_lat * (1 + (spike_sensitivity / 100))) and lat > 100:
                                is_spike, alert_type = True, "Spike Detected"
                    
                    if r.status_code not in [200, 201]:
                        is_spike, alert_type = True, f"HTTP Error {r.status_code}"

                    if is_spike:
                        detail = f"{alert_type}: {lat}ms"
                        send_telegram(f"🚨 *ALERT:* {name}\n{detail}")
                        alert_row = {"Timestamp": now.strftime("%H:%M:%S"), "Module": name, "Latency(ms)": lat, "Details": alert_type}
                        st.session_state.alert_log = pd.concat([st.session_state.alert_log, pd.DataFrame([alert_row])], ignore_index=True)

                    new_row = {"Timestamp": now.strftime("%H:%M"), "Module": name, "Latency(ms)": lat, "Status": r.status_code, "IsError": 1 if is_spike else 0}
                    st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)
                except: pass

        # --- Dashboard UI ---
        st.subheader("Calibrated Real-time Latency")
        latest = st.session_state.log_data.tail(len(API_ENDPOINTS))
        for _, row in latest.iterrows():
            st.write(f"{'🔴' if row['IsError'] else '🟢'} **{row['Module']}**: {row['Latency(ms)']}ms")
        
        st.plotly_chart(px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", height=380), use_container_width=True)

        # --- SYSTEM ALERT LOG TAB ---
        st.markdown("---")
        st.subheader("📋 System Alert History")
        if not st.session_state.alert_log.empty:
            st.table(st.session_state.alert_log.tail(10))
        else:
            st.caption("No alerts triggered in this session.")

        time.sleep(5)
        st.rerun()
else:
    st.info("Please verify both Citizen and Official sessions.")