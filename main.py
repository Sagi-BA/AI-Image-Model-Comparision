import requests
import asyncio
import streamlit as st
from urllib.parse import urlparse
import json
import tempfile
from jinja2 import Template
import base64
from io import BytesIO
import os
from dotenv import load_dotenv
import random
from deep_translator import GoogleTranslator

# Initialize components
from utils.init import initialize
from utils.counter import initialize_user_count, increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender

from utils.text_to_image.pollinations_generator import PollinationsGenerator
# from utils.text_to_image.sdxl_lightning_generator import SDXLLightningGenerator
from utils.text_to_image.hand_drawn_cartoon_generator import HandDrawnCartoonGenerator
from utils.text_to_video.animatediff_lightning_generator import AnimateDiffLightningGenerator
from utils.imgur_uploader import ImgurUploader

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

# Read the HTML template
with open("template.html", "r", encoding="utf-8") as file:
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

def add_random_spaces(prompt):
    words = list(prompt)
    num_spaces = random.randint(1, 100)
    
    for _ in range(num_spaces):
        position = random.randint(0, len(words))
        words.insert(position, ' ')
    
    return ''.join(words)

def generate_image(prompt, model_name):    
    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_URL = os.getenv("HF_URL")    

    if not HF_TOKEN:
        raise ValueError("Hugging Face token must be set in environment variables")
    if not HF_URL:
        raise ValueError("Hugging Face URL must be set in environment variables")
    
    # Add random spaces to the prompt
    prompt_with_spaces = add_random_spaces(prompt)

    url = HF_URL + model_name        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}    

    try:
        print(f"Attempting to connect to {model_name}:")
        print(url)
        payload = ({"inputs": f"{prompt_with_spaces}"})
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
        # elif model['generation_app'] == 'sdxl_lightning':
        #     sdxl_lightning_generator = SDXLLightningGenerator()
        #     return sdxl_lightning_generator.generate_image(prompt)
        else:
            print(f"Image generation for {model['generation_app']} is not implemented")            
            image_url = generate_image(prompt, model['generation_app'])
            # return image_url
    except Exception as e:
        print(f"Error generating media for {model['title']}: {str(e)}")
        return None
    
    # Remove 'https://' from the media_url if it exists
    # if 'https://' in image_url:
    #     image_url = image_url.replace('https://', '')

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

async def main():
    title, image_path, footer_content = initialize()
    st.title("מחולל תמונות AI 🌟")
    
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
        index=None,
        placeholder="פרומפטים לדוגמא 👈",
    )

    # Allow user to select models, with "Turbo" as default
    model_options = [model['title'] for model in models]
    default_model = "Flux.1 (Grok)"
    selected_model_titles = st.multiselect(
        "בחרו מודלי תמונה מהרשימה 👈",
        model_options,
        placeholder="בחרו מודלי תמונה מהרשימה 👈",
        default=[default_model] if default_model in model_options else []
    )

    # Create a form for the chat input and submit button
    with st.form(key='chat_form'):
        prompt = ""
        
        # Update prompt if an example is selected
        if selected_example:
            selected_example_data = next((example for example in examples if example["title"] == selected_example), None)
            if selected_example_data:
                prompt = selected_example_data["prompt"]                
        
        prompt = st.text_area("יש לכתוב פרומפט לייצור תמונה...", prompt, key='prompt_input',help="יצירת תמונות")
        submit_button = st.form_submit_button(label='Generate', use_container_width=True)

    if submit_button and prompt and selected_model_titles:
        st.markdown(prompt)
        selected_models = [model for model in models if model['title'] in selected_model_titles]

        progress_bar = st.progress(0)
        status_text = st.empty()

        # Create a placeholder for the spinner
        with st.spinner("מייצר תמונות נא להמתין בסבלנות ..."):
            html_content = generate_html(prompt, selected_models, progress_bar, status_text)

            # st.success("התמונות נוצרו בהצלחה!")
            # status_text.text("התמונות נוצרו בהצלחה!")
            # st.success("נוצר קובץ HTML להורדה!")

            # Provide a download link for the HTML content
            bio = BytesIO(html_content.encode('utf-8'))
            
            download_link = get_binary_file_downloader_html(bio, 'comparison_results.html')
            st.markdown(download_link, unsafe_allow_html=True)

            # Display the HTML content directly in Streamlit
            st.components.v1.html(html_content, height=600, scrolling=True)

            # Send message to Telegram
            try:
                await send_telegram_message_and_file(prompt, html_content)
            except Exception as e:
                print(f"Failed to send to Telegram: {str(e)}")

    # Display footer content
    st.markdown(footer_content, unsafe_allow_html=True)    

    # Display user count after the chatbot
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)
# Add this function to load examples

def load_examples():
    with open("data/Examples.json", "r", encoding="utf-8") as file:
        return json.load(file)
    
if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    initialize_user_count()
    asyncio.run(main())