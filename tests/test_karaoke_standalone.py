
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, VideoClip

# Mock VideoGenerator for testing
class MockVideoGenerator:
    def __init__(self, output_width=500, output_height=200):
        self.width = output_width
        self.height = output_height
    
    def _create_text_image_np(self, text, fontsize, color, stroke_width, stroke_fill):
        # Simplified version of the method in video_gen.py
        img_w = self.width
        img_h = self.height
        img = Image.new('RGBA', (img_w, img_h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", fontsize)
        except:
            font = ImageFont.load_default()
            
        # Draw centered
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        x = (img_w - text_w) // 2
        y = (img_h - fontsize) // 2
        
        # Stroke
        for off_x in range(-stroke_width, stroke_width+1):
             for off_y in range(-stroke_width, stroke_width+1):
                 draw.text((x+off_x, y+off_y), text, font=font, fill=stroke_fill)
        # Main text
        draw.text((x, y), text, font=font, fill=color)
        
        return np.array(img)

    def create_karaoke_clip(self, text, duration, fontsize=50, color_base='white', color_active='yellow', stroke_width=2, stroke_fill='black'):
        # Paste the EXACT code from video_gen.py here to test logic
        
        # 1. Create Base Image (Unspoken color, e.g., White)
        img_base_np = self._create_text_image_np(text, fontsize, color_base, stroke_width, stroke_fill)
        clip_base = ImageClip(img_base_np).with_duration(duration)
        
        # 2. Create Active Image (Spoken color, e.g., Yellow)
        img_active_np = self._create_text_image_np(text, fontsize, color_active, stroke_width, stroke_fill)
        clip_active = ImageClip(img_active_np).with_duration(duration)
        
        # 3. Create Dynamic Wipe Mask
        w, h = clip_base.w, clip_base.h
        
        # FIX: Get original alpha to ensure we don't draw yellow box over empty space
        original_alpha = img_active_np[:, :, 3].astype(float) / 255.0
        
        def make_mask(t):
            wipe = np.zeros((h, w), dtype=float)
            
            if duration <= 0: progress = 1.0
            else: progress = t / duration
            progress = max(0.0, min(1.0, progress))
            
            reveal_w = int(w * progress)
            if reveal_w > 0:
                wipe[:, :reveal_w] = 1.0
            
            # Combine
            final_mask = wipe * original_alpha
            return final_mask

        # Apply mask to active clip
        from moviepy import VideoClip
        # MoviePy 2.x requires make_frame as the first positional argument
        # And 'is_mask' instead of 'ismask'
        mask_clip = VideoClip(make_mask, duration=duration, is_mask=True)
        clip_active = clip_active.with_mask(mask_clip)
        
        final_clip = CompositeVideoClip([clip_base, clip_active], size=(w,h))
        return final_clip

def test_karaoke():
    gen = MockVideoGenerator()
    text = "Hello Karaoke World!"
    duration = 3
    
    print("Generating Karaoke clip...")
    clip = gen.create_karaoke_clip(text, duration)
    
    # Write to a file to check visual
    output_file = "test_karaoke.mp4"
    # We need a background color to see white text
    bg = ColorClip(size=(500, 200), color=(50, 50, 50), duration=duration)
    final = CompositeVideoClip([bg, clip])
    
    final.write_videofile(output_file, fps=24)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    from moviepy import ColorClip
    test_karaoke()
