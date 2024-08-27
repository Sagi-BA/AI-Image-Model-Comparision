import streamlit as st
from urllib.parse import urlparse
import json
from jinja2 import Template
import base64
from io import BytesIO
import os

from utils.text_to_image.HuggingfaceImageGenerator import HuggingfaceImageGenerator

from utils.text_to_image.pollinations_generator import PollinationsGenerator
from utils.text_to_image.sdxl_lightning_generator import SDXLLightningGenerator
from utils.text_to_image.hand_drawn_cartoon_generator import HandDrawnCartoonGenerator
from utils.text_to_video.animatediff_lightning_generator import AnimateDiffLightningGenerator

# Read the HTML template
with open("template.html", "r") as file:
    html_template = file.read()

# Read models from JSON file
with open("data/models.json", "r") as file:
    models_data = json.load(file)
    models = models_data["models"]

def get_file_type_from_url(url):
    if url is None:
        return 'error'
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('.mp4'):
        return 'video'
    elif path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return 'image'
    else:
        return 'unknown'

def generate_media(prompt, model):
    try:
        if model['generation_app'] == 'pollinations':
            pollinations_generator = PollinationsGenerator()
            image_url= pollinations_generator.generate_image(prompt, model['name'])
        # elif model['generation_app'] == 'flux_koda':
        #     flux_koda = FluxKodanGenerator()
        #     return flux_koda.generate_image(prompt)
        elif model['generation_app'] == 'hand_drawn_cartoon_style':
            hand_drawn_cartoon_generator = HandDrawnCartoonGenerator()
            image_url= hand_drawn_cartoon_generator.generate_image(prompt)
        elif model['generation_app'] == 'animatediff_lightning':
            animatediff_lightning_generator = AnimateDiffLightningGenerator()
            image_url= animatediff_lightning_generator.generate_image(prompt)        
        # elif model['generation_app'] == 'sdxl_lightning':
        #     sdxl_lightning_generator = SDXLLightningGenerator()
        #     return sdxl_lightning_generator.generate_image(prompt)
        else:
            # print(f"Image generation for {model['generation_app']} is not implemented")
            generator = HuggingfaceImageGenerator(model['generation_app'])
            image_url = generator.generate_image(prompt)
            return None
    except Exception as e:
        print(f"Error generating media for {model['title']}: {str(e)}")
        return None
    
    return image_url

def generate_html(prompt, selected_models, progress_bar, status_text):
    template = Template(html_template)    

    total_models = len(selected_models)
    for i, model in enumerate(selected_models, 1):
        status_text.text(f"Generating comparison for model: {model['title']} ({i}/{total_models})")
        model['media_url'] = generate_media(prompt, model)
        model['media_type'] = get_file_type_from_url(model['media_url'])
        if model['media_url']:
            print(f"Generated media URL for {model['title']}: {model['media_url']}")
        else:
            print(f"Failed to generate media for {model['title']}")
        progress_bar.progress(i / total_models)

    html_content = template.render(prompt=prompt, models=selected_models)
    
    return html_content

def get_binary_file_downloader_html(bin_file, file_label='File'):
    bin_file.seek(0)
    bin_str = base64.b64encode(bin_file.read()).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

# Set page config for better mobile responsiveness
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for better mobile responsiveness
st.markdown("""
    <style>
    .reportview-container .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stTextArea>div>div>textarea {
        height: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("AI Model Comparison Generator")

prompt = st.text_area("Enter your prompt:", height=100)

# Allow user to select models, with "Turbo" as default
model_options = [model['title'] for model in models]
default_model = "Turbo"
selected_model_titles = st.multiselect(
    "Select models to compare:",
    model_options,
    default=[default_model] if default_model in model_options else []
)

if st.button("Generate Comparison"):
    if prompt.strip() and selected_model_titles:
        selected_models = [model for model in models if model['title'] in selected_model_titles]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create a placeholder for the spinner
        with st.spinner("Generating comparison..."):
            html_content = generate_html(prompt, selected_models, progress_bar, status_text)
        
        status_text.text("Comparison generated successfully!")
        st.success("HTML content generated successfully!")
        
        # Display the HTML content directly in Streamlit
        st.components.v1.html(html_content, height=600, scrolling=True)
        
        # Provide a download link for the HTML content
        bio = BytesIO(html_content.encode())
        st.markdown(get_binary_file_downloader_html(bio, 'comparison_results.html'), unsafe_allow_html=True)
    else:
        st.warning("Please enter a prompt and select at least one model.")