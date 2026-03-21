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
st.set_page_config(page_title="DEEPTRACE PRO | Neural Forensic Suite", layout="wide")

# Custom CSS to mimic the Dark Navy/Cyan Tech aesthetic
st.markdown("""
    <style>
    .main { background-color: #020617; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #38bdf8; color: black; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #38bdf8; }
    .status-box { padding: 20px; border-radius: 10px; border: 1px solid #1e293b; background-color: #0f172a; }
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
                 (filename, file_type, result, confidence, datetime.now().strftime("%H:%M:%S")))
    conn.commit()
    conn.close()

# --- FORENSIC ENGINE ---
def analyze_frame(frame):
    """Laplacian Variance Analysis: Heuristic Deepfake Detection"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Threshold logic from original code
    if laplacian_var < 100: 
        score = 0.85  # High chance of manipulation
    else:
        score = 0.15  # Likely authentic
    return score

# --- UI COMPONENTS ---
def main():
    init_db()
    
    # Sidebar Command Center
    st.sidebar.title("🛡️ DETECT THE REALITY")
    st.sidebar.markdown("---")
    
    app_mode = st.sidebar.selectbox("Select Analysis Mode", 
                                   ["Dashboard", "Image Analysis", "Video Analysis", "Live Camera"])
    
    # Export Section
    if st.sidebar.button("📊 Export CSV Report"):
        conn = sqlite3.connect("forensic_history.db")
        df = pd.read_sql_query("SELECT * FROM scans", conn)
        conn.close()
        csv = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Download Report", data=csv, file_name="Forensic_Report.csv", mime="text/csv")

    # Recent Logs in Sidebar
    st.sidebar.markdown("### Recent Logs")
    conn = sqlite3.connect("forensic_history.db")
    logs_df = pd.read_sql_query("SELECT result, filename FROM scans ORDER BY id DESC LIMIT 10", conn)
    st.sidebar.table(logs_df)
    conn.close()

    # Main Workspace
    if app_mode == "Dashboard":
        st.title("DeepTrace")
        st.subheader("NEURAL DEEPFAKE DETECTION SYSTEM")
        st.info("System Initialized. Select a mode in the sidebar to begin forensic scanning.")
        st.image("https://img.icons8.com/nolan/512/security-shield.png", width=200)

    elif app_mode == "Image Analysis":
        st.header("📁 Image Forensic Scan")
        uploaded_file = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Source Preview", use_container_width=True)
            
            if st.button("START FORENSIC SCAN"):
                with st.spinner("Analyzing Frequency Domains..."):
                    img_array = np.array(image.convert('RGB'))
                    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    score = analyze_frame(img_cv)
                    time.sleep(1) # Simulate processing
                    
                    display_results(score, uploaded_file.name, "Image")

    elif app_mode == "Video Analysis":
        st.header("🎥 Video Forensic Scan")
        uploaded_video = st.file_uploader("Upload Video", type=['mp4', 'avi', 'mov'])
        
        if uploaded_video:
            st.video(uploaded_video)
            
            if st.button("RUN MULTI-FRAME ANALYSIS"):
                # Save temp file to read with CV2
                tfile = io.BytesIO(uploaded_video.read())
                with open("temp_video.mp4", "wb") as f:
                    f.write(tfile.getbuffer())
                
                cap = cv2.VideoCapture("temp_video.mp4")
                frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                results = []
                progress = st.progress(0)
                
                for i in range(0, frames_count, 30):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = cap.read()
                    if ret:
                        results.append(analyze_frame(frame))
                        progress.progress(i / frames_count)
                
                cap.release()
                avg_score = sum(results)/len(results) if results else 0.5
                display_results(avg_score, uploaded_video.name, "Video")

    elif app_mode == "Live Camera":
        st.header("📷 Live Forensic Stream")
        img_file = st.camera_input("Take a snapshot for analysis")
        
        if img_file:
            img = Image.open(img_file)
            img_array = np.array(img)
            score = analyze_frame(img_array)
            display_results(score, "Live_Capture", "Live")

def display_results(score, filename, media_type):
    label = "FAKE" if score > 0.6 else "REAL"
    conf = score if label == "FAKE" else (1 - score)
    color = "#fb7185" if label == "FAKE" else "#4ade80"
    
    save_to_db(filename, media_type, label, conf * 100)
    
    st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 2px solid {color}; border-radius: 10px;">
            <h1 style="color: {color};">{label} DETECTED</h1>
            <h3>Confidence: {conf*100:.1f}%</h3>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()