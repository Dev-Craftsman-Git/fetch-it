import asyncio
import json
from playwright.async_api import async_playwright
import os

URL = "https://terasharefile.com/s/1moHCDFt2bf40AF4RpkwTfg"

async def debug():
    # Load cookie
    if not os.path.exists("cookies.json"):
        print("No cookies.json found!")
        return

    with open("cookies.json") as f:
        cookie_data = json.load(f)
        cookie_val = cookie_data.get("ndus")
    
    print(f"Loaded cookie: {cookie_val[:10]}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        # Inject Cookie logic from scraper.py
        if cookie_val:
            cookie_list = []
            if "=" in cookie_val:
                    parts = cookie_val.split(';')
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            cookie_list.append({"name": key.strip(), "value": value.strip()})
            else:
                    cookie_list.append({"name": "ndus", "value": cookie_val.strip()})

            final_cookies = []
            for c in cookie_list:
                final_cookies.append({**c, "domain": ".terabox.com", "path": "/"})
                final_cookies.append({**c, "domain": ".1024tera.com", "path": "/"})
            
            await context.add_cookies(final_cookies)
            print(f"Injected {len(final_cookies)} cookies.")

        page = await context.new_page()
        
        # Test Normalized URL
        target = URL.replace("terasharefile.com", "1024tera.com")
        print(f"Navigating to {target}...")
        
        try:
            await page.goto(target, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            title = await page.title()
            print(f"Page Title: {title}")
            print(f"Final URL: {page.url}")

            # content = await page.content()
            # print(f"Content snippet: {content[:500]}")
            
            # Check for specific elements
            yunData = await page.evaluate("() => window.yunData")
            print(f"yunData present: {bool(yunData)}")
            
            if yunData:
                 print(f"FILEINFO: {bool(yunData.get('FILEINFO'))}")
                 print(f"filelist: {bool(yunData.get('filelist'))}")

            await page.screenshot(path="debug_cookie.png")
            print("Screenshot saved to debug_cookie.png")

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="debug_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
