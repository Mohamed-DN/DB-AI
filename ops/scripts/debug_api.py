
import requests
import json

try:
    print("🌍 Testing API Connection: http://localhost:8000/api/oem/instances")
    response = requests.get("http://localhost:8000/api/oem/instances", timeout=5)
    
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Data Received: {len(data)} items")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Connection Failed: {e}")
