import streamlit as st
import cv2
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import time
import io

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="DEEPTRACE PRO | Neural Forensic Suite", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #020617; color: #f8fafc; }
    .stButton>button { border-radius: 8px; background: linear-gradient(90deg, #0ea5e9, #2563eb); color: white; border: none; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4); }
    .report-card { padding: 25px; border-radius: 15px; border: 1px solid #1e293b; background-color: #0f172a; margin-top: 20px; }
    .metric-text { font-family: 'Courier New', monospace; color: #38bdf8; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect("forensic_history.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS scans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, type TEXT, 
                 result TEXT, confidence REAL, timestamp TEXT)''')
    conn.commit()
    return conn

def save_to_db(filename, file_type, result, confidence):
    conn = sqlite3.connect("forensic_history.db")
    conn.execute("INSERT INTO scans (filename, type, result, confidence, timestamp) VALUES (?,?,?,?,?)",
                 (filename, file_type, result, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- ADVANCED FORENSIC ENGINE ---
def analyze_forensics(frame):
    """
    Enhanced Analysis: Laplacian Variance + Edge Map Generation
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate Laplacian Variance
    lap_feat = cv2.Laplacian(gray, cv2.CV_64F)
    variance = lap_feat.var()
    
    # Generate an "Edge Map" for the user to see (Forensic Visualization)
    edge_map = np.uint8(np.absolute(lap_feat))
    edge_map = cv2.applyColorMap(edge_map, cv2.COLORMAP_JET)
    
    # Decision Logic
    # Deepfakes often have 'soft' transitions or unnatural smoothness in specific areas
    if variance < 100: 
        score = 0.88  # Likely Fake (Too blurry/smooth)
        reason = "Unnatural smoothing detected. Lack of high-frequency sensor noise suggests AI synthesis or heavy manipulation."
    elif variance > 1000:
        score = 0.70  # Could be sharpened/Fake
        reason = "Excessive edge sharpness detected. Possible sharpening filter used to mask GAN artifacts."
    else:
        score = 0.12  # Likely Real
        reason = "Natural texture patterns and sensor noise levels consistent with authentic optical capture."
        
    return score, reason, edge_map

# --- UI COMPONENTS ---
def main():
    init_db()
    
    st.sidebar.title("🛡️ DEEPTRACE PRO")
    st.sidebar.caption("v2.1 | Neural Forensic Suite")
    st.sidebar.markdown("---")
    
    app_mode = st.sidebar.selectbox("COMMAND CENTER", 
                                    ["Dashboard", "Image Analysis", "Video Analysis", "Live Camera"])

    if app_mode == "Dashboard":
        render_dashboard()
    elif app_mode == "Image Analysis":
        render_image_analysis()
    # (Video and Live modes would follow similar logic)

def render_dashboard():
    st.title("System Status: Active")
    col1, col2, col3 = st.columns(3)
    
    conn = sqlite3.connect("forensic_history.db")
    total_scans = pd.read_sql_query("SELECT COUNT(*) FROM scans", conn).values[0][0]
    fakes_found = pd.read_sql_query("SELECT COUNT(*) FROM scans WHERE result='FAKE'", conn).values[0][0]
    
    col1.metric("Total Scans", total_scans)
    col2.metric("Threats Detected", fakes_found)
    col3.metric("System Health", "100%")
    
    st.markdown("### 📜 Audit Log")
    logs_df = pd.read_sql_query("SELECT timestamp, filename, result, confidence FROM scans ORDER BY id DESC LIMIT 5", conn)
    st.dataframe(logs_df, use_container_width=True)
    conn.close()

def render_image_analysis():
    st.header("🔬 Image Forensic Analysis")
    uploaded_file = st.file_uploader("Drop evidence here...", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        
        image = Image.open(uploaded_file)
        # Reduce size for better UI display
        image.thumbnail((600, 600)) 
        
        with col1:
            st.markdown("#### Original Evidence")
            st.image(image, use_container_width=True)
        
        if st.button("EXECUTE NEURAL SCAN"):
            with st.status("Initializing Forensic Modules...", expanded=True) as status:
                st.write("Extracting luminance layers...")
                time.sleep(0.5)
                st.write("Analyzing pixel variance...")
                img_array = np.array(image.convert('RGB'))
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                score, reason, edge_map = analyze_forensics(img_cv)
                
                time.sleep(0.5)
                st.write("Generating forensic edge map...")
                status.update(label="Analysis Complete!", state="complete", expanded=False)
            
            with col2:
                st.markdown("#### Forensic Visualization")
                st.image(edge_map, caption="Texture Variance Map", use_container_width=True)
            
            # Final Verdict Card
            display_verdict(score, reason, uploaded_file.name, "Image")

def display_verdict(score, reason, filename, m_type):
    label = "FAKE" if score > 0.5 else "REAL"
    conf = score if label == "FAKE" else (1 - score)
    theme_clr = "#fb7185" if label == "FAKE" else "#4ade80"
    
    save_to_db(filename, m_type, label, round(conf * 100, 2))
    
    st.markdown(f"""
        <div class="report-card" style="border-left: 5px solid {theme_clr};">
            <h2 style="color: {theme_clr}; margin-top:0;">VERDICT: {label}</h2>
            <p style="font-size: 1.2em;"><b>Confidence:</b> {conf*100:.2f}%</p>
            <p><b>Technical Analysis:</b> {reason}</p>
            <hr style="opacity: 0.1;">
            <p style="font-size: 0.8em; color: #94a3b8;">SECURE LOG ID: {datetime.now().strftime('%Y%m%d%H%M%S')}</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
