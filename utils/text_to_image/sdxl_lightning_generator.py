import sys
import os
from gradio_client import Client
from PIL import Image
from dotenv import load_dotenv
import base64
import time
import random
from tenacity import retry, stop_after_attempt, wait_fixed

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

# Load environment variables from .env file
load_dotenv()

class SDXLLightningGenerator:
    def __init__(self):
        # https://huggingface.co/ByteDance/SDXL-Lightning
        HF_TOKEN = os.getenv("HF_TOKEN")
        if not HF_TOKEN:
            raise ValueError("Hugging Face token must be set in environment variables")
        self.client = Client("ByteDance/SDXL-Lightning", hf_token=HF_TOKEN)
        
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt, model_name="SDXL Lightning"):        
        try:
            print(f"Attempting to connect to SDXL-Lightning to generate image with prompt: {prompt}")

            result = self.client.predict(
                prompt,
                ckpt="4-Step",
                api_name="/generate_image"
            )
            
            image_path = self.convert_webp_to_png(result)
            # convert webp file to base64
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode()

            uploader = ImgurUploader()

            image_url = uploader.upload_media_to_imgur(
                    image_base64, 
                    "image",
                    model_name,  # Title
                    prompt  # Description
            )
            return image_url
        except Exception as e:
                print(f"Error generating image: {e}")
                return None
        
    @staticmethod
    def convert_webp_to_png(image_path):
        # Check if the file is a .webp image
        if image_path.lower().endswith('.webp'):
            # Open the image using PIL
            with Image.open(image_path) as img:
                # Change the file extension to .png
                png_path = image_path[:-5] + '.png'
                # Save the image as .png
                img.save(png_path, 'PNG')
                print(f"Converted {image_path} to {png_path}")
            return png_path
        else:
            # If the image is not .webp, return the original path
            return image_path
        
def test_generator(upload_dir="uploads", filename=None):    
    generator = SDXLLightningGenerator()
    prompt = "A steampunk-inspired octopus riding a unicycle made of clockwork gears, juggling neon cubes while floating in a bubble tea sea."    
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    result = generator.generate_image(prompt)
    
    if result:
        print(f"Image generated successfully. URL: {result}")
        return True
    else:
        print("Failed to generate image.")
        return False

if __name__ == "__main__":
    test_result = test_generator()
    print(f"Test {'passed' if test_result else 'failed'}")