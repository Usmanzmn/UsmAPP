import streamlit as st
from moviepy.editor import VideoFileClip, vfx
import tempfile
import os
import shutil
import time

st.set_page_config(page_title="🎬 Video Stylizer", layout="centered")
st.title("🎨 Video Cartoonizer with Cinematic Filter")

def apply_cartoon_and_filter(input_path, output_path):
    clip = VideoFileClip(input_path)

    # 🟠 Cartoon effect (simple edge-preserving technique)
    cartoon_clip = clip.fx(vfx.colorx, 1.1).fx(vfx.lum_contrast, 0, 30, 255)

    # 🟠 Cinematic warm color grading
    warm_clip = cartoon_clip.fx(vfx.colorx, 1.2)

    warm_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="medium", verbose=False, logger=None)

    clip.close()
    cartoon_clip.close()
    warm_clip.close()

def save_uploaded_file(uploadedfile):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(uploadedfile.read())
        return tmp_file.name

# Upload
uploaded_file = st.file_uploader("📤 Upload an MP4 video (Max ~100MB)", type=["mp4"])
if uploaded_file is not None:
    input_path = save_uploaded_file(uploaded_file)

    with st.spinner("✨ Applying cartoon effect and cinematic filter..."):
        try:
            start_time = time.time()
            tmpdir = tempfile.mkdtemp()
            styled_path = os.path.join(tmpdir, "styled.mp4")
            apply_cartoon_and_filter(input_path, styled_path)

            # ✅ Ensure styled video is valid before previews
            if not os.path.exists(styled_path) or os.path.getsize(styled_path) < 1000:
                st.error("❌ Styled video generation failed. File is empty or corrupted.")
                raise ValueError("Styled video is corrupted or empty.")

            # 🎬 Attempt preview creation (360p)
            preview_original_path = os.path.join(tmpdir, "preview_original.mp4")
            preview_styled_path = os.path.join(tmpdir, "preview_styled.mp4")

            try:
                clip_original = VideoFileClip(input_path)
                clip_original.resize(height=360).write_videofile(
                    preview_original_path, codec="libx264", audio=False, verbose=False, logger=None
                )
                clip_original.close()
            except Exception as e:
                st.warning(f"⚠️ Failed to create original preview: {e}")
                preview_original_path = None

            try:
                clip_styled = VideoFileClip(styled_path)
                clip_styled.resize(height=360).write_videofile(
                    preview_styled_path, codec="libx264", audio=False, verbose=False, logger=None
                )
                clip_styled.close()
            except Exception as e:
                st.warning(f"⚠️ Failed to create styled preview: {e}")
                preview_styled_path = None

            st.success(f"✅ Done in {round(time.time() - start_time, 2)} seconds!")
            st.markdown("### 🔍 Side-by-Side Preview (360p)")
            col1, col2 = st.columns(2)
            with col1:
                if preview_original_path and os.path.exists(preview_original_path):
                    st.video(preview_original_path)
                    st.caption("📹 Original")
            with col2:
                if preview_styled_path and os.path.exists(preview_styled_path):
                    st.video(preview_styled_path)
                    st.caption("🎨 Styled")

            # 🟢 Play styled video again for download + persistent view
            st.markdown("---")
            st.markdown("### 📥 Download Styled Video")
            st.video(styled_path)
            with open(styled_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Styled MP4",
                    data=f,
                    file_name="styled_output.mp4",
                    mime="video/mp4"
                )

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")

        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
