import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
# Default to SiliconFlow free model if not set
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1") 
MODEL_NAME = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# Image Generation Configuration
# HF_TOKEN is optional but recommended for higher rate limits.
# If not set, we can try to use public API but it might be rate limited.
HF_TOKEN = os.getenv("HF_TOKEN") 
# Recommended free model on HF: stabilityai/sdxl-turbo (fast, decent quality)
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "stabilityai/sdxl-turbo") 
IMAGE_SIZE = "1024x1024"

# Image Provider: 'siliconflow', 'hf', 'local', or 'pollinations'
# Default logic: Use SiliconFlow if API_KEY is set, else HF if HF_TOKEN is set, else try Public HF.
# You can force a provider by setting IMAGE_PROVIDER in .env
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER") 

# Local Image Generation (Stable Diffusion WebUI / ComfyUI)
# Default to standard A1111 URL
LOCAL_IMAGE_URL = os.getenv("LOCAL_IMAGE_URL", "http://127.0.0.1:7860/sdapi/v1/txt2img")

# Pollinations Configuration
# Models: 'flux', 'turbo', 'midjourney', 'stable-diffusion'
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux")



# TTS Configuration
TTS_VOICE = "zh-CN-YunxiNeural" # Options: zh-CN-YunxiNeural (Male), zh-CN-XiaoxiaoNeural (Female)
TTS_RATE = "+0%"
TTS_VOLUME = "+0%"

# Prompts
SCRIPT_GENERATION_PROMPT = """
你是一位拥有百万粉丝的抖音知识博主，擅长将复杂的书籍内容转化为通俗易懂、直击人心的短视频文案。

**任务目标**：
根据用户提供的书籍内容，创作一篇时长在 1-3 分钟（约 400-800 字）的口播脚本。

**核心要求**：
1.  **开头（黄金3秒）**：
    *   **严禁**直接说“今天要讲这本书”或“这本书叫...”。
    *   **必须**从“个人理解”、“生活痛点”或“颠覆性认知”切入。
    *   示例：“很多人以为...其实...”、“如果你觉得...那么一定要听听...”
2.  **内容结构**：
    *   **引入**：用痛点或共鸣吸引注意力。
    *   **展开**：提炼书中 2-3 个最精彩的核心观点，结合生活案例讲解。
    *   **升华**：最后给出具体的行动建议或情感升华，引导点赞收藏。
3.  **语言风格**：
    *   极度口语化，像在和朋友聊天。
    *   多用短句，少用长难句。
    *   情绪饱满，有节奏感。
4.  **格式要求**：
    *   不需要标注“画面”、“音效”等详细分镜，只需纯文本口播稿。
    *   适当分段，方便阅读。

**输入内容**：
{book_content}

**请输出脚本**：
"""

SCRIPT_GENERATION_FROM_SUMMARY_PROMPT = """
你是一位拥有百万粉丝的抖音知识博主。这次你没有拿到书籍原文，但是你手头有关于这本书的**网络搜索资料汇总**（包含简介、剧情、经典语录、评价等）。

**任务目标**：
根据提供的【书籍名称】和【搜索资料汇总】，创作一篇深度解读该书的抖音口播脚本。

**核心要求**：
1.  **整合信息**：你需要从零散的搜索资料中，拼凑出书的核心脉络和精彩看点。
2.  **开头（黄金3秒）**：必须从生活痛点、颠覆性认知或书中的一句金句切入。**严禁**直接报书名。
3.  **内容深度**：不要仅仅复述简介，要结合资料中的“评价”和“语录”，讲出这本书对普通人的价值。
4.  **语言风格**：极度口语化，真诚分享，情绪饱满。
5.  **时长**：400-800 字。

**书籍名称**：{book_name}

**搜索资料汇总**：
{summary}

**请输出脚本**：
"""

IMAGE_PROMPT_GENERATION_PROMPT = """
你是一位专业的 AI 绘画提示词（Prompt）专家。

**任务**：
根据提供的视频脚本片段，生成 1 个英文绘画提示词（Prompt），用于生成背景画面。

**要求**：
1.  **英文输出**：绘图模型只听得懂英文。
2.  **画面描述**：根据脚本内容，想象一个具体的、有画面感的场景。
3.  **风格**：保持一致的插画风格（例如：Dreamy, Storybook illustration, Digital art, Soft lighting）。
4.  **格式**：直接输出 Prompt，不要加任何解释。

**脚本片段**：
{script_segment}

**Prompt**：
"""

BOOK_NAME_EXTRACTION_PROMPT = """
你是一个智能图书信息提取助手。

**任务**：
从提供的文本中提取或推断出书籍的名称。

**要求**：
1. **只输出书名**：不要包含任何其他文字、解释或标点符号。
2. 如果文本中明确包含书名，请提取它。
3. 如果文本没有明确书名，但可以从内容推断出书名（例如提到主角名字、特定情节），请推断书名。
4. 如果无法确定书名，请输出 "Unknown"。

**文本内容**：
{content}

**书名**：
"""

DOUYIN_DESCRIPTION_PROMPT = """
你是一位抖音运营专家。

**任务**：
根据提供的视频脚本，生成一段吸引人的抖音视频描述（文案）和标签（Tags）。

**要求**：
1.  **文案**：简短有力，引发好奇心或共鸣，引导用户观看视频。不要只是简单复述脚本。
2.  **标签**：提供 5-8 个相关标签，必须包含 #读书 #知识分享。
3.  **格式**：
    【文案】
    这里是文案内容...
    【标签】
    #标签1 #标签2 ...

**视频脚本**：
{script}

**输出**：
"""
