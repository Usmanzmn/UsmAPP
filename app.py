import streamlit as st
import os
import tempfile
import cv2
import time
import shutil
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter

# Title and description
st.set_page_config(page_title="Video Style Transfer", layout="centered")
st.title("🎨 Soft Pastel Anime-Like Video Stylizer")
st.markdown("Upload a video and apply a soft pastel anime-like filter to it.")

# Style transfer function
def apply_soft_pastel_style(frame):
    # Example soft pastel filter (you can modify this)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[...,1] = hsv[...,1] * 0.5  # reduce saturation
    hsv[...,2] = cv2.equalizeHist(hsv[...,2])
    pastel = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    pastel = cv2.bilateralFilter(pastel, 9, 75, 75)
    return pastel

# Upload section
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        st.video(input_path)
        st.markdown("⬆️ Uploaded Video")

        if st.button("✨ Apply Soft Pastel Anime-Like Filter"):
            start_time = time.time()
            clip = VideoFileClip(input_path)
            fps = clip.fps
            w, h = clip.size

            styled_path = os.path.join(tmpdir, "styled.mp4")
            writer = FFMPEG_VideoWriter(styled_path, (w, h), fps, codec="libx264", audio=False)

            frame_count = int(clip.fps * clip.duration)
            progress_bar = st.progress(0)
            frame_num = 0

            for frame in clip.iter_frames(dtype="uint8"):
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                styled = apply_soft_pastel_style(bgr)
                rgb = cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)
                writer.write_frame(rgb)

                frame_num += 1
                progress_bar.progress(min(frame_num / frame_count, 1.0))

            writer.close()
            time.sleep(2)

            if not os.path.exists(styled_path) or os.path.getsize(styled_path) < 1000:
                st.error("❌ Styled video was not created properly.")
            else:
                preview_original = os.path.join(tmpdir, "preview_original.mp4")
                preview_styled = os.path.join(tmpdir, "preview_styled.mp4")

                shutil.copy(input_path, preview_original)
                shutil.copy(styled_path, preview_styled)

                st.success(f"✅ Done in {round(time.time() - start_time, 2)} seconds")
                st.markdown("### 🔍 Preview (Original vs. Styled)")

                col1, col2 = st.columns(2)
                with col1:
                    st.video(preview_original)
                    st.caption("📹 Original")
                with col2:
                    st.video(preview_styled)
                    st.caption("🎨 Styled")

                st.markdown("### ⬇️ Download")
                with open(styled_path, "rb") as f:
                    st.download_button("Download Styled Video", f, file_name="styled_output.mp4", mime="video/mp4")
