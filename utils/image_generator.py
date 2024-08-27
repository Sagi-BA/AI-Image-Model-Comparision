import base64
import json
import requests

from base64 import b64encode
import os, sys
from dotenv import load_dotenv
import requests
from PIL import Image
from urllib.parse import quote

from .text_to_image.pollinations_generator import PollinationsGenerator  # Fixed line
from .text_to_image.sdxl_lightning_generator import SDXLLightningGenerator
from .text_to_image.hand_drawn_cartoon_generator import HandDrawnCartoonGenerator
from .text_to_video.animatediff_lightning_generator import AnimateDiffLightningGenerator

# Load environment variables from .env file
load_dotenv()

class ImageGenerator:
    def __init__(self):        
        self.imgur_client_id = os.getenv("IMGUR_CLIENT_ID")

    def generate_media(self, prompt, model):
        if model['generation_app'] == 'pollinations':
            pollinations_generator = PollinationsGenerator()
            return pollinations_generator.generate_image(prompt, model['name'])
        elif model['generation_app'] == 'hand_drawn_cartoon_style':
            hand_drawn_cartoon_generator = HandDrawnCartoonGenerator()
            return hand_drawn_cartoon_generator.generate_image(prompt)
        elif model['generation_app'] == 'animatediff_lightning':
            animatediff_lightning_generator = AnimateDiffLightningGenerator()
            return animatediff_lightning_generator.generate_image(prompt)        
        elif model['generation_app'] == 'sdxl_lightning':
            sdxl_lightning_generator = SDXLLightningGenerator()
            return sdxl_lightning_generator.generate_image(prompt)
        else:
            # Placeholder for other generation methods
            print(f"Image generation for {model['generation_app']} is not implemented")
            return None
