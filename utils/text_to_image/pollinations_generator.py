import requests
from PIL import Image
import io
import sys, os
from urllib.parse import quote
import base64
import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader
# from pollinations_generator import PollinationsGenerator  # Circular import - commented out
# from together_ai_generator import TogetherAIGenerator  # File doesn't exist - commented out

# https://pollinations.ai/
## Parameters
# - prompt (required): The text description of the image you want to generate. Should be URL-encoded.
# - model (optional): The model to use for generation. Options: 'flux' or 'turbo'. Default: 'turbo'
# - seed (optional): Seed for reproducible results. Default: random
# - width (optional): Width of the generated image. Default: 1024
# - height (optional): Height of the generated image. Default: 1024
# - nologo (optional): Set to 'true' to turn off the rendering of the logo
# - nofeed (optional): Set to 'true' to prevent the image from appearing in the public feed
# - enhance (optional): Set to 'true' or 'false' to turn on or off prompt enhancing (passes prompts through an LLM to add detail)

## Example Usage
# https://image.pollinations.ai/prompt/A%20beautiful%20sunset%20over%20the%20ocean?model=flux&width=1280&height=720&seed=42&nologo=true&enhance=true

## Response
# The API returns a raw image file (typically JPEG or PNG) as the response body. You can directly embed the image in your HTML or Markdown.
class PollinationsGenerator:
    def __init__(self):
        self.pollinations_url = "https://image.pollinations.ai/prompt/{prompt}?model={model}&width=1280&height=720&seed=42&nologo=true&enhance=true"

    def generate_image(self, prompt, model_name, negative_prompt=None):
        encoded_prompt = quote(prompt)
        url = self.pollinations_url.format(prompt=encoded_prompt, model=model_name)
        
        if negative_prompt:
            url += f"&negative_prompt={quote(negative_prompt)}"
        
        try:
            uploader = ImgurUploader()
            base64_image = self.convert_image_url_to_base64(url)
            if base64_image:
                image_url = uploader.upload_media_to_imgur(
                     base64_image, 
                     "image",
                     model_name,  # Title
                     prompt  # Description
                )
                return image_url
            else:
                print("Failed to convert image to base64")
                return None 
        except requests.exceptions.RequestException as e:
            print(f"Error generating image with Pollinations: {e}")
            return None    

    @staticmethod
    def convert_image_url_to_base64(image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            buffered = io.BytesIO()
            img.save(buffered, format=img.format)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return image_base64
        except Exception as e:
            print(f"Failed to convert image from URL: {image_url}")
            print(f"Error: {str(e)}")
            return None

def test(upload_dir="uploads", model_name="turbo", filename=None):    
    generator = PollinationsGenerator()
    prompt = "A fast red color car"
    negative_prompt = "low quality, worst quality"
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    image_url = generator.generate_image(prompt, model_name, negative_prompt)
    return image_url

if __name__ == "__main__":
    test_result = test("uploads", "turbo", "pollinations_generator.png")
    print(f"Test {'passed' if test_result else 'failed'}")   

# דוגמאות מוכנות
EXAMPLES = [
    "מנגו, גבינת עיזים, דבש, אהבה",
    "ענבים, תאנים, רימונים, שמחה",
    "עוגת גבינה, פרחים, חיטה, שוקולד",
    "תמרים, יין, גבינה צפתית, חיוך",
    "אבטיח, לחם, שמן זית, ברכה"
]

def transcribe_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 הקלטה מתחילה...")
        audio = r.listen(source)
        st.info("🎵 מעבד את ההקלטה...")
    try:
        text = r.recognize_google(audio, language="he-IL")
        return text
    except sr.UnknownValueError:
        st.error("לא הצלחתי להבין את ההקלטה")
        return None
    except sr.RequestError:
        st.error("שגיאה בשירות ההקלטה")
        return None

def generate_image(prompt):
    basket_prompt = (
        f"A beautiful Shavuot basket on a festive table, containing: {prompt}. "
        "The basket is overflowing with fresh, colorful produce, cheeses, and flowers. "
        "Ultra-realistic, vibrant, joyful, high detail, 4k, cinematic lighting."
    )
    return pollinations.generate_image(basket_prompt, "flux")

def generate_hebrew_text(prompt):
    # Simple placeholder since TogetherAIGenerator is not available
    return f"סל ביכורים מקסים עם {prompt} - מוכן לחג שבועות!"

def main():
    st.set_page_config(
        page_title="מה תביא לביכורים? 🎉",
        page_icon="🎉",
        layout="centered"
    )

    # עיצוב וואו + RTL
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Varela+Round&display=swap');
        .stApp { background: linear-gradient(135deg, #fffbe7 0%, #ffe5ec 100%); font-family: 'Varela Round', sans-serif; direction: rtl; }
        .wow-box { border-radius: 24px; box-shadow: 0 4px 32px #ffb6b6; border: 3px solid #ffb6b6; padding: 24px; background: #fff8; direction: rtl; text-align: right;}
        .example-btn { background: #fffbe7; border: 2px solid #ffb6b6; border-radius: 16px; margin: 4px; font-size: 1.1em; transition: 0.2s; }
        .example-btn:hover { background: #ffe5ec; color: #d72660; transform: scale(1.05);}
        .result-img { border-radius: 18px; box-shadow: 0 2px 16px #d7266060; border: 2px solid #d72660; }
        .circle-btn { width: 70px; height: 70px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 2.2em; margin: 0 12px; border: none; box-shadow: 0 2px 12px #d7266040; cursor: pointer; transition: 0.2s; }
        .mic-btn { background: linear-gradient(135deg, #ffb6b6 0%, #ff8c8c 100%); color: white; }
        .text-btn { background: linear-gradient(135deg, #5ec6ff 0%, #3a8dde 100%); color: white; }
        .circle-btn:hover { transform: scale(1.08);}
        .input-box { width: 100%; font-size: 1.1em; border-radius: 12px; border: 2px solid #ffb6b6; padding: 10px; margin-bottom: 10px; direction: rtl; text-align: right;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center; color:#222;'>ספרו לנו מה תרצו להביא לסל הביכורים שלכם</h2>", unsafe_allow_html=True)

    # כפתורי הקלטה/הקלדה
    st.markdown("""
    <div style='text-align:center; margin: 20px 0;'>
        <button class="circle-btn text-btn" id="text-btn" title="הקלדה">&#9993;</button>
        <button class="circle-btn mic-btn" id="mic-btn" title="הקלטה">&#127908;</button>
    </div>
    <div style='text-align:center; color:#888; font-size:1em;'>לחצו על המיקרופון לדיבור | לחצו על המעטפה להקלדה</div>
    """, unsafe_allow_html=True)

    # דוגמאות לבחירה
    st.markdown("<div style='text-align:center; margin-top:18px;'>", unsafe_allow_html=True)
    cols = st.columns(len(EXAMPLES))
    example_clicked = None
    for i, example in enumerate(EXAMPLES):
        if cols[i].button(example, key=f"ex_{i}"):
            example_clicked = example
    st.markdown("</div>", unsafe_allow_html=True)

    # --- לוגיקת קלט ---
    user_input = None
    # שליטה על מצב (הקלדה/הקלטה) בעזרת session_state
    if 'input_mode' not in st.session_state:
        st.session_state.input_mode = None

    # JS to handle button clicks and set session_state
    st.markdown("""
    <script>
    const textBtn = window.parent.document.getElementById('text-btn');
    const micBtn = window.parent.document.getElementById('mic-btn');
    if (textBtn) textBtn.onclick = () => { window.parent.postMessage({type: 'setInputMode', mode: 'text'}, '*'); };
    if (micBtn) micBtn.onclick = () => { window.parent.postMessage({type: 'setInputMode', mode: 'mic'}, '*'); };
    </script>
    """, unsafe_allow_html=True)

    # Streamlit can't directly listen to JS, so use a workaround:
    input_mode = st.radio("בחרו דרך להזין:", ["הקלדה", "הקלטה"], horizontal=True, index=0, key="input_mode_radio", label_visibility="collapsed")
    if input_mode == "הקלדה":
        user_input = st.text_input("מה תרצו שיהיה בסל?", value="", key="text_input", placeholder="הקלידו כאן בעברית...")
    elif input_mode == "הקלטה":
        if st.button("התחל להקליט 🎤", key="record"):
            user_input = transcribe_audio()
    if example_clicked:
        user_input = example_clicked

    if user_input:
        st.markdown(f"<div class='wow-box'><b>🎯 מה ששמענו/בחרת:</b> {user_input}</div>", unsafe_allow_html=True)

        # 1. טקסט שירי
        with st.spinner("📝 יוצר טקסט שירי לסל שלך..."):
            hebrew_text = generate_hebrew_text(user_input)
        if hebrew_text:
            st.markdown(f"<div class='wow-box' style='border-color:#d72660;'><b>📝</b> {hebrew_text}</div>", unsafe_allow_html=True)

            # 2. תמונה עם progress bar
            progress_bar = st.progress(0, text="🎨 יוצר תמונה של הסל שלך...")
            import time
            for percent_complete in range(1, 101, 10):
                progress_bar.progress(percent_complete, text="🎨 יוצר תמונה של הסל שלך...")
                time.sleep(0.03)
            image_url = generate_image(user_input)
            progress_bar.progress(100, text="✅ התמונה מוכנה!")
            if image_url:
                st.image(image_url, caption="הסל שלך לביכורים", use_column_width=True, output_format="auto")

            # כפתור שיתוף
            share_text = f"הנה הסל שלי לביכורים! {hebrew_text}"
            whatsapp_url = f"https://wa.me/?text={share_text}"
            st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="font-size:1.3em; color:#25d366;">📱 שתף בוואטסאפ</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    # אתחול הגנרטורים
    pollinations = PollinationsGenerator()
    # together_ai = TogetherAIGenerator()  # Commented out - file doesn't exist
    main()