import edge_tts
import asyncio
import os
import subprocess

class TTSClient:
    def __init__(self, voice="zh-CN-YunxiNeural", rate="+0%", volume="+0%"):
        """
        Initialize the TTS Client.
        
        :param voice: The voice to use (default: zh-CN-YunxiNeural).
                      Other options: zh-CN-XiaoxiaoNeural, zh-CN-YunyangNeural, etc.
        :param rate: Speed of speech (e.g., "+0%", "+10%", "-10%").
        :param volume: Volume of speech (e.g., "+0%", "+10%").
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def generate_audio(self, text, output_path):
        """
        Generates audio from text and saves it to the output path.
        """
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
        await communicate.save(output_path)

    def run_generate_audio(self, text, output_path):
        """
        Synchronous wrapper for generating audio.
        """
        asyncio.run(self.generate_audio(text, output_path))

    def generate_audio_with_subtitles(self, text, output_audio_path, output_sub_path):
        """
        Generates audio and subtitles (VTT) using edge-tts CLI.
        This is more reliable for obtaining aligned subtitles.
        """
        # Create a temporary text file for input
        temp_text_file = "temp_tts_input.txt"
        with open(temp_text_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Build command
        # python -m edge_tts --file "temp.txt" --voice "voice" --write-media "out.mp3" --write-subtitles "out.vtt"
        # Note: --rate and --volume might need to be passed differently or not supported in simple CLI arg parsing 
        # for all versions, but let's try standard args.
        
        cmd = [
            "python", "-m", "edge_tts",
            "--file", temp_text_file,
            "--voice", self.voice,
            "--rate", self.rate,
            "--volume", self.volume,
            "--write-media", output_audio_path,
            "--write-subtitles", output_sub_path
        ]
        
        try:
            print(f"Running TTS command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            # Clean up temp file
            if os.path.exists(temp_text_file):
                os.remove(temp_text_file)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running edge-tts: {e.stderr}")
            if os.path.exists(temp_text_file):
                os.remove(temp_text_file)
            return False

if __name__ == "__main__":
    # Test stub
    client = TTSClient()
    test_text = "你好，这是一段测试音频。欢迎使用抖音说书 Agent。"
    output_file = "test_audio.mp3"
    
    print(f"Generating audio to {output_file}...")
    client.run_generate_audio(test_text, output_file)
    print("Done.")
