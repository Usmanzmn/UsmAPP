import streamlit as st
import cv2
import os
import time
import shutil
import tempfile
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter

st.set_page_config(page_title="Cartoon Video Generator", layout="centered")

# ---------- Style Filter Functions ----------
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.2 + 30, 0, 255)
            g = np.clip(g * 1.15 + 20, 0, 255)
            b = np.clip(b * 1.25 + 35, 0, 255)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0).astype(np.float32)
            blended = (frame.astype(np.float32) * 0.3 + blurred * 0.7)
            tint = np.array([15, -10, 20], dtype=np.float32)
            result = np.clip(blended + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style

    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.25 + 30, 0, 255)
            g = np.clip(g * 1.15 + 15, 0, 255)
            b = np.clip(b * 0.85, 0, 255)
            result = np.stack([r, g, b], axis=2).astype(np.float32)
            grain = np.random.normal(0, 6, frame.shape).astype(np.float32)
            return np.clip(result + grain, 0, 255).astype(np.uint8)
        return warm_style

    return lambda frame: frame

# ========== UI ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"])
style = st.selectbox(
    "🎨 Choose a Style",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"]
)
generate = st.button("🌸 Generate Styled Video")
output_dir = "processed_videos"
os.makedirs(output_dir, exist_ok=True)

if uploaded_file and generate:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Reload clip after writing to ensure it’s fresh
        clip = VideoFileClip(input_path, audio=False)
        fps = clip.fps
        w, h = clip.size
        transform_fn = get_transform_function(style)

        styled_path = os.path.join(tmpdir, "styled.mp4")
        writer = FFMPEG_VideoWriter(styled_path, (w, h), fps, codec="libx264")

        for frame in clip.iter_frames(fps=fps, dtype="uint8", progress_bar=True):
            bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            styled = transform_fn(bgr)
            rgb = cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)
            writer.write_frame(rgb)
        writer.close()
        clip.reader.close()
        clip.close()

        # Create 360p previews
        preview_original = os.path.join(tmpdir, "preview_original.mp4")
        preview_styled = os.path.join(tmpdir, "preview_styled.mp4")
        VideoFileClip(input_path, audio=False).resize(height=360).write_videofile(preview_original, codec="libx264", audio=False, verbose=False, logger=None)
        VideoFileClip(styled_path, audio=False).resize(height=360).write_videofile(preview_styled, codec="libx264", audio=False, verbose=False, logger=None)

        # Move final outputs
        final_original = os.path.join(output_dir, "original.mp4")
        final_styled = os.path.join(output_dir, "styled.mp4")
        shutil.copy(input_path, final_original)
        shutil.copy(styled_path, final_styled)

        # Store session paths
        st.session_state["original_path"] = final_original
        st.session_state["styled_path"] = final_styled
        st.session_state["preview_original"] = preview_original
        st.session_state["preview_styled"] = preview_styled
        st.session_state["process_time"] = time.time() - start_time

# ========== Result Display ==========
if all(k in st.session_state for k in ["original_path", "styled_path", "preview_original", "preview_styled"]):
    st.subheader("🎬 Side-by-Side Preview (360p)")
    col1, col2 = st.columns(2)

    with col1:
        st.caption("🔹 Original")
        st.video(st.session_state["preview_original"])
        with open(st.session_state["original_path"], "rb") as f:
            st.download_button("⬇️ Download Original", f.read(), file_name="original.mp4")

    with col2:
        st.caption("🔸 Styled")
        st.video(st.session_state["preview_styled"])
        with open(st.session_state["styled_path"], "rb") as f:
            st.download_button("⬇️ Download Styled", f.read(), file_name="styled.mp4")

    st.success(f"✅ Done in {st.session_state['process_time']:.2f} sec")
