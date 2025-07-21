import streamlit as st
import cv2
import os
import tempfile
from moviepy.editor import VideoFileClip
import numpy as np

st.set_page_config(page_title="Cartoon Video Generator", layout="centered")

st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
        color: #4A90E2;
    }
    .upload-box {
        background-color: #f0f2f6;
        padding: 1em;
        border-radius: 10px;
        margin-top: 1em;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="centered-title">🎨 Cartoon Video Generator</div>', unsafe_allow_html=True)
st.markdown("Upload a video and turn it into a cartoon-style animation using OpenCV.", unsafe_allow_html=True)

def cartoonize_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 9, 9
    )
    color = cv2.bilateralFilter(frame, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

def process_cartoon_video(input_path, output_path):
    clip = VideoFileClip(input_path)
    fps = clip.fps
    width, height = clip.size
    temp_dir = tempfile.mkdtemp()

    frames = []
    for frame in clip.iter_frames():
        cartoon = cartoonize_frame(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        cartoon = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
        frames.append(cartoon)

    output_temp = os.path.join(temp_dir, "cartoon_output.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_temp, fourcc, fps, (width, height))

    for f in frames:
        out.write(f)
    out.release()

    final = VideoFileClip(output_temp).set_audio(clip.audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path

st.markdown('<div class="upload-box">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("📤 Upload a video file", type=["mp4", "mov", "avi"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    generate = st.button("✨ Generate Cartoon Video")
    if generate:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name

        output_path = os.path.join("processed_videos", "cartoonized_output.mp4")
        os.makedirs("processed_videos", exist_ok=True)

        with st.spinner("🎬 Processing... please wait!"):
            final_path = process_cartoon_video(input_path, output_path)

        st.success("✅ Cartoon video is ready!")
        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("⬇️ Download Cartoon Video", f, file_name="cartoonized_output.mp4")
