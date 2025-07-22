import streamlit as st
import os
import tempfile
import time
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter


# Transform Functions
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.15 + 30, 0, 255)
            g = np.clip(g * 1.10 + 20, 0, 255)
            b = np.clip(b * 1.25 + 35, 0, 255)
            blurred = (frame.astype(np.float32) * 0.35 +
                       cv2.GaussianBlur(frame, (7, 7), 0).astype(np.float32) * 0.65)
            tint = np.array([15, -10, 25], dtype=np.float32)
            result = np.clip(blurred + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style

    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.30 + 25, 0, 255)
            g = np.clip(g * 1.20 + 20, 0, 255)
            b = np.clip(b * 0.85, 0, 255)
            return np.stack([r, g, b], axis=2).astype(np.uint8)
        return warm_style

    return lambda frame: frame


# Preview Video Generator (Safe Resize)
def create_preview_video(input_path, output_path, height=360):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video file: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if h == 0 or w == 0 or fps == 0:
        raise ValueError("Invalid video file: height, width, or fps is zero.")

    scale = height / h
    new_w = int(w * scale)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (new_w, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        resized = cv2.resize(frame, (new_w, height))
        out.write(resized)

    cap.release()
    out.release()


# Streamlit UI
st.set_page_config(page_title="🎨 AI Video Styler", layout="centered")
st.title("🎨 AI Video Styler")
st.markdown("Upload a video and choose a style to apply. Preview the result side-by-side!")

uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov", "avi"])
style_option = st.selectbox("🎨 Choose a Style", [
    "🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"
])

if uploaded_file and style_option:
    generate = st.button("🚀 Generate Styled Video")

    if generate:
        start_time = time.time()

        with st.spinner("⏳ Processing... Please wait."):
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, "input_video.mp4")
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.read())

                cap = cv2.VideoCapture(input_path)
                if not cap.isOpened():
                    st.error("Failed to read uploaded video.")
                    st.stop()

                fps = cap.get(cv2.CAP_PROP_FPS)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                if fps == 0 or w == 0 or h == 0:
                    st.error("Uploaded video has invalid properties.")
                    st.stop()

                styled_path = os.path.join(tmpdir, "styled.mp4")
                writer = FFMPEG_VideoWriter(styled_path, (w, h), fps, codec="libx264")

                transform_fn = get_transform_function(style_option)
                progress_bar = st.progress(0, text="Starting frame-by-frame processing...")

                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    styled = transform_fn(frame)
                    writer.write_frame(cv2.cvtColor(styled, cv2.COLOR_BGR2RGB))
                    frame_count += 1
                    progress_bar.progress(min(frame_count / total_frames, 1.0),
                                          text=f"{frame_count}/{total_frames} frames done")

                cap.release()
                writer.close()

                preview_original_path = os.path.join(tmpdir, "preview_original.mp4")
                preview_styled_path = os.path.join(tmpdir, "preview_styled.mp4")

                try:
                    create_preview_video(input_path, preview_original_path)
                    create_preview_video(styled_path, preview_styled_path)
                except ValueError as e:
                    st.error(f"⚠️ Preview creation failed: {e}")
                    st.stop()

                st.success(f"✅ Done in {round(time.time() - start_time, 2)} seconds!")
                st.markdown("### 🔍 Side-by-Side Preview (360p)")

                col1, col2 = st.columns(2)
                with col1:
                    st.video(preview_original_path)
                    st.caption("📹 Original")
                with col2:
                    st.video(preview_styled_path)
                    st.caption("🎨 Styled")

                st.markdown("### ⬇️ Download Full Styled Video")
                with open(styled_path, "rb") as f:
                    st.download_button("Download Styled Video", f,
                                       file_name="styled_output.mp4", mime="video/mp4")
