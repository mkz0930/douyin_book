from playwright.sync_api import sync_playwright
import os
import time

class DouyinUploader:
    def __init__(self, cookie_file="douyin_cookies.json"):
        self.cookie_file = cookie_file
        self.upload_url = "https://creator.douyin.com/creator/content/upload"

    def upload(self, video_path, title, location=None, tags=[], cover_path=None):
        print(f"准备上传视频: {video_path}")
        if cover_path:
            print(f"封面图片: {cover_path}")
        
        with sync_playwright() as p:
            # Launch browser (Headless=False so user can see/scan QR)
            browser = p.chromium.launch(headless=False)
            
            # Create context
            if os.path.exists(self.cookie_file):
                print(f"加载 Cookies: {self.cookie_file}")
                context = browser.new_context(storage_state=self.cookie_file)
            else:
                context = browser.new_context()
            
            page = context.new_page()
            
            # Go to upload page
            print(f"访问: {self.upload_url}")
            try:
                page.goto(self.upload_url, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"Loading page timed out or failed: {e}")
                # Try to continue anyway as we might be partially loaded
                pass
            
            page.wait_for_timeout(3000) # Wait for SPA routing
            
            # Check login status
            # If redirected to login page or passport page, OR if page content suggests login
            print(f"当前页面 URL: {page.url}")
            page_content = page.content()
            is_login_page = "login" in page.url or "passport" in page.url or "creator" not in page.url
            if not is_login_page:
                # Double check content for login keywords
                if "扫码登录" in page_content or "创作者登录" in page_content or "登录/注册" in page_content:
                    print("检测到页面包含登录提示...")
                    is_login_page = True

            if is_login_page:
                print(">>> 检测到未登录或不在创作中心，请在浏览器中扫码登录... <<<")
                print(">>> 程序将自动检测登录状态 (最长等待 10 分钟)... <<<")
                
                # Polling for login success
                # We wait until "扫码登录" is no longer in the page content
                # AND we can find some element indicative of the dashboard
                max_retries = 120 # 120 * 5s = 600s = 10 mins
                logged_in = False
                
                for i in range(max_retries):
                    try:
                        content = page.content()
                        # Conditions for success:
                        # 1. No "扫码登录"
                        # 2. URL is correct
                        # 3. Found upload button or "首页" or similar
                        
                        if "扫码登录" not in content and "登录/注册" not in content:
                            # Potential success, double check URL
                            if "creator/content" in page.url:
                                print("检测到登录成功页面！")
                                logged_in = True
                                break
                        
                        if i % 5 == 0:
                            print(f"等待登录中... ({i*5}s)")
                        
                        page.wait_for_timeout(5000)
                    except Exception as e:
                        print(f"Check login status error: {e}")
                        page.wait_for_timeout(5000)
                
                if not logged_in:
                    print("登录超时，退出。")
                    browser.close()
                    return False

                # Save cookies immediately after successful login detection
                context.storage_state(path=self.cookie_file)
                print("Cookies 已保存。")
                
            # Ensure we are on the upload page

            # Ensure we are on the upload page
            # Sometimes we are on the dashboard home even if URL says upload
            if "creator/content/upload" not in page.url or "抖音排行榜" in page.locator("body").inner_text()[:500]:
                print(f"尝试重新跳转至上传页面: {self.upload_url}")
                page.goto(self.upload_url, wait_until="networkidle")
                page.wait_for_timeout(5000)
            
            # Check if we need to click a "Publish" button to get to the upload area
            # Try common button texts
            potential_buttons = ["发布作品", "高清发布", "发布视频"]
            for btn_text in potential_buttons:
                if page.locator(f"text={btn_text}").first.is_visible():
                    print(f"Found '{btn_text}' button, clicking...")
                    page.locator(f"text={btn_text}").first.click()
                    page.wait_for_timeout(3000)
                    break

            try:
                page.wait_for_selector(".upload-btn, input[type='file'], div:has-text('点击上传')", timeout=10000)
            except:
                print("Wait for upload selector timeout, proceeding anyway...")
            
            print(f"准备上传，当前页面标题: {page.title()}")

            # Upload Video
            print("开始上传视频文件...")
            upload_success = False
            
            # Retry mechanism for upload start
            for attempt in range(3):
                print(f"尝试上传 (第 {attempt+1} 次)...")
                try:
                    # Method A: File Chooser via Click
                    try:
                        # Check for input first
                        # input_el = page.locator("input[type='file']").first
                        
                        # Try broader click for upload area
                        # We want the big drag-and-drop area
                        # Try to find a trigger that works
                        upload_trigger = None
                        if page.locator("div:has-text('点击上传')").count() > 0:
                            upload_trigger = page.locator("div:has-text('点击上传')").first
                        elif page.locator(".semi-upload-drag-area").count() > 0:
                            upload_trigger = page.locator(".semi-upload-drag-area").first
                        
                        if upload_trigger and upload_trigger.is_visible():
                            print(f"Found upload trigger: {upload_trigger}")
                            
                            # Use expect_file_chooser only if we click
                            with page.expect_file_chooser(timeout=10000) as fc_info:
                                upload_trigger.click(force=True)
                            
                            file_chooser = fc_info.value
                            file_chooser.set_files(video_path)
                            print("File set via FileChooser.")
                            
                            # Wait a bit after setting files
                            page.wait_for_timeout(3000)
                        else:
                            print("No visible trigger found. Trying input[type='file'] directly.")
                            page.set_input_files("input[type='file']", video_path)
                            print("File set directly on input.")

                    except Exception as e:
                        print(f"File chooser error: {e}")
                        # Fallback
                        try:
                            print("Fallback: Setting input[type='file'] directly...")
                            page.set_input_files("input[type='file']", video_path)
                        except Exception as e2:
                            print(f"Fallback failed: {e2}")

                    # Wait and check if upload started
                    print("等待上传开始响应...")
                    
                    # Sometimes we need to click "确定" in a system dialog or something, 
                    # but set_files usually handles it.
                    # Let's try to verify if the input has files
                    # input_val = page.eval_on_selector("input[type='file']", "el => el.value")
                    # print(f"Input value: {input_val}")

                    # If the page doesn't react, maybe we need to click the area AGAIN or dispatch event
                    # Some Vue apps need 'change' event on the input
                    
                    # Wait for either progress bar, video player, or "re-upload" text
                    # "取消上传" is also a good indicator that upload is running
                    try:
                        # Wait for a longer time
                        page.wait_for_selector("text=取消上传, text=重新上传, .player-container, video, .progress-bar", timeout=30000)
                        print("✅ 检测到上传已开始！")
                        upload_success = True
                        break
                    except:
                        print("❌ 未检测到上传开始信号，尝试手动触发事件...")
                        # Try dispatching change event on the file input
                        try:
                             page.evaluate("""() => {
                                 const input = document.querySelector('input[type="file"]');
                                 if (input) {
                                     input.dispatchEvent(new Event('change', { bubbles: true }));
                                     input.dispatchEvent(new Event('input', { bubbles: true }));
                                 }
                             }""")
                             print("Dispatched change/input events manually.")
                             # Wait again
                             page.wait_for_selector("text=取消上传, text=重新上传, .player-container, video, .progress-bar", timeout=5000)
                             print("✅ 检测到上传已开始 (Event Triggered)！")
                             upload_success = True
                             break
                        except:
                             pass

                except Exception as e:
                    print(f"上传尝试异常: {e}")
                    # Try direct input fallback if click failed
                    try:
                        print("尝试直接设置 input[type='file']...")
                        page.set_input_files("input[type='file']", video_path)
                        page.wait_for_timeout(2000)
                        # Dispatch events
                        page.eval_on_selector("input[type='file']", "el => { el.dispatchEvent(new Event('change', {bubbles: true})); el.dispatchEvent(new Event('input', {bubbles: true})); }")
                    except Exception as e2:
                        print(f"Direct input failed: {e2}")
                
                if not upload_success:
                    print("Retrying upload...")
                    page.wait_for_timeout(2000)
            
            if not upload_success:
                print("❌ 3次尝试后上传均失败，无法继续。")
                browser.close()
                return False

            # Wait for upload completion
            print("正在上传中，请稍候...")
            # Douyin usually shows a progress bar or "上传成功" text
            # We can wait for the video player or success message to appear
            try:
                # Wait for "上传成功" or similar text. Or wait for the video preview to appear.
                # Adjust timeout based on file size.
                
                # First, ensure we didn't just flash through.
                # If set_input_files worked, the page content should change to show progress or preview.
                # Let's wait for either:
                # 1. "重新上传" (Re-upload) -> Indicates a file is selected
                # 2. "上传成功" (Upload Success)
                # 3. ".player-container" -> Video player
                
                print("等待上传状态变更...")
                page.wait_for_selector("text=重新上传, text=上传成功, .player-container, video", timeout=60000)
                
                print("检测到文件已加载，等待上传完成...")
                page.wait_for_selector("text=上传成功", timeout=600000) 
                print("视频上传完成！")
            except Exception as e:
                print(f"等待上传完成超时或异常: {e}")
                print("尝试继续填写信息，但上传可能未完成。")

            # Fill Title
            print("填写标题和话题...")
            # Title input is usually a div[contenteditable] or input
            # Try to find the input with placeholder containing "标题"
            try:
                # Construct title text
                full_title = f"{title} {' '.join(['#'+t for t in tags])}"
                
                # Locate title input
                title_box = page.locator("div[contenteditable='true'], input[placeholder*='标题']").first
                title_box.click()
                title_box.fill(full_title)
                print(f"已填写标题: {full_title}")
            except Exception as e:
                print(f"填写标题失败: {e}")

            # Set Cover (Optional but recommended)
            print("尝试设置封面...")
            try:
                # 1. Click "设置封面" or "选择封面"
                cover_btn = page.locator("div:has-text('设置封面'), div:has-text('选择封面')").last
                if cover_btn.is_visible():
                    cover_btn.click(force=True)
                    page.wait_for_timeout(3000) # Wait for modal
                    
                    # Strategy: Use Smart/Recommended Cover
                    print("切换到智能/推荐封面...")
                    try:
                        # Try to find "智能推荐封面" or "截取封面"
                        # Prioritize Smart Recommendation if available
                        smart_tab = page.locator("div:has-text('智能推荐封面'), div:has-text('智能封面')").last
                        if smart_tab.is_visible():
                            smart_tab.click(force=True)
                            print("已选择：智能推荐封面")
                            page.wait_for_timeout(1000)
                            # Usually it auto-selects one, or we pick the first one
                            # first_img = page.locator(".smart-cover-item").first
                            # if first_img.is_visible(): first_img.click()
                        else:
                            # Fallback to Capture
                            print("未找到智能推荐，尝试截取封面...")
                            capture_tab = page.locator("div:has-text('截取封面')").last
                            if capture_tab.is_visible():
                                capture_tab.click(force=True)
                                page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"切换封面标签失败: {e}")

                    # 4. Click Confirm
                    confirm_btn = page.locator("button:has-text('完成'), button:has-text('确定'), button:has-text('裁剪完成')").last
                    if confirm_btn.is_visible():
                        confirm_btn.click(force=True)
                        print("封面设置/确认完成。")
                        page.wait_for_timeout(2000)
                    else:
                        print("未找到封面确认按钮，尝试关闭。")
                        page.keyboard.press("Escape")

                else:
                    print("未找到'设置封面'入口。")
            except Exception as e:
                print(f"设置封面失败: {e}")
                # Try to close modal
                page.keyboard.press("Escape")

            # Location (Optional)
            if location:
                print(f"尝试添加位置: {location}")
                # Implementation omitted for stability
                pass

            # Save Draft (Draft Button)
            print("准备保存草稿...")
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            try:
                # Find button with exact text "暂存离开" or "存草稿"
                # Use get_by_text for better precision
                draft_btn = page.get_by_text("暂存离开").first
                if not draft_btn.is_visible():
                     draft_btn = page.get_by_text("存草稿").first
                
                if draft_btn.is_visible():
                    draft_btn.click(force=True)
                    print("点击了'暂存离开/存草稿'按钮。")
                    
                    # Check for confirmation dialog (e.g. "是否保存草稿？")
                    page.wait_for_timeout(1000)
                    confirm_btn = page.locator("button:has-text('确定'), button:has-text('保存')").first
                    if confirm_btn.is_visible():
                        print(f"检测到确认弹窗，点击: {confirm_btn.inner_text()}")
                        confirm_btn.click(force=True)

                    # Wait for success confirmation
                    # "保存草稿成功" or just wait a bit
                    try:
                        page.wait_for_selector("text=成功", timeout=10000)
                        print("✅ 草稿/暂存 保存成功！请去抖音 App 或网页端查看。")
                    except:
                        print("未检测到保存成功提示，但已点击按钮。")
                else:
                    print("❌ 找不到'存草稿'或'暂存'按钮。")
                    # Debug: Print all buttons
                    print("Debug: Visible buttons:")
                    buttons = page.locator("button").all()
                    for b in buttons:
                        if b.is_visible():
                            print(f"Button: {b.inner_text()}")
            except Exception as e:
                print(f"保存草稿操作失败: {e}")

            # Keep browser open for a few seconds to ensure requests are sent
            time.sleep(5)
            browser.close()
            return True

if __name__ == "__main__":
    # Test Stub
    import sys
    if len(sys.argv) > 1:
        video = sys.argv[1]
        uploader = DouyinUploader()
        uploader.upload(video, "测试视频 #自动发布", tags=["测试"])
    else:
        print("Usage: python src/douyin_uploader.py <video_path>")
