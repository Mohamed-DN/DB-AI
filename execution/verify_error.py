import requests
try:
    response = requests.post("http://localhost:8001/chat", json={"message": "hi", "session_id": "test"}, timeout=10)
    print(response.json())
except Exception as e:
    print(e)
