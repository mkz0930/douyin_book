import os
import sys
from dotenv import load_dotenv

# Force load .env
load_dotenv()

# Override env for test
os.environ["IMAGE_PROVIDER"] = "local"
os.environ["LOCAL_IMAGE_URL"] = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.image_client import ImageClient

def test_local_generation():
    print("Initializing ImageClient with forced local provider...")
    client = ImageClient()
    
    if client.provider != "local":
        print(f"FAILED: Provider should be 'local', but got '{client.provider}'")
        return

    print(f"Provider: {client.provider}")
    print(f"URL: {client.local_url}")
    
    prompt = "A cute robot reading a book"
    output = "test_local.png"
    
    print(f"Attempting to generate image (Expect failure if no local server running)...")
    success = client.generate_image(prompt, output, width=512, height=512)
    
    if success:
        print("SUCCESS: Image generated successfully!")
    else:
        print("NOTE: Generation failed (Expected if no local SD server is running).")
        print("Make sure you are running Stable Diffusion WebUI with --api argument.")

if __name__ == "__main__":
    test_local_generation()
