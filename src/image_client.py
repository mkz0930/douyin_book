import requests
import os
import sys
import base64
import time
import random
from io import BytesIO
from PIL import Image

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import API_KEY, BASE_URL, IMAGE_MODEL, IMAGE_SIZE, HF_TOKEN, IMAGE_PROVIDER, LOCAL_IMAGE_URL, POLLINATIONS_MODEL
import urllib.parse

class ImageClient:
    def __init__(self):
        # We can support multiple backends.
        # Priority: Configured IMAGE_PROVIDER > SiliconFlow (via API_KEY) > Hugging Face (via HF_TOKEN)
        
        self.api_key = API_KEY
        self.base_url = BASE_URL
        self.model = IMAGE_MODEL
        self.provider = "unknown"
        self.local_url = LOCAL_IMAGE_URL
        self.pollinations_model = POLLINATIONS_MODEL
        
        # Parse default image size
        self.default_width, self.default_height = self._parse_image_size(IMAGE_SIZE)
        
        # 1. Check explicit configuration
        if IMAGE_PROVIDER:
            if IMAGE_PROVIDER.lower() == "local":
                self.provider = "local"
                print(f"Using Local Image API at: {self.local_url}")
            elif IMAGE_PROVIDER.lower() == "pollinations":
                self.provider = "pollinations"
                print(f"Using Pollinations.AI API with model: {self.pollinations_model}")
            elif IMAGE_PROVIDER.lower() == "hf":
                self.provider = "hf"
                self.use_hf = True
                self.api_key = HF_TOKEN
                self.base_url = "https://router.huggingface.co/hf-inference/models"
                print(f"Using Hugging Face Inference API for model: {self.model}")
            elif IMAGE_PROVIDER.lower() == "siliconflow":
                self.provider = "siliconflow"
                self.use_hf = False
                print(f"Using SiliconFlow API for model: {self.model}")
        
        # 2. Auto-detect if not set
        if self.provider == "unknown":
            if self.api_key:
                self.provider = "siliconflow"
                self.use_hf = False
                print(f"Using SiliconFlow API for model: {self.model}")
            elif HF_TOKEN:
                self.provider = "hf"
                self.use_hf = True
                self.api_key = HF_TOKEN
                self.base_url = "https://router.huggingface.co/hf-inference/models"
                print(f"Using Hugging Face Inference API for model: {self.model}")
            else:
                # Fallback for public HF models
                if "stabilityai" in IMAGE_MODEL:
                     self.provider = "hf"
                     self.use_hf = True
                     self.base_url = "https://router.huggingface.co/hf-inference/models"
                     print(f"Using Public Hugging Face Inference API (No Token) for model: {self.model}")
                else:
                    # Last resort: try Pollinations if nothing else works? 
                    # For now, stick to explicit configuration to avoid unexpected behavior.
                    raise ValueError("API_KEY (SiliconFlow) or HF_TOKEN not found. Please check your .env file.")
    
    def _parse_image_size(self, size_str):
        try:
            width, height = map(int, size_str.lower().split('x'))
            return width, height
        except:
            return 1024, 1024

    def generate_image(self, prompt, output_path, negative_prompt=None, width=None, height=None, 
                       num_inference_steps=None, guidance_scale=None, seed=None):
        """
        Generates an image from prompt and saves it to output_path.
        
        Args:
            prompt (str): The prompt for image generation.
            output_path (str): Path to save the generated image.
            negative_prompt (str, optional): Negative prompt.
            width (int, optional): Image width. Defaults to config IMAGE_SIZE.
            height (int, optional): Image height. Defaults to config IMAGE_SIZE.
            num_inference_steps (int, optional): Number of inference steps.
            guidance_scale (float, optional): Guidance scale.
            seed (int, optional): Random seed.
        """
        # Use defaults if not provided
        width = width or self.default_width
        height = height or self.default_height
        
        # Default parameters if not specified
        # Note: Different models might have different optimal defaults
        steps = num_inference_steps or 25
        scale = guidance_scale or 7.5
        
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        print(f"Generating image with model {self.model}...")
        print(f"Size: {width}x{height}, Steps: {steps}, Scale: {scale}, Seed: {seed}")
        
        if self.provider == "local":
            return self._generate_image_local(prompt, output_path, negative_prompt, width, height, steps, scale, seed)
        elif self.provider == "pollinations":
            return self._generate_image_pollinations(prompt, output_path, negative_prompt, width, height, steps, scale, seed)
        elif self.provider == "hf":
            return self._generate_image_hf(prompt, output_path, negative_prompt, width, height, steps, scale, seed)
        else:
            return self._generate_image_siliconflow(prompt, output_path, negative_prompt, width, height, steps, scale, seed)

    def _generate_image_pollinations(self, prompt, output_path, negative_prompt, width, height, steps, scale, seed):
        """
        Generate image using Pollinations.AI API (Free, No Key).
        URL Format: https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&model={model}&nologo=true&seed={seed}
        """
        # Enhance prompt with negative prompt if provided, as Pollinations puts everything in URL
        full_prompt = prompt
        if negative_prompt:
             # Some models on Pollinations might support negative prompt via specific syntax or parameter, 
             # but usually appending "exclude [negative]" or similar works better for simple GET APIs.
             # However, Pollinations documentation suggests 'negative' parameter might not be standard across all their models.
             # We will try to pass it as a parameter if supported, or just ignore for now as GET URL param support is model-dependent.
             # Let's try adding it to the prompt for better compatibility: "... --no {negative_prompt}" is a common convention
             pass 

        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        params = {
            "width": width,
            "height": height,
            "model": self.pollinations_model, # 'flux', 'turbo', etc.
            "nologo": "true",
            "seed": seed,
            "enhance": "false" # Set to true to let them optimize prompt
        }
        
        # Pollinations usually doesn't strictly support 'steps' or 'guidance' in the GET API for all models,
        # but we can try passing them if they update their API. For now, we stick to core params.
        
        try:
            print(f"Requesting Pollinations.AI: {url} with params {params}")
            response = requests.get(url, params=params, timeout=60) # Generative AI can be slow
            response.raise_for_status()
            
            # Response is the image binary directly
            image = Image.open(BytesIO(response.content))
            image.save(output_path)
            print(f"Image saved to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating image (Pollinations): {e}")
            return False

    def _generate_image_local(self, prompt, output_path, negative_prompt, width, height, steps, scale, seed):
        """
        Generate image using local Stable Diffusion API (Automatic1111 / ComfyUI / SD.Next).
        Targeting /sdapi/v1/txt2img endpoint.
        """
        url = self.local_url
        headers = {"Content-Type": "application/json"}
        
        # A1111 payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": scale,
            "seed": seed,
            "sampler_name": "Euler a", # Configurable?
            "batch_size": 1
        }

        try:
            print(f"Requesting Local API at {url}...")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # A1111 returns {"images": ["base64string", ...]}
            if 'images' in data and len(data['images']) > 0:
                img_data = data['images'][0]
                img_bytes = base64.b64decode(img_data)
                image = Image.open(BytesIO(img_bytes))
                image.save(output_path)
                print(f"Image saved to {output_path}")
                return True
            else:
                print(f"Unexpected local response format: {data.keys()}")
                return False
                
        except Exception as e:
            print(f"Error generating image (Local): {e}")
            if 'response' in locals() and response is not None:
                print(f"Response: {response.text[:200]}")
            
            # Help user debug connection
            print("Tip: Ensure your local Stable Diffusion WebUI is running with '--api' flag.")
            return False

    def _generate_image_hf(self, prompt, output_path, negative_prompt, width, height, steps, scale, seed):
        url = f"{self.base_url}/{self.model}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # HF Inference API payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": negative_prompt or "blurry, bad quality, distorted",
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": scale,
                "seed": seed
            }
        }
        
        # Retry loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Requesting HF API (Attempt {attempt+1}/{max_retries})...")
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # HF returns raw bytes for image usually
                image = Image.open(BytesIO(response.content))
                image.save(output_path)
                print(f"Image saved to {output_path}")
                return True
            except Exception as e:
                print(f"Error generating image (HF) attempt {attempt+1}: {e}")
                if 'response' in locals() and response is not None:
                    try:
                        print(f"Response error: {response.json()}")
                    except:
                        print(f"Response content: {response.text}")
                
                if attempt < max_retries - 1:
                    time.sleep(2) # Wait before retry
                else:
                    return False

    def _generate_image_siliconflow(self, prompt, output_path, negative_prompt, width, height, steps, scale, seed):
        url = f"{self.base_url}/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "image_size": f"{width}x{height}",
            "batch_size": 1,
            "num_inference_steps": steps, 
            "guidance_scale": scale,
            "seed": seed
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        # Retry loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Requesting SiliconFlow API (Attempt {attempt+1}/{max_retries})...")
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
                        print(f"Image saved to {output_path}")
                        return True
                    elif 'b64_json' in image_data:
                        img_bytes = base64.b64decode(image_data['b64_json'])
                        image = Image.open(BytesIO(img_bytes))
                        image.save(output_path)
                        print(f"Image saved to {output_path}")
                        return True
                
                print(f"Unexpected response format: {data}")
                return False
                
            except Exception as e:
                print(f"Error generating image (SF) attempt {attempt+1}: {e}")
                if 'response' in locals() and response is not None:
                    try:
                        print(f"Response content: {response.text}")
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return False

if __name__ == "__main__":
    # Test stub
    try:
        client = ImageClient()
        test_prompt = "A dreamy illustration of a little prince standing on a small planet, starry night background, soft lighting"
        output_file = "test_image.jpg"
        
        # Test with new parameters
        print("Testing image generation with custom parameters...")
        client.generate_image(
            prompt=test_prompt, 
            output_path=output_file,
            negative_prompt="ugly, low quality, distorted, watermark, text",
            width=512,
            height=512, # Try smaller size for test speed
            num_inference_steps=20,
            guidance_scale=7.5
        )
        # print(f"Image saved to {output_file}") # Already printed in method
    except Exception as e:
        print(f"Test failed: {e}")
