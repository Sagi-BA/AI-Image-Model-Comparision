import os, sys
from gradio_client import Client
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_fixed
import base64

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imgur_uploader import ImgurUploader

# https://huggingface.co/spaces/ByteDance/AnimateDiff-Lightning
class AnimateDiffLightningGenerator:
    def __init__(self):
        self.client = Client("ByteDance/AnimateDiff-Lightning")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def generate_image(self, prompt):
        try:
            print(f"Attempting to generate animation with prompt: {prompt}")
            
            # Try with different parameter combinations
            try:
                result = self.client.predict(
                    prompt,
                    api_name="/generate_image"
                )
            except ValueError:
                print("Trying alternative parameter structure...")
                # result = self.client.predict(
                #     prompt,
                #     api_name="/generate_image"
                # )
            
            print(f"Animation generated at: {result}")
            # return result['video']  # This should be the file path
            # Read the MP4 file and encode it in base64
            with open(result['video'], "rb") as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
            
            uploader = ImgurUploader()

            video_url = uploader.upload_media_to_imgur(
                 video_base64, 
                 "video",
                 "Hand drawn cartoon style",  # Title
                 prompt  # Description
            )

            return video_url
        
        except Exception as e:
            print(f"Error generating animation: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {e.args}")
            return None

def test_generator(upload_dir="uploads", filename=None):    
    generator = AnimateDiffLightningGenerator()
    prompt = "A steampunk-inspired octopus riding a unicycle made of clockwork gears, juggling neon cubes while floating in a bubble tea sea."    
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    video_url = generator.generate_image(prompt)
    
    # if base64result:  # If the result is not None or empty
    #     if filename:
    #         dest_path = os.path.join(upload_dir, filename)
    #     else:
    #         dest_path = os.path.join(upload_dir, "generated_animation.mp4")
        
    #     # Decode the base64 string and write it to a file
    #     with open(dest_path, "wb") as the_file:
    #         the_file.write(base64.b64decode(base64result))
        
    #     print(f"Animation generated successfully and saved as '{dest_path}'")
    #     return True
    # else:
    #     print(f"Failed to generate animation or unexpected result: {base64result}")
    #     return False

if __name__ == "__main__":
    test_result = test_generator("uploads", "AnimateDiff_Lightning.mp4")
    print(f"Test {'passed' if test_result else 'failed'}")