
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

# Initialize components
from utils.init import initialize
from utils.counter import increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender

from utils.text_to_image.pollinations_generator import PollinationsGenerator
from utils.text_to_image.hand_drawn_cartoon_generator import HandDrawnCartoonGenerator
from utils.text_to_video.animatediff_lightning_generator import AnimateDiffLightningGenerator
from utils.imgur_uploader import ImgurUploader
from utils.text_to_image.unsplash_generator import UnsplashGenerator
from utils.text_to_image.huggins_generator import HugginsGenerator

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
# Set page config at the very beginning
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
    # elif path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
    #     return 'image'
    # else:
    #     return 'unknown'

def add_timestamp(prompt):
    timestamp = int(time.time())
    return f"{prompt} [Timestamp: {timestamp}]"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_image(prompt, model_name):    
    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_URL = os.getenv("HF_URL")    

    if not HF_TOKEN:
        raise ValueError("Hugging Face token must be set in environment variables")
    if not HF_URL:
        raise ValueError("Hugging Face URL must be set in environment variables")
    
    # Add random timestamp to the prompt
    prompt_with_timestamp = add_timestamp(prompt)

    url = HF_URL + model_name        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}    

    try:
        print(f"Attempting to connect to {model_name}:")
        print(url)
        payload = ({"inputs": f"{prompt_with_timestamp}"})
        response = requests.post(url, headers=headers, json=payload)
        
        image_bytes = response.content
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        uploader = ImgurUploader()
        image_url = uploader.upload_media_to_imgur(
            image_base64, 
            "image",
            model_name,  # Title
            prompt  # Description
        )
        if image_url:
            return image_url
        else:
            return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None
    
def generate_media(prompt, model):
    try:
        if model['generation_app'] == 'pollinations':
            pollinations_generator = PollinationsGenerator()
            image_url= pollinations_generator.generate_image(prompt, model['name'])        
        elif model['generation_app'] == 'hand_drawn_cartoon_style':
            hand_drawn_cartoon_generator = HandDrawnCartoonGenerator()
            image_url= hand_drawn_cartoon_generator.generate_image(prompt)
        elif model['generation_app'] == 'animatediff_lightning':
            animatediff_lightning_generator = AnimateDiffLightningGenerator()
            image_url= animatediff_lightning_generator.generate_image(prompt)    
        elif model['generation_app'] == 'unsplash':
            unsplash_generator = UnsplashGenerator()
            image_url= unsplash_generator.generate_image(prompt)         
        # elif model['generation_app'] == 'sdxl_lightning':
        #     sdxl_lightning_generator = SDXLLightningGenerator()
        #     return sdxl_lightning_generator.generate_image(prompt)
        else: 
             huggins_generator = HugginsGenerator()
             image_url= huggins_generator.generate_image(prompt, model['generation_app'])
            # image_url = generate_image(prompt, model['generation_app'])
            # return image_url
    except Exception as e:
        print(f"Error generating media for {model['title']}: {str(e)}")
        return None
    
    # Remove 'https://' from the media_url if it exists
    # if 'https://' in image_url:
    #     image_url = image_url.replace('https://', '')
    
    print(f"Image generation for {model['generation_app']} is not implemented")
    return image_url

def generate_html(prompt, selected_models, progress_bar, status_text):
    template = Template(html_template)    
    english_prompt = translate_to_hebrew(prompt)

    print(english_prompt)

    total_models = len(selected_models)
    for i, model in enumerate(selected_models, 1):
        status_text.text(f"מייצר תמונה במודל: {model['title']} ({i}/{total_models})")
        model['media_url'] = generate_media(english_prompt, model)
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
    href = f'''
    <div class="download-button-container">
        <a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}" class="download-button">
            לשמירת התמונות
        </a>
    </div>
    '''
    return href

@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='en')

def translate_to_hebrew(text):
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
        # Verify bot token
        if await sender.verify_bot_token():
            # Reset the file pointer to the beginning
            # file_content.seek(0)
            
            # Modify the send_document method to accept BytesIO
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
                    st.image(image, None, use_column_width=True)
                    st.markdown(f'<div class="model-name">{model["name"]}</div>', unsafe_allow_html=True)
                    # st.markdown(f'<div class="model-name">{model['name']}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading image: {model['image_path']}. Error: {str(e)}")
    
    st.markdown("<hr>", unsafe_allow_html=True)

# Add this function to load image styles
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
                #background-color: red;
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
        label="",  # Empty string for label
        options=example_titles,
        index=None,  # Set default to empty option
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

    # 1. Text area for prompt
    prompt = st.text_area("יש לכתוב פרומפט ליצירת תמונה...", value=st.session_state.prompt, key='prompt_input', help="יצירת תמונות")

    # 2. Selectbox for style
    image_styles = load_image_styles()
    style_options = [style['name'] for style in image_styles]
    selected_style = st.selectbox(
        "בחרו סגנון תמונה 🎨",
        options=style_options,
        index=0,  # Set default to the first style (which should be "סגנון חופשי")
        key='style_input'
    )

    # 3. Multiselect for models
    total_models = len(models)
    new_models = sum(1 for model in models if model['title'].startswith('🆕'))
    model_options = [model['title'] for model in models]
    default_model = "⚡ Flux.1 (Grok)"
    selected_model_titles = st.multiselect(
       f"בחרו מודלי תמונה מהרשימה ({total_models} מודלים, מתוכם {new_models} חדשים) 👈 ",
        model_options,
        placeholder=f"בחרו מודלי תמונה מהרשימה ({total_models} מודלים, מתוכם {new_models} חדשים) 👈 ",
        default=[default_model] if default_model in model_options else []
    )

    # Generate button
    if st.button('Generate', use_container_width=True):
        if prompt and selected_model_titles:
            st.markdown(prompt)
            selected_models = [model for model in models if model['title'] in selected_model_titles]

            # Process selected style
            selected_style_prefix = next(style['prompt_prefix'] for style in image_styles if style['name'] == selected_style)
            
            # Combine style prefix with the user's prompt
            if selected_style != "סגנון חופשי" and selected_style_prefix:
                full_prompt = f"{selected_style_prefix} {prompt}"
            else:
                full_prompt = prompt

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Create a placeholder for the spinner
            with st.spinner("מייצר תמונות נא להמתין בסבלנות ..."):
                html_content = generate_html(full_prompt, selected_models, progress_bar, status_text)

                # Provide a download link for the HTML content
                bio = BytesIO(html_content.encode('utf-8'))
                
                download_link = get_binary_file_downloader_html(bio, 'comparison_results.html')
                st.markdown(download_link, unsafe_allow_html=True)

                # Display the HTML content directly in Streamlit
                st.components.v1.html(html_content, height=600, scrolling=True)

                # Send message to Telegram
                try:
                    await send_telegram_message_and_file(full_prompt, html_content)
                except Exception as e:
                    print(f"Failed to send to Telegram: {str(e)}")

    # dISPLAY models_comparison_template.html
    # ADD examples.py
    add_examples_images()
    # Display footer content
    st.markdown(footer_content, unsafe_allow_html=True)    

    # Display user count after the chatbot
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)

    # Display LAST_DATETIME_USE value
    last_datetime_use = os.getenv("LAST_DATETIME_USE")
    st.markdown(f"<p class='last-datetime-use'>משתמש אחרון נכנס ב {last_datetime_use}</p>", unsafe_allow_html=True)

    # עדכון LAST_DATETIME_USE בכניסה הראשונה של המשתמש בדף
    if 'initial_visit' not in st.session_state:
        st.session_state.initial_visit = True
        # השגת הזמן הנוכחי לפי אזור הזמן של ישראל
        israel_time = datetime.now(pytz.timezone("Asia/Jerusalem"))
        formatted_time = israel_time.strftime("%d/%m/%Y %H:%M")
        # עדכון המשתנה ב- .env
        os.environ['LAST_DATETIME_USE'] = formatted_time
        with open(".env", "r") as file:
            lines = file.readlines()
        with open(".env", "w") as file:
            for line in lines:
                if line.startswith("LAST_DATETIME_USE"):
                    file.write(f"LAST_DATETIME_USE=\"{formatted_time}\"\n")
                else:
                    file.write(line)

# Add this function to load examples

if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    
    asyncio.run(main())