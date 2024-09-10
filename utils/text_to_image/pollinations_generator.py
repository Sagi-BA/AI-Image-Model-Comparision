import requests
from PIL import Image
import io
import sys, os
from urllib.parse import quote
import base64

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

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

    def generate_image(self, prompt, model_name):
        encoded_prompt = quote(prompt)
        url = self.pollinations_url.format(prompt=encoded_prompt, model=model_name)
        
        try:
            uploader = ImgurUploader()
            image_url = uploader.upload_media_to_imgur(
                 self.convert_image_url_to_base64(url), 
                 "image",
                 model_name,  # Title
                 prompt  # Description
            )
            return image_url 
        except requests.exceptions.RequestException as e:
            print(f"Error generating image with Pollinations: {e}")
            return None    

    @staticmethod
    def convert_image_url_to_base64(image_url):
        try:
            # Send a GET request to the image URL
            response = requests.get(image_url)
            response.raise_for_status()  # Check if the request was successful
            
            # Open the image from the response content
            img = Image.open(io.BytesIO(response.content))
            
            # Convert the image to base64
            buffered = io.BytesIO()
            img.save(buffered, format=img.format)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return image_base64
        except Exception as e:
            print(f"Failed to convert image from URL: {image_url}")
            print(f"Error: {str(e)}")
            return None

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt}"
    response = requests.get(url)
    with open('generated_image.jpg', 'wb') as file:
        file.write(response.content)
    print('Image downloaded!')



# Failed to convert image from URL: https://image.pollinations.ai/prompt/Close-up%20of%20the%20face%20of%20a%20gruff%20old%20fisherman%2C%20with%20deep%20wrinkles%2C%20wearing%20a%20yellow%20raincoat%20and%20a%20woolen%20hat%2C%20against%20a%20background%20of%20a%20stormy%20sea?model=turbo&width=1280&height=720&seed=42&nologo=true&enhance=true

# download_image("conceptual_isometric_world_of_pollinations_ai_surreal_hyperrealistic_digital_garden")

def test(upload_dir="uploads", model_name="turbo", filename=None):    
    generator = PollinationsGenerator()
    prompt = "A fast red color car"    
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    dest_path = os.path.join(upload_dir, filename)

    image_url = generator.generate_image(prompt, model_name)
    return image_url

    # if image_url:        
    #     if filename:
    #         dest_path = os.path.join(upload_dir, filename)
    #     else:
    #         dest_path = os.path.join(upload_dir, filename)

    #     print(f"Image generated successfully and saved as '{dest_path}'")
    #     return True
    # else:
    #     print(f"Failed to generate image or unexpected result: {base64result}")
    #     return False        

if __name__ == "__main__":
    test_result = test("uploads", "turbo", "pollinations_generator.png")
    print(f"Test {'passed' if test_result else 'failed'}")        