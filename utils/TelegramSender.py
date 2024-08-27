from io import BytesIO
import os
import asyncio
import aiohttp
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment variables")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def verify_bot_token(self):
        url = f"{self.base_url}/getMe"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Failed to verify bot token. Status: {response.status}")
                        print(f"Response: {await response.text()}")
                        return False
                    data = await response.json()
                    print(f"Bot verified: {data['result']['first_name']} (@{data['result']['username']})")
                    return True
            except aiohttp.ClientError as e:
                print(f"Network error during bot token verification: {str(e)}")
                return False

    async def send_message(self, text: str) -> None:
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": text
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, params=params) as response:
                    if response.status != 200:
                        print(f"Failed to send message. Status: {response.status}")
                        print(f"Response: {await response.text()}")
                    else:
                        print("Message sent successfully")
            except aiohttp.ClientError as e:
                print(f"Network error during message sending: {str(e)}")

    async def send_image_and_text(self, image_path: str, caption: Optional[str] = None) -> None:
        url = f"{self.base_url}/sendPhoto"
        data = aiohttp.FormData()
        data.add_field("chat_id", self.chat_id)
        data.add_field("photo", open(image_path, "rb"))
        if caption:
            data.add_field("caption", caption)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        print(f"Failed to send image. Status: {response.status}")
                        print(f"Response: {await response.text()}")
                    else:
                        print("Image sent successfully")
            except aiohttp.ClientError as e:
                print(f"Network error during image sending: {str(e)}")

    async def send_pdf(self, pdf_buffer: BytesIO) -> None:
        url = f"{self.base_url}/sendDocument"
        data = aiohttp.FormData()
        data.add_field("chat_id", self.chat_id)
        data.add_field("document", pdf_buffer, filename="document.pdf", content_type="application/pdf")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        print(f"Failed to send PDF. Status: {response.status}")
                        print(f"Response: {await response.text()}")
                    else:
                        print("PDF sent successfully")
            except aiohttp.ClientError as e:
                print(f"Network error during PDF sending: {str(e)}")

async def main():
    try:
        sender = TelegramSender()
        
        # Print bot token (first 5 and last 5 characters) and chat ID for verification
        print(f"Bot Token: {sender.bot_token[:5]}...{sender.bot_token[-5:]}")
        print(f"Chat ID: {sender.chat_id}")
        
        # Verify bot token
        if not await sender.verify_bot_token():
            print("Bot token verification failed. Please check your TELEGRAM_BOT_TOKEN.")
            return

        # Send a simple text message
        await sender.send_message("Hello, this is a test message!")
        
        # Uncomment the following lines if you want to test sending an image
        image_path = "uploads/test.jpg"  # Replace with actual path to an image
        await sender.send_image_and_text(image_path, caption="Test image")
        
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())