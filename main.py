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
import replicate

# Initialize components
from utils.init import initialize
from utils.counter import initialize_user_count, increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender

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

# Read models and styles from JSON file
@st.cache_data
def load_models_and_styles():
    with open("data/models_and_styles.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        return data["models"], data["styles"]

models, styles = load_models_and_styles()

def get_file_type_from_url(url):
    if url is None:
        return 'error'
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('.mp4'):
        return 'video'
    else:
        return 'image'

def add_timestamp(prompt):
    timestamp = int(time.time())
    return f"{prompt} [Timestamp: {timestamp}]"

def generate_media(prompt, style, model):
    image_url = None    

    try:
        if model['generation_app'] == 'replicate': 
            input_data = {"prompt": prompt.strip()} 
            
            if model.get('supports_negative_prompt', False):
                combined_negative_prompt = f"{model['negative_prompt']}, {style['negative_prompt']}".strip(', ')
                input_data["negative_prompt"] = combined_negative_prompt
            
            output = replicate.run(
                model['link'],
                input=input_data
            )
            image_url = output[0]
            # print(f"Model Name: {model['name']}")
            # print(f"Prompt Style: {style['name']}")
            # print(f"Negative prompt: {input_data.get('negative_prompt', 'Not used')}")
            # print(f"Generated prompt: {input_data['prompt']}")
            
            # print(f"Output: {output}")
    except Exception as e:
        print(f"Error generating media for {model['title']}: {str(e)}")
        return None
    
    print(f"Image generated for {model['generation_app']}")
    return image_url

def get_style_by_name(styles, style_name):
    return next((style for style in styles if style['name'] == style_name), None)

def generate_html(prompt, style_input, selected_models, progress_bar, status_text):
    template = Template(html_template)    
    english_prompt = translate_to_english(prompt)

    # Check if style_input is a string (name) or a dictionary (full style object)
    if isinstance(style_input, str):
        style = get_style_by_name(styles, style_input)
        if not style:
            raise ValueError(f"Style '{style_input}' not found")
    else:
        style = style_input  # It's already the full style object

    total_models = len(selected_models)
    for i, model in enumerate(selected_models, 1):
        status_text.text(f"מייצר תמונה במודל: {model['title']} ({i}/{total_models})")
        
        full_prompt = f"{style['prompt_prefix']} {english_prompt}".strip()  # Add prompt_prefix here
        full_negative_prompt = f"{style['negative_prompt']}, {model['negative_prompt']}" if model.get('supports_negative_prompt', False) else ""
        
        model['media_url'] = generate_media(full_prompt, style, model)
        model['media_type'] = get_file_type_from_url(model['media_url'])
        if model['media_url']:
            print(f"Generated media URL for {model['title']}: {model['media_url']}")
        else:
            print(f"Failed to generate media for {model['title']}")
        progress_bar.progress(i / total_models)

    html_content = template.render(prompt=prompt, style=style['name'], models=selected_models)
    
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
                    image = st.image(model['image_path'], use_column_width=True)
                    st.markdown(f'<div class="model-name">{model["name"]}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading image: {model['image_path']}. Error: {str(e)}")
    
    st.markdown("<hr>", unsafe_allow_html=True)

def get_compatible_styles(selected_models, styles):
    compatible_styles = set(styles[0]['name'])  # Always include "סגנון חופשי"
    for model in selected_models:
        compatible_styles.update(model.get('compatible_styles', []))
    return [style for style in styles if style['name'] in compatible_styles]

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
        label="",
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

    # 1. Text area for prompt
    prompt = st.text_area("יש לכתוב פרומפט ליצירת תמונה...", value=st.session_state.prompt, key='prompt_input', help="יצירת תמונות")

    # 2. Multiselect for models
    model_options = [model['title'] for model in models]
    default_model = "Playground"
    selected_model_titles = st.multiselect(
       f"בחרו מודלי תמונה מהרשימה ({len(models)} מודלים) 👈 ",
        model_options,
        default=[default_model] if default_model in model_options else []
    )

    # 3. Selectbox for style
    selected_models = [model for model in models if model['title'] in selected_model_titles]
    compatible_styles = get_compatible_styles(selected_models, styles)
    style_options = [style['name'] for style in compatible_styles]
    
    selected_style_name = st.selectbox(
        "בחרו סגנון תמונה 🎨",
        options=style_options,
        index=0,
        key='style_input'
    )
    selected_style = next((style for style in compatible_styles if style['name'] == selected_style_name), None)

    # Generate button
    if st.button('Generate', use_container_width=True):
        if prompt and selected_model_titles and selected_style:
            st.markdown(prompt)
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Create a placeholder for the spinner
            with st.spinner("מייצר תמונות נא להמתין בסבלנות ..."):
                html_content = generate_html(prompt, selected_style, selected_models, progress_bar, status_text)

                # Provide a download link for the HTML content
                bio = BytesIO(html_content.encode('utf-8'))
                
                download_link = get_binary_file_downloader_html(bio, 'comparison_results.html')
                st.markdown(download_link, unsafe_allow_html=True)

                # Display the HTML content directly in Streamlit
                st.components.v1.html(html_content, height=600, scrolling=True)

                # Send message to Telegram
                try:
                    await send_telegram_message_and_file("from OHAD AVIAD\n" + prompt, BytesIO(html_content.encode('utf-8')))
                except Exception as e:
                    print(f"Failed to send to Telegram: {str(e)}")

    # Display examples
    add_examples_images()
    # Display footer content
    st.markdown(footer_content, unsafe_allow_html=True)    

    # Display user count after the chatbot
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    initialize_user_count()
    asyncio.run(main())