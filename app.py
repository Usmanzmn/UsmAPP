import streamlit as st
import numpy as np
import tempfile
import os
import shutil
import cv2
from moviepy.editor import VideoFileClip, clips_array, concatenate_videoclips

st.set_page_config(page_title="Video Style Filter", layout="centered")

# --- Transform functions ---
def get_transform_function(style_name):
    if style_name == "🔥 Cinematic Warm Filter":
        def warm_filter(frame):
            frame = frame.astype(np.float32)
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.1 + 10, 0, 255)
            frame[:, :, 1] = np.clip(frame[:, :, 1] * 1.05 + 5, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.95 - 5, 0, 255)
            return frame.astype(np.uint8)
        return warm_filter

    elif style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.1 + 30, 0, 255)
            g = np.clip(g * 1.08 + 20, 0, 255)
            b = np.clip(b * 1.2 + 35, 0, 255)
            blurred = (frame.astype(np.float32) * 0.3 +
                       cv2.GaussianBlur(frame, (7, 7), 0).astype(np.float32) * 0.7)
            tint = np.array([15, -5, 25], dtype=np.float32)
            result = np.clip(blurred + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style

    return lambda frame: frame

# --- App UI ---
st.title("🎨 Video Style Filter")
st.markdown("Apply custom filters to your video. Upload a video, select a style, and download the result.")

video_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov", "avi"])

style_name = st.selectbox("🎭 Choose a style", ["🔥 Cinematic Warm Filter", "🌸 Soft Pastel Anime-Like Style"])

if video_file is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(video_file.read())

        clip = VideoFileClip(input_path)
        fps = clip.fps
        width, height = clip.size
        # Ensure dimensions are even
        if width % 2 != 0 or height % 2 != 0:
            new_width = width - (width % 2)
            new_height = height - (height % 2)
            clip = clip.resize(newsize=(new_width, new_height))

        st.video(input_path, format="video/mp4")

        if st.button("✨ Apply Style"):
            with st.spinner("Processing video..."):
                transform = get_transform_function(style_name)
                styled = clip.fl_image(transform)

                styled_temp = os.path.join(tmpdir, "styled.mp4")

                # Detect GPU availability
                use_gpu = shutil.which("nvidia-smi") is not None
                codec = "h264_nvenc" if use_gpu else "libx264"
                preset = "p1" if use_gpu else "ultrafast"
                params = ["-rc", "vbr", "-cq", "23"] if use_gpu else ["-crf", "23"]

                styled.write_videofile(
                    styled_temp,
                    codec=codec,
                    audio=False,
                    preset=preset,
                    ffmpeg_params=params,
                    threads=0,
                    fps=fps
                )

                # Combine side-by-side preview
                preview = clips_array([[clip.resize(height=200), VideoFileClip(styled_temp).resize(height=200)]])
                preview_path = os.path.join(tmpdir, "preview.mp4")
                preview.write_videofile(
                    preview_path,
                    codec="libx264",
                    audio=False,
                    preset="ultrafast",
                    fps=fps
                )

                st.success("✅ Done!")
                st.video(preview_path, format="video/mp4")

                # Final downloads
                st.download_button("⬇️ Download Styled Video", open(styled_temp, "rb"), file_name="styled.mp4")
                st.download_button("⬇️ Download Original Video", open(input_path, "rb"), file_name="original.mp4")
