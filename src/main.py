import os
import sys
import glob
import argparse
import re
import shutil

# 将父目录添加到系统路径，以便可以导入 src 模块
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入各个功能模块的客户端类
from src.llm_client import LLMClient        # 大语言模型客户端，用于生成脚本和绘画提示词
from src.tts_client import TTSClient        # 语音合成客户端，用于生成语音和字幕
from src.video_gen import VideoGenerator    # 视频生成器，用于合成视频
from src.image_client import ImageClient    # 图像生成客户端，用于生成封面/背景图
from src.search_client import SearchClient  # 搜索客户端，用于联网检索书籍信息
from src.config import TTS_VOICE, TTS_RATE, TTS_VOLUME  # 导入 TTS 配置参数
from src.utils import clean_script, parse_vtt           # 导入工具函数
from src.douyin_uploader import DouyinUploader          # 抖音上传工具

def main():
    """
    抖音说书 Agent 主程序流程 (Main Pipeline)
    
    该函数执行以下全自动化流程：
    1. 初始化各个 AI 客户端 (LLM, TTS, Image, Video, Uploader)。
    2. 扫描 data/ 目录下的 .txt 书籍文件。
    3. 对每个文件执行以下步骤：
       A. 脚本生成: 
          - 如果文件内容充足，调用 LLM 将书籍内容转化为口播脚本。
          - 如果文件内容极短（仅包含书名），自动联网搜索该书的简介与评价，再生成脚本。
       B. 图像生成: 根据脚本内容生成 AI 绘画提示词，并生成封面图。
       C. 语音合成: 调用 Edge-TTS 生成语音 (MP3) 和字幕 (VTT)。
       D. 视频合成: 将音频、字幕、背景图、背景音乐合成为最终视频 (MP4)。
       E. 自动上传: (可选) 登录抖音创作者平台并上传草稿。
    """
    
    # --- 0. 命令行参数解析 (Argument Parsing) ---
    parser = argparse.ArgumentParser(description="Douyin Book Agent - Main Pipeline (抖音说书智能体主程序)")
    
    # 添加控制各个步骤是否跳过的参数，方便调试和断点续传
    parser.add_argument("--skip-llm", action="store_true", help="跳过 LLM 脚本生成，直接使用 output/ 下现有的脚本文件")
    parser.add_argument("--skip-tts", action="store_true", help="跳过 TTS 语音生成，直接使用 output/ 下现有的音频文件")
    parser.add_argument("--skip-image", action="store_true", help="跳过 AI 绘图，直接使用 output/ 下现有的图片文件")
    parser.add_argument("--skip-video", action="store_true", help="跳过视频合成，直接使用 output/ 下现有的视频文件")
    parser.add_argument("--upload", action="store_true", help="生成完成后，自动将视频上传到抖音创作者平台草稿箱")
    
    args = parser.parse_args()

    # --- 1. 初始化客户端 (Initialize Clients) ---
    print("正在初始化各个 AI 客户端...")
    try:
        # 初始化 LLM 客户端 (需在 .env 配置 API Key)
        llm_client = LLMClient()
        # 初始化 TTS 客户端 (配置音色、语速、音量)
        tts_client = TTSClient(voice=TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
        # 初始化图像生成客户端
        image_client = ImageClient()
        # 初始化视频生成器
        video_gen = VideoGenerator()
        # 初始化抖音上传器
        uploader = DouyinUploader()
        # 初始化搜索客户端
        search_client = SearchClient()
    except ValueError as e:
        print(f"初始化失败: {e}")
        return

    # --- 2. 设置目录路径 (Setup Directories) ---
    # 获取项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 输入目录: 存放书籍 txt, 背景图, 背景音乐
    input_dir = os.path.join(base_dir, "data")
    # 历史归档目录: 存放已处理的书籍 txt
    history_dir = os.path.join(input_dir, "history")
    # 输出目录: 存放生成的脚本, 音频, 图片, 视频
    output_dir = os.path.join(base_dir, "output")
    
    # 如果输出目录不存在，则自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 如果历史目录不存在，则自动创建
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)

    # --- 3. 处理逻辑 (Process Logic) ---
    # 扫描 input_dir 下所有的 .txt 文件
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not txt_files:
        print(f"在 {input_dir} 目录下未找到 .txt 文件。请放入书籍文本文件。")
        return

    print(f"找到 {len(txt_files)} 个文件待处理。")

    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0] # 去除扩展名的文件名，用于生成输出文件名
        
        # 读取书籍原始内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except Exception as e:
            print(f"[{file_name}] 读取文件失败: {e}")
            continue

        # 检查是否为空文件
        if not content:
            print(f"[{file_name}] 文件内容为空，跳过处理。")
            continue

        # 尝试提取书名，用于优化输出文件名
        if not args.skip_llm and content:
             try:
                 print(f"[{file_name}] 正在分析文本以提取书名...")
                 extracted_name = llm_client.extract_book_name(content)
                 if extracted_name and extracted_name != "Unknown":
                    print(f"[{file_name}] 提取到书名: {extracted_name}")
                    # 简单清洗书名，确保可用作文件名
                    safe_name = re.sub(r'[\\/*?:"<>|]', "", extracted_name)
                    safe_name = safe_name.replace(" ", "_").strip()
                    if safe_name:
                        base_name = safe_name
             except Exception as e:
                 print(f"[{file_name}] 书名提取失败，将使用文件名: {e}")
        
        print(f"[{file_name}] 将使用基础名称: {base_name}")

        # 创建该书籍的专属输出目录
        book_output_dir = os.path.join(output_dir, base_name)
        if not os.path.exists(book_output_dir):
            os.makedirs(book_output_dir)

        # 定义该文件的所有输出路径 (全部放入专属子目录)
        script_path = os.path.join(book_output_dir, f"script_{base_name}.txt")
        audio_path = os.path.join(book_output_dir, f"audio_{base_name}.mp3")
        vtt_path = os.path.join(book_output_dir, f"audio_{base_name}.vtt")
        video_path = os.path.join(book_output_dir, f"video_{base_name}.mp4")
        image_path = os.path.join(book_output_dir, f"image_{base_name}.jpg")

        script_content = ""

        # --- 步骤 A: 生成脚本 (Generate Script) ---
        # 如果指定跳过 LLM 且脚本文件已存在，则读取现有脚本
        if args.skip_llm and os.path.exists(script_path):
            print(f"[{file_name}] 跳过 LLM 生成，读取现有脚本: {script_path}")
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()
        else:
            print(f"[{file_name}] 正在处理文本，准备生成脚本...")
            # content 已经在上面读取
            
            # 判断是否需要走“仅书名搜索”模式
            # 条件：内容长度小于 200 字符，且没有被跳过
            if len(content) < 200 and not args.skip_llm:
                print(f"[{file_name}] 检测到内容较短 ({len(content)} 字符)，尝试联网搜索书籍信息...")
                # 尝试提取书名，如果内容就是书名则用内容，否则用文件名
                # 假设内容如果是 "百年孤独"，那 content 就是书名
                # 如果内容是空的，用文件名
                book_query = content if len(content) > 0 else base_name
                print(f"正在搜索书籍: {book_query}")
                
                search_summary = search_client.search_book_info(book_query)
                
                if search_summary:
                    print(f"[{file_name}] 搜索成功，正在基于搜索结果生成脚本...")
                    script_content = llm_client.generate_script_from_summary(book_query, search_summary)
                    if script_content:
                        # 保存生成的脚本
                        with open(script_path, "w", encoding="utf-8") as f:
                            f.write(script_content)
                        print(f"脚本已保存至: {script_path}")
                    else:
                        print(f"[{file_name}] 基于搜索结果的脚本生成失败。")
                        continue
                else:
                    print(f"[{file_name}] 联网搜索失败（可能是网络问题）。")
                    if len(content) == 0:
                        print(f"[{file_name}] 且原文内容为空，无法生成脚本。请在 txt 文件中填入书籍内容或简介后重试。")
                        continue
                    else:
                        print(f"[{file_name}] 尝试使用现有短文本 ({len(content)} 字符) 生成脚本...")
                        script_content = llm_client.generate_script(content)
            
            # 正常长文本模式
            elif not args.skip_llm: 
                # 截断过长的文本 (MVP 阶段限制 10000 字符，避免 token 溢出)
                if len(content) > 10000: content = content[:10000]
                
                script_content = llm_client.generate_script(content)
                if script_content:
                    # 保存生成的脚本
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(script_content)
                    print(f"脚本已保存至: {script_path}")
                else:
                    print(f"[{file_name}] 脚本生成失败，跳过后续步骤。")
                    continue

        # 清洗脚本 (去除 Markdown 标记等，以便用于 TTS)
        cleaned_script = clean_script(script_content)
        if not cleaned_script:
            print("清洗后的脚本为空！")
            continue

        # --- 步骤 B: 生成图像 (Generate Image) ---
        # MVP 策略: 根据脚本前段内容生成一张封面图作为视频背景
        if args.skip_image and os.path.exists(image_path):
            print(f"[{file_name}] 跳过图像生成，使用现有图片: {image_path}")
        else:
            print(f"[{file_name}] 正在生成 AI 配图...")
            # 截取前 300 个字符作为 prompt 的上下文
            context = cleaned_script[:300] 
            # 调用 LLM 生成英文绘画提示词
            image_prompt = llm_client.generate_image_prompt(context)
            
            if image_prompt:
                print(f"生成的绘画提示词: {image_prompt}")
                # 调用绘图 API 生成图片
                success = image_client.generate_image(image_prompt, image_path)
                if success:
                    print(f"图片已保存至: {image_path}")
                else:
                    print("图片生成失败，后续将尝试使用默认背景。")
            else:
                print("绘画提示词生成失败。")

        # --- 步骤 C: 生成语音与字幕 (Generate Audio & Subtitles) ---
        audio_exists = os.path.exists(audio_path)
        vtt_exists = os.path.exists(vtt_path)
        
        if args.skip_tts and audio_exists:
            print(f"[{file_name}] 跳过 TTS，使用现有音频: {audio_path}")
        else:
            print(f"[{file_name}] 正在生成语音和字幕 (Edge-TTS)...")
            # 调用 TTS 客户端生成 MP3 和 VTT
            success = tts_client.generate_audio_with_subtitles(cleaned_script, audio_path, vtt_path)
            if success:
                print(f"音频已保存至: {audio_path}")
                print(f"字幕已保存至: {vtt_path}")
                audio_exists = True
                vtt_exists = True
            else:
                print(f"语音/字幕生成失败。")
                audio_exists = False
        
        # --- 步骤 D: 合成视频 (Generate Video) ---
        if audio_exists:
            # 确定背景图路径: 优先使用生成的 AI 图片，其次使用 data/background.jpg，最后使用黑屏
            bg_path = image_path if os.path.exists(image_path) else os.path.join(input_dir, "background.jpg")
            if not os.path.exists(bg_path):
                bg_path = None # VideoGenerator 会处理 None 为黑色背景
            
            # 确定背景音乐路径: 查找 bgm.mp3 或 bgm.wav
            bgm_path = os.path.join(input_dir, "bgm.mp3")
            if not os.path.exists(bgm_path):
                bgm_path = os.path.join(input_dir, "bgm.wav") 
                if not os.path.exists(bgm_path):
                    bgm_path = None # 无背景音乐
            
            # 检查是否跳过视频合成
            if args.skip_video and os.path.exists(video_path):
                print(f"[{file_name}] 跳过视频合成，使用现有视频: {video_path}")
            else:
                print(f"[{file_name}] 正在合成视频...")
                success = video_gen.generate_simple_video(
                    audio_path, 
                    script_content, # 如果提供了 vtt_path，这个参数主要用于备用或日志
                    video_path, 
                    bg_image_path=bg_path,
                    vtt_path=vtt_path if vtt_exists else None,
                    bgm_path=bgm_path
                )
                if success:
                    print(f"视频已成功生成: {video_path}")
                else:
                    print("视频合成失败。")
                    video_path = None # 标记为失败，不进行上传
        else:
             # 如果音频缺失但视频已存在且只做上传，则继续
             if args.upload and os.path.exists(video_path):
                 print(f"警告: 音频缺失，但检测到现有视频，将尝试上传: {video_path}")
             else:
                 video_path = None

        # --- 步骤 E: 上传至抖音 (Upload to Douyin) ---
        if args.upload and video_path and os.path.exists(video_path):
            print(f"[{file_name}] 准备上传至抖音...")
            # 生成标题: 书名 + 后缀
            title = f"《{base_name}》深度解读，读懂这本书只需要 3 分钟 #读书 #知识分享"
            tags = ["读书", "推荐", "知识", "正能量", base_name]
            
            # 封面图: 使用生成的 AI 图片
            cover_path = image_path if os.path.exists(image_path) else None
            
            # 调用上传器
            uploader.upload(video_path, title, tags=tags, cover_path=cover_path)

        # --- 归档原文 (Archive Original File) ---
        print(f"[{file_name}] 处理流程结束，正在归档原文至 history 目录...")
        try:
            # 使用提取或处理后的书名作为归档文件名，保留原扩展名
            ext = os.path.splitext(file_name)[1]
            archive_name = f"{base_name}{ext}"
            target_path = os.path.join(history_dir, archive_name)
            
            # 如果目标已存在，先删除，确保能覆盖
            if os.path.exists(target_path):
                os.remove(target_path)
            shutil.move(file_path, target_path)
            print(f"[{file_name}] 原文已重命名并归档至: {target_path}")
        except Exception as e:
            print(f"[{file_name}] 归档失败: {e}")

    # --- 4. 生成空的 input.txt (Create Empty Input File) ---
    input_file_path = os.path.join(input_dir, "input.txt")
    if not os.path.exists(input_file_path):
        try:
            with open(input_file_path, "w", encoding="utf-8") as f:
                f.write("")
            print(f"已生成空的输入文件: {input_file_path}")
        except Exception as e:
            print(f"生成 input.txt 失败: {e}")

if __name__ == "__main__":
    main()
