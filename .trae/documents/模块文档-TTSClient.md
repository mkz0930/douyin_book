# 模块文档 - TTSClient

**文件**: `src/tts_client.py`

**职责**
- 通过 Edge-TTS 生成配音音频与字幕（VTT）。

**配置**
- 语音：`zh-CN-YunxiNeural`（男声），可切换为 `zh-CN-XiaoxiaoNeural` 等。
- 速率与音量：`TTS_RATE`、`TTS_VOLUME`（见 `src/config.py`）。

**主要接口**
- `generate_audio_with_subtitles(text, mp3_path, vtt_path)`: 同步生成音频与 VTT 字幕，CLI 方式更稳健。
- `run_generate_audio(text, mp3_path)`: 仅生成音频（无字幕）。

**使用示例**
```python
from src.tts_client import TTSClient
tts = TTSClient()
ok = tts.generate_audio_with_subtitles("脚本文本...", "output/audio_xxx.mp3", "output/audio_xxx.vtt")
```

**注意事项**
- 生成字幕后，视频模块会按时间轴渲染底部半透明字幕条。
- Windows 环境下需确保 `python -m edge_tts` 可执行。

