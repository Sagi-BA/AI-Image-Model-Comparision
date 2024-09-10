from io import BytesIO
import streamlit as st
import os
from PIL import Image
import base64

def load_image(image_path):
    return Image.open(image_path)

def get_image_data(base_path):
    image_data = {}
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            # Read the description file
            description_file = os.path.join(folder_path, "prompt_description.md")
            description = ""
            if os.path.exists(description_file):
                with open(description_file, 'r', encoding='utf-8') as f:
                    description = f.read().strip()
            
            image_data[folder] = {
                'description': description,
                'models': []
            }
            for image_file in os.listdir(folder_path):
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    model_name = os.path.splitext(image_file)[0]
                    image_data[folder]['models'].append({
                        'name': model_name,
                        'image_path': os.path.join(folder_path, image_file)
                    })
    return image_data

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def main():
    st.set_page_config(layout="wide", page_title="AI Model Image Comparison")
    
    # Custom CSS and JavaScript for RTL layout, styling, and interactivity
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&display=swap');
    .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }
    .stApp > header {
        direction: ltr;
    }
    h1 {
        color: #333;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    h2 {
        color: #555;
        font-weight: 500;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 0.5rem;
    }
    .description-container {
        background-color: #f7f7f7;
        border-radius: 8px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .description {
        padding: 1rem;
        font-size: 0.9rem;
        color: #333;
    }
    .model-name {
        font-weight: 500;
        color: #444;
        margin-bottom: 0.25rem;
        text-align: center;
    }
    .model-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .model-image {
        width: 200px;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        transition: transform 0.3s ease;
        cursor: pointer;
    }
    .model-image:hover {
        transform: scale(1.1);
    }
    .modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.9);
    }
    .modal-content {
        margin: auto;
        display: block;
        width: 80%;
        max-width: 700px;
    }
    .close {
        position: absolute;
        top: 15px;
        right: 35px;
        color: #f1f1f1;
        font-size: 40px;
        font-weight: bold;
        transition: 0.3s;
    }
    .close:hover,
    .close:focus {
        color: #bbb;
        text-decoration: none;
        cursor: pointer;
    }
                
    </style>
    
    <div id="imageModal" class="modal">
        <span class="close">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
    var modal = document.getElementById("imageModal");
    var modalImg = document.getElementById("modalImage");
    var span = document.getElementsByClassName("close")[0];

    function showModal(imgSrc) {
        modal.style.display = "block";
        modalImg.src = imgSrc;
    }

    span.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
    </script>
    """, unsafe_allow_html=True)

    # st.title("השוואת תמונות מודלים של AI")

    base_path = 'uploads'
    image_data = get_image_data(base_path)

    for prompt, data in image_data.items():
        # st.header(prompt)
        
        desc_col, models_col = st.columns([1, 4])
        
        with desc_col:
            st.markdown(f"""
            <div class="description-container">
                <div class="description">{data['description']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with models_col:
            model_cols = st.columns(len(data['models']))
            
            for col, model in zip(model_cols, data['models']):
                with col:
                    img = load_image(model['image_path'])
                    img_b64 = image_to_base64(img)
                    st.markdown(f"""
                    <div class="model-container">
                        <div class="model-name">{model['name']}</div>
                        <img src="data:image/png;base64,{img_b64}" 
                             class="model-image" 
                             onclick="showModal(this.src)"
                             alt="{model['name']}">
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()