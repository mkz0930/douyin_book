# 抖音说书 Agent - MVP 视频生成计划

我们将执行最后一步，将生成的脚本、音频和背景图合成为最终的 MP4 视频。

## 1. 执行命令
运行主程序，跳过 LLM 和 TTS 阶段，直接使用现有素材：
```powershell
python src/main.py --skip-llm --skip-tts
```

## 2. 预期产出
*   **输入**:
    *   脚本: `output/script_little_prince.txt`
    *   音频: `output/audio_little_prince.mp3`
    *   背景: `data/background.jpg` (深灰色背景)
*   **输出**:
    *   视频: `output/video_little_prince.mp4`
    *   规格: 1080x1920 (抖音竖屏), 24fps, H.264编码。

## 3. 验证
执行完成后，我们将检查 `output` 目录是否存在 `.mp4` 文件，并确认文件大小不为 0。