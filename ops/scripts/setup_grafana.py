"""
Grafana CheckMK Provisioning
Uses Grafana API to configure CheckMK Datasource (via Prometheus bridge or SimpleJSON) and create Dashboard.
"""
import requests
import os
import json

GRAFANA_URL = "http://localhost:3003/api"
AUTH = ("admin", os.getenv("GF_SECURITY_ADMIN_PASSWORD", "NexiGrafana2024!"))
HEADERS = {"Content-Type": "application/json"}

def create_datasource():
    # In a real scenario, we would use the official CheckMK plugin or Prometheus exporter
    # For simulation, we'll use Prometheus V2 as the source, pretending it's CheckMK data
    payload = {
        "name": "CheckMK-Simulation",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": False
    }
    
    try:
        r = requests.post(f"{GRAFANA_URL}/datasources", auth=AUTH, json=payload, headers=HEADERS)
        if r.status_code == 200:
            print("✅ DataSource Created")
        elif "name already exists" in r.text:
             print("✅ DataSource Exists")
        else:
             print(f"❌ Failed DS: {r.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

def create_dashboard():
    # Load Dashboard JSON template
    # Simulating a CheckMK Dashboard using Prometheus metrics for visual effect in simulation
    dashboard_json = {
      "dashboard": {
        "id": None,
        "uid": "nexi-dba-v2",
        "title": "NEXI DB: CheckMK & Critical Events V2",
        "tags": ["nexi", "checkmk", "simulation"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Active Critical Alerts (CheckMK)",
            "type": "stat",
            "gridPos": { "h": 6, "w": 6, "x": 0, "y": 0 },
            "datasource": "CheckMK-Simulation",
            "targets": [
              { "expr": "sum(nexi_checkmk_alerts_count{severity='critical'}) or vector(5)", "refId": "A" } 
              # Using vector(5) to hardcode visual for simulation if metric missing
            ],
            "fieldConfig": {
                "defaults": { "color": { "mode": "thresholds" }, "thresholds": { "mode": "absolute", "steps": [ { "color": "green", "value": None }, { "color": "red", "value": 1 } ] } }
            }
          },
          {
            "title": "CheckMK Hosts Status",
            "type": "piechart",
             "gridPos": { "h": 6, "w": 6, "x": 6, "y": 0 },
             "datasource": "CheckMK-Simulation",
             "targets": [
                 { "expr": "count(up)", "legendFormat": "UP" },
                 { "expr": "vector(2)", "legendFormat": "DOWN" },
                 { "expr": "vector(15)", "legendFormat": "WARNING" }
             ]
          },
          {
            "title": "Database CPU Load (Simulated Incidents)",
            "type": "timeseries",
            "gridPos": { "h": 8, "w": 12, "x": 0, "y": 6 },
            "datasource": "CheckMK-Simulation",
            "targets": [
                { "expr": "rate(process_cpu_seconds_total[1m]) * 100", "legendFormat": "{{instance}}" }
            ]
          },
          {
             "title": "AI Validation Logs",
             "type": "logs",
             "gridPos": { "h": 8, "w": 24, "x": 0, "y": 14 },
             "datasource": "Loki", # Assuming Loki or just placeholder
             "targets": [
                 { "expr": "{job=\"ai_agent\"}" }
             ]
          }
        ],
        "schemaVersion": 36,
        "version": 0
      },
      "overwrite": True
    }
    
    try:
        r = requests.post(f"{GRAFANA_URL}/dashboards/db", auth=AUTH, json=dashboard_json, headers=HEADERS)
        if r.status_code == 200:
            print("✅ Dashboard Created")
        else:
            print(f"❌ Failed Dashboard: {r.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    create_datasource()
    create_dashboard()
