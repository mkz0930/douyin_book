from playwright.sync_api import sync_playwright
import os
import time

def login_and_save_cookies(output_file="douyin_cookies.json"):
    with sync_playwright() as p:
        print("启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        url = "https://creator.douyin.com/creator/content/upload"
        print(f"访问: {url}")
        page.goto(url)
        
        # Wait for page to load a bit
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass

        print(">>> 请在浏览器中扫码登录抖音创作服务平台 <<<")
        print(">>> 登录成功后，脚本将自动检测并保存 Cookies <<<")
        print(">>> 如果长时间未检测到，请手动按 Ctrl+C 结束 <<<")
        
        max_wait = 600 # 10 minutes
        start_time = time.time()
        
        while True:
            if time.time() - start_time > max_wait:
                print("登录等待超时 (10分钟)。")
                break
                
            try:
                # Check current URL and content
                current_url = page.url
                content = page.content()
                
                # Success criteria:
                # 1. URL contains 'creator'
                # 2. We see elements typical of the dashboard (e.g., '首页', '投稿', '上传', user avatar)
                # 3. We DO NOT see '扫码登录'
                
                is_logged_in = False
                
                if "creator" in current_url:
                    if "扫码登录" not in content and "登录/注册" not in content:
                        # Double check for positive indicators
                        if "上传" in content or "作品" in content or "首页" in content:
                            is_logged_in = True
                
                if is_logged_in:
                    print("检测到登录成功！")
                    # Wait a bit for cookies to be set fully
                    time.sleep(3)
                    
                    # Save storage state
                    context.storage_state(path=output_file)
                    print(f"✅ Cookies 已保存至: {os.path.abspath(output_file)}")
                    break
                else:
                    # Print status every 5 seconds
                    if int(time.time() - start_time) % 5 == 0:
                         print("等待登录...", end="\r")
            except Exception as e:
                # print(f"Check error: {e}")
                pass
            
            time.sleep(2)
            
        print("\n关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    login_and_save_cookies()
