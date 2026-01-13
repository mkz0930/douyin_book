import requests
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "stabilityai/sdxl-turbo"

urls = [
    f"https://router.huggingface.co/hf-inference/models/{MODEL}",
    f"https://router.huggingface.co/models/{MODEL}",
    f"https://api-inference.huggingface.co/models/{MODEL}"
]

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

for url in urls:
    print(f"Testing {url}...")
    try:
        resp = requests.post(url, json={"inputs": "test"}, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
