import os
import base64
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.imgur_uploader import ImgurUploader

# Load environment variables from .env file
load_dotenv()

class HuggingfaceImageGenerator:
    def __init__(self):
        self.HF_TOKEN = os.getenv("HF_TOKEN")
        self.HF_URL = os.getenv("HF_URL")
        
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face token must be set in environment variables")
        if not self.HF_URL:
            raise ValueError("Hugging Face URL must be set in environment variables")
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt, model_name):
        url = self.HF_URL + model_name        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
    
        try:
            print(f"Attempting to connect to {model_name} model with prompt: {prompt}")
            print(url)
            payload = {"inputs": f"{prompt}"}
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
