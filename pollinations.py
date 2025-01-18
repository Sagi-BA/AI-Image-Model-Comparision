# import streamlit as st
# import requests
# from PIL import Image
# from io import BytesIO
# import pollinations as ai

# st.set_page_config(page_title="Image Generator", layout="wide")

# st.title("🎨 AI Image Generator")

# # Input section
# with st.form("image_generation_form"):
#     prompt = st.text_area("Enter your image description:", height=100)
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         width = st.number_input("Width", min_value=256, max_value=1024, value=768, step=128)
#     with col2:
#         height = st.number_input("Height", min_value=256, max_value=1024, value=768, step=128)
#     with col3:
#         seed = st.number_input("Seed", min_value=0, value=42, step=1)
    
#     generate_button = st.form_submit_button("Generate Image")

# # Function to generate image using pollinations API
# def generate_image(prompt, width, height, seed):
#     try:
#         # Method 1: Using direct API
#         image_url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}&model=flux"
#         response = requests.get(image_url)
#         if response.status_code == 200:
#             return Image.open(BytesIO(response.content)), image_url
        
#         # Method 2: Using pollinations package as fallback
#         model_obj = ai.Model()
#         image = model_obj.generate(
#             prompt=f'{prompt} {ai.realistic}',
#             model=ai.flux,
#             width=width,
#             height=height,
#             seed=seed
#         )
#         return image, image.url
    
#     except Exception as e:
#         st.error(f"Error generating image: {str(e)}")
#         return None, None

# # Generate and display image
# if generate_button and prompt:
#     with st.spinner("Generating your image... Please wait"):
#         image, image_url = generate_image(prompt, width, height, seed)
        
#         if image:
#             # Display the generated image
#             st.image(image, caption="Generated Image", use_column_width=True)
            
#             # Create download buttons
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 # Convert PIL Image to bytes for download
#                 img_byte_arr = BytesIO()
#                 image.save(img_byte_arr, format='PNG')
#                 img_byte_arr = img_byte_arr.getvalue()
                
#                 st.download_button(
#                     label="Download Image",
#                     data=img_byte_arr,
#                     file_name="generated_image.png",
#                     mime="image/png"
#                 )
            
#             with col2:
#                 st.markdown(f"[View Original URL]({image_url})")
            
#             # Display image details
#             with st.expander("Image Generation Details"):
#                 st.write(f"**Prompt:** {prompt}")
#                 st.write(f"**Dimensions:** {width}x{height}")
#                 st.write(f"**Seed:** {seed}")
# else:
#     st.info("Enter a prompt and click 'Generate Image' to create an image.")