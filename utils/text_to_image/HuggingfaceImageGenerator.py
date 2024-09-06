import sys, os
import base64
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

import time

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

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
        
        self.uploader = ImgurUploader()
    
    @staticmethod
    def add_timestamp(prompt):
        timestamp = int(time.time())
        return f"{prompt} [Timestamp: {timestamp}]"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt, model_name):
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face token must be set in environment variables")
        if not self.HF_URL:
            raise ValueError("Hugging Face URL must be set in environment variables")
        
        prompt_with_timestamp = self.add_timestamp(prompt)

        url = self.HF_URL + model_name        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
    
        try:
            print(f"Attempting to connect to model '{model_name}' at URL: {url}")            
            payload = {"inputs": prompt_with_timestamp}
            response = requests.post(url, headers=headers, json=payload)

            # Debugging: print response details
            # print(f"Response Status Code: {response.status_code}")
            # print(f"Response Headers: {response.headers}")
            # print(f"Response Content: {response.content[:100]}...")  # print first 100 bytes for brevity

            if response.status_code != 200:
                print(f"Error: Non-200 response received: {response.status_code}")
                return None

            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            print(f"Image Base64 (truncated): {image_base64[:100]}...")  # print first 100 chars for brevity

            image_url = self.uploader.upload_media_to_imgur(
                image_base64, 
                "image",
                model_name,  # Title
                prompt  # Description
            )
            return image_url
        except Exception as e:
            print(f"Error generating image: {e}")
            return None

def test_huggingface_image_generator():
    try:
        # Create an instance of HuggingfaceImageGenerator
        generator = HuggingfaceImageGenerator()
        
        # Define a sample prompt and model name for testing
        sample_prompt = "Close-up of the face of a gruff old fisherman, with deep wrinkles, wearing a yellow raincoat and a woolen hat, against a background of a stormy sea"
        sample_model_name = "markury/surrealidescent"
        
        # Call the generate_image method
        image_url = generator.generate_image(sample_prompt, sample_model_name)
        
        # Check if an image URL is returned
        if image_url:
            print("Test passed! Image generated and uploaded successfully.")
            print(f"Image URL: {image_url}")
        else:
            print("Test failed! No image URL returned.")
    except Exception as e:
        print(f"Test failed with exception: {e}")


if __name__ == "__main__":
    # Run the test
    test_huggingface_image_generator()