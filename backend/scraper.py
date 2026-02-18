import random
import time
import asyncio
from playwright.async_api import async_playwright

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def extract_terabox_url(share_url: str, cookie: str = None):
    """
    Extracts the direct download URL from a Terabox share link.
    """
    async with async_playwright() as p:
        # Retry logic optimized
        max_retries = 2
        
        # Domain Normalization: 1024tera.com is often less blocked than terabox.com
        # Replace common domains with 1024tera.com
        normalized_url = share_url.replace("terabox.com", "1024tera.com") \
                                  .replace("teraboxapp.com", "1024tera.com") \
                                  .replace("terasharefile.com", "1024tera.com") \
                                  .replace("miracledown.com", "1024tera.com")
        
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} for {normalized_url}")
            browser = None
            try:
                # 1. Launch browser with stealth args
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--disable-gpu",
                    ]
                )
                
                # 2. Randomize User-Agent and Viewport
                user_agent = random.choice(UA_LIST)
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York"
                )

                # Inject User Cookies if provided
                if cookie:
                    try:
                        # Simple parsing: check if name=value or just value (assume ndus)
                        cookie_list = []
                        if "=" in cookie:
                             # Handle "name=value; name2=value2"
                             parts = cookie.split(';')
                             for part in parts:
                                 if '=' in part:
                                     key, value = part.split('=', 1)
                                     cookie_list.append({"name": key.strip(), "value": value.strip()})
                        else:
                             # Assume it's the 'ndus' token
                             cookie_list.append({"name": "ndus", "value": cookie.strip()})

                        final_cookies = []
                        for c in cookie_list:
                            # Add for both domains to be safe
                            final_cookies.append({**c, "domain": ".terabox.com", "path": "/"})
                            final_cookies.append({**c, "domain": ".1024tera.com", "path": "/"})
                        
                        await context.add_cookies(final_cookies)
                        print(f"Injected {len(cookie_list)} user cookies.")
                    except Exception as e:
                        print(f"Failed to inject cookies: {e}")
                
                # 3. Inject Stealth Scripts (Critical for bypassing bot detection)
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    // Overwrite the `plugins` property to use a custom getter.
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    // Pass the Permissions Query Test
                    const originalQuery = window.navigator.permissions.query;
                    return window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                    );
                """)

                page = await context.new_page()

                # 4. Navigate with extra wait
                print(f"Navigating to {normalized_url}...")
                await page.goto(normalized_url, wait_until="domcontentloaded", timeout=45000)
                
                # Wait for potential redirects or JS execution
                await page.wait_for_timeout(3000) # Give it a moment to settle

                # 5. Check for password protection or validity
                content = await page.content()
                if "Extract code" in content or "input-code" in content:
                     return {"error": "Password-protected links are not supported yet."}
                
                if "The link has expired" in content:
                    return {"error": "This Terabox link has expired or is invalid."}
                    
                if "we can’t find the page" in content or "404" in await page.title():
                    return {"error": "Link was not found (404). It may be deleted or region-blocked."}

                # Detect Login Page Redirect
                if "passport.terabox.com" in page.url or "login" in page.url.lower():
                    return {"error": "LOGIN_REQUIRED", "details": "This file can only be accessed by a logged-in user."}

                # 6. Extract File Info
                # Strategy: Check DOM first (Download Button), then JS variables as fallback.
                
                final_url = None
                filename = "downloaded_file"
                size = 0

                # Check DOM for Download Button
                print("Checking DOM for download button...")
                download_btn = await page.query_selector('.download-btn, .btn-download, a[title="Download"], a:has-text("Download")')
                if download_btn:
                     href = await download_btn.get_attribute('href')
                     if href and href.startswith('http'):
                         final_url = href
                         print(f"Found URL via DOM: {final_url}")
                         
                         # Try to get filename from title or other elements
                         try:
                             title = await page.title()
                             if title and "TeraBox" in title:
                                 # Format: "Filename - Share Files Online..."
                                 clean_name = title.split(" - Share Files")[0].strip()
                                 if clean_name:
                                     filename = clean_name
                         except: pass

                # Fallback: JS Variables
                if not final_url:
                    file_info = await page.evaluate("""() => {
                        try {
                            if (window.yunData && window.yunData.FILEINFO) return window.yunData.FILEINFO[0];
                            if (window.yunData && window.yunData.filelist) return window.yunData.filelist[0];
                            if (window.msg && window.msg.list) return window.msg.list[0];
                        } catch (e) { return null; }
                        return null;
                    }""")

                    if file_info:
                        print(f"Found file info via JS: {file_info.get('server_filename')}")
                        filename = file_info.get('server_filename', filename)
                        size = file_info.get('size', 0)
                        if 'dlink' in file_info:
                            final_url = file_info['dlink']
                     if download_btn:
                         href = await download_btn.get_attribute('href')
                         if href and href.startswith('http'):
                             final_url = href

                if final_url:
                    # Validate URL format
                    if "d.terabox.com" in final_url or "d.1024tera.com" in final_url:
                        pass

                    cookies = await context.cookies()
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                    return {
                        "success": True,
                        "url": final_url,
                        "filename": filename,
                        "size": size,
                        "headers": {
                            "User-Agent": user_agent,
                            "Cookie": cookie_str,
                            "Referer": normalized_url
                        }
                    }
                else:
                    print("Could not find URL on this attempt.")
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                # Wait longer before retrying
                await asyncio.sleep(2 * (attempt + 1))
            
            finally:
                if browser:
                    await browser.close()
        
        return {"error": "Unable to extract file. The link is likely Dead, Blocked, or requires Login/CAPTCHA."}
