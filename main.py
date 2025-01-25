import requests
import asyncio
import streamlit as st
from urllib.parse import urlparse
import json
from jinja2 import Template
import base64
from io import BytesIO
import os
from dotenv import load_dotenv
import time
from deep_translator import GoogleTranslator
from tenacity import retry, stop_after_attempt, wait_fixed
from PIL import Image
from urllib.parse import quote

# Initialize components
from utils.init import initialize
from utils.counter import increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender
from utils.text_to_image.pollinations_generator import PollinationsGenerator

from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {
        'telegram_sender': TelegramSender(),
        'counted': False,
    }

# Set page config for better mobile responsiveness
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="מחולל תמונות AI", page_icon="📷")

UPLOAD_FOLDER = "uploads"

# Read the HTML template
with open("template.html", "r", encoding="utf-8") as file:
    html_template = file.read()

# Read models from JSON file
with open("data/models.json", "r", encoding="utf-8") as file:
    models_data = json.load(file)
    models = models_data["models"]

def get_file_type_from_url(url):
    if url is None:
        return 'error'
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('.mp4'):
        return 'video' 
    else:
        return 'image'

@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='en')

def translate_to_english(text):
    try:
        translator = get_translator()
        return translator.translate(text)
    except Exception as e:
        st.error(f"שגיאה בתרגום: {str(e)}")
        return text
                
def load_html_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return f.read()

async def send_telegram_message_and_file(message, file_content: BytesIO):
    sender = TelegramSender()
    try:
        if await sender.verify_bot_token():
            await sender.send_document(file_content, caption=message)
        else:
            raise Exception("Bot token verification failed")
    except Exception as e:
        raise Exception(f"Failed to send Telegram message: {str(e)}")
    finally:
        await sender.close_session()

def load_examples():
    with open("data/Examples.json", "r", encoding="utf-8") as file:
        return json.load(file)

@st.cache_data
def load_image(image_path):
    return Image.open(image_path)

@st.cache_data
def get_image_data(base_path):
    image_data = {}
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
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
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
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
 
def add_examples_images():    
    image_data = get_image_data(UPLOAD_FOLDER)
        
    for prompt, data in image_data.items():
        st.markdown(f"""
            <div class="description-container">
                <div class="description">{data['description']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        model_cols = st.columns(len(data['models']))
        
        for col, model in zip(model_cols, data['models']):            
            with col:
                try:
                    image = Image.open(model['image_path'])
                    st.markdown(f'<div class="model-container">', unsafe_allow_html=True)
                    st.image(image, None, use_container_width=True)
                    st.markdown(f'<div class="model-name">{model["name"]}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading image: {model['image_path']}. Error: {str(e)}")
    
    st.markdown("<hr>", unsafe_allow_html=True)

@st.cache_data
def load_image_styles():
    with open("data/image_styles.json", "r", encoding="utf-8") as file:
        return json.load(file)["styles"]

def hide_streamlit_header_footer():
    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
                content:'goodbye'; 
                visibility: visible;
                display: block;
                position: relative;
                padding: 5px;
                top: 2px;
            }
            header {visibility: hidden;}
            #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)

async def main():    
    title, image_path, footer_content = initialize()
    st.title("מחולל תמונות AI 🌟")
    hide_streamlit_header_footer()
    
    # Load and display the custom expander HTML
    expander_html = load_html_file('expander.html')
    st.markdown(expander_html, unsafe_allow_html=True)    
    
    # Load examples
    examples = load_examples()

    # Create a selectbox for examples with a label
    example_titles = [""] + [example["title"] for example in examples]
    selected_example = st.selectbox(
        label="פרומפטים לדוגמא",
        options=example_titles,
        index=None,
        key="example_selector",
        placeholder="פרומפטים לדוגמא 👈",
    )

    # Initialize session state for prompt if it doesn't exist
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""

    # Update prompt if an example is selected
    if selected_example and selected_example != "":
        selected_example_data = next((example for example in examples if example["title"] == selected_example), None)
        if selected_example_data:
            st.session_state.prompt = selected_example_data["prompt"]

    # Text area for prompt
    prompt = st.text_area("יש לכתוב פרומפט ליצירת תמונה...", value=st.session_state.prompt, key='prompt_input', help="יצירת תמונות")

    # Selectbox for style
    image_styles = load_image_styles()
    style_options = [style['name'] for style in image_styles]
    selected_style = st.selectbox(
        "בחרו סגנון תמונה 🎨",
        options=style_options,
        index=0,
        key='style_input'
    )

    # Set default model to use PollinationsGenerator
    default_model = "⚡ Pollinations"        

    # Generate button
    if st.button('יצירת תמונה', use_container_width=True):
        if prompt:
            st.markdown(prompt)            

            # Process selected style
            selected_style_prefix = next(style['prompt_prefix'] for style in image_styles if style['name'] == selected_style)
            english_prompt=translate_to_english(prompt)

            # Combine style prefix with the user's prompt
            if selected_style != "סגנון חופשי" and selected_style_prefix:
                full_prompt = f"{selected_style_prefix} {english_prompt}"
            else:
                full_prompt = english_prompt

            print("sagi")

            # Create a placeholder for the spinner
            with st.spinner("מייצר תמונות נא להמתין בסבלנות ..."):   
                try:
                    # First encode the prompt
                    encoded_prompt = quote(full_prompt)
                    # Construct the URL with the encoded prompt
                    image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1280&height=720&seed=42&nologo=true&enhance=true"
                    print(f"Image URL: {image_url}")

                    # Fetching the image from the URL
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        if image:
                            # Display the generated image
                            st.image(image, use_container_width=True)
                            
                            # Add balloons celebration after successful generation
                            st.balloons()
                            st.success("התמונה נוצרה בהצלחה! 🎉")
                    else:
                        st.error(f"Error: Server returned status code {response.status_code}")
                        print(f"Server response: {response.text}")
                        
                except Exception as e:
                    print(f"Error generating media: {str(e)}")
                    st.error(f"Error generating image: {str(e)}")

    # Add examples images
    add_examples_images()
    
    # Display footer content
    st.markdown(footer_content, unsafe_allow_html=True)    

    # Display user count
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)

    # Display LAST_DATETIME_USE value
    last_datetime_use = os.getenv("LAST_DATETIME_USE")
    st.markdown(f"<p class='last-datetime-use'>משתמש אחרון נכנס ב {last_datetime_use}</p>", unsafe_allow_html=True)

    # Update LAST_DATETIME_USE on first user entry
    if 'initial_visit' not in st.session_state:
        st.session_state.initial_visit = True
        israel_time = datetime.now(pytz.timezone("Asia/Jerusalem"))
        formatted_time = israel_time.strftime("%d/%m/%Y %H:%M")
        os.environ['LAST_DATETIME_USE'] = formatted_time

if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    
    asyncio.run(main())