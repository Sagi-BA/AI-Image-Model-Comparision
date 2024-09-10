import os
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

class StableDiffusion:
    def __init__(self):
        model_id = "stabilityai/stable-diffusion-2"
        scheduler = EulerDiscreteScheduler.from_pretrained(model_id, subfolder="scheduler")
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id, 
            scheduler=scheduler, 
            torch_dtype=torch_dtype
        )
        self.pipe = self.pipe.to(device)
        
        print(f"Using device: {device}")

    def generate_image(self, prompt):
        try:
            image = self.pipe(prompt).images[0]
            return image
        except Exception as e:
            print(f"Error generating image: {e}")
            return None

def test_generator(upload_dir="uploads", filename=None):    
    generator = StableDiffusion()
    prompt = "A small cabin on top of a snowy mountain in the style of Disney, artstation"    
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    dest_path = os.path.join(upload_dir, filename)

    img = generator.generate_image(prompt)
    
    if img:        
        img.save(dest_path)
        print(f"Image generated successfully and saved as: '{dest_path}'")
        
        return True
    else:
        print("Failed to generate image")
        return False

if __name__ == "__main__":
    test_result = test_generator("uploads", "stable_diffusion_2.png")
    print(f"Test {'passed' if test_result else 'failed'}")