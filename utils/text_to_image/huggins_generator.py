import sys, os
import base64
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

load_dotenv()

class HugginsGenerator:
    def __init__(self):
        self.HF_TOKEN = os.getenv("HF_TOKEN")
        self.HF_URL = os.getenv("HF_URL")
        
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face token must be set in environment variables")
        if not self.HF_URL:
            raise ValueError("Hugging Face URL must be set in environment variables")
        
        self.uploader = ImgurUploader()
    
    @staticmethod
    def add_timestamp(prompt):
        timestamp = int(time.time())
        return f"{prompt} [Timestamp: {timestamp}]"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt, model_name, negative_prompt=None):
        if not self.HF_TOKEN or not self.HF_URL:
            raise ValueError("Hugging Face token and URL must be set in environment variables")
        
        prompt_with_timestamp = self.add_timestamp(prompt)

        url = self.HF_URL + model_name        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
    
        try:
            print(f"Attempting to connect to model '{model_name}' at URL: {url}")            
            payload = {
                "inputs": prompt_with_timestamp,
                "negative_prompt": negative_prompt
            }
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                print(f"Error: Non-200 response received: {response.status_code}")
                return None

            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            image_url = self.uploader.upload_media_to_imgur(
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

def test_huggingface_image_generator():
    try:
        generator = HugginsGenerator()
        sample_model_name = "kudzueye/boreal-flux-dev-v2"
        sample_prompt = "Close-up of the face of a gruff old fisherman, with deep wrinkles, wearing a yellow raincoat and a woolen hat, against a background of a stormy sea"
        sample_negative_prompt = "young, smooth skin, calm sea"
        
        image_url = generator.generate_image(sample_prompt, sample_model_name, sample_negative_prompt)
        
        if image_url:
            print("Test passed! Image generated and uploaded successfully.")
            print(f"Image URL: {image_url}")
        else:
            print("Test failed! No image URL returned.")
    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    test_huggingface_image_generator()