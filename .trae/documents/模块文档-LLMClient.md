# 模块文档 - LLMClient

**文件**: `src/llm_client.py`

**职责**
- 基于书籍文本生成抖音口播脚本。
- 基于脚本片段生成 AI 绘图提示词（英文 Prompt）。

**配置**
- 环境变量：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`（见 `src/config.py`）。
- 提示词模板：`SCRIPT_GENERATION_PROMPT`、`IMAGE_PROMPT_GENERATION_PROMPT`。

**主要接口**
- `generate_script(book_content)`: 输入书籍内容，返回脚本文本。
- `generate_image_prompt(script_segment)`: 输入脚本片段，返回英文绘图 Prompt。

**使用示例**
```python
from src.llm_client import LLMClient
client = LLMClient()
script = client.generate_script("...书籍文本...")
prompt = client.generate_image_prompt(script[:300])
```

**注意事项**
- 输出脚本为口语化中文，后续会用 `clean_script` 进行清洗以适配 TTS。
- 图像 Prompt 必须为英文，已在模板中约束风格统一。

