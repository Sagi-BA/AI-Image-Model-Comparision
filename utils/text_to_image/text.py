import requests

API_URL = "https://api-inference.huggingface.co/models/khalilRehman/lale"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.content
image_bytes = query({
	"inputs": "Close-up of the face of a gruff old fisherman, with deep wrinkles, wearing a yellow raincoat and a woolen hat, against a background of a stormy sea",
})
# You can access the image with PIL.Image for example
import io
from PIL import Image
image = Image.open(io.BytesIO(image_bytes))
image.show()
