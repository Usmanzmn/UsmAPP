import streamlit as st
import os
import tempfile
import shutil
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter

# ---------- Style Filter Functions ----------
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
            rows, cols = r.shape
            Y, X = np.ogrid[:rows, :cols]
            center = (rows / 2, cols / 2)
            vignette = 1 - ((X - center[1])**2 + (Y - center[0])**2) / (1.5 * center[0] * center[1])
            vignette = np.clip(vignette, 0.2, 1)[..., np.newaxis]
            result = np.stack([r, g, b], axis=2).astype(np.float32) * vignette
            grain = np.random.normal(0, 5, frame.shape).astype(np.float32)
            return np.clip(result + grain, 0, 255).astype(np.uint8)
        return warm_style

    return lambda frame: frame

# ---------- Streamlit UI ----------
st.set_page_config(page_title="🎨 AI Video Styler", layout="centered")
st.title("🎨 AI Video Styler")
st.markdown("Upload a video and choose a style to apply. Enjoy side-by-side results!")

uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov", "avi"])

style_option = st.selectbox(
    "🎨 Choose a Style",
    ["🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"]
)

if uploaded_file and style_option:
    with st.spinner("⏳ Processing..."):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input_video.mp4")
            with open(input_path, "wb") as f:
                f.write(uploaded_file.read())

            clip = VideoFileClip(input_path, audio=False)
            w, h = clip.w, clip.h
            fps = clip.fps

            # Resize for preview
            preview_clip = clip.resize(height=360)
            preview_original = os.path.join(tmpdir, "preview_original.mp4")
            preview_clip.write_videofile(preview_original, codec="libx264", audio=False, verbose=False, logger=None)

            styled_path = os.path.join(tmpdir, "styled.mp4")
            transform_fn = get_transform_function(style_option)
            writer = FFMPEG_VideoWriter(styled_path, (w, h), fps, codec="libx264")

            for frame in clip.iter_frames(dtype="uint8", progress_bar=True):
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                styled = transform_fn(bgr)
                rgb = cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)
                writer.write_frame(rgb)

            writer.close()
            clip.reader.close()
            clip.close()

            # Resize styled video for preview
            styled_preview_path = os.path.join(tmpdir, "styled_preview.mp4")
            styled_clip = VideoFileClip(styled_path).resize(height=360)
            styled_clip.write_videofile(styled_preview_path, codec="libx264", audio=False, verbose=False, logger=None)
            styled_clip.close()

            st.success(f"✅ Done in {round(clip.duration, 2)} seconds\n**{style_option}** applied!")

            st.markdown("### 🔍 Comparison Preview (360p)")
            col1, col2 = st.columns(2)
            with col1:
                st.video(preview_original)
                st.caption("📹 Original Preview")
            with col2:
                st.video(styled_preview_path)
                st.caption("🎨 Styled Preview")

            st.markdown("### ⬇️ Download Full Styled Video")
            with open(styled_path, "rb") as f:
                st.download_button("Download Styled Video", f, file_name="styled_output.mp4", mime="video/mp4")
