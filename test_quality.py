import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_quality_flow():
    print("1. Resolving URL...")
    # Use a video with 4K/1080p
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo (Short, likely only has 240p/etc but let's see format logic)
    # Better test video: Costa Rica 4K
    video_url = "https://www.youtube.com/watch?v=LXb3EKWsInQ"
    
    resp = requests.post(f"{BASE_URL}/api/resolve", json={"url": video_url})
    if resp.status_code != 200:
        print(f"Resolve failed: {resp.text}")
        return

    data = resp.json()
    print("Resolved!")
    print(f"Title: {data.get('title')}")
    formats = data.get("formats", [])
    print(f"Found {len(formats)} formats.")
    
    # Print formats
    for f in formats:
        print(f" - {f['label']} ({f['ext']}) Direct: {f['is_direct']}")

    # Find a processed format (not direct)
    processed_fmt = next((f for f in formats if not f['is_direct']), None)
    
    if not processed_fmt:
        print("No processed formats found. Skipping process test.")
        return

    print(f"\n2. Testing Processing for {processed_fmt['label']}...")
    print("Sending process request (this might take time)...")
    
    start_time = time.time()
    proc_resp = requests.post(f"{BASE_URL}/api/process", json={
        "url": data.get("webpage_url") or video_url,
        "format_id": processed_fmt['format_id']
    }, timeout=300) # Long timeout for download
    
    if proc_resp.status_code != 200:
        print(f"Processing failed: {proc_resp.text}")
        return
        
    proc_data = proc_resp.json()
    print(f"Processing Complete in {time.time() - start_time:.2f}s!")
    print(f"File ID: {proc_data.get('fileId')}")
    
    print("\n3. Verifying Download Link...")
    dl_url = f"{BASE_URL}/api/download/{proc_data.get('fileId')}"
    dl_resp = requests.head(dl_url)
    print(f"Download Status: {dl_resp.status_code}")
    print(f"Content Type: {dl_resp.headers.get('Content-Type')}")
    print(f"Content Length: {dl_resp.headers.get('Content-Length')}")
    
    if dl_resp.status_code == 200:
        print("SUCCESS: High-Res Audio Download Verified!")
    else:
        print("FAILED: Download link not accessible.")

if __name__ == "__main__":
    test_quality_flow()
