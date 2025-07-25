import streamlit as st
import os
import tempfile
import subprocess
import time
from moviepy.editor import VideoFileClip
import numpy as np
import cv2
import shutil
import random

st.set_page_config(page_title="🎨 AI Video Effects App", layout="centered")
st.title("🎨 AI Video Effects App")

@st.cache_resource
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            frame = frame.astype(np.float32)
            r = np.clip(frame[:, :, 0] * 1.12 + 24, 0, 255)
            g = np.clip(frame[:, :, 1] * 1.09 + 18, 0, 255)
            b = np.clip(frame[:, :, 2] * 1.2 + 30, 0, 255)
            frame[:, :, 0], frame[:, :, 1], frame[:, :, 2] = r, g, b
            blurred = cv2.GaussianBlur(frame, (7, 7), 1)
            blended = frame * 0.35 + blurred * 0.65
            tint = np.array([15, -5, 18], dtype=np.float32)
            result = np.clip(blended + tint, 0, 255)
            return result.astype(np.uint8)
        return pastel_style

    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            frame = frame.astype(np.float32)
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.2 + 20, 0, 255)
            frame[:, :, 1] = np.clip(frame[:, :, 1] * 1.1 + 10, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.95, 0, 255)
            frame = np.clip(frame * 1.05 + 5, 0, 255)
            noise = np.random.normal(0, 2, frame.shape).astype(np.float32)
            return np.clip(frame + noise, 0, 255).astype(np.uint8)
        return warm_style

    else:
        return lambda frame: frame

def add_rain_effect(frame, density=0.002):
    frame = frame.copy()
    h, w, _ = frame.shape
    num_drops = int(h * w * density)
    for _ in range(num_drops):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 20)
        length = random.randint(10, 20)
        color = (200, 200, 255)
        cv2.line(frame, (x, y), (x, y + length), color, 1)
    return frame

def apply_watermark(input_path, output_path, text="@USMIKASHMIRI"):
    watermark_filter = (
        "scale=ceil(iw/2)*2:ceil(ih/2)*2," +
        f"drawtext=fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':" +
        f"text='{text}':x=w-mod(t*240\\,w+tw):y=h-160:" +
        "fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
    )
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", watermark_filter,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-threads", "4", "-pix_fmt", "yuv420p", output_path
    ]
    subprocess.run(cmd, check=True)

st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")

# Reset session state if new file is uploaded
if uploaded_file:
    st.session_state.pop("original_video_bytes", None)
    st.session_state.pop("styled_video_bytes", None)

style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"])
add_watermark = st.checkbox("✅ Add Watermark (@USMIKASHMIRI)", value=False)
rain_option = st.selectbox("🌧️ Add Rain Overlay", ["None", "🌧️ Light Rain (Default)", "🌦️ Extra Light Rain", "🌤️ Ultra Light Rain"])
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
        original_w, original_h = clip.size
        max_height = 720

        # Resize if needed
        if original_h > max_height:
            resize_ratio = max_height / original_h
            clip = clip.resize((int(original_w * resize_ratio), max_height))
            resized = True
        else:
            resized = False

        transform_fn = get_transform_function(style)
        rain_density = {
            "🌧️ Light Rain (Default)": 0.002,
            "🌦️ Extra Light Rain": 0.0008,
            "🌤️ Ultra Light Rain": 0.0004,
            "None": None
        }[rain_option]

        def full_effect(frame):
            frame = transform_fn(frame)
            if rain_density:
                frame = add_rain_effect(frame, rain_density)
            return frame

        styled_clip = clip.fl_image(full_effect)

        if resized:
            styled_clip = styled_clip.resize((original_w, original_h))

        styled_temp = os.path.join(tmpdir, "styled.mp4")
        styled_clip.write_videofile(styled_temp, codec="libx264", audio=False, preset="ultrafast", threads=4)

        final_path = styled_temp
        if add_watermark:
            watermarked_output = os.path.join(tmpdir, "styled_watermarked.mp4")
            apply_watermark(styled_temp, watermarked_output)
            final_path = watermarked_output

        original_save = os.path.join(output_dir, "original.mp4")
        styled_save = os.path.join(output_dir, "styled.mp4")
        shutil.copy(input_path, original_save)
        shutil.copy(final_path, styled_save)

        # Save preview videos
        preview_orig = os.path.join(tmpdir, "preview_orig.mp4")
        preview_styled = os.path.join(tmpdir, "preview_styled.mp4")
        clip.resize(height=200).write_videofile(preview_orig, codec="libx264", audio=False, preset="ultrafast")
        VideoFileClip(final_path).resize(height=200).write_videofile(preview_styled, codec="libx264", audio=False, preset="ultrafast")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔍 Original Preview")
            st.video(preview_orig)
        with col2:
            st.subheader("🎨 Styled Preview")
            st.video(preview_styled)

        # Store in session_state for persistent download
        if "original_video_bytes" not in st.session_state:
            with open(original_save, "rb") as f:
                st.session_state.original_video_bytes = f.read()

        if "styled_video_bytes" not in st.session_state:
            with open(styled_save, "rb") as f:
                st.session_state.styled_video_bytes = f.read()

        st.download_button("⬇️ Download Original", st.session_state.original_video_bytes, file_name="original.mp4")
        st.download_button("⬇️ Download Styled", st.session_state.styled_video_bytes, file_name="styled.mp4")

        st.success(f"✅ Done in {time.time() - start_time:.2f} seconds")
