import os
import requests
from urllib.parse import urlencode

class UnsplashGenerator:
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.base_url = "https://api.unsplash.com/search/photos"
    
    def generate_image(self, query):
        # URL-encode the query
        encoded_query = urlencode({'query': query})
        url = f"{self.base_url}?{encoded_query}&client_id={self.access_key}"
        response = requests.get(url)
        data = response.json()
        if data['results']:
            return data['results'][0]['urls']['regular']
        return None

# Example usage
if __name__ == "__main__":
    unsplash = UnsplashGenerator()
    query = "A futuristic city with twisted glass and chrome skyscrapers, floating bridges, and flying cars between buildings glowing in neon colors"
    image_url = unsplash.generate_image(query)
    if image_url:
        print(f"Image URL for '{query}': {image_url}")
    else:
        print(f"No images found for '{query}'.")
