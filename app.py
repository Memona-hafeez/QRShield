import streamlit as st
import cv2
import numpy as np
import webbrowser
import json
from datetime import datetime
from utils import preprocess_qr_image, extract_url_features
from tls_utils import check_tls_certificate
from crypto_utils import verify_signature
from keras.models import load_model
import joblib
import time

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="Secure QR Scanner",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== STYLES ==============
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    * { font-family: 'Poppins', sans-serif; }

    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #4a1d96 0%, #7c3aed 50%, #9f67fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1.5rem 0;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Mode Selector Cards */
    .mode-card {
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        margin: 0.5rem;
        border: 3px solid transparent;
    }

    .mode-card-security {
        background: linear-gradient(135deg, #3b1f6e 0%, #6d28d9 100%);
        color: white;
    }

    .mode-card-signature {
        background: linear-gradient(135deg, #374151 0%, #6b7280 100%);
        color: white;
    }

    .mode-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.2);
    }

    .mode-icon { font-size: 3rem; margin-bottom: 1rem; }
    .mode-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
    .mode-desc { font-size: 0.9rem; opacity: 0.85; line-height: 1.5; }

    .mode-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.8rem;
        background: rgba(255,255,255,0.25);
    }

    .active-mode-banner {
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        text-align: center;
        margin: 1rem 0;
    }

    .banner-security {
        background: linear-gradient(135deg, #3b1f6e 0%, #7c3aed 100%);
        color: white;
    }

    .banner-signature {
        background: linear-gradient(135deg, #374151 0%, #6b7280 100%);
        color: white;
    }

    .status-card {
        padding: 1.8rem;
        border-radius: 15px;
        margin: 1.2rem 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }

    .safe { background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%); color: white; }
    .danger { background: linear-gradient(135deg, #4b5563 0%, #374151 100%); color: white; }
    .warning { background: linear-gradient(135deg, #7c3aed 0%, #9f67fa 100%); color: white; }
    .info { background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%); color: white; }
    .processing { background: linear-gradient(135deg, #4b5563 0%, #6b7280 100%); color: white; }

    .control-panel {
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(109,40,217,0.08);
        margin: 2rem 0;
    }

    .control-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #3b1f6e;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }

    .camera-container {
        background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
        padding: 0.8rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        margin-bottom: 1.2rem;
        max-height: 380px;
        overflow: hidden;
    }

    .camera-title {
        color: #1f2937;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
        text-align: center;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin: 0.8rem 0;
    }

    .metric-card {
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        padding: 0.3rem;
        border-radius: 5px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #c4b5fd;
    }

    .metric-card.success { border-color: #7c3aed; background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%); }
    .metric-card.danger  { border-color: #374151; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); }
    .metric-card.warning { border-color: #9f67fa; background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); }
    .metric-card.purple  { border-color: #6d28d9; background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%); }

    .metric-title  { font-size: 0.55rem; font-weight: 600; color: #3b1f6e; margin-bottom: 0.05rem; }
    .metric-value  { font-size: 0.85rem; font-weight: 700; color: #3b1f6e; margin: 0.05rem 0; }
    .metric-label  { font-size: 0.45rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.2px; }
    .metric-status { font-size: 0.5rem; font-weight: 600; margin-top: 0.15rem; padding: 0.15rem; border-radius: 3px; }
    .metric-status.verified { background: #7c3aed; color: white; }
    .metric-status.failed   { background: #374151; color: white; }
    .metric-status.signed   { background: #6d28d9; color: white; }
    .metric-status.invalid  { background: #4b5563; color: white; }

    .success-message {
        background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%);
        color: white;
        padding: 0.6rem;
        border-radius: 6px;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 700;
        margin: 0.6rem 0;
    }

    .signature-success {
        background: linear-gradient(135deg, #374151 0%, #6b7280 100%);
        color: white;
        padding: 0.6rem;
        border-radius: 6px;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 700;
        margin: 0.6rem 0;
    }

    .sidebar-metric {
        background: linear-gradient(135deg, #4c1d95 0%, #6d28d9 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem 0;
        border-left: 5px solid #9f67fa;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.8rem 1.5rem;
        border-radius: 30px;
        font-weight: 600;
        margin: 0.5rem;
    }

    .status-active   { background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%); color: white; }
    .status-inactive { background: linear-gradient(135deg, #374151 0%, #4b5563 100%); color: white; }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e1b2e 0%, #2e1f5e 100%); }
    [data-testid="stSidebar"] * { color: white !important; }

    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .qr-detected { animation: pulse 1.5s infinite; border: 4px solid #7c3aed; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# ============== SESSION STATE ==============
defaults = {
    'camera_active': False,
    'scan_history': [],
    'total_scans': 0,
    'safe_scans': 0,
    'blocked_scans': 0,
    'auto_open_url': True,
    'sound_enabled': True,
    'scanner_mode': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============== LOAD MODELS ==============
@st.cache_resource
def load_models():
    with st.spinner("🔄 Loading AI models..."):
        image_model = load_model("models/qr_model.h5")
        url_model = joblib.load("models/random_forest_model.joblib")
    return image_model, url_model

try:
    image_model, url_model = load_models()
    models_loaded = True
except Exception as e:
    st.error(f"⚠️ Error loading models: {str(e)}")
    models_loaded = False

# ============== SIDEBAR ==============
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-top: 0;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.scanner_mode:
        mode_label = "🛡️ Security Scanner" if st.session_state.scanner_mode == 'security' else "🔏 Signature Scanner"
        st.markdown(f"<div style='text-align:center; padding:0.8rem; background:rgba(255,255,255,0.1); border-radius:10px; font-weight:600;'>Active Mode:<br>{mode_label}</div>", unsafe_allow_html=True)
        st.markdown("---")

    st.markdown("### 🎯 Scan Settings")
    st.session_state.auto_open_url = st.checkbox("🌐 Auto-open safe URLs", value=st.session_state.auto_open_url)
    st.session_state.sound_enabled = st.checkbox("🔊 Enable sound alerts", value=st.session_state.sound_enabled)
    sensitivity = st.slider("🎚️ Detection Sensitivity", 1, 10, 5)

    st.markdown("---")
    st.markdown("### 📊 Live Statistics")
    for label, val, color in [
        ("Total Scans", st.session_state.total_scans, "#e9d5ff"),
        ("Safe Scans",  st.session_state.safe_scans,  "#c4b5fd"),
        ("Blocked",     st.session_state.blocked_scans,"#d1d5db"),
    ]:
        st.markdown(f"""
            <div class='sidebar-metric'>
                <div class='metric-value' style='color:{color};'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    rate = (st.session_state.safe_scans / st.session_state.total_scans * 100) if st.session_state.total_scans > 0 else 0
    st.markdown(f"""
        <div class='sidebar-metric'>
            <div class='metric-value' style='color:#ddd6fe;'>{rate:.1f}%</div>
            <div class='metric-label'>Success Rate</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📜 Recent Activity")
    if st.session_state.scan_history:
        for scan in reversed(st.session_state.scan_history[-5:]):
            icon  = "✅" if scan['safe'] else "❌"
            color = "#a78bfa" if scan['safe'] else "#9ca3af"
            st.markdown(f"""
                <div style='background:rgba(255,255,255,0.1);padding:0.8rem;border-radius:8px;margin:0.5rem 0;border-left:3px solid {color};'>
                    <div style='font-weight:600;'>{icon} {scan['timestamp']}</div>
                    <div style='font-size:0.85rem;opacity:0.9;'>{scan['status']}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("📭 No scans yet")

    st.markdown("---")
    if st.button("🗑️ Clear All History", use_container_width=True):
        for k in ['scan_history', 'total_scans', 'safe_scans', 'blocked_scans']:
            st.session_state[k] = [] if k == 'scan_history' else 0
        st.rerun()

    if st.session_state.scanner_mode and st.button("🔙 Change Scanner Mode", use_container_width=True):
        st.session_state.scanner_mode = None
        st.session_state.camera_active = False
        st.rerun()

# ============== MAIN HEADER ==============
st.markdown('<h1 class="main-header">🔐 Secure QR Scanner</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Multi-Layer Security Validation System</p>', unsafe_allow_html=True)

# ============================================================
# MODE SELECTION SCREEN
# ============================================================
if st.session_state.scanner_mode is None:
    st.markdown("## 🎯 Select Scanner Mode")
    st.markdown("Choose the scanning mode based on your QR code type:")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='mode-card mode-card-security'>
                <div class='mode-icon'>🛡️</div>
                <div class='mode-title'>Security Scanner</div>
                <div class='mode-desc'>
                    3-Layer AI-powered verification for standard QR codes.<br><br>
                    ✅ Image Tamper Detection<br>
                    ✅ Malicious URL Analysis<br>
                    ✅ TLS Certificate Validation
                </div>
                <div class='mode-badge'>Standard QR Codes</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🛡️ Launch Security Scanner", use_container_width=True, disabled=not models_loaded):
            st.session_state.scanner_mode = 'security'
            st.rerun()

    with col2:
        st.markdown("""
            <div class='mode-card mode-card-signature'>
                <div class='mode-icon'>🔏</div>
                <div class='mode-title'>Advanced Signature Verification</div>
                <div class='mode-desc'>
                    Cryptographic ECDSA signature verification for signed QR codes.<br><br>
                    ✅ ECDSA Signature Verification<br>
                    ✅ Tamper-Proof Authentication<br>
                    ✅ Cryptographically Signed URLs Only
                </div>
                <div class='mode-badge'>Signed QR Codes Only</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔏 Launch Signature Scanner", use_container_width=True):
            st.session_state.scanner_mode = 'signature'
            st.rerun()

    st.stop()

# ============================================================
# ACTIVE MODE BANNER
# ============================================================
if st.session_state.scanner_mode == 'security':
    st.markdown('<div class="active-mode-banner banner-security">🛡️ Security Scanner — 3-Layer AI Verification Active</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="active-mode-banner banner-signature">🔏 Advanced Signature Verification System — ECDSA Authentication Active</div>', unsafe_allow_html=True)

# ============== STATUS INDICATORS ==============
st.markdown("### 📡 System Status")
col1, col2, col3 = st.columns(3)
with col1:
    cls  = "status-active" if st.session_state.camera_active else "status-inactive"
    text = "🟢 Active" if st.session_state.camera_active else "🔴 Inactive"
    st.markdown(f'<div class="status-indicator {cls}">📷 Camera: {text}</div>', unsafe_allow_html=True)
with col2:
    text = "🟢 Ready" if models_loaded else "🔴 Error"
    label = "🤖 AI Models" if st.session_state.scanner_mode == 'security' else "🔑 Crypto Engine"
    st.markdown(f'<div class="status-indicator status-inactive">{label}: {text}</div>', unsafe_allow_html=True)
with col3:
    mode_text = "Auto-Open" if st.session_state.auto_open_url else "Manual"
    st.markdown(f'<div class="status-indicator status-inactive">🎯 Mode: {mode_text}</div>', unsafe_allow_html=True)

st.markdown("---")

# ============== CONTROL PANEL ==============
st.markdown('<div class="control-panel">', unsafe_allow_html=True)
st.markdown('<div class="control-title">🎮 Scanner Controls</div>', unsafe_allow_html=True)

if not st.session_state.camera_active:
    disabled = (not models_loaded) if st.session_state.scanner_mode == 'security' else False
    if st.button("📷 START CAMERA", type="primary", disabled=disabled, use_container_width=True):
        st.session_state.camera_active = True
        st.rerun()
else:
    if st.button("⏸️ STOP CAMERA", type="primary", use_container_width=True):
        st.session_state.camera_active = False
        st.rerun()

if st.button("ℹ️ HOW TO USE", use_container_width=True):
    with st.expander("📖 User Guide", expanded=True):
        if st.session_state.scanner_mode == 'security':
            st.markdown("""
            ### 🛡️ Security Scanner Guide
            **Step 1:** Click START CAMERA  
            **Step 2:** Point camera at any QR code  
            **Step 3:** System runs 3 checks automatically:
            - ✅ **Layer 1 — Image Tamper Detection** (AI model)
            - ✅ **Layer 2 — Malicious URL Check** (Random Forest)
            - ✅ **Layer 3 — TLS Certificate Validation**
            
            **Step 4:** Safe URLs open automatically (if enabled)
            """)
        else:
            st.markdown("""
            ### 🔏 Signature Verification Guide
            **Step 1:** Click START CAMERA  
            **Step 2:** Point camera at a **Signed QR Code** (generated by your system)  
            **Step 3:** System verifies the ECDSA cryptographic signature  
            - ✅ **Valid Signature** → URL opens automatically  
            - ❌ **Invalid/Fake** → URL is blocked  
            
            **Note:** Only QR codes generated by your `qr_generator.py` will pass.
            """)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")

# ============== CAMERA FEED ==============
st.markdown('<div class="camera-container">', unsafe_allow_html=True)
st.markdown('<div class="camera-title">📹 Live Camera Feed</div>', unsafe_allow_html=True)
frame_placeholder = st.empty()
st.markdown('</div>', unsafe_allow_html=True)

status_placeholder = st.empty()
result_placeholder  = st.empty()

# ============================================================
# SECURITY SCANNER LOOP (3 Layers)
# ============================================================
def run_security_scanner():
    detector = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("❌ Unable to access camera.")
        st.session_state.camera_active = False
        return

    status_placeholder.markdown('<div class="status-card info">🔍 Scanning for QR codes...</div>', unsafe_allow_html=True)
    frame_count   = 0
    last_qr_data  = None
    last_scan_time = 0

    while st.session_state.camera_active:
        ret, frame = cap.read()
        if not ret:
            status_placeholder.markdown('<div class="status-card warning">⚠️ Camera feed interrupted</div>', unsafe_allow_html=True)
            break

        frame_count += 1
        current_time = time.time()

        if frame_count % (11 - sensitivity) == 0:
            data, bbox, _ = detector.detectAndDecode(frame)

            if data and data != last_qr_data and (current_time - last_scan_time) > 3:
                last_qr_data   = data
                last_scan_time = current_time

                try:
                    qr_json = json.loads(data)
                    qr_data = qr_json.get("data") or qr_json.get("d") or data
                except:
                    qr_data = data

                if bbox is not None:
                    bbox = np.int32(bbox)
                    cv2.polylines(frame, [bbox], True, (124, 58, 237), 4)
                    cv2.putText(frame, "QR CODE DETECTED!", (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (124, 58, 237), 3)

                    x = int(bbox[0][0][0]); y = int(bbox[0][0][1])
                    w = int(bbox[0][2][0] - bbox[0][0][0])
                    h = int(bbox[0][2][1] - bbox[0][0][1])
                    qr_image = frame[y:y+h, x:x+w]

                    status_placeholder.markdown('<div class="status-card processing">🔄 Processing QR Code...</div>', unsafe_allow_html=True)

                    img_confidence = url_confidence = 0
                    img_authentic  = url_safe = tls_valid = False
                    tls_status = "Pending"

                    try:
                        # --- Layer 1: Image Tamper ---
                        img_input = preprocess_qr_image(qr_image)
                        img_pred  = image_model.predict(img_input, verbose=0)
                        img_label = np.argmax(img_pred)
                        img_confidence = float(img_pred[0][img_label]) * 100

                        if img_label == 1:
                            st.session_state.blocked_scans += 1
                            st.session_state.total_scans   += 1
                            st.session_state.scan_history.append({'url': qr_data, 'safe': False, 'status': 'Image Tampered', 'timestamp': datetime.now().strftime("%H:%M:%S")})
                            with result_placeholder.container():
                                st.markdown(f"""
                                    <div class='metrics-grid'>
                                        <div class='metric-card danger'>
                                            <div class='metric-title'>Image Authenticity</div>
                                            <div class='metric-value'>{img_confidence:.1f}%</div>
                                            <div class='metric-label'>Tamper Detection</div>
                                            <div class='metric-status failed'>TAMPERED</div>
                                        </div>
                                        <div class='metric-card'><div class='metric-title'>URL Security</div><div class='metric-value'>--</div><div class='metric-label'>Not Checked</div><div class='metric-status'>SKIPPED</div></div>
                                        <div class='metric-card'><div class='metric-title'>TLS Certificate</div><div class='metric-value'>--</div><div class='metric-label'>Not Checked</div><div class='metric-status'>SKIPPED</div></div>
                                    </div>""", unsafe_allow_html=True)
                                st.error("🚫 **Scan Blocked:** Tampered QR image detected!")
                            time.sleep(2)
                            continue
                        else:
                            img_authentic = True

                        # --- Layer 2: URL Security ---
                        url_features = extract_url_features(qr_data)
                        url_pred     = url_model.predict(url_features)
                        url_proba    = url_model.predict_proba(url_features)
                        url_confidence = float(max(url_proba[0])) * 100

                        if url_pred[0] == 1:
                            st.session_state.blocked_scans += 1
                            st.session_state.total_scans   += 1
                            st.session_state.scan_history.append({'url': qr_data, 'safe': False, 'status': 'Malicious URL', 'timestamp': datetime.now().strftime("%H:%M:%S")})
                            with result_placeholder.container():
                                st.markdown(f"""
                                    <div class='metrics-grid'>
                                        <div class='metric-card success'>
                                            <div class='metric-title'>Image Authenticity</div>
                                            <div class='metric-value'>{img_confidence:.1f}%</div>
                                            <div class='metric-label'>Tamper Detection</div>
                                            <div class='metric-status verified'>AUTHENTIC</div>
                                        </div>
                                        <div class='metric-card danger'>
                                            <div class='metric-title'>URL Security</div>
                                            <div class='metric-value'>{url_confidence:.1f}%</div>
                                            <div class='metric-label'>Malicious Detection</div>
                                            <div class='metric-status failed'>MALICIOUS</div>
                                        </div>
                                        <div class='metric-card'><div class='metric-title'>TLS Certificate</div><div class='metric-value'>--</div><div class='metric-label'>Not Checked</div><div class='metric-status'>SKIPPED</div></div>
                                    </div>""", unsafe_allow_html=True)
                                st.error("🚫 **Scan Blocked:** Malicious URL detected!")
                            time.sleep(2)
                            continue
                        else:
                            url_safe = True

                        # --- Layer 3: TLS ---
                        tls_valid, tls_msg = check_tls_certificate(qr_data)
                        tls_status = tls_msg
                        tls_class  = "success" if tls_valid else "warning"
                        tls_label  = "VALID" if tls_valid else "WARNING"

                        st.session_state.safe_scans   += 1
                        st.session_state.total_scans  += 1
                        st.session_state.scan_history.append({'url': qr_data, 'safe': True, 'status': 'All checks passed', 'timestamp': datetime.now().strftime("%H:%M:%S")})

                        with result_placeholder.container():
                            st.markdown(f"""
                                <div class='metrics-grid'>
                                    <div class='metric-card success'>
                                        <div class='metric-title'>Image Authenticity</div>
                                        <div class='metric-value'>{img_confidence:.1f}%</div>
                                        <div class='metric-label'>Tamper Detection</div>
                                        <div class='metric-status verified'>AUTHENTIC</div>
                                    </div>
                                    <div class='metric-card success'>
                                        <div class='metric-title'>URL Security</div>
                                        <div class='metric-value'>{url_confidence:.1f}%</div>
                                        <div class='metric-label'>Safety Confidence</div>
                                        <div class='metric-status verified'>SAFE</div>
                                    </div>
                                    <div class='metric-card {tls_class}'>
                                        <div class='metric-title'>TLS Certificate</div>
                                        <div class='metric-value'>{"Valid" if tls_valid else "Issue"}</div>
                                        <div class='metric-label'>{tls_status}</div>
                                        <div class='metric-status {"verified" if tls_valid else ""}'>{tls_label}</div>
                                    </div>
                                </div>""", unsafe_allow_html=True)
                            st.markdown('<div class="success-message">✅ All Security Checks Passed!</div>', unsafe_allow_html=True)
                            st.markdown(f"<div style='font-size:0.75rem;padding:0.4rem;background:#f5f3ff;border-radius:5px;margin:0.5rem 0;'>🔗 <strong>URL:</strong> {qr_data}</div>", unsafe_allow_html=True)

                            if st.session_state.auto_open_url:
                                webbrowser.open(qr_data)
                            else:
                                if st.button("🌐 OPEN URL", key=f"open_{current_time}", use_container_width=True):
                                    webbrowser.open(qr_data)

                    except Exception as e:
                        st.error(f"⚠️ Error: {str(e)}")

            elif bbox is not None and data:
                bbox = np.int32(bbox)
                cv2.polylines(frame, [bbox], True, (107, 114, 128), 3)
                cv2.putText(frame, "ALREADY SCANNED", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (107, 114, 128), 2)

        cv2.putText(frame, f"Frame: {frame_count} | Scans: {st.session_state.total_scans}",
                    (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
        time.sleep(0.01)

    cap.release()
    status_placeholder.markdown('<div class="status-card safe">✅ Camera stopped successfully</div>', unsafe_allow_html=True)


# ============================================================
# SIGNATURE SCANNER LOOP (ECDSA)
# ============================================================
def run_signature_scanner():
    detector = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("❌ Unable to access camera.")
        st.session_state.camera_active = False
        return

    status_placeholder.markdown('<div class="status-card processing">🔍 Scanning for Signed QR codes...</div>', unsafe_allow_html=True)
    last_data      = None
    last_scan_time = 0
    frame_count    = 0

    while st.session_state.camera_active:
        ret, frame = cap.read()
        if not ret:
            status_placeholder.markdown('<div class="status-card warning">⚠️ Camera feed interrupted</div>', unsafe_allow_html=True)
            break

        frame_count  += 1
        current_time  = time.time()

        if frame_count % (11 - sensitivity) == 0:
            data, bbox, _ = detector.detectAndDecode(frame)

            if data and data != last_data and (current_time - last_scan_time) > 3:
                last_data      = data
                last_scan_time = current_time

                if bbox is not None:
                    bbox = np.int32(bbox)

                try:
                    qr_json  = json.loads(data)
                    qr_data  = qr_json.get("d")
                    signature = qr_json.get("s")

                    if not qr_data or not signature:
                        raise ValueError("Missing fields")

                    if bbox is not None:
                        cv2.polylines(frame, [bbox], True, (107, 114, 128), 4)
                        cv2.putText(frame, "SIGNED QR DETECTED", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (107, 114, 128), 3)

                    status_placeholder.markdown('<div class="status-card processing">🔐 Verifying Cryptographic Signature...</div>', unsafe_allow_html=True)

                    sig_valid = verify_signature(qr_data, signature)

                    if sig_valid:
                        st.session_state.safe_scans  += 1
                        st.session_state.total_scans += 1
                        st.session_state.scan_history.append({'url': qr_data, 'safe': True, 'status': 'Signature Valid', 'timestamp': datetime.now().strftime("%H:%M:%S")})

                        with result_placeholder.container():
                            st.markdown(f"""
                                <div class='metrics-grid'>
                                    <div class='metric-card purple'>
                                        <div class='metric-title'>ECDSA Signature</div>
                                        <div class='metric-value'>✔</div>
                                        <div class='metric-label'>Cryptographic Proof</div>
                                        <div class='metric-status signed'>VERIFIED</div>
                                    </div>
                                    <div class='metric-card purple'>
                                        <div class='metric-title'>Origin</div>
                                        <div class='metric-value'>✔</div>
                                        <div class='metric-label'>Trusted Source</div>
                                        <div class='metric-status signed'>AUTHENTIC</div>
                                    </div>
                                    <div class='metric-card purple'>
                                        <div class='metric-title'>Tamper Check</div>
                                        <div class='metric-value'>✔</div>
                                        <div class='metric-label'>Integrity Confirmed</div>
                                        <div class='metric-status signed'>INTACT</div>
                                    </div>
                                </div>""", unsafe_allow_html=True)
                            st.markdown('<div class="signature-success">🔏 Signature Verified — Cryptographically Authentic!</div>', unsafe_allow_html=True)
                            st.markdown(f"<div style='font-size:0.75rem;padding:0.4rem;background:#f5f3ff;border-radius:5px;margin:0.5rem 0;'>🔗 <strong>URL:</strong> {qr_data}</div>", unsafe_allow_html=True)

                            if st.session_state.auto_open_url:
                                webbrowser.open(qr_data)
                            else:
                                if st.button("🌐 OPEN URL", key=f"sig_open_{current_time}", use_container_width=True):
                                    webbrowser.open(qr_data)
                    else:
                        st.session_state.blocked_scans += 1
                        st.session_state.total_scans   += 1
                        st.session_state.scan_history.append({'url': qr_data, 'safe': False, 'status': 'Invalid Signature', 'timestamp': datetime.now().strftime("%H:%M:%S")})

                        with result_placeholder.container():
                            st.markdown(f"""
                                <div class='metrics-grid'>
                                    <div class='metric-card danger'>
                                        <div class='metric-title'>ECDSA Signature</div>
                                        <div class='metric-value'>✗</div>
                                        <div class='metric-label'>Verification Failed</div>
                                        <div class='metric-status invalid'>INVALID</div>
                                    </div>
                                    <div class='metric-card danger'>
                                        <div class='metric-title'>Origin</div>
                                        <div class='metric-value'>✗</div>
                                        <div class='metric-label'>Untrusted Source</div>
                                        <div class='metric-status invalid'>FAKE</div>
                                    </div>
                                    <div class='metric-card danger'>
                                        <div class='metric-title'>Tamper Check</div>
                                        <div class='metric-value'>✗</div>
                                        <div class='metric-label'>Data Modified</div>
                                        <div class='metric-status invalid'>TAMPERED</div>
                                    </div>
                                </div>""", unsafe_allow_html=True)
                            st.error("🚫 **Blocked:** Invalid or forged QR signature!")

                except (json.JSONDecodeError, ValueError, KeyError):
                    with result_placeholder.container():
                        st.warning("⚠️ Not a signed QR code — this mode only accepts cryptographically signed QR codes.")

                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

        cv2.putText(frame, f"Frame: {frame_count} | Scans: {st.session_state.total_scans}",
                    (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
        time.sleep(0.01)

    cap.release()
    status_placeholder.markdown('<div class="status-card safe">✅ Camera stopped successfully</div>', unsafe_allow_html=True)


# ============================================================
# TRIGGER CORRECT SCANNER
# ============================================================
if st.session_state.camera_active:
    if st.session_state.scanner_mode == 'security' and models_loaded:
        run_security_scanner()
    elif st.session_state.scanner_mode == 'signature':
        run_signature_scanner()
    elif st.session_state.scanner_mode == 'security' and not models_loaded:
        st.error("⚠️ AI Models not loaded. Please check your model files.")
elif not st.session_state.camera_active:
    result_placeholder.info("👆 Click **START CAMERA** above to begin scanning")

# ============== FOOTER ==============
st.markdown("---")
st.markdown("""
    <div style='text-align:center;padding:2rem 0;background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%);border-radius:15px;margin-top:2rem;'>
        <h3 style='color:#3b1f6e;margin-bottom:0.5rem;'>🔐 Secure QR Scanner</h3>
        <p style='color:#6d28d9;font-size:1rem;margin:0.5rem 0;'>Multi-Layer AI Security + Cryptographic Signature Verification</p>
        <p style='color:#7c3aed;font-size:0.85rem;'>Image Analysis • URL Detection • TLS Validation • ECDSA Signature</p>
    </div>
""", unsafe_allow_html=True)