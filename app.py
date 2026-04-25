import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os

# Set page config
st.set_page_config(page_title="Skin Cancer Detection", page_icon="🩺")

st.title("Skin Cancer Detection 🩺")
st.write("Upload a skin lesion image to detect potential concerns using YOLOv8.")

# Function to load model
@st.cache_resource
def load_model():
    model_path = os.path.join("YOLOv8", "weights", "best.pt")
    if not os.path.exists(model_path):
        st.error(f"Model file not found at: {model_path}")
        return None
    return YOLO(model_path)

model = load_model()

if model:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(res_image, caption="Detection Result", use_column_width=True)
            if st.button("Analyze Image"):
                with st.spinner("Analyzing..."):
                    # Perform inference
                    results = model(image)
                    
                    # Visualize results
                    # plot() returns a BGR numpy array
                    res_plotted = results[0].plot()
                    
                    # Convert BGR to RGB for PIL/Streamlit
                    res_rgb = res_plotted[..., ::-1]
                    res_image = Image.fromarray(res_rgb)
                    
                    st.image(res_image, caption="Detection Result",  width="stretch")
                    
                    # Display detection details
                    boxes = results[0].boxes
                    if len(boxes) > 0:
                        st.success(f"Detected {len(boxes)} lesion(s).")
                        # Optional: Display confidence scores/classes if needed
                    else:
                        st.info("No lesions detected.")
                        
        except Exception as e:
            st.error(f"Error processing image: {e}")
