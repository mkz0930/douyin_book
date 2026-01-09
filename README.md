# 抖音说书 Agent (Douyin Book Agent)

这是一个全自动化的智能 Agent，旨在帮助创作者将书籍内容快速转化为适合抖音传播的短视频。它利用大语言模型 (LLM) 进行内容分析与脚本创作，结合 TTS 语音合成与自动化剪辑技术，实现从“一本电子书”到“一个成片视频”的流水线生产。

## 🚀 功能特点

- **智能脚本创作**: 自动提取书籍核心观点，生成符合抖音爆款逻辑的口播文案。
- **多模态生成**: 
  - **文案**: 自动生成脚本。
  - **语音**: 集成 Edge-TTS，生成逼真的旁白配音。
  - **字幕**: 自动生成与语音对齐的 SRT/VTT 字幕。
  - **视觉**: AI 生成相关配图，或使用动态文字/背景图。
- **自动化剪辑**: 使用 MoviePy 自动合成视频、音频、字幕与背景音乐。
- **自动上传**: 支持扫码登录抖音创作平台，自动上传草稿（含标题、封面）。

## 🛠️ 环境准备

1. **克隆项目**
   ```bash
   git clone <repository_url>
   cd douyin_book
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装 Playwright 浏览器 (用于上传功能)**
   ```bash
   playwright install
   ```

4. **配置环境变量**
   复制 `.env.example` 为 `.env`，并填入必要的 API Key (如 SiliconFlow, OpenAI 等)。
   ```bash
   cp .env.example .env
   ```
   *注意: 必须配置 LLM 相关 Key 才能生成脚本。*

## 📖 使用指南

### 1. 准备素材
将你需要制作视频的书籍文本文件 (`.txt`) 放入 `data/` 目录。
* 可选: 在 `data/` 目录下放置 `background.jpg` 作为默认背景图。
* 可选: 在 `data/` 目录下放置 `bgm.mp3` 作为背景音乐。

### 2. 登录抖音 (仅首次或 Cookies 失效时需要)
如果你需要使用自动上传功能，请先运行登录脚本：
```bash
python src/login_douyin.py
```
* 运行后会弹出浏览器，请用抖音 App 扫码登录。
* 登录成功后，Cookies 会自动保存到 `douyin_cookies.json`。

### 3. 运行主程序
执行主程序开始生成视频：
```bash
python src/main.py
```

## 🔄 详细执行流程 (每一步的输入输出)

程序按以下顺序自动执行，你也可以通过命令行参数跳过某些步骤：

**1. 脚本生成 (Script Generation)**
* **执行逻辑**: 读取书籍文本，调用 LLM 生成适合抖音的口播文案。
* **输入**: `data/<book_name>.txt`
* **输出**: `output/script_<book_name>.txt`
* **参数**: `--skip-llm` (跳过此步，使用已有脚本)

**2. 图像生成 (Image Generation)**
* **执行逻辑**: 根据脚本内容生成 AI 绘画提示词，并调用绘图模型生成封面/背景图。
* **输入**: 脚本内容
* **输出**: `output/image_<book_name>.jpg`
* **参数**: `--skip-image` (跳过此步，使用已有图片或默认背景)

**3. 语音与字幕生成 (TTS & Subtitles)**
* **执行逻辑**: 使用 Edge-TTS 将脚本转为语音，并生成时间轴对齐的字幕文件。
* **输入**: 清洗后的脚本
* **输出**: 
  - `output/audio_<book_name>.mp3` (音频)
  - `output/audio_<book_name>.vtt` (字幕)
* **参数**: `--skip-tts` (跳过此步，使用已有音频)

**4. 视频合成 (Video Composition)**
* **执行逻辑**: 将音频、字幕、背景图（或 AI 图片）、背景音乐合成最终视频。
* **输入**: 音频、字幕、图片、BGM (`data/bgm.mp3`)
* **输出**: `output/video_<book_name>.mp4`
* **参数**: `--skip-video` (跳过此步，使用已有视频)

**5. 自动上传 (Upload)**
* **执行逻辑**: 调用 Playwright 模拟浏览器，使用保存的 Cookies 登录并上传视频。
* **输入**: 最终视频文件、标题、封面
* **输出**: 抖音创作者中心草稿箱中的新条目
* **参数**: 必须添加 `--upload` 参数才会执行

## 📂 目录结构说明

### 输入 (data/)
* **目录**: `data/`
* **文件**: 
  * `*.txt`: 书籍原始内容 (必须)。
  * `background.jpg`: 默认背景图 (可选)。
  * `bgm.mp3` / `bgm.wav`: 背景音乐 (可选)。

### 输出 (Output)
* **目录**: `output/`
* **文件**:
  * `script_<book_name>.txt`: LLM 生成的口播脚本。
  * `image_<book_name>.jpg`: AI 生成或选用的视频封面/背景。
  * `audio_<book_name>.mp3`: TTS 生成的语音文件。
  * `audio_<book_name>.vtt`: 字幕文件。
  * `video_<book_name>.mp4`: 最终合成的视频文件。

## 🧩 模块说明

* **src/main.py**: 主程序入口，串联各个模块。
* **src/llm_client.py**: 调用大模型生成脚本与绘画提示词。
* **src/tts_client.py**: 处理语音合成与字幕生成。
* **src/image_client.py**: 调用绘图接口生成封面。
* **src/video_gen.py**: 视频合成逻辑 (MoviePy)。
* **src/douyin_uploader.py**: 抖音上传自动化 (Playwright)。
* **src/login_douyin.py**: 抖音扫码登录工具。

## 📝 常见问题

1. **TTS 生成失败?**
   请检查网络连接，Edge-TTS 需要访问外网。
2. **视频合成慢?**
   视频渲染需要消耗 CPU/GPU 资源，请耐心等待。
3. **上传失败?**
   检查 `douyin_cookies.json` 是否存在且未过期，必要时重新运行 `login_douyin.py`。
