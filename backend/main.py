import uuid
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from universal_downloader import UniversalDownloader
import os
import shutil
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for file metadata (URL, headers, etc.)
# Key: file_id, Value: dict
FILE_CACHE = {}

class URLRequest(BaseModel):
    url: str
    cookie: Optional[str] = None

class ProcessRequest(BaseModel):
    url: str
    format_id: str

import json

# Cookie Storage
COOKIE_FILE = "cookies.json"

def load_stored_cookie():
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("ndus")
        except:
            return None
    return None

def save_stored_cookie(cookie_value):
    with open(COOKIE_FILE, 'w') as f:
        json.dump({"ndus": cookie_value}, f)

@app.post("/api/resolve")
async def resolve_url(request: URLRequest):
    # Use provided cookie OR fallback to stored cookie
    effective_cookie = request.cookie or load_stored_cookie()
    
    print(f"Resolving URL: {request.url} (Cookie Active: {bool(effective_cookie)})")
    
    # If a cookie was provided in this request, suggest saving it? 
    # For now, we just use it.
    
    result = await UniversalDownloader.resolve(request.url, effective_cookie)
    
    if "error" in result:
        return JSONResponse(status_code=400, content={"success": False, "error": result["error"], "details": result.get("details")})
    
    # Smart Auth: If the request succeeded with a manually provided cookie, save it for future use.
    if request.cookie:
        print("Auto-saving working cookie for future requests.")
        save_stored_cookie(request.cookie)
    
    file_id = str(uuid.uuid4())
    FILE_CACHE[file_id] = result
    
    return {
        "success": True, 
        "fileId": file_id, 
        "url": result.get("url"), # Direct URL (useful for 720p/legacy)
        "webpage_url": result.get("webpage_url"), # Original URL (needed for processing)
        "filename": result.get("filename", "download"), 
        "size": result.get("size", 0),
        "thumbnail": result.get("thumbnail"), 
        "title": result.get("title"),
        "formats": result.get("formats", [])
    }

@app.post("/api/process")
async def process_media(request: ProcessRequest):
    print(f"Processing media: {request.url} (Format: {request.format_id})")
    file_path, filename = await UniversalDownloader.process_download(request.url, request.format_id)
    
    if not file_path:
        return JSONResponse(status_code=500, content={"success": False, "error": "Processing failed"})
    
    # Store minimal metadata to map file_id to filename on disk
    # We use the filename (uuid.mp4) prefix as the ID
    file_id = filename.split('.')[0]
    
    return {
        "success": True,
        "fileId": file_id,
        "filename": filename,
        "processed": True
    }

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    print(f"Download request: {file_id}")
    
    # 1. Check for processed file on disk
    if os.path.exists("downloads"):
        for f in os.listdir("downloads"):
            if f.startswith(file_id):
                file_path = os.path.join("downloads", f)
                print(f"Serving local file: {file_path}")
                return FileResponse(file_path, filename=f, media_type="application/octet-stream")

    # 2. Check for direct download in cache
    if file_id not in FILE_CACHE:
        print("File ID not found in cache or disk")
        raise HTTPException(status_code=404, detail="File link expired or invalid")
    
    file_data = FILE_CACHE[file_id]
    download_url = file_data["url"]
    headers = file_data.get("headers", {})
    filename = file_data["filename"]
    
    print(f"Proxying download from: {download_url}")
    
    return StreamingResponse(
        proxy_download(download_url, headers),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

async def proxy_download(url, headers):
    async with aiohttp.ClientSession() as session:
        # Filter headers that might cause issues?
        # Usually User-Agent and Cookie are strict requirements for Terabox.
        cleaned_headers = {k: v for k, v in headers.items() if k in ['User-Agent', 'Cookie', 'Referer']}
        
        try:
            async with session.get(url, headers=cleaned_headers) as resp:
                if resp.status != 200:
                    print(f"Upstream error: {resp.status}")
                    yield b"" # Close stream effectively
                    return

                async for chunk in resp.content.iter_chunked(1024 * 1024): # 1MB chunks for better throughput
                    yield chunk
        except Exception as e:
            print(f"Proxy download error: {e}")
            yield b""

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    # Clean up old partial downloads on startup
    for f in os.listdir("downloads"):
        if f.endswith(".part"):
            try:
                os.remove(os.path.join("downloads", f))
            except: pass

    uvicorn.run(app, host="0.0.0.0", port=8000)
