import asyncio
from playwright.async_api import async_playwright
import random

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

async def debug_terabox(url):
    async with async_playwright() as p:
        print(f"Launching browser for {url}...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(UA_LIST),
            viewport={"width": 1280, "height": 720}
        )
        
        # Stealth
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        
        page = await context.new_page()
        try:
            print("Navigating...")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"Page Title: {await page.title()}")
            
            # Screenshot
            await page.screenshot(path="debug_terabox.png")
            print("Screenshot saved to debug_terabox.png")
            
            # Dump content
            content = await page.content()
            with open("debug_terabox.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("HTML saved to debug_terabox.html")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    url = "https://1024tera.com/wap/share/filelist?surl=1geUXGdflLPmys2sZPnaaYLg"
    asyncio.run(debug_terabox(url))
