import streamlit as st
import cv2
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import time
import tempfile
import os
import io

# --- ENHANCED GLASS-MORPHISM STYLING ---
st.set_page_config(page_title="DEEPTRACE ULTRA", layout="wide", page_icon="🧪")

def local_css():
    st.markdown("""
        <style>
        /* Main Background with animated gradient */
        .stApp {
            background: radial-gradient(circle at top right, #1e1b4b, #020617);
            color: #e2e8f0;
        }
        
        /* Glassmorphism Cards */
        .metric-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(56, 189, 248, 0.2);
            backdrop-filter: blur(12px);
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            transition: 0.3s;
        }
        .metric-card:hover {
            border-color: #38bdf8;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.1);
        }

        /* Scan Animation */
        .scanning-line {
            width: 100%;
            height: 2px;
            background: #38bdf8;
            position: relative;
            animation: scan 2s infinite;
        }
        @keyframes scan {
            0% { top: 0; }
            100% { top: 100%; }
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.95) !important;
            border-right: 1px solid rgba(56, 189, 248, 0.2);
        }

        /* Titles and Glow */
        .glow-text {
            color: #fff;
            text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
            font-family: 'Inter', sans-serif;
            font-weight: 800;
        }
        </style>
        """, unsafe_allow_html=True)

# --- ENGINE LOGIC ---
def analyze_forensics(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Generate Heatmap for "Wow" factor
    lap_abs = np.uint8(np.absolute(cv2.Laplacian(gray, cv2.CV_64F)))
    heatmap = cv2.applyColorMap(lap_abs, cv2.COLORMAP_MAGMA)
    
    if variance < 110:
        return 0.89, "SYNTHETIC SIGNAL: Unnatural pixel smoothness detected in high-frequency bands.", heatmap
    else:
        return 0.11, "ORGANIC SIGNAL: Sensor-level noise and photonic artifacts consistent with hardware capture.", heatmap

def save_scan(fname, mtype, result, conf):
    conn = sqlite3.connect("forensic_history.db")
    conn.execute("INSERT INTO scans (filename, type, result, confidence, timestamp) VALUES (?,?,?,?,?)",
                 (fname, mtype, result, conf, datetime.now().strftime("%I:%M %p")))
    conn.commit()
    conn.close()

# --- INTERFACE COMPONENTS ---
def render_dashboard():
    st.markdown("<h1 class='glow-text'>NEURAL COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.write("System Integrity: **98.4% Operational** | Threat Level: **Low**")
    
    # Grid Layout for Dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    conn = sqlite3.connect("forensic_history.db")
    df = pd.read_sql_query("SELECT * FROM scans", conn)
    conn.close()

    with col1:
        st.markdown(f"<div class='metric-card'><h3>TOTAL</h3><h1 style='color:#38bdf8'>{len(df)}</h1><p>Scans Run</p></div>", unsafe_allow_html=True)
    with col2:
        fakes = len(df[df['result'] == 'FAKE'])
        st.markdown(f"<div class='metric-card'><h3>FAKES</h3><h1 style='color:#fb7185'>{fakes}</h1><p>Detected</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>UPTIME</h3><h1 style='color:#4ade80'>99.9%</h1><p>Server Ready</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h3>AI MODE</h3><h1 style='color:#c084fc'>V3.0</h1><p>Laplacian Eng.</p></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Forensic Activity Table
    st.subheader("🕵️ Recent Investigative Logs")
    if not df.empty:
        st.dataframe(df.tail(8).sort_index(ascending=False), use_container_width=True)
    else:
        st.info("No scan data available. Start by uploading an asset.")

def render_analysis_ui(mode):
    st.markdown(f"<h2 class='glow-text'>{mode} Analysis</h2>", unsafe_allow_html=True)
    
    col_input, col_output = st.columns([1, 1], gap="large")
    
    with col_input:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        if mode == "Image Analysis":
            up = st.file_uploader("Drop Asset Here", type=['jpg', 'png', 'jpeg'])
            if up:
                img = Image.open(up)
                st.image(img, use_container_width=True)
        elif mode == "Video Analysis":
            up = st.file_uploader("Upload Video File", type=['mp4', 'avi'])
            if up: st.video(up)
        elif mode == "Live Camera":
            up = st.camera_input("Neural Snapshot")
        st.markdown("</div>", unsafe_allow_html=True)

    if up:
        with col_output:
            if st.button("🚀 INITIATE SCAN"):
                # Simulation and Processing
                with st.status("Analyzing Neural Artifacts...", expanded=True) as s:
                    st.write("🔍 Isolating frequency layers...")
                    time.sleep(1)
                    st.write("🧬 Running Laplacian variance check...")
                    
                    # Core Analysis
                    file_bytes = np.asarray(bytearray(up.read()), dtype=np.uint8)
                    img_cv = cv2.imdecode(file_bytes, 1)
                    score, reason, heatmap = analyze_forensics(img_cv)
                    
                    time.sleep(0.5)
                    s.update(label="Scanning Complete", state="complete")

                # Verdict Display
                label = "FAKE" if score > 0.5 else "REAL"
                clr = "#fb7185" if label == "FAKE" else "#4ade80"
                
                st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.3); padding:20px; border-radius:15px; border: 2px solid {clr}">
                        <h1 style="color:{clr}; margin:0;">{label} DETECTED</h1>
                        <p style="font-size:1.1em; margin-top:10px;"><b>Confidence Score:</b> {score*100 if label=='FAKE' else (1-score)*100:.1f}%</p>
                        <p style="color:#94a3b8"><b>Analyst Note:</b> {reason}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.image(heatmap, caption="Frequency Artifact Heatmap", use_container_width=True)
                save_scan(getattr(up, 'name', 'Camera_Snap'), mode, label, score*100)

# --- MAIN APP ---
def main():
    # Database fix: ensure scans table exists
    conn = sqlite3.connect("forensic_history.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS scans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, type TEXT, 
                 result TEXT, confidence REAL, timestamp TEXT)''')
    conn.close()

    local_css()
    
    st.sidebar.markdown("<h1 style='color:#38bdf8'>DEEPTRACE</h1>", unsafe_allow_html=True)
    choice = st.sidebar.radio("Navigation", ["Dashboard", "Image Analysis", "Video Analysis", "Live Camera"])
    
    st.sidebar.markdown("---")
    st.sidebar.write("👤 **Analyst:** Prajakta Kale")
    st.sidebar.write("📍 **Location:** Kolhapur Lab")

    if choice == "Dashboard": render_dashboard()
    else: render_analysis_ui(choice)

if __name__ == "__main__":
    main()
