# # greenapi.py

# import requests
# import os
# from dotenv import load_dotenv
# from typing import Optional
# import json

# load_dotenv()

# class WhatsAppSender:
#     def __init__(self):
#         self.id_instance = os.getenv("GREEN_API_INSTANCE_ID")
#         self.api_token = os.getenv("GREEN_API_TOKEN")
#         if not self.id_instance or not self.api_token:
#             raise ValueError("GREEN_API_INSTANCE_ID and GREEN_API_TOKEN must be set in environment variables")
#         self.base_url = f"https://api.green-api.com/waInstance{self.id_instance}"

#     def _make_request(self, method: str, endpoint: str, json_data: dict = None) -> Optional[dict]:
#         url = f"{self.base_url}/{endpoint}/{self.api_token}"
#         try:
#             response = requests.request(method, url, json=json_data)
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error in WhatsApp API request: {str(e)}")
#             return None

#     def format_phone_number(self, phone: str) -> str:
#         """Remove any non-digit characters and ensure proper format"""
#         clean_number = ''.join(filter(str.isdigit, phone))
#         # If number starts with '0', replace it with country code '972'
#         if clean_number.startswith('0'):
#             clean_number = '972' + clean_number[1:]
#         elif not clean_number.startswith('972'):
#             clean_number = '972' + clean_number
#         return clean_number

#     def send_message(self, phone: str, message: str) -> bool:
#         """Send a text message to WhatsApp"""
#         formatted_phone = self.format_phone_number(phone)
#         json_data = {
#             "chatId": f"{formatted_phone}@c.us",
#             "message": message
#         }
#         result = self._make_request('POST', 'sendMessage', json_data)
#         return result is not None and 'idMessage' in result

#     def send_image(self, phone: str, image_url: str, caption: Optional[str] = None) -> bool:
#         """Send an image to WhatsApp using a URL"""
#         formatted_phone = self.format_phone_number(phone)
#         json_data = {
#             "chatId": f"{formatted_phone}@c.us",
#             "urlFile": image_url,
#             "caption": caption or ""
#         }
#         result = self._make_request('POST', 'sendFileByUrl', json_data)
#         return result is not None and 'idMessage' in result

#     def send_image_bytes(self, phone: str, image_bytes: bytes, caption: Optional[str] = None) -> bool:
#         """Send an image to WhatsApp using bytes data"""
#         formatted_phone = self.format_phone_number(phone)
#         # Convert image bytes to base64
#         import base64
#         base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
#         json_data = {
#             "chatId": f"{formatted_phone}@c.us",
#             "fileData": {
#                 "fileName": "generated_image.png",
#                 "base64Data": f"data:image/png;base64,{base64_image}"
#             },
#             "caption": caption or ""
#         }
#         result = self._make_request('POST', 'sendFileByBase64', json_data)
#         return result is not None and 'idMessage' in result

# Example usage
# if __name__ == "__main__":
#     sender = WhatsAppSender()
#     test_phone = "0549995050"
#     result = sender.send_message(test_phone, "Test message from Green API")
#     print(f"Message sent: {result}")
#########################

import requests
import os
from dotenv import load_dotenv
from typing import Optional
import base64
from io import BytesIO

load_dotenv()

class WhatsAppSender:
    def __init__(self):
        self.id_instance = os.getenv("GREEN_API_INSTANCE_ID")
        self.api_token = os.getenv("GREEN_API_TOKEN")
        if not self.id_instance or not self.api_token:
            raise ValueError("GREEN_API_INSTANCE_ID and GREEN_API_TOKEN must be set in environment variables")
        self.base_url = f"https://api.green-api.com/waInstance{self.id_instance}"

    def format_phone_number(self, phone: str) -> str:
        """Remove any non-digit characters and ensure proper format"""
        clean_number = ''.join(filter(str.isdigit, phone))
        # If number starts with '0', replace it with country code '972'
        if clean_number.startswith('0'):
            clean_number = '972' + clean_number[1:]
        elif not clean_number.startswith('972'):
            clean_number = '972' + clean_number
        return clean_number

    def send_image_from_bytesio(self, phone: str, image_bytesio: BytesIO, caption: Optional[str] = None) -> bool:
        """Send an image using file upload"""
        try:
            url = f"{self.base_url}/sendFileByUpload/{self.api_token}"
            
            # Format phone number
            formatted_phone = self.format_phone_number(phone)
            
            # Prepare payload
            payload = {
                'chatId': f'{formatted_phone}@c.us',
                'caption': caption or ''
            }
            
            # Prepare file
            image_bytesio.seek(0)
            files = [
                ('file', ('image.png', image_bytesio, 'image/png'))
            ]
            
            # Make request
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            
            print(f"Response from API: {response.text}")
            return True
            
        except Exception as e:
            print(f"Error sending image via WhatsApp: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    sender = WhatsAppSender()
    
    try:
        # Test phone number (replace with your test number)
        test_phone = "0549995050"  # Replace with your number
        
        # Load and send example image
        print(f"Opening example_image.png...")
        with open("example_image.png", "rb") as image_file:
            image_bytesio = BytesIO(image_file.read())
            
            print(f"Sending image to {test_phone}...")
            success = sender.send_image_from_bytesio(
                test_phone,
                image_bytesio,
                caption="Test image sent via Green API"
            )
            
            if success:
                print("✅ Image sent successfully!")
            else:
                print("❌ Failed to send image")
                
    except FileNotFoundError:
        print("❌ Error: example_image.png not found in current directory")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")