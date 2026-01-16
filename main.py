import os
import sys
import glob
import argparse
import re
import shutil

# 将当前目录添加到系统路径，以便可以导入 src 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各个功能模块的客户端类
from src.llm_client import LLMClient        # 大语言模型客户端
from src.tts_client import TTSClient        # 语音合成客户端
from src.video_gen import VideoGenerator    # 视频生成器
from src.image_client import ImageClient    # 图像生成客户端
from src.search_client import SearchClient  # 搜索客户端
from src.config import TTS_VOICE, TTS_RATE, TTS_VOLUME
from src.utils import clean_script
from src.douyin_uploader import DouyinUploader

def process_book(file_path, args, clients, dirs, is_todo=False):
    """
    处理单本书籍的核心逻辑
    """
    llm_client = clients['llm']
    tts_client = clients['tts']
    image_client = clients['image']
    video_gen = clients['video']
    uploader = clients['uploader']
    search_client = clients['search']

    input_dir = dirs['input']
    output_dir = dirs['output']
    history_dir = dirs['history']

    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0] # 默认使用文件名

    # 读取书籍原始内容
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        print(f"[{file_name}] 读取文件失败: {e}")
        return

    # 检查是否为空文件
    if not content:
        print(f"[{file_name}] 文件内容为空，跳过处理。")
        return

    # 尝试提取书名
    if not args.skip_llm and content:
         try:
             print(f"[{file_name}] 正在分析文本以提取书名...")
             extracted_name = llm_client.extract_book_name(content)
             if extracted_name and extracted_name != "Unknown":
                print(f"[{file_name}] 提取到书名: {extracted_name}")
                safe_name = re.sub(r'[\\/*?:"<>|]', "", extracted_name)
                safe_name = safe_name.replace(" ", "_").strip()
                if safe_name:
                    base_name = safe_name
         except Exception as e:
             print(f"[{file_name}] 书名提取失败，将使用文件名: {e}")
    
    print(f"[{file_name}] 将使用基础名称: {base_name}")

    # 创建专属输出目录
    book_output_dir = os.path.join(output_dir, base_name)
    if not os.path.exists(book_output_dir):
        os.makedirs(book_output_dir)

    # 定义输出路径
    script_path = os.path.join(book_output_dir, f"script_{base_name}.txt")
    desc_path = os.path.join(book_output_dir, f"desc_{base_name}.txt")
    audio_path = os.path.join(book_output_dir, f"audio_{base_name}.mp3")
    vtt_path = os.path.join(book_output_dir, f"audio_{base_name}.vtt")
    video_path = os.path.join(book_output_dir, f"video_{base_name}.mp4")
    image_path = os.path.join(book_output_dir, f"image_{base_name}.jpg")

    script_content = ""

    # --- 步骤 A: 生成脚本 ---
    if args.skip_llm and os.path.exists(script_path):
        print(f"[{file_name}] 跳过 LLM 生成，读取现有脚本: {script_path}")
        with open(script_path, "r", encoding="utf-8") as f:
            script_content = f.read()
    else:
        print(f"[{file_name}] 正在处理文本，准备生成脚本...")
        
        # 仅书名搜索模式
        if len(content) < 200 and not args.skip_llm:
            print(f"[{file_name}] 检测到内容较短 ({len(content)} 字符)，尝试联网搜索书籍信息...")
            book_query = content if len(content) > 0 else base_name
            print(f"正在搜索书籍: {book_query}")
            
            search_summary = search_client.search_book_info(book_query)
            
            if search_summary:
                print(f"[{file_name}] 搜索成功，正在基于搜索结果生成脚本...")
                script_content = llm_client.generate_script_from_summary(book_query, search_summary)
                if script_content:
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(script_content)
                    print(f"脚本已保存至: {script_path}")
                    
                    # 生成抖音文案
                    print(f"[{file_name}] 正在生成抖音文案...")
                    try:
                        desc_content = llm_client.generate_douyin_description(script_content)
                        if desc_content:
                            with open(desc_path, "w", encoding="utf-8") as f:
                                f.write(desc_content)
                            print(f"抖音文案已保存至: {desc_path}")
                    except Exception as e:
                        print(f"[{file_name}] 抖音文案生成失败: {e}")
                else:
                    print(f"[{file_name}] 基于搜索结果的脚本生成失败。")
                    return
            else:
                print(f"[{file_name}] 联网搜索失败。")
                if len(content) == 0:
                    print(f"[{file_name}] 原文为空，无法生成脚本。")
                    return
                else:
                    print(f"[{file_name}] 尝试使用现有短文本生成脚本...")
                    script_content = llm_client.generate_script(content)
        
        # 正常长文本模式
        elif not args.skip_llm: 
            if len(content) > 10000: content = content[:10000]
            
            script_content = llm_client.generate_script(content)
            if script_content:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                print(f"脚本已保存至: {script_path}")
                
                # 生成抖音文案
                print(f"[{file_name}] 正在生成抖音文案...")
                try:
                    desc_content = llm_client.generate_douyin_description(script_content)
                    if desc_content:
                        with open(desc_path, "w", encoding="utf-8") as f:
                            f.write(desc_content)
                        print(f"抖音文案已保存至: {desc_path}")
                except Exception as e:
                    print(f"[{file_name}] 抖音文案生成失败: {e}")
            else:
                print(f"[{file_name}] 脚本生成失败，跳过后续步骤。")
                return

    # 清洗脚本
    cleaned_script = clean_script(script_content)
    if not cleaned_script:
        print("清洗后的脚本为空！")
        return

    # --- 步骤 B: 生成图像 ---
    if args.skip_image and os.path.exists(image_path):
        print(f"[{file_name}] 跳过图像生成，使用现有图片: {image_path}")
    else:
        print(f"[{file_name}] 正在生成 AI 配图...")
        context = cleaned_script[:300] 
        image_prompt = llm_client.generate_image_prompt(context)
        
        if image_prompt:
            print(f"生成的绘画提示词: {image_prompt}")
            success = image_client.generate_image(image_prompt, image_path)
            if success:
                print(f"图片已保存至: {image_path}")
            else:
                print("图片生成失败，后续将尝试使用默认背景。")
        else:
            print("绘画提示词生成失败。")

    # --- 步骤 C: 生成语音与字幕 ---
    audio_exists = os.path.exists(audio_path)
    vtt_exists = os.path.exists(vtt_path)
    
    if args.skip_tts and audio_exists:
        print(f"[{file_name}] 跳过 TTS，使用现有音频: {audio_path}")
    else:
        print(f"[{file_name}] 正在生成语音和字幕 (Edge-TTS)...")
        success = tts_client.generate_audio_with_subtitles(cleaned_script, audio_path, vtt_path)
        if success:
            print(f"音频已保存至: {audio_path}")
            print(f"字幕已保存至: {vtt_path}")
            audio_exists = True
            vtt_exists = True
        else:
            print(f"语音/字幕生成失败。")
            audio_exists = False
    
    # --- 步骤 D: 合成视频 ---
    if audio_exists:
        bg_path = image_path if os.path.exists(image_path) else os.path.join(input_dir, "background.jpg")
        if not os.path.exists(bg_path):
            bg_path = None
        
        bgm_path = os.path.join(input_dir, "bgm.mp3")
        if not os.path.exists(bgm_path):
            bgm_path = os.path.join(input_dir, "bgm.wav") 
            if not os.path.exists(bgm_path):
                bgm_path = None
        
        if args.skip_video and os.path.exists(video_path):
            print(f"[{file_name}] 跳过视频合成，使用现有视频: {video_path}")
        else:
            print(f"[{file_name}] 正在合成视频...")
            success = video_gen.generate_simple_video(
                audio_path, 
                script_content,
                video_path, 
                bg_image_path=bg_path,
                vtt_path=vtt_path if vtt_exists else None,
                bgm_path=bgm_path
            )
            if success:
                print(f"视频已成功生成: {video_path}")
            else:
                print("视频合成失败。")
                video_path = None
    else:
         if args.upload and os.path.exists(video_path):
             print(f"警告: 音频缺失，但检测到现有视频，将尝试上传: {video_path}")
         else:
             video_path = None

    # --- 步骤 E: 上传至抖音 ---
    if args.upload and video_path and os.path.exists(video_path):
        print(f"[{file_name}] 准备上传至抖音...")
        title = f"《{base_name}》深度解读，读懂这本书只需要 3 分钟 #读书 #知识分享"
        tags = ["读书", "推荐", "知识", "正能量", base_name]
        cover_path = image_path if os.path.exists(image_path) else None
        uploader.upload(video_path, title, tags=tags, cover_path=cover_path)

    # --- 归档逻辑 ---
    print(f"[{file_name}] 处理流程结束，正在归档...")
    try:
        # 归档目标路径 (使用提取到的书名)
        ext = os.path.splitext(file_name)[1]
        archive_name = f"{base_name}{ext}"
        target_path = os.path.join(history_dir, archive_name)
        
        # 如果目标已存在，先删除
        if os.path.exists(target_path):
            os.remove(target_path)

        if is_todo:
            # Todo 模式: 复制内容到 History，清空原文件
            print(f"[{file_name}] (Todo模式) 正在复制内容到 history 并清空原文件...")
            # 复制内容
            with open(file_path, 'r', encoding='utf-8') as src:
                content_to_archive = src.read()
            with open(target_path, 'w', encoding='utf-8') as dst:
                dst.write(content_to_archive)
            
            # 清空原文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"[{file_name}] 内容已归档至: {target_path}")
            print(f"[{file_name}] 原文件已清空: {file_path}")
        else:
            # 标准模式: 移动文件
            print(f"[{file_name}] (标准模式) 正在移动文件到 history...")
            shutil.move(file_path, target_path)
            print(f"[{file_name}] 原文已重命名并归档至: {target_path}")

    except Exception as e:
        print(f"[{file_name}] 归档失败: {e}")


def main():
    """
    抖音说书 Agent 主程序流程
    支持多任务队列：优先处理 data/ 下的文件，再处理 data/todo/ 下的文件
    """
    parser = argparse.ArgumentParser(description="Douyin Book Agent - Main Pipeline")
    parser.add_argument("--skip-llm", action="store_true", help="跳过 LLM 脚本生成")
    parser.add_argument("--skip-tts", action="store_true", help="跳过 TTS 语音生成")
    parser.add_argument("--skip-image", action="store_true", help="跳过 AI 绘图")
    parser.add_argument("--skip-video", action="store_true", help="跳过视频合成")
    parser.add_argument("--upload", action="store_true", help="自动上传到抖音")
    args = parser.parse_args()

    # --- 1. 初始化客户端 ---
    print("正在初始化各个 AI 客户端...")
    try:
        clients = {
            'llm': LLMClient(),
            'tts': TTSClient(voice=TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME),
            'image': ImageClient(),
            'video': VideoGenerator(),
            'uploader': DouyinUploader(),
            'search': SearchClient()
        }
    except ValueError as e:
        print(f"初始化失败: {e}")
        return

    # --- 2. 设置目录路径 ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = {
        'input': os.path.join(base_dir, "data"),
        'todo': os.path.join(base_dir, "data", "todo"),
        'history': os.path.join(base_dir, "data", "history"),
        'output': os.path.join(base_dir, "output")
    }
    
    for d in dirs.values():
        if not os.path.exists(d):
            os.makedirs(d)

    # --- 3. 优先级 1: 处理 data/ 下的文件 (标准输入) ---
    print("\n=== 检查标准输入队列 (data/) ===")
    # 仅获取 data/ 根目录下的 txt，不递归
    standard_files = glob.glob(os.path.join(dirs['input'], "*.txt"))
    # 过滤掉 input.txt (如果是空的) 或其他特定文件? 
    # glob不会包含子目录文件。但 data/input.txt 可能存在且为空，process_book 会处理为空的情况(跳过)。
    
    if standard_files:
        print(f"找到 {len(standard_files)} 个标准任务待处理。")
        for file_path in standard_files:
            process_book(file_path, args, clients, dirs, is_todo=False)
    else:
        print("标准输入队列为空。")

    # --- 4. 优先级 2: 处理 data/todo/ 下的文件 (Todo 队列) ---
    print("\n=== 检查 Todo 队列 (data/todo/) ===")
    todo_files = glob.glob(os.path.join(dirs['todo'], "*.txt"))
    
    if todo_files:
        print(f"找到 {len(todo_files)} 个 Todo 任务待处理。")
        for file_path in todo_files:
            process_book(file_path, args, clients, dirs, is_todo=True)
    else:
        print("Todo 队列为空。")

    # --- 5. 生成空的 input.txt (方便下次使用) ---
    input_file_path = os.path.join(dirs['input'], "input.txt")
    if not os.path.exists(input_file_path):
        try:
            with open(input_file_path, "w", encoding="utf-8") as f:
                f.write("")
            print(f"\n已生成空的输入文件: {input_file_path}")
        except Exception as e:
            print(f"生成 input.txt 失败: {e}")

if __name__ == "__main__":
    main()
