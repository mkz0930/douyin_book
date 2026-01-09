from moviepy import VideoFileClip, AudioFileClip, TextClip, ColorClip, CompositeVideoClip, ImageClip, CompositeAudioClip
import os
import sys
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import parse_vtt
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoGenerator:
    def __init__(self, output_width=1080, output_height=1920):
        """
        Initialize Video Generator for Douyin (Vertical video).
        :param output_width: Width of the video (default 1080 for TikTok/Douyin)
        :param output_height: Height of the video (default 1920)
        """
        self.width = output_width
        self.height = output_height

    def generate_simple_video(self, audio_path, script_text, output_path, bg_image_path=None, vtt_path=None, bgm_path=None):
        """
        Generates a simple video with audio and a static background/text.
        """
        try:
            # 1. Load Voice Audio
            voice_audio = AudioFileClip(audio_path)
            duration = voice_audio.duration

            # 2. Setup Audio (Voice + BGM)
            final_audio = voice_audio
            if bgm_path and os.path.exists(bgm_path):
                try:
                    bgm = AudioFileClip(bgm_path)
                    # Loop BGM if shorter than video, or cut if longer
                    # In MoviePy 2.0+, loop is an effect.
                    # If we encounter issues, we can try manual looping by concatenation or just subclip if long enough
                    
                    if bgm.duration < duration:
                        # Manual loop: concatenate bgm with itself enough times
                        n_loops = int(duration / bgm.duration) + 1
                        bgm = CompositeAudioClip([bgm.with_start(i*bgm.duration) for i in range(n_loops)])
                        bgm = bgm.subclipped(0, duration)
                    else:
                        bgm = bgm.subclipped(0, duration)
                    
                    # Lower BGM volume
                    bgm = bgm.with_volume_scaled(0.1)
                    
                    # Mix voice and BGM
                    final_audio = CompositeAudioClip([voice_audio, bgm])
                except Exception as e:
                    print(f"Error processing BGM: {e}. Proceeding without BGM.")
                    import traceback
                    traceback.print_exc()

            # 3. Create Background
            if bg_image_path and os.path.exists(bg_image_path):
                # Use provided background image
                bg_clip = ImageClip(bg_image_path).with_duration(duration)
                # Resize to fill screen (crop if necessary)
                bg_clip = bg_clip.resized(height=self.height)
                if bg_clip.w < self.width:
                    bg_clip = bg_clip.resized(width=self.width)
                bg_clip = bg_clip.cropped(x_center=bg_clip.w/2, y_center=bg_clip.h/2, width=self.width, height=self.height)
            else:
                # Default black background
                bg_clip = ColorClip(size=(self.width, self.height), color=(0, 0, 0), duration=duration)

            # 4. Create Subtitles (if VTT provided)
            clips = [bg_clip]
            
            if vtt_path and os.path.exists(vtt_path):
                subs = parse_vtt(vtt_path)
                print(f"Parsed {len(subs)} subtitle lines.")
                
                # Create a clip for each subtitle
                # We use PIL to generate text images because TextClip requires ImageMagick
                for sub in subs:
                    start = sub['start']
                    end = sub['end']
                    text = sub['text']
                    
                    if end > duration: end = duration
                    
                    if start < end:
                        txt_clip = self.create_text_clip_pil(text, duration=end-start)
                        txt_clip = txt_clip.with_start(start).with_position(('center', 0.8), relative=True) # Bottom 20%
                        clips.append(txt_clip)

            # 5. Composite
            video = CompositeVideoClip(clips).with_audio(final_audio).with_duration(duration)
            
            # Write file
            video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            return True

        except Exception as e:
            print(f"Error generating video: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_text_clip_pil(self, text, duration, fontsize=60, color='white', bg_color='black'):
        """
        Creates a MoviePy clip from text using PIL.
        """
        # Create image with PIL
        # Estimate size: width=1000 (padding 40), height=auto
        img_w = self.width - 80
        
        # Use default font or try to find a system font
        # Windows font path example: C:/Windows/Fonts/msyh.ttc (Microsoft YaHei)
        font_path = "C:/Windows/Fonts/msyh.ttc"
        if not os.path.exists(font_path):
            font_path = "arial.ttf" # Fallback
            
        try:
            font = ImageFont.truetype(font_path, fontsize)
        except:
            font = ImageFont.load_default()

        # Calculate text size (multiline wrapping)
        lines = []
        words = text
        # Simple wrapping (naive)
        # For Chinese, we can split by characters mostly, but let's keep it simple: split by length
        # A better way requires measuring text width.
        
        current_line = ""
        for char in text:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w > img_w:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
            
        line_height = fontsize * 1.5
        img_h = int(len(lines) * line_height) + 40 # Padding
        
        # Create image
        img = Image.new('RGBA', (img_w, img_h), (0,0,0,128)) # Semi-transparent background
        draw = ImageDraw.Draw(img)
        
        y = 20
        for line in lines:
            draw.text((10, y), line, font=font, fill=color)
            y += line_height
            
        # Convert to numpy array for MoviePy
        img_np = np.array(img)
        
        return ImageClip(img_np).with_duration(duration)

if __name__ == "__main__":
    # Test Stub
    pass
