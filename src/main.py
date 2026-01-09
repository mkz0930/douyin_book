import os
import sys
import glob
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_client import LLMClient
from src.tts_client import TTSClient
from src.video_gen import VideoGenerator
from src.image_client import ImageClient
from src.config import TTS_VOICE, TTS_RATE, TTS_VOLUME
from src.utils import clean_script, parse_vtt
from src.douyin_uploader import DouyinUploader

def main():
    parser = argparse.ArgumentParser(description="Douyin Book Agent - Main Pipeline")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM generation and use existing script files")
    parser.add_argument("--skip-tts", action="store_true", help="Skip TTS generation and use existing audio files")
    parser.add_argument("--skip-image", action="store_true", help="Skip Image generation and use existing image files")
    parser.add_argument("--skip-video", action="store_true", help="Skip Video generation and use existing video files")
    parser.add_argument("--upload", action="store_true", help="Upload the generated video to Douyin draft")
    args = parser.parse_args()

    # 1. Initialize Clients
    try:
        llm_client = LLMClient()
        tts_client = TTSClient(voice=TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
        image_client = ImageClient()
        video_gen = VideoGenerator()
        uploader = DouyinUploader()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # 2. Setup Directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 3. Process Logic
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"Found {len(txt_files)} files to process.")

    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        script_path = os.path.join(output_dir, f"script_{base_name}.txt")
        audio_path = os.path.join(output_dir, f"audio_{base_name}.mp3")
        vtt_path = os.path.join(output_dir, f"audio_{base_name}.vtt")
        video_path = os.path.join(output_dir, f"video_{base_name}.mp4")
        image_path = os.path.join(output_dir, f"image_{base_name}.jpg")

        script_content = ""

        # Step A: Generate Script (or read existing)
        if args.skip_llm and os.path.exists(script_path):
            print(f"Skipping LLM, reading existing script: {script_path}")
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()
        else:
            print(f"Processing Text: {file_name}...")
            # ... (Reading logic remains same, but better to be safe)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 10000: content = content[:10000]
            
            if not args.skip_llm: # Only generate if not skipped
                script_content = llm_client.generate_script(content)
                if script_content:
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(script_content)
                    print(f"Script saved to: {script_path}")
                else:
                    print(f"Failed to generate script for {file_name}")
                    continue

        # Clean script for TTS (remove headers, etc.)
        cleaned_script = clean_script(script_content)
        if not cleaned_script:
            print("Script is empty after cleaning!")
            continue

        # Step B: Generate Image (AI Art)
        # For MVP, we generate one image based on the first paragraph or summary
        if args.skip_image and os.path.exists(image_path):
            print(f"Skipping Image Gen, using existing image: {image_path}")
        else:
            print(f"Generating Image for: {file_name}...")
            # Take first 300 chars for prompt generation context
            context = cleaned_script[:300] 
            image_prompt = llm_client.generate_image_prompt(context)
            
            if image_prompt:
                print(f"Generated Image Prompt: {image_prompt}")
                success = image_client.generate_image(image_prompt, image_path)
                if success:
                    print(f"Image saved to: {image_path}")
                else:
                    print("Failed to generate image, falling back to default.")
            else:
                print("Failed to generate image prompt.")

        # Step C: Generate Audio & Subtitles
        audio_exists = os.path.exists(audio_path)
        vtt_exists = os.path.exists(vtt_path)
        
        if args.skip_tts and audio_exists:
            print(f"Skipping TTS, using existing audio: {audio_path}")
        else:
            print(f"Generating Audio & Subtitles for: {file_name}...")
            # Use the CLI-based method to get subtitles
            success = tts_client.generate_audio_with_subtitles(cleaned_script, audio_path, vtt_path)
            if success:
                print(f"Audio saved to: {audio_path}")
                print(f"Subtitles saved to: {vtt_path}")
                audio_exists = True
                vtt_exists = True
            else:
                print(f"Failed to generate audio/subtitles.")
                audio_exists = False
        
        # Step D: Generate Video (Simple)
        if audio_exists:
            # Use generated image if exists, else default background, else black
            bg_path = image_path if os.path.exists(image_path) else os.path.join(input_dir, "background.jpg")
            if not os.path.exists(bg_path):
                bg_path = None # Will use black screen
            
            # Check for BGM
            bgm_path = os.path.join(input_dir, "bgm.mp3")
            if not os.path.exists(bgm_path):
                bgm_path = os.path.join(input_dir, "bgm.wav") # Try wav
                if not os.path.exists(bgm_path):
                    bgm_path = None

            # Pass VTT path if available
            if args.skip_video and os.path.exists(video_path):
                print(f"Skipping Video Gen, using existing video: {video_path}")
            else:
                print(f"Generating Video for: {file_name}...")
                success = video_gen.generate_simple_video(
                    audio_path, 
                    script_content, # Not used directly if vtt is present
                    video_path, 
                    bg_image_path=bg_path,
                    vtt_path=vtt_path if vtt_exists else None,
                    bgm_path=bgm_path
                )
                if success:
                    print(f"Video saved to: {video_path}")
                else:
                    print("Failed to generate video.")
                    video_path = None # Mark as failed
        else:
             if args.upload and os.path.exists(video_path):
                 print(f"Audio missing but video exists. Using existing video: {video_path}")
             else:
                 video_path = None

        # Step E: Upload to Douyin (Optional)
        if args.upload and video_path and os.path.exists(video_path):
            print("Starting Douyin Upload Process...")
            # Extract title from script or filename
            # Simple title: Book Name + "读后感"
            # Or use the first line of script
            title = f"《{base_name}》深度解读"
            tags = ["读书", "推荐", "知识", "正能量"]
            
            # Use the generated image as cover if available
            cover_path = image_path if os.path.exists(image_path) else None
            
            uploader.upload(video_path, title, tags=tags, cover_path=cover_path)

if __name__ == "__main__":
    main()
