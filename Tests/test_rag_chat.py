import requests

url = "http://localhost:8001/chat"
query = {
    "message": "Come risolvo un errore ORA-00600? Cerca nelle knowledge base.",
    "session_id": "test_rag"
}

try:
    response = requests.post(url, json=query, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Failed: {e}")
