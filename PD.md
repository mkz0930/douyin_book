# 抖音说书 Agent 产品需求文档 (PRD)

## 1. 项目背景

用户希望开发一个智能 Agent，能够自动分析书籍内容，并生成适合抖音平台传播的短视频。该工具旨在通过 AI 自动化解决“读书难、做视频难”的痛点，帮助创作者快速产出高质量的读书类短视频。

## 2. 产品目标

* **自动化**: 从书籍输入到视频生成的全流程尽可能自动化。
* **高质量**: 生成的文案具有吸引力（黄金 3 秒原则），视频画面与内容匹配度高。
* **可定制**: 用户可以调整视频风格、时长、配音角色等。

## 3. 核心功能流程

1. **书籍输入**: 上传书籍文件 (PDF/EPUB/TXT)。
2. **智能分析**: Agent 阅读书籍，提取核心观点、精彩故事、金句。
3. **脚本创作**: 根据抖音爆款逻辑，将分析结果转化为口播文案（脚本）。
4. **素材生成**:
   * **语音合成 (TTS)**: 将脚本转化为语音。
   * **画面生成**: 根据脚本关键词生成 AI 图片或匹配素材库视频。
5. **视频合成**: 自动剪辑，将语音、画面、字幕、背景音乐合成视频。
6. **输出/发布**: 导出 MP4 文件或尝试对接抖音 API 发布。

## 4. 功能模块详情

### 4.1 输入模块

* 支持格式：PDF, EPUB, TXT, Markdown。
* 功能：文本清洗、章节拆分（用于长文本处理）。

### 4.2 内容分析 Agent (Brain)

* **角色**: 资深拆书稿作者。
* **能力**:
  * 提取书籍元数据（书名、作者、简介）。
  * 生成“一句话推荐”。
  * 提炼 3-5 个核心知识点或精彩情节。
  * 识别适合视觉化的场景描述。

### 4.3 脚本写作 Agent (Copywriter)

* **角色**: 抖音爆款文案写手。
* **能力**:
  * **个人视角引入**: 开头必须加入“个人理解”或“生活痛点”作为切入点，避免生硬的摘要堆砌。
  * **时长控制**: 目标时长 1-3 分钟（文案字数控制在 300-800 字之间）。
  * **黄金开头**: 生成吸引人的钩子（Hook）。
  * **口语化处理**: 将书面语转化为适合短视频的口语。
  * **情绪调动**: 在脚本中加入情绪标记。
  * **分镜设计**: 为每一段文案建议画面提示词 (Prompt)。

### 4.4 多媒体生成模块 (Media Factory)

* **配音 (TTS)**: 集成 Edge TTS, OpenAI TTS 或 CosyVoice。支持多种音色（深沉男声、知性女声等）。
* **视觉 (Visuals)**:
  * 方案 A (低成本): 动态文字视频 (字说模式)。
  * 方案 B (中成本): 书籍封面 + 关键图 + 缩放平移效果 (Ken Burns)。
  * 方案 C (高成本): 根据分镜提示词调用 AI 绘图模型 (Flux, SDXL, MJ) 生成画面。
* **字幕 (Subtitles)**: 自动生成 SRT/ASS 字幕，支持高亮关键词。

### 4.5 视频合成模块 (Editor)

* 技术栈推荐: FFmpeg, Python MoviePy。
* 功能: 音画对齐、自动配乐（根据情感）、转场效果。

## 5. 技术架构规划 (Tech Stack)

* **开发语言**: Python
* **大模型**: SiliconFlow + Qwen2.5-7B-Instruct（默认），可替换为 DeepSeek / GPT / Claude
* **TTS**: Edge-TTS（语音与字幕对齐，CLI 方式稳定）
* **文生图**: Hugging Face Inference（stabilityai/SDXL）或 SiliconFlow 图像生成
* **视频处理**: MoviePy + FFmpeg（竖屏 1080x1920 合成）
* **自动上传**: Playwright（扫码登录、保存 Cookies、草稿保存）
* **配置管理**: dotenv（`.env`）

## 6. 开发路线图 (Roadmap)

* **Phase 1 (MVP)**:
  * 输入 TXT 文本。
  * LLM 生成简短解说脚本。
  * Edge-TTS 生成语音与 VTT 字幕。
  * MoviePy 合成“静态底图/AI 图片 + 字幕 + 语音”的视频。
* **Phase 2 (进阶)**:
  * 支持 PDF 解析。
  * 引入 AI 绘图，实现“文生图”视频。
  * 优化脚本 Agent 的爆款逻辑。
* **Phase 3 (完善)**:
  * Web 界面 (Streamlit/Gradio)。
  * 支持背景音乐自动匹配。
  * 一键发布功能（如可行）。

## 7. 

## 8. 进度更新（2026-01-08）
- **MVP 完成**：已实现从 TXT 输入到脚本、语音（含字幕）、背景图（AI 生成或默认）、视频合成全流程，示例产出位于 `output/` 目录：
  - `script_little_prince.txt`、`audio_little_prince.mp3`、`audio_little_prince.vtt`、`image_little_prince.jpg`、`video_little_prince.mp4`
- **自动上传草稿**：已集成抖音创作平台上传草稿流程，支持扫码登录、Cookies 保存、标题与封面设置，代码参见 `src/douyin_uploader.py`。
- **实际技术选型**：
  - LLM：默认 SiliconFlow（`Qwen/Qwen2.5-7B-Instruct`），通过 `.env` 可替换。
  - 文生图：优先 Hugging Face Inference（`stabilityai/stable-diffusion-xl-base-1.0`），备选 SiliconFlow。
  - TTS：Edge-TTS（CLI 调用，稳健获取字幕）。
  - 视频：MoviePy 合成竖屏视频，支持 BGM 混音与字幕渲染。
 - **文档链接行为**：已统一为本地 `file://` 绝对路径，点击将在 IDE 中打开（2026-01-08）。

## 9. 进度更新（2026-01-09）
- **文档完善**: 补全了 `README.md`，详细记录了环境准备、安装步骤、使用指南（含命令行参数）、输入输出说明及常见问题。
- **项目结构清晰化**: 明确了 `data/` 为输入目录，`output/` 为输出目录的规范。
- **联网搜索功能**: 新增 `src/search_client.py`，支持对无内容书籍（仅书名）进行联网搜索，并生成脚本。
  - **多引擎支持**: 集成 DuckDuckGo (优先) 和 Google Search (`googlesearch-python`，备选) 双引擎，提高搜索成功率。
  - **稳定性优化**: 增加重试机制和多种后端模式 (API/HTML/Lite) 切换。
- **依赖更新**: 修复了 `ModuleNotFoundError`，安装了 `duckduckgo-search` 和 `googlesearch-python`。

## 10. 功能完成情况（2026-01-08）
- 输入模块：
  - TXT 文本输入与清洗（完成）
  - PDF/EPUB/Markdown 解析（未开始）
- 内容分析 Agent（Brain）：
  - 书籍元数据提取、核心观点提炼（未开始，当前仅使用统一提示词直接生成脚本）
- 脚本写作 Agent（Copywriter）：
  - 开头黄金 3 秒、口语化风格、节奏控制（部分完成，模板与提示词已纳入）
  - 分镜提示词（英文 Prompt）生成（完成）
- 多媒体生成模块（Media Factory）：
  - 配音 TTS（完成，音频与 VTT 字幕对齐）
  - 视觉画面（部分完成，支持单张 AI 图片生成；分镜多图与动画未实现）
  - 字幕（完成，VTT 解析与渲染）
- 视频合成模块（Editor）：
  - 竖屏 1080x1920 合成、BGM 混音、字幕叠加（完成）
- 输出/发布：
  - 网页端草稿上传（完成，扫码登录、Cookies 保存、标题与封面设置）
  - 一键发布（未开始，受平台限制评估中）
- 登录与稳定性：
  - 登录等待与轮询（完成，最长 10 分钟，已保存 Cookies）
- 配置与环境：
  - `.env` 配置管理与示例（完成）

## 11. 进度更新（2026-01-12）
- **智能书名提取**: 新增了从输入文档内容中自动提取书名的功能。
  - 在 `src/main.py` 流程中增加了 `extract_book_name` 步骤，利用 LLM 从文本前 2000 字符中提取书名。
  - 输出文件（脚本、音频、视频等）将优先使用提取到的书名（如 `找事`）而非输入文件名（如 `input`），提升了文件管理的语义化。
- **Bug 修复**: 修复了视频生成过程中 `MoviePy` 资源未正常释放导致的 `ResourceWarning` 和 `OSError: [WinError 6]` 问题。
  - 在 `src/video_gen.py` 中添加了显式的资源释放逻辑 (`finally` 块中关闭 `AudioFileClip`, `CompositeVideoClip` 等)。
  - 确保了 `ffmpeg` 子进程和文件句柄在视频生成后被正确关闭，避免了内存泄漏和文件占用报错。

## 12. 下一步计划（短期）
- 支持 PDF/EPUB 解析与章节拆分，完善输入模块。
- 优化脚本生成的爆款逻辑与节奏控制，加入更多模板与可配置参数。
- 提升字幕样式（高亮关键词、描边、半透明背景美化）。
- 自动选择/生成更贴合脚本的封面，并在上传时优先使用。
- 增加 Web 界面（Streamlit/Gradio），便于一键运行与参数配置。

## 13. 进度更新（2026-01-13）
- **图像生成能力增强**:
  - 新增 **本地 Stable Diffusion** 支持：通过 `.env` 配置 `IMAGE_PROVIDER=local` 可调用本地 WebUI API，实现免费无限生图。
  - 新增 **Pollinations.AI** 集成：支持免费、免 Key 的开源云端生图服务（`Flux` / `Turbo` 模型）。
- **视频效果升级**:
  - **卡拉OK字幕效果**: 字幕现在具有“逐字变色跟随”效果（白色 -> 金黄色），配合语音节奏，视觉引导性更强。
  - **字幕样式优化**: 字体改为更粗的样式，添加黑色描边，去除了半透明背景框，画面更通透。
  - **语句切分优化**: 强制根据标点符号换行，字幕展示更符合短视频阅读习惯。
- **工程结构优化**:
  - **输出目录重构**: 每个任务的输出文件（脚本、音频、视频等）现在会自动归类到 `output/<书名>/` 子目录下。
  - **自动归档**: 处理完成的输入文件会自动重命名为 `<书名>.txt` 并移动到 `data/history/` 目录，保持工作区整洁。

## 14. 功能文档索引
- 模块说明：
  - LLM 客户端：[模块文档-LLMClient](file:///d:/learn/douyin_book/.trae/documents/模块文档-LLMClient.md)
  - 图像生成：[模块文档-ImageClient](file:///d:/learn/douyin_book/.trae/documents/模块文档-ImageClient.md)
  - 语音合成与字幕：[模块文档-TTSClient](file:///d:/learn/douyin_book/.trae/documents/模块文档-TTSClient.md)
  - 视频合成：[模块文档-VideoGenerator](file:///d:/learn/douyin_book/.trae/documents/模块文档-VideoGenerator.md)
  - 抖音上传草稿：[模块文档-DouyinUploader](file:///d:/learn/douyin_book/.trae/documents/模块文档-DouyinUploader.md)
- 里程碑文档：
  - MVP 视频生成计划：[生成 MVP 视频](file:///d:/learn/douyin_book/.trae/documents/生成%20MVP%20视频.md)
  - 上传登录等待优化：[优化抖音上传登录等待逻辑](file:///d:/learn/douyin_book/.trae/documents/优化抖音上传登录等待逻辑.md)

## 15. 进度更新（2026-01-15）
- **环境配置优化**:
  - **Git 忽略规则更新**: 更新了 `.gitignore` 文件，添加了 `*.mp4` 规则，确保生成的视频文件不会被误上传到代码仓库。
  - **文档目录创建**: 创建了 `doc/` 目录，用于集中管理项目文档和更新记录。
  - **程序入口调整**: 将 `src/main.py` 移动到项目根目录 `main.py`，简化调用路径，无需再进入 `src` 目录运行。
- **脚本生成优化**:
  - 优化了 Prompt 中的“黄金 5 秒”策略，引入权威背书、痛点反差、颠覆认知等高完播率钩子。
  - 引入了“辩证视角”要求，要求从正反双角度解读书籍，增加内容深度。
- **多任务执行支持**:
  - 重构了 `main.py`，支持多任务队列执行。
  - **优先级策略**: 优先处理 `data/` 下的标准输入文件，随后处理 `data/todo/` 下的任务文件。
  - **Todo 队列归档**: 针对 `todo` 目录下的文件，处理完成后将内容归档至 `data/history/<书名>.txt`，并清空源文件内容（保留空文件）。
- **项目结构整理**:
  - 创建了 `tests/` 目录，将所有测试脚本（`test_*.py`）归类整理。
  - 更新了 `.gitignore`，将测试生成的临时文件（`.jpg`, `.mp3` 等）排除在版本控制之外。
