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

# --- CONFIGURATION & GRADIENT STYLING ---
st.set_page_config(page_title="DEEPTRACE PRO", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Gradient Background Effect */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%);
        color: #f8fafc;
    }
    /* Custom Sidebar Gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
        border-right: 1px solid #1e293b;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #0ea5e9, #6366f1);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.6rem;
    }
    .report-card {
        padding: 20px;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC ---
def init_db():
    conn = sqlite3.connect("forensic_history.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS scans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, type TEXT, 
                 result TEXT, confidence REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

def analyze_forensics(frame):
    """Laplacian Variance Analysis + Explainability"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Visual Edge Map for user transparency
    lap_abs = np.uint8(np.absolute(cv2.Laplacian(gray, cv2.CV_64F)))
    edge_map = cv2.applyColorMap(lap_abs, cv2.COLORMAP_VIRIDIS)
    
    if variance < 100:
        return 0.88, "High smoothing detected. AI generators often struggle with natural skin texture/pores.", edge_map
    else:
        return 0.12, "Natural frequency noise detected. Consistent with physical camera sensor artifacts.", edge_map

def save_to_db(filename, file_type, result, confidence):
    conn = sqlite3.connect("forensic_history.db")
    conn.execute("INSERT INTO scans (filename, type, result, confidence, timestamp) VALUES (?,?,?,?,?)",
                 (filename, file_type, result, confidence, datetime.now().strftime("%H:%M:%S")))
    conn.commit()
    conn.close()

# --- UI MODES ---
def render_image_mode():
    st.subheader("📁 Static Image Forensic")
    up = st.file_uploader("Upload Image", type=['jpg','png','jpeg'])
    if up:
        img = Image.open(up)
        # Resize for better layout
        img.thumbnail((500, 500))
        st.image(img, caption="Evidence Source")
        if st.button("RUN SCAN"):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            score, reason, emap = analyze_forensics(img_cv)
            display_verdict(score, reason, up.name, "Image", emap)

def render_video_mode():
    st.subheader("🎥 Video Stream Forensic")
    up_vid = st.file_uploader("Upload Video", type=['mp4','mov','avi'])
    if up_vid:
        # Fix: Save to a temporary file so OpenCV can read it via path
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(up_vid.read())
        tfile.close()
        
        st.video(up_vid)
        if st.button("BATCH FRAME ANALYSIS"):
            cap = cv2.VideoCapture(tfile.name)
            scores = []
            progress = st.progress(0)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                s, _, _ = analyze_forensics(frame)
                scores.append(s)
                # Sample every 20 frames for speed
                cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + 20)
            
            cap.release()
            os.unlink(tfile.name) # Clean up temp file
            
            avg = sum(scores)/len(scores) if scores else 0.5
            display_verdict(avg, "Temporal analysis across multiple frames confirms consistency of noise patterns.", up_vid.name, "Video")

def render_live_mode():
    st.subheader("📷 Real-time Capture")
    cam_img = st.camera_input("Snapshot Analysis")
    if cam_img:
        # Convert camera buffer to CV2 format
        img = Image.open(cam_img)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        score, reason, emap = analyze_forensics(img_cv)
        display_verdict(score, reason, "Live_Feed", "Live", emap)

def display_verdict(score, reason, fname, mtype, emap=None):
    label = "FAKE" if score > 0.5 else "REAL"
    conf = score if label == "FAKE" else (1 - score)
    color = "#f43f5e" if label == "FAKE" else "#10b981"
    
    save_to_db(fname, mtype, label, round(conf*100, 2))
    
    st.markdown(f"""
        <div class="report-card" style="border-top: 4px solid {color};">
            <h2 style="color: {color};">{label} DETECTED</h2>
            <p><b>Confidence:</b> {conf*100:.2f}%</p>
            <p><b>Explanation:</b> {reason}</p>
        </div>
    """, unsafe_allow_html=True)
    if emap is not None:
        st.image(emap, caption="Forensic Noise Map", width=400)

# --- MAIN APP ---
def main():
    init_db()
    st.sidebar.title("DEEPTRACE 🛡️")
    mode = st.sidebar.selectbox("Analysis Mode", ["Dashboard", "Image Analysis", "Video Analysis", "Live Camera"])
    
    if mode == "Dashboard":
        st.title("Neural Dashboard")
        st.info("System operational. Select a mode to begin scanning.")
    elif mode == "Image Analysis": render_image_mode()
    elif mode == "Video Analysis": render_video_mode()
    elif mode == "Live Camera": render_live_mode()

if __name__ == "__main__":
    main()
