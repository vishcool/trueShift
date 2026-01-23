import requests
import sys

BASE_URL = "http://localhost:8000"
API_V1_BASE = f"{BASE_URL}/api/v1"

def test_endpoint(name, url, method="GET", expected_status=200):
    try:
        print(f"Testing {name} ({method} {url})...", end=" ")
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url)
        
        if response.status_code == expected_status:
            print(f"✅ OK ({response.status_code})")
            return True
        else:
            print(f"❌ FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED (Connection Error - Is the server running on {BASE_URL}?)")
        return False

def main():
    print("--- TrueShift API Verification ---")
    
    # 1. Test Root Health (from main.py)
    test_endpoint("Root Health", f"{BASE_URL}/health")

    # 2. Test API v1 Health (from routers)
    test_endpoint("API v1 Health", f"{API_V1_BASE}/health")

    # 3. Test Auth Me (Expected 401 Unauthorized without token, confirming route exists)
    test_endpoint("Auth Me (Route Check)", f"{API_V1_BASE}/auth/me", expected_status=401)
    
    # 4. Test Docs
    test_endpoint("API Docs", f"{BASE_URL}/docs")
    
    print("\n----------------------------------")

if __name__ == "__main__":
    main()
