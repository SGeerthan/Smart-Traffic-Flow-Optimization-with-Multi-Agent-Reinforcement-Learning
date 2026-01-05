import streamlit as st
import cv2
import tempfile
import numpy as np
from ultralytics import YOLO
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Pedestrian Classification",
    layout="wide"
)

st.title("🚶 Pedestrian Classification System")
st.markdown(
    "Classes: **Adult | Elder | Student | Mobility Aid**"
)

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    return YOLO("best.pt")  # make sure best.pt is in same folder

model = load_model()

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Settings")
conf_threshold = st.sidebar.slider("Confidence Threshold", 0.1, 1.0, 0.25)

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload an Image or Video",
    type=["jpg", "jpeg", "png", "mp4", "avi", "mov"]
)

# ---------------- IMAGE HANDLER ----------------
def process_image(image):
    results = model(image, conf=conf_threshold)
    annotated = results[0].plot()
    return annotated

# ---------------- VIDEO HANDLER ----------------
def process_video(video_path):
    cap = cv2.VideoCapture(video_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    progress = st.progress(0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    processed = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=conf_threshold)
        annotated_frame = results[0].plot()

        out.write(annotated_frame)

        processed += 1
        progress.progress(min(processed / frame_count, 1.0))

    cap.release()
    out.release()

    return output_path

# ---------------- MAIN LOGIC ----------------
if uploaded_file is not None:
    file_type = uploaded_file.type

    # ---------- IMAGE ----------
    if file_type.startswith("image"):
        image = Image.open(uploaded_file).convert("RGB")
        st.subheader("📷 Original Image")
        st.image(image, use_column_width=True)

        if st.button("Run Detection"):
            with st.spinner("Detecting pedestrians..."):
                result_img = process_image(np.array(image))
            st.subheader("✅ Detection Result")
            st.image(result_img, use_column_width=True)

    # ---------- VIDEO ----------
    elif file_type.startswith("video"):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())

        st.subheader("🎥 Original Video")
        st.video(uploaded_file)

        if st.button("Run Video Detection"):
            with st.spinner("Processing video frames..."):
                output_video = process_video(tfile.name)

            st.subheader("✅ Detection Result Video")
            st.video(output_video)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("Built with ❤️ using **YOLOv8 + Streamlit**")
