import yt_dlp
import json

url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo (low quality, let's pick a better one)
# url = "https://www.youtube.com/watch?v=BaW_jenozKc" # Hello World
url = "https://www.youtube.com/watch?v=LXb3EKWsInQ" # Costa Rica 4K

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    formats = info.get('formats', [])
    
    print(f"Title: {info.get('title')}")
    print(f"Total Formats: {len(formats)}")
    
    for f in formats:
        # Filter for relevant fields
        f_id = f.get('format_id')
        ext = f.get('ext')
        res = f.get('resolution')
        note = f.get('format_note')
        vcodec = f.get('vcodec')
        acodec = f.get('acodec')
        filesize = f.get('filesize')
        
        has_video = vcodec != 'none'
        has_audio = acodec != 'none'
        
        print(f"[{f_id}] {ext} {res} ({note}) | V:{has_video} A:{has_audio} | Size: {filesize}")
