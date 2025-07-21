import streamlit as st
import cv2
import os
import tempfile
from moviepy.editor import VideoFileClip
import numpy as np

st.set_page_config(page_title="Cartoon Video App", layout="centered")
st.title("🎨 Cartoonize Your Video")

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

    output_clip = VideoFileClip(input_path).set_duration(clip.duration)
    output_clip = output_clip.set_fps(fps)
    output_clip = output_clip.set_audio(clip.audio)

    # Save as temp video using OpenCV
    output_temp = os.path.join(temp_dir, "cartoon_output.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_temp, fourcc, fps, (width, height))

    for f in frames:
        out.write(f)
    out.release()

    # Combine audio back using MoviePy
    final = VideoFileClip(output_temp).set_audio(clip.audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path

uploaded_file = st.file_uploader("📤 Upload a video", type=["mp4", "mov", "avi"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    output_path = os.path.join("processed_videos", "cartoonized_output.mp4")
    os.makedirs("processed_videos", exist_ok=True)

    with st.spinner("🌀 Processing video..."):
        final_path = process_cartoon_video(input_path, output_path)

    st.success("✅ Cartoon video is ready!")
    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("⬇️ Download Cartoon Video", f, file_name="cartoonized_output.mp4")
