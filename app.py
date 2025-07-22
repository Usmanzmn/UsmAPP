import streamlit as st
import cv2
import os
import time
import shutil
import tempfile
import numpy as np

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

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎮 Cinematic Warm Filter"], key="style_select")
generate = st.button("🌸 Generate Styled Video")
output_dir = "processed_videos"
os.makedirs(output_dir, exist_ok=True)

if uploaded_file and generate:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "styled.mp4")

        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        transform_fn = get_transform_function(style)

        # Use OpenCV to process frames
        cap = cv2.VideoCapture(input_path)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        progress = st.progress(0, text="Processing...")

        i = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            styled_frame = transform_fn(frame)
            out.write(styled_frame)
            i += 1
            progress.progress(i / frame_count, text=f"Processing frame {i}/{frame_count}...")

        cap.release()
        out.release()

        preview_path = os.path.join(tmpdir, "preview.mp4")
        os.system(f"ffmpeg -i {output_path} -vf scale=-1:360 {preview_path} -y")

        styled_final = os.path.join(output_dir, "styled.mp4")
        preview_final = os.path.join(output_dir, "styled_preview.mp4")
        shutil.copy(output_path, styled_final)
        shutil.copy(preview_path, preview_final)

        st.session_state["styled_output_path"] = styled_final
        st.session_state["preview_styled"] = preview_final
        st.session_state["process_time"] = time.time() - start_time

# ========== Display Result ==========
if "styled_output_path" in st.session_state:
    st.subheader("🔸 Styled Preview")
    st.video(st.session_state["preview_styled"])
    with open(st.session_state["styled_output_path"], "rb") as f:
        st.download_button("⬇️ Download Styled Video", f.read(), file_name="styled.mp4")

    st.success(f"✅ Done in {st.session_state['process_time']:.2f} sec")
