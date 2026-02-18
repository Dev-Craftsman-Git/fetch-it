import requests
import json

def test_endpoint(url, name, test_url):
    print(f"Testing {name} at {url} with {test_url}...")
    try:
        payload = {"url": test_url}
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response Text: {response.text[:200]}")
        
        if response.status_code in [200, 400, 422]:
            print(f"[OK] {name} is reachable.")
        else:
            print(f"[FAIL] {name} returned unexpected status.")
            
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] {name} is NOT reachable (Connection Refused).")
    except Exception as e:
        print(f"[ERR] {name} failed with error: {e}")
    print("-" * 30)

if __name__ == "__main__":
    # 1. Test YouTube (yt-dlp)
    print("Testing YouTube (yt-dlp)...")
    test_endpoint("http://localhost:8000/api/resolve", "YouTube Test", "https://www.youtube.com/watch?v=jNQXAC9IVRw") # Me at the zoo
    
    # 2. Test Terabox (Custom Scraper) - Expecting failure/block but checking routing
    print("\nTesting Terabox (Custom Scraper)...")
    test_endpoint("http://localhost:8000/api/resolve", "Terabox Test", "https://teraboxurl.com/s/1zdtsNGLVL1C7TMpKcn6JzA")
