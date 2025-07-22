import streamlit as st
import os
import tempfile
import subprocess
import time
from moviepy.editor import VideoFileClip, clips_array
from PIL import Image
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
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.08 + 30, 0, 255)
            g = np.clip(g * 1.06 + 20, 0, 255)
            b = np.clip(b * 1.15 + 30, 0, 255)
            blurred = (frame.astype(np.float32) * 0.4 +
                       cv2.GaussianBlur(frame, (7, 7), 0).astype(np.float32) * 0.6)
            tint = np.array([10, -5, 15], dtype=np.float32)
            return np.clip(blurred + tint, 0, 255).astype(np.uint8)
        return pastel_style

    elif style_name == "🎮 Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.15 + 35, 0, 255)
            g = np.clip(g * 1.08 + 20, 0, 255)
            b = np.clip(b * 0.95, 10, 255)
            rows, cols = r.shape
            Y, X = np.ogrid[:rows, :cols]
            center = (rows / 2, cols / 2)
            vignette = 1 - ((X - center[1])**2 + (Y - center[0])**2) / (1.5 * center[0] * center[1])
            vignette = np.clip(vignette, 0.3, 1)[..., np.newaxis]
            result = np.stack([r, g, b], axis=2).astype(np.float32) * vignette
            grain = np.random.normal(0, 3, frame.shape).astype(np.float32)
            return np.clip(result + grain, 0, 255).astype(np.uint8)
        return warm_style

    return lambda frame: frame

def add_rain_effect(frame, density=0.002):
    frame = frame.copy()
    h, w, _ = frame.shape
    num_drops = int(h * w * density)
    for _ in range(num_drops):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 20)
        length = random.randint(10, 20)
        thickness = 1
        color = (200, 200, 255)
        cv2.line(frame, (x, y), (x, y + length), color, thickness)
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

# === UI ===
st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"])
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

        # Full and small clips
        full_clip = VideoFileClip(input_path)
        preview_clip = full_clip.resize(height=360)

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
                frame = add_rain_effect(frame, density=rain_density)
            return frame

        # Styled clip
        styled_clip = full_clip.fl_image(full_effect)
        styled_temp = os.path.join(tmpdir, "styled.mp4")
        styled_clip.write_videofile(styled_temp, codec="libx264", audio=False, preset="ultrafast", threads=4)

        # Apply watermark if checked
        final_path = styled_temp
        if add_watermark:
            watermarked_output = os.path.join(tmpdir, "styled_watermarked.mp4")
            apply_watermark(styled_temp, watermarked_output)
            final_path = watermarked_output

        # Save high-res versions for download
        final_original = os.path.join(output_dir, "original.mp4")
        final_styled = os.path.join(output_dir, "styled.mp4")
        full_clip.write_videofile(final_original, codec="libx264", audio=False, preset="ultrafast")
        shutil.copy(final_path, final_styled)

        # Generate side-by-side preview (360p)
        preview_styled = styled_clip.resize(height=360)
        combined_preview = clips_array([[preview_clip, preview_styled]]).set_duration(min(preview_clip.duration, preview_styled.duration))
        preview_output = os.path.join(output_dir, "side_by_side_preview.mp4")
        combined_preview.write_videofile(preview_output, codec="libx264", audio=False, preset="ultrafast")

        # Show preview
        st.video(preview_output)

        # Downloads
        st.download_button("⬇️ Download Original", open(final_original, "rb").read(), file_name="original.mp4")
        st.download_button("⬇️ Download Styled", open(final_styled, "rb").read(), file_name="styled.mp4")
        st.success(f"✅ Done in {time.time() - start_time:.2f} sec")
