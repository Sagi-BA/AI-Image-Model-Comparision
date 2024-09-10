import sys, os
from gradio_client import Client
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_fixed
import base64

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

class HandDrawnCartoonGenerator:
    def __init__(self):
        # https://huggingface.co/spaces/fujohnwang/alvdansen-littletinies
        self.client = Client("fujohnwang/alvdansen-littletinies")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt, model_name="Hand drawn cartoon style"):
        try:            
            print(f"Attempting to connect to alvdansen-littletinies generate image with prompt: {prompt}")

            result = self.client.predict(prompt, api_name="/predict") #return the image path for example: "C:\Users\nerom\AppData\Local\Temp\gradio\3b0fa64204cf190d1fa77b49010b28c50a662ece\image.webp"
            print(f"Image generated at: {result}")

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
            print(f"Error generating hand-drawn cartoon image: {e}")
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
    
def test(upload_dir="uploads", filename=None):    
    generator = HandDrawnCartoonGenerator()
    prompt = "A steampunk-inspired octopus riding a unicycle made of clockwork gears, juggling neon cubes while floating in a bubble tea sea."    
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    dest_path = os.path.join(upload_dir, filename)

    image_url = generator.generate_image(prompt)
    return image_url

    # if base64result:        
    #     if filename:
    #         dest_path = os.path.join(upload_dir, filename)
    #     else:
    #         dest_path = os.path.join(upload_dir, "hand_drawn_cartoon_test_output.png")

    #     #  # Decode the base64 string and write it to a file
    #     # with open(dest_path, "wb") as the_file:
    #     #     the_file.write(base64.b64decode(base64result))

    #     print(f"Image generated successfully and saved as '{dest_path}'")
    #     return True
    # else:
    #     print(f"Failed to generate image or unexpected result: {base64result}")
    #     return False        

if __name__ == "__main__":
    test_result = test("uploads", "hand_drawn_cartoon_test_output.png")
    print(f"Test {'passed' if test_result else 'failed'}")