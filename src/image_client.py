import requests
import os
import sys
import base64
from io import BytesIO
from PIL import Image

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import API_KEY, BASE_URL, IMAGE_MODEL, IMAGE_SIZE, HF_TOKEN

class ImageClient:
    def __init__(self):
        # We can support multiple backends.
        # If HF_TOKEN is present, we prefer HF inference API for HF models.
        # Otherwise we try SiliconFlow.
        self.use_hf = False
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.model = IMAGE_MODEL
        
        if HF_TOKEN and "stabilityai" in IMAGE_MODEL:
             self.use_hf = True
             self.api_key = HF_TOKEN
             # Updated endpoint
             self.base_url = "https://router.huggingface.co/hf-inference/models" 
             print(f"Using Hugging Face Inference API for model: {self.model}")
        elif not API_KEY:
            # If no SiliconFlow key, and no HF token, we can try public HF API without token (might fail)
            if "stabilityai" in IMAGE_MODEL:
                 self.use_hf = True
                 self.base_url = "https://router.huggingface.co/hf-inference/models"
                 print(f"Using Public Hugging Face Inference API (No Token) for model: {self.model}")
            else:
                raise ValueError("API_KEY not found. Please check your .env file.")
        
    def generate_image(self, prompt, output_path):
        """
        Generates an image from prompt and saves it to output_path.
        """
        if self.use_hf:
            return self._generate_image_hf(prompt, output_path)
        else:
            return self._generate_image_siliconflow(prompt, output_path)

    def _generate_image_hf(self, prompt, output_path):
        url = f"{self.base_url}/{self.model}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {"inputs": prompt}
        
        try:
            print(f"Generating image (HF) with prompt: {prompt[:50]}...")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # HF returns raw bytes for image usually
            image = Image.open(BytesIO(response.content))
            image.save(output_path)
            return True
        except Exception as e:
            print(f"Error generating image (HF): {e}")
            if 'response' in locals():
                # HF errors are often JSON
                try:
                    print(f"Response error: {response.json()}")
                except:
                    print(f"Response content: {response.text}")
            return False

    def _generate_image_siliconflow(self, prompt, output_path):
        url = f"{self.base_url}/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "image_size": IMAGE_SIZE,
            "batch_size": 1,
            "num_inference_steps": 20, 
            "guidance_scale": 7.5
        }
        
        try:
            print(f"Generating image (SF) with prompt: {prompt[:50]}...")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                image_data = data['data'][0]
                
                if 'url' in image_data:
                    image_url = image_data['url']
                    img_response = requests.get(image_url)
                    image = Image.open(BytesIO(img_response.content))
                    image.save(output_path)
                    return True
                elif 'b64_json' in image_data:
                    import base64
                    img_bytes = base64.b64decode(image_data['b64_json'])
                    image = Image.open(BytesIO(img_bytes))
                    image.save(output_path)
                    return True
            
            print(f"Unexpected response format: {data}")
            return False
            
        except Exception as e:
            print(f"Error generating image (SF): {e}")
            if 'response' in locals():
                print(f"Response content: {response.text}")
            return False

if __name__ == "__main__":
    # Test stub
    try:
        client = ImageClient()
        test_prompt = "A dreamy illustration of a little prince standing on a small planet, starry night background, soft lighting"
        output_file = "test_image.jpg"
        client.generate_image(test_prompt, output_file)
        print(f"Image saved to {output_file}")
    except Exception as e:
        print(f"Test failed: {e}")
