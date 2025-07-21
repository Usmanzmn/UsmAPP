import streamlit as st
import cv2
import os
import time
import shutil
import tempfile
from moviepy.editor import VideoFileClip
import numpy as np

st.set_page_config(page_title="Cartoon Video Generator", layout="centered")

# ---------- Style Filter Functions ----------
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.08 + 20, 0, 255)
            g = np.clip(g * 1.06 + 15, 0, 255)
            b = np.clip(b * 1.15 + 25, 0, 255)
            blurred = (frame.astype(np.float32) * 0.4 +
                       cv2.GaussianBlur(frame, (7, 7), 0).astype(np.float32) * 0.6)
            tint = np.array([10, -5, 15], dtype=np.float32)
            result = np.clip(blurred + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style

    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.25 + 30, 0, 255)  # boost reds
            g = np.clip(g * 1.15 + 15, 0, 255)  # enhance greens
            b = np.clip(b * 0.85, 0, 255)       # reduce blues

            result = np.stack([r, g, b], axis=2).astype(np.float32)
            grain = np.random.normal(0, 6, frame.shape).astype(np.float32)

            return np.clip(result + grain, 0, 255).astype(np.uint8)

        return warm_style

    return lambda frame: frame

# ========== FEATURE 1 ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox(
    "🎨 Choose a Style",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"],
    key="style_select"
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

        clip = VideoFileClip(input_path)
        transform_fn = get_transform_function(style)

        styled_path = os.path.join(tmpdir, "styled.mp4")

        def process_frame(get_frame, t):
            frame = get_frame(t)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            styled = transform_fn(frame)
            return cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)

        styled_clip = clip.fl(process_frame)
        styled_clip.write_videofile(styled_path, codec="libx264", audio_codec="aac")

        # Generate previews (scaled to height 360)
        preview_original_temp = os.path.join(tmpdir, "original_preview.mp4")
        preview_styled_temp = os.path.join(tmpdir, "styled_preview.mp4")
        clip.resize(height=360).write_videofile(preview_original_temp, codec="libx264", audio_codec="aac")
        VideoFileClip(styled_path).resize(height=360).write_videofile(preview_styled_temp, codec="libx264", audio_codec="aac")

        # Save files to persistent directory
        orig_final = os.path.join(output_dir, "original.mp4")
        styled_final = os.path.join(output_dir, "styled.mp4")
        preview_orig_final = os.path.join(output_dir, "original_preview.mp4")
        preview_styled_final = os.path.join(output_dir, "styled_preview.mp4")

        shutil.copy(input_path, orig_final)
        shutil.copy(styled_path, styled_final)
        shutil.copy(preview_original_temp, preview_orig_final)
        shutil.copy(preview_styled_temp, preview_styled_final)

        # Save in session
        st.session_state["styled_output_path"] = styled_final
        st.session_state["original_path"] = orig_final
        st.session_state["preview_original"] = preview_orig_final
        st.session_state["preview_styled"] = preview_styled_final
        st.session_state["process_time"] = time.time() - start_time

# Display result
if "styled_output_path" in st.session_state:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔹 Original")
        st.video(st.session_state["preview_original"])
        with open(st.session_state["original_path"], "rb") as f:
            st.download_button("⬇️ Download Original", f.read(), file_name="original.mp4")

    with col2:
        st.subheader("🔸 Styled")
        st.video(st.session_state["preview_styled"])
        with open(st.session_state["styled_output_path"], "rb") as f:
            st.download_button("⬇️ Download Styled", f.read(), file_name="styled.mp4")

    st.success(f"✅ Done in {st.session_state['process_time']:.2f} sec")
