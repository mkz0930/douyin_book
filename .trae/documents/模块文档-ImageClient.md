# 模块文档 - ImageClient

**文件**: `src/image_client.py`

**职责**
- 调用图像生成后端，生成背景图片并保存到指定路径。

**后端支持**
- Hugging Face Inference（`stabilityai/stable-diffusion-xl-base-1.0`）。
- SiliconFlow 图像生成接口（`/images/generations`）。

**配置**
- 环境变量：`HF_TOKEN`（可选，提升速率与稳定性）、`IMAGE_MODEL`、`LLM_API_KEY`、`LLM_BASE_URL`。
- 图片尺寸：`IMAGE_SIZE = "1024x1024"`。

**主要接口**
- `generate_image(prompt, output_path)`: 输入英文 Prompt，生成图片保存到 `output_path`。

**使用示例**
```python
from src.image_client import ImageClient
client = ImageClient()
ok = client.generate_image("Dreamy storybook illustration of ...", "output/image_xxx.jpg")
```

**注意事项**
- HF 后端返回字节流，直接保存为图片；SiliconFlow 返回 `url` 或 `b64_json`。
- 当无背景图可用时，视频生成模块会退化为纯色背景。

