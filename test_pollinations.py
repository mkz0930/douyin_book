import os
import sys
from dotenv import load_dotenv

# Force load .env
load_dotenv()

# Override env for test
os.environ["IMAGE_PROVIDER"] = "pollinations"
os.environ["POLLINATIONS_MODEL"] = "flux" # Try 'flux' or 'turbo'

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.image_client import ImageClient

def test_pollinations_generation():
    print("Initializing ImageClient with forced pollinations provider...")
    client = ImageClient()
    
    if client.provider != "pollinations":
        print(f"FAILED: Provider should be 'pollinations', but got '{client.provider}'")
        return

    print(f"Provider: {client.provider}")
    print(f"Model: {client.pollinations_model}")
    
    prompt = "A cute cyberpunk cat wearing neon glasses, digital art"
    output = "test_pollinations.jpg"
    
    print(f"Attempting to generate image via Pollinations.AI...")
    success = client.generate_image(prompt, output, width=1024, height=1024, seed=42)
    
    if success:
        print(f"SUCCESS: Image generated successfully and saved to {output}!")
    else:
        print("FAILED: Image generation failed.")

if __name__ == "__main__":
    test_pollinations_generation()
