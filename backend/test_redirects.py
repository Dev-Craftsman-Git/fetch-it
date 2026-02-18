import requests

urls = [
    "https://www.1024tera.com/share/list?app_id=250528&shorturl=1geUXGdflLPmys2sZPnaaYLg&root=1",
    "https://www.1024tera.com/share/list?app_id=250528&shorturl=geUXGdflLPmys2sZPnaaYLg&root=1", # Stripped 1
    "https://terabox.com/share/list?app_id=250528&shorturl=1geUXGdflLPmys2sZPnaaYLg&root=1"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

for url in urls:
    try:
        print(f"Testing {url}...")
        resp = requests.get(url, headers=headers, allow_redirects=True)
        print(f"Status: {resp.status_code}")
        if "404" in resp.url or "error" in resp.url:
             print("Redirected to Error")
        elif len(resp.text) < 5000:
             print("Content too short, likely error/captcha")
        else:
             print("Potentially valid content!")
    except Exception as e:
        print(e)
