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
        voice_audio = None
        bgm_source = None
        bg_clip = None
        video = None
        
        try:
            # 1. Load Voice Audio
            voice_audio = AudioFileClip(audio_path)
            duration = voice_audio.duration

            # 2. Setup Audio (Voice + BGM)
            final_audio = voice_audio
            if bgm_path and os.path.exists(bgm_path):
                try:
                    bgm_source = AudioFileClip(bgm_path)
                    bgm = bgm_source
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
                        # Use Karaoke Clip
                        # color_base='white', color_active='#FFD700' (Gold)
                        txt_clip = self.create_karaoke_clip(text, duration=end-start, color_base='white', color_active='#FFD700')
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
        finally:
            # Explicitly close all clips to release resources (file handles, subprocesses)
            try:
                if video: video.close()
                if voice_audio: voice_audio.close()
                if bgm_source: bgm_source.close()
                if bg_clip: bg_clip.close()
            except Exception as e:
                print(f"Error closing clips: {e}")

    def create_karaoke_clip(self, text, duration, fontsize=70, color_base='white', color_active='#FFD700', stroke_width=4, stroke_fill='black'):
        """
        Creates a karaoke-style clip where text changes color progressively.
        Simulates "follow-along" effect using a wipe mask.
        """
        # 1. Create Base Image (Unspoken color, e.g., White)
        img_base_np = self._create_text_image_np(text, fontsize, color_base, stroke_width, stroke_fill)
        clip_base = ImageClip(img_base_np).with_duration(duration)
        
        # 2. Create Active Image (Spoken color, e.g., Yellow)
        img_active_np = self._create_text_image_np(text, fontsize, color_active, stroke_width, stroke_fill)
        clip_active = ImageClip(img_active_np).with_duration(duration)
        
        # 3. Create Dynamic Wipe Mask
        # The mask reveals the active clip from left to right over 'duration'
        w, h = clip_base.w, clip_base.h
        
        # NOTE: MoviePy masks should be grayscale (HxW) float in [0,1]
        # BUT ImageClip already has an alpha mask if loaded from RGBA.
        # We need to MULTIPLY the active clip's existing alpha with our wipe mask.
        # However, ImageClip.with_mask REPLACEs the mask.
        # So we must combine the wipe mask with the text's original alpha channel.
        
        # Get the original alpha channel from the text image (0 where no text, 255 where text is)
        # img_active_np is RGBA, so index 3 is alpha.
        original_alpha = img_active_np[:, :, 3].astype(float) / 255.0
        
        def make_mask(t):
            # Create the wipe mask (H, W)
            wipe = np.zeros((h, w), dtype=float)
            
            if duration <= 0: progress = 1.0
            else: progress = t / duration
            progress = max(0.0, min(1.0, progress))
            
            reveal_w = int(w * progress)
            if reveal_w > 0:
                wipe[:, :reveal_w] = 1.0
            
            # Combine wipe mask with original text alpha
            # This ensures we only show "Yellow" where there is text AND where the wipe has reached.
            # Otherwise, the wipe would show a yellow rectangle over transparent areas if we just used the wipe.
            final_mask = wipe * original_alpha
            return final_mask

        # Apply mask to active clip
        from moviepy import VideoClip
        # MoviePy 2.x requires make_frame as the first positional argument
        # And 'is_mask' instead of 'ismask'
        mask_clip = VideoClip(make_mask, duration=duration, is_mask=True)
        clip_active = clip_active.with_mask(mask_clip)
        
        # 4. Composite: Base + Active (masked)
        # The active clip is layered ON TOP of the base clip. 
        # Where mask is 1, we see Yellow. Where mask is 0, we see the underlying Base clip (White).
        final_clip = CompositeVideoClip([clip_base, clip_active], size=(w,h))
        return final_clip

    def _create_text_image_np(self, text, fontsize, color, stroke_width, stroke_fill):
        """
        Helper to generate the numpy image for text. Refactored from create_text_clip_pil.
        """
        img_w = self.width - 80
        
        # Font loading logic (same as before)
        font_paths = [
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "arialbd.ttf",
            "arial.ttf"
        ]
        font_path = "arial.ttf"
        for p in font_paths:
            if os.path.exists(p):
                font_path = p
                break
        try:
            font = ImageFont.truetype(font_path, fontsize)
        except:
            font = ImageFont.load_default()

        # Wrap text
        lines = []
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
        img_h = int(len(lines) * line_height) + 40 
        
        img = Image.new('RGBA', (img_w, img_h), (0,0,0,0)) 
        draw = ImageDraw.Draw(img)
        
        y = 20
        for line in lines:
            try:
                draw.text((10, y), line, font=font, fill=color, stroke_width=stroke_width, stroke_fill=stroke_fill)
            except TypeError:
                 for off_x in range(-stroke_width, stroke_width+1):
                     for off_y in range(-stroke_width, stroke_width+1):
                         draw.text((10+off_x, y+off_y), line, font=font, fill=stroke_fill)
                 draw.text((10, y), line, font=font, fill=color)
            y += line_height
            
        return np.array(img)

if __name__ == "__main__":
    # Test Stub
    pass
