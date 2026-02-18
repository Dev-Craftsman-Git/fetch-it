import yt_dlp
import asyncio
import os
import uuid
from scraper import extract_terabox_url

# Directory for processed downloads
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class UniversalDownloader:
    @staticmethod
    async def resolve(url: str, cookie: str = None):
        # 1. Custom Handlers
        if any(x in url for x in ["terabox", "1024tera", "terashare", "miracledown", "teraboxapp"]):
            return await extract_terabox_url(url, cookie)
            
        # 2. General Handler (yt-dlp)
        return await UniversalDownloader._fetch_with_ytdlp(url)

    @staticmethod
    async def _fetch_with_ytdlp(url: str):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: UniversalDownloader._ytdlp_extract(url, ydl_opts))
            
            formats = []
            seen_res = set()
            
            # Extract available formats
            all_formats = info.get('formats', [])
            
            # Sort order:
            # 1. Resolution (Height) - Descending
            # 2. Extension is mp4 (for compatibility/speed) - True first
            # 3. Bitrate (tbr) - Descending
            all_formats.sort(key=lambda x: (
                x.get('height') or 0, 
                1 if x.get('ext') == 'mp4' else 0, 
                x.get('tbr') or 0
            ), reverse=True)
            
            for f in all_formats:
                height = f.get('height')
                if not height: continue
                
                # We want unique resolutions for the UI
                if height in seen_res: continue
                
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                is_video = vcodec != 'none'
                has_audio = acodec != 'none'
                
                if not is_video: continue

                # Determine if direct or processed
                is_direct = has_audio
                
                formats.append({
                    "label": f"{height}p",
                    "format_id": f['format_id'],
                    "ext": f['ext'],
                    "resolution": f.get('resolution'),
                    "filesize": f.get('filesize'),
                    "is_direct": is_direct,
                    "url": f.get('url') if is_direct else None # Only expose URL if direct
                })
                seen_res.add(height)

            return {
                "success": True,
                "url": info.get('url'), # Default (likely best)
                "webpage_url": info.get('webpage_url'), # Original URL for processing
                "title": info.get('title'),
                "filename": info.get('title', 'download') + '.' + info.get('ext', 'mp4'),
                "size": info.get('filesize', 0),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            }
        except Exception as e:
            return {"error": f"Supported site extraction failed: {str(e)}"}

    @staticmethod
    def _ytdlp_extract(url, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    async def process_download(url: str, format_id: str):
        """
        Downloads and merges the specific format with best audio.
        Returns the path to the local file.
        """
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp4"
        output_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Optimize: Request M4A audio to match MP4 video for instant merge (avoids re-encode)
        ydl_opts = {
            'format': f'{format_id}+bestaudio[ext=m4a]/bestaudio',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{file_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': './', # Assumes ffmpeg.exe is in current dir
            'concurrent_fragment_downloads': 4, # Tuned: 4 is often more stable than 8
            'buffersize': 1024 * 1024, # 1MB buffer
            'http_chunk_size': 10485760, # 10MB chunks
            'retries': 10, # Add retries
            'fragment_retries': 10,
        }
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: UniversalDownloader._ytdlp_download(url, ydl_opts))
            
            # yt-dlp might have saved it as .mkv or other container if merge failed or wasn't needed
            # Check for the file
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(file_id):
                    return os.path.join(DOWNLOAD_DIR, f), f 
            
            return None, None
        except Exception as e:
            print(f"Processing failed: {e}")
            return None, None

    @staticmethod
    def _ytdlp_download(url, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
