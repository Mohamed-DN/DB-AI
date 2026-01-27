
import requests
import time
import sys

VM_HOST = "localhost"
VM_PORT = 8428
INFLUX_URL = f"http://{VM_HOST}:{VM_PORT}/write"

def test_ingest():
    print(f"📉 Testing VictoriaMetrics Ingestion at {INFLUX_URL}...")
    
    # InfluxDB Line Protocol format
    # measurement,tag_set field_set timestamp
    metric_line = f"rali_test_metric,host=test_script value=1.0 {int(time.time() * 1e9)}"
    
    try:
        response = requests.post(INFLUX_URL, data=metric_line)
        if response.status_code == 204:
            print("✅ Metric inserted successfully (HTTP 204)")
        else:
            print(f"❌ Failed to insert metric: {response.status_code} - {response.text}")
            sys.exit(1)
            
        # Verify Retrieval
        query_url = f"http://{VM_HOST}:{VM_PORT}/api/v1/query"
        print("📈 Verifying retrieval...")
        time.sleep(1) # tiny wait for commit
        r = requests.get(query_url, params={"query": "rali_test_metric"})
        data = r.json()
        
        if data["status"] == "success" and len(data["data"]["result"]) > 0:
             print(f"✅ Metric retrieved: {data['data']['result'][0]['metric']}")
        else:
             print(f"⚠️  Metric inserted but not retrieved yet (async commit?). Response: {data}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_ingest()
