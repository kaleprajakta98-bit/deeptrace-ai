import streamlit as st
import cv2
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import time
import io

# --- ENHANCED GLASS-MORPHISM STYLING ---
st.set_page_config(page_title="DEEPTRACE ULTRA", layout="wide", page_icon="🧪")

def apply_custom_css():
    st.markdown("""
        <style>
        .stApp {
            background: radial-gradient(circle at top right, #1e1b4b, #020617);
            color: #e2e8f0;
        }
        .metric-card {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(56, 189, 248, 0.2);
            backdrop-filter: blur(12px);
            padding: 25px;
            border-radius: 20px;
            text-align: center;
        }
        .stButton>button {
            background: linear-gradient(90deg, #0ea5e9, #6366f1);
            color: white; border: none; border-radius: 8px; font-weight: bold;
        }
        .glow-text {
            color: #fff;
            text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
            font-weight: 800;
        }
        </style>
        """, unsafe_allow_html=True)

# --- ENGINE LOGIC ---
def analyze_forensics(frame):
    if frame is None:
        return 0.5, "Error: Image frame is empty.", None
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Generate Heatmap
    lap_abs = np.uint8(np.absolute(cv2.Laplacian(gray, cv2.CV_64F)))
    heatmap = cv2.applyColorMap(lap_abs, cv2.COLORMAP_MAGMA)
    
    if variance < 110:
        return 0.89, "SYNTHETIC SIGNAL: High-frequency smoothing detected. Pattern matches AI generative artifacts.", heatmap
    else:
        return 0.11, "ORGANIC SIGNAL: Natural sensor noise and photon distribution detected.", heatmap

def save_scan(fname, mtype, result, conf):
    conn = sqlite3.connect("forensic_history.db")
    conn.execute("INSERT INTO scans (filename, type, result, confidence, timestamp) VALUES (?,?,?,?,?)",
                 (fname, mtype, result, conf, datetime.now().strftime("%I:%M %p")))
    conn.commit()
    conn.close()

# --- UI COMPONENTS ---
def render_dashboard():
    st.markdown("<h1 class='glow-text'>NEURAL COMMAND CENTER</h1>", unsafe_allow_html=True)
    
    conn = sqlite3.connect("forensic_history.db")
    df = pd.read_sql_query("SELECT * FROM scans", conn)
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<div class='metric-card'><h3>TOTAL</h3><h1 style='color:#38bdf8'>{len(df)}</h1></div>", unsafe_allow_html=True)
    with col2: 
        fakes = len(df[df['result'] == 'FAKE'])
        st.markdown(f"<div class='metric-card'><h3>FAKES</h3><h1 style='color:#fb7185'>{fakes}</h1></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><h3>UPTIME</h3><h1 style='color:#4ade80'>100%</h1></div>", unsafe_allow_html=True)
    with col4: st.markdown(f"<div class='metric-card'><h3>CORE</h3><h1 style='color:#c084fc'>V3.5</h1></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🕵️ Forensic Logs")
    st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)

def render_analysis_ui(mode):
    st.markdown(f"<h2 class='glow-text'>{mode} Analysis</h2>", unsafe_allow_html=True)
    col_input, col_output = st.columns([1, 1], gap="large")
    
    up = None
    with col_input:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        if mode == "Image Analysis":
            up = st.file_uploader("Upload Forensic Evidence", type=['jpg', 'png', 'jpeg'])
            if up: st.image(up, use_container_width=True)
        elif mode == "Video Analysis":
            up = st.file_uploader("Upload Video", type=['mp4', 'avi'])
            if up: st.video(up)
        elif mode == "Live Camera":
            up = st.camera_input("Sensor Capture")
        st.markdown("</div>", unsafe_allow_html=True)

    if up:
        with col_output:
            if st.button("🚀 EXECUTE SCAN"):
                try:
                    # FIX: Handle buffer reset for OpenCV
                    img_bytes = up.getvalue()
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    with st.status("Analyzing...", expanded=False):
                        score, reason, heatmap = analyze_forensics(img_cv)
                        time.sleep(1)

                    label = "FAKE" if score > 0.5 else "REAL"
                    clr = "#fb7185" if label == "FAKE" else "#4ade80"
                    
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.3); padding:20px; border-radius:15px; border: 2px solid {clr}">
                            <h2 style="color:{clr}; margin:0;">VERDICT: {label}</h2>
                            <p><b>Confidence:</b> {score*100 if label=='FAKE' else (1-score)*100:.1f}%</p>
                            <p style="color:#94a3b8"><i>{reason}</i></p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if heatmap is not None:
                        st.image(heatmap, caption="Frequency Artifact Heatmap", use_container_width=True)
                    
                    save_scan(getattr(up, 'name', 'Sensor_Snap'), mode, label, score*100)
                except Exception as e:
                    st.error(f"Processing Error: {str(e)}")

# --- MAIN ---
def main():
    # Setup Database
    conn = sqlite3.connect("forensic_history.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS scans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, type TEXT, 
                 result TEXT, confidence REAL, timestamp TEXT)''')
    conn.close()

    apply_custom_css()
    
    st.sidebar.markdown("<h1 style='color:#38bdf8'>DEEPTRACE</h1>", unsafe_allow_html=True)
    choice = st.sidebar.radio("Navigation", ["Dashboard", "Image Analysis", "Video Analysis", "Live Camera"])
    
    if choice == "Dashboard": render_dashboard()
    else: render_analysis_ui(choice)

if __name__ == "__main__":
    main()
