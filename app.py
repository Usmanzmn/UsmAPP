import streamlit as st
import os
import tempfile
import time
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter

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
                fps = cap.get(cv2.CAP_PROP_FPS)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                if fps == 0 or total_frames == 0:
                    st.error("❌ Unable to read video properties. FPS or frame count is zero.")
                    st.stop()

                styled_path = os.path.join(tmpdir, "styled.mp4")
                writer = FFMPEG_VideoWriter(
                    styled_path, (w, h), fps, codec="libx264", preset="ultrafast", audio=False
                )

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

                if not os.path.exists(styled_path) or os.path.getsize(styled_path) == 0:
                    st.error("❌ Styled video generation failed. File is empty or corrupted.")
                    st.stop()

                # Generate 360p preview
                try:
                    preview_original_path = os.path.join(tmpdir, "preview_original.mp4")
                    preview_styled_path = os.path.join(tmpdir, "preview_styled.mp4")

                    VideoFileClip(input_path, audio=False).resize(height=360).write_videofile(
                        preview_original_path, codec="libx264", audio=False,
                        verbose=False, logger=None, preset="ultrafast"
                    )
                    VideoFileClip(styled_path, audio=False).resize(height=360).write_videofile(
                        preview_styled_path, codec="libx264", audio=False,
                        verbose=False, logger=None, preset="ultrafast"
                    )

                    st.success(f"✅ Done in {round(time.time() - start_time, 2)} seconds!")
                    st.markdown("### 🔍 Side-by-Side Preview (360p)")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.video(preview_original_path)
                        st.caption("📹 Original")
                    with col2:
                        st.video(preview_styled_path)
                        st.caption("🎨 Styled")
                except Exception as e:
                    st.warning(f"⚠️ Preview creation failed: {e}")

                # Display and download full styled video
                with open(styled_path, "rb") as f:
                    styled_video_bytes = f.read()

                st.markdown("### 🎥 Full Styled Video")
                st.video(styled_video_bytes)

                st.download_button(
                    "⬇️ Download Styled Video",
                    data=styled_video_bytes,
                    file_name="styled_output.mp4",
                    mime="video/mp4"
                )
