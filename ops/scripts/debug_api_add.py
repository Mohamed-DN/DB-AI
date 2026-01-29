
import requests
import json

url = "http://localhost:8000/api/oem/instances"
payload = {
    "name": "OEM Docker Beast",
    "url": "https://oemserver:7802/em",
    "username": "sysman",
    "password": "password123",
    "verify_ssl": False
}

try:
    print(f"🌍 POST {url}...")
    response = requests.post(url, json=payload, timeout=5)
    
    print(f"📊 Status: {response.status_code}")
    print(f"📄 Response: {response.text}")

except Exception as e:
    print(f"❌ Failed: {e}")
