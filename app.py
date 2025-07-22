import streamlit as st
import os
import tempfile
import shutil
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
from moviepy.video.fx.resize import resize

st.set_page_config(page_title="Video Style Filter", layout="centered")
st.title("🎨 Video Style Filter")

# Initialize session state
if "original_path" not in st.session_state:
    st.session_state.original_path = ""
if "styled_path" not in st.session_state:
    st.session_state.styled_path = ""

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
            result = np.stack([r, g, b], axis=2).astype(np.uint8)
            return result
        return warm_style

    return lambda frame: frame

style = st.selectbox("✨ Choose a Filter Style", ["🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"])

uploaded_file = st.file_uploader("📤 Upload a video", type=["mp4", "mov", "avi"])

if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    st.session_state.original_path = tfile.name
    st.video(st.session_state.original_path, format="video/mp4")

    if st.button("🎬 Apply Filter"):
        with st.spinner("✨ Applying style, please wait..."):
            transform_fn = get_transform_function(style)

            with tempfile.TemporaryDirectory() as tmpdir:
                styled_path = os.path.join(tmpdir, "styled.mp4")
                clip = VideoFileClip(st.session_state.original_path)
                fps = clip.fps
                w, h = clip.size

                writer = FFMPEG_VideoWriter(styled_path, (w, h), fps, codec="libx264")

                total_frames = int(clip.fps * clip.duration)
                for i, frame in enumerate(clip.iter_frames(dtype="uint8")):
                    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    styled = transform_fn(bgr)
                    rgb = cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)
                    writer.write_frame(rgb)
                    st.progress((i + 1) / total_frames)

                writer.close()

                st.session_state.styled_path = styled_path
                preview_original = os.path.join(tmpdir, "preview_original.mp4")
                preview_styled = os.path.join(tmpdir, "preview_styled.mp4")

                resize(clip, height=360).write_videofile(preview_original, codec="libx264", audio=False, verbose=False, logger=None)
                resize(VideoFileClip(styled_path), height=360).write_videofile(preview_styled, codec="libx264", audio=False, verbose=False, logger=None)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original Preview**")
                    st.video(preview_original)
                with col2:
                    st.markdown("**Styled Preview**")
                    st.video(preview_styled)

        st.success("✅ Filter applied successfully!")
        with open(st.session_state.styled_path, "rb") as f:
            st.download_button("⬇️ Download Styled Video", f, file_name="styled_video.mp4")
