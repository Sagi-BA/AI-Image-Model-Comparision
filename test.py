import replicate
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

REPLICATE_API_TOKEN=os.environ["REPLICATE_API_TOKEN"]


prompt = "hello birdy"

output = replicate.run(
    "playgroundai/playground-v2.5-1024px-aesthetic:a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
    input={"prompt": prompt}
)
print(output)
#=> ["https://replicate.delivery/pbxt/XAK4XRgpjYaCGRrm9yxzO2b...