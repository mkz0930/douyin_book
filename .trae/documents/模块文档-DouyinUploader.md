# 模块文档 - DouyinUploader

**文件**: `src/douyin_uploader.py`

**职责**
- 通过 Playwright 自动化登录抖音创作平台并上传视频为草稿。

**流程概述**
- 启动 Chromium（非无头），访问上传页。
- 判断是否需要扫码登录；若需要，最长等待 10 分钟并轮询登录状态。
- 登录成功后保存 Cookies 到 `douyin_cookies.json`。
- 定位上传区域，触发文件选择并设置视频文件。
- 监控上传进度与完成状态，填写标题、话题与封面，保存草稿。

**主要接口**
- `upload(video_path, title, location=None, tags=[], cover_path=None)`: 执行完整上传流程。

**使用示例**
```python
from src.douyin_uploader import DouyinUploader
uploader = DouyinUploader()
uploader.upload(
    "output/video_xxx.mp4",
    "《书名》深度解读",
    tags=["读书", "推荐"],
    cover_path="output/image_xxx.jpg"
)
```

**注意事项**
- 首次运行需人工扫码；后续将复用本地 `douyin_cookies.json`。
- 页面结构可能变化，脚本包含多重选择器与回退逻辑以提升稳定性。

