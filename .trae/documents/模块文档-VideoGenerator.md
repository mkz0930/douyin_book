# 模块文档 - VideoGenerator

**文件**: `src/video_gen.py`

**职责**
- 将配音音频、背景图与字幕合成为竖屏视频（1080x1920）。
- 支持背景音乐（BGM）混音与循环。

**主要接口**
- `generate_simple_video(audio_path, script_text, output_path, bg_image_path=None, vtt_path=None, bgm_path=None)`。

**渲染细节**
- 背景图：自动裁切与缩放以适配竖屏。
- 字幕：基于 VTT 时间轴，PIL 生成半透明背景文本图片并叠加。
- BGM：按时长循环或截断，默认降音量至 10%。

**使用示例**
```python
from src.video_gen import VideoGenerator
vg = VideoGenerator()
ok = vg.generate_simple_video(
    "output/audio_xxx.mp3",
    "原始脚本文本",
    "output/video_xxx.mp4",
    bg_image_path="output/image_xxx.jpg",
    vtt_path="output/audio_xxx.vtt",
    bgm_path="data/bgm.wav"
)
```

**注意事项**
- 需要安装 FFmpeg 支持编码；MoviePy 会调用系统 FFmpeg。
- 字幕超出视频时长会被截断以保证合成成功。

