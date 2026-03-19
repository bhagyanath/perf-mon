import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import uuid 

# --- 1. CONFIGURATION & PAYLOAD RECOVERY ---
BASE_URL = "https://api.ksmart.lsgkerala.gov.in"

def get_dynamic_payloads():
    """Generates payloads with fresh UUIDs to prevent 500 errors from duplicate IDs"""
    now_date = datetime.now().strftime("%d-%m-%Y")
    iso_date = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "File Inbox (Off)": {"url": f"{BASE_URL}/file-management-services/v2/inbox-homepage?currentPostId=ce83ea76-ddf5-4d00-9076-f51990f8a480&excludeServiceCode=BFIF01&fileStatus=RUNNING&officeId=10132101210&page=0&size=100", "method": "POST", "auth_type": "official", "payload": {}},
        "CR Marriage (Cit)": {
            "url": f"{BASE_URL}/marriage-services/cr/marriage-registration/information",
            "method": "POST", "auth_type": "citizen",
            "payload": {
                "dateOfMarriage": now_date, "districtId": 503001, "lbTypeId": 3, "lbOfficeCode": 10132100173,
                "placeOfMarriageType": "RELIGIOUS_INSTITUTION", 
                "religiousInstitutionInformation": {"religiousInstitutionOfficeCode": 10532107556, "id": None},
                "registrationType": "C"
            }
        },
        "Property Tax - PTX (Cit)": {
            "url": f"{BASE_URL}/property-services/v1/tax-assessment-requests/building-address",
            "method": "PATCH", "auth_type": "citizen",
            "payload": {
                "id": str(uuid.uuid4()), # Fresh UUID
                "applicationId": "9f33935f-200d-489c-be06-f69d91c59994",
                "houseName": "Sfsfs", "streetName": "Adad", "localPlaceName": "Asdad",
                "requestId": str(uuid.uuid4()) # Fresh Request ID
            }
        },
        "License Create (Cit)": {
            "url": f"{BASE_URL}/bf-ifteos-services/application/create",
            "method": "POST", "auth_type": "citizen",
            "payload": {
                "license": {
                    "id": str(uuid.uuid4()), # Fresh UUID
                    "officeCode": "10132100266", "applicationType": "NEW", "applicationDate": iso_date,
                    "status": "INITIATED", "financialYear": 2025, "active": True,
                    "application": {"officeCode": "10132100266", "userName": "Bhagyanath V V"}
                }
            }
        },
        "Inbox (Cit)": {"url": f"{BASE_URL}/inbox-services/inbox/myApplications/cca5abd0-c82a-4942-99fa-9b57deee8670?category=CR", "method": "POST", "auth_type": "citizen", "payload": {}}
    }

INTELLIGENT_OFFSETS = {"File Inbox (Off)": 233, "CR Marriage (Cit)": 373, "Property Tax - PTX (Cit)": 490, "License Create (Cit)": 222, "Inbox (Cit)": 112}

st.set_page_config(page_title="K-SMART Hub Pro", layout="wide")

# --- 2. SESSION STATE ---
for key in ['log_data', 'monitoring_active', 'citizen_token', 'official_token', 'alert_log']:
    if key not in st.session_state:
        if key in ['log_data', 'alert_log']: st.session_state[key] = pd.DataFrame(columns=["Timestamp", "Module", "Latency(ms)", "Status", "IsError", "Details"])
        elif key == 'monitoring_active': st.session_state[key] = False
        else: st.session_state[key] = None
if 'last_run' not in st.session_state: st.session_state.last_run = datetime.now() - timedelta(days=1)

# --- 3. UI HEADER ---
st.title("🛡️ K-SMART Performance Hub Pro")

# --- 4. SIDEBAR FEATURES ---
st.sidebar.header("⚙️ Global Settings")
interval_min = st.sidebar.slider("Pulse Interval (Min)", 1, 60, 5)
spike_sensitivity = st.sidebar.slider("Spike Sensitivity (%)", 10, 100, 30)

if st.sidebar.button("📥 Export Audit CSV"):
    if not st.session_state.log_data.empty:
        csv = st.session_state.log_data.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Click to Download", csv, "ksmart_audit.csv", "text/csv")

if st.sidebar.button("🗑️ Clear All Logs", type="secondary"):
    st.session_state.log_data = st.session_state.log_data.iloc[0:0]
    st.session_state.alert_log = st.session_state.alert_log.iloc[0:0]
    st.rerun()

# --- 5. AUTHENTICATION ---
with st.expander("🔐 Session Access Control", expanded=not st.session_state.monitoring_active):
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Citizen: {'✅' if st.session_state.citizen_token else '❌'}")
        c_phone = st.text_input("Phone", value="9947788325")
        if st.button("Send Cit OTP"):
            res = requests.post(f"{BASE_URL}/user-service/v1/re-send-otp", json={"phoneNumber": c_phone, "userType": "CITIZEN"}).json()
            st.session_state.c_uuid = res['data']['otp']['UUID']
        c_otp = st.text_input("Verify Cit OTP")
        if st.button("Log In Citizen"):
            res = requests.post(f"{BASE_URL}/user-service/v1/login", json={"phoneNumber": c_phone, "otp": c_otp, "otpId": st.session_state.c_uuid, "userType": "CITIZEN"}).json()
            st.session_state.citizen_token = res['data']['token']
            st.rerun()
    with col2:
        st.info(f"Official: {'✅' if st.session_state.official_token else '❌'}")
        e_pen = st.text_input("PEN", value="M10021")
        if st.button("Send Off OTP"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/generate-otp?pen={e_pen}").json()
            st.session_state.e_uuid = res['payload']
        e_otp = st.text_input("Verify Off OTP")
        if st.button("Log In Official"):
            res = requests.post(f"{BASE_URL}/employee-services/auth/verify-otp", json={"pen": e_pen, "otp": e_otp, "id": st.session_state.e_uuid}).json()
            st.session_state.official_token = res['payload']['token']
            st.rerun()

# --- 6. MAIN MONITORING ENGINE ---
if st.session_state.citizen_token and st.session_state.official_token:
    if st.sidebar.button("▶️ TOGGLE MONITORING", type="primary"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
        st.rerun()

    if st.session_state.monitoring_active:
        now = datetime.now()
        next_pulse = st.session_state.last_run + timedelta(minutes=interval_min)
        time_left = (next_pulse - now).total_seconds()
        
        # --- TOP METRICS BAR ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Status", "RUNNING" if time_left > 0 else "PULSING")
        m2.metric("Next Pulse", f"{int(max(0, time_left)//60)}m {int(max(0, time_left)%60)}s")
        
        if not st.session_state.log_data.empty:
            health = int((1 - (st.session_state.log_data['IsError'].mean())) * 100)
            m3.metric("Health Score", f"{health}%")
            m4.metric("Total Pings", len(st.session_state.log_data))

        if time_left <= 0:
            st.session_state.last_run = now
            CURRENT_ENDPOINTS = get_dynamic_payloads()
            
            for name, cfg in CURRENT_ENDPOINTS.items():
                token = st.session_state.official_token if cfg["auth_type"] == "official" else st.session_state.citizen_token
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-STATE-CODE": "kl"}
                
                s_time = time.time()
                try:
                    r = requests.request(cfg["method"], cfg["url"], headers=headers, json=cfg["payload"], timeout=20)
                    lat = round(max(0, ((time.time() - s_time) * 1000) - INTELLIGENT_OFFSETS.get(name, 0)), 2)
                    
                    is_err = 0
                    detail = "OK"
                    if r.status_code not in [200, 201]:
                        is_err = 1
                        detail = f"Error {r.status_code}"
                    elif not st.session_state.log_data.empty:
                        # Logic for spike detection
                        prev = st.session_state.log_data[st.session_state.log_data['Module'] == name]['Latency(ms)'].tail(3).mean()
                        if lat > (prev * (1 + spike_sensitivity/100)) and lat > 150:
                            is_err = 1
                            detail = "Latency Spike"

                    new_row = {"Timestamp": now.strftime("%H:%M:%S"), "Module": name, "Latency(ms)": lat, "Status": r.status_code, "IsError": is_err, "Details": detail}
                    st.session_state.log_data = pd.concat([st.session_state.log_data, pd.DataFrame([new_row])], ignore_index=True)
                    
                    if is_err:
                        st.session_state.alert_log = pd.concat([pd.DataFrame([new_row]), st.session_state.alert_log], ignore_index=True)
                except: pass
            st.rerun()

        # --- VISUALIZATION ---
        tab1, tab2, tab3 = st.tabs(["📈 Latency Trends", "🧱 Performance Matrix", "🚨 Alert Console"])
        
        with tab1:
            if not st.session_state.log_data.empty:
                fig = px.line(st.session_state.log_data, x="Timestamp", y="Latency(ms)", color="Module", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if not st.session_state.log_data.empty:
                st.subheader("Module Stability (Last 5 Cycles)")
                pivot = st.session_state.log_data.pivot_table(index='Module', columns='Timestamp', values='Latency(ms)').iloc[:, -5:]
                st.dataframe(pivot.style.background_gradient(cmap='YlOrRd', axis=None), use_container_width=True)

        with tab3:
            st.subheader("Incident History")
            if not st.session_state.alert_log.empty:
                st.table(st.session_state.alert_log.head(15))
            else:
                st.success("No system incidents recorded.")

        time.sleep(1)
        st.rerun()
else:
    st.warning("Please authenticate both accounts to proceed.")