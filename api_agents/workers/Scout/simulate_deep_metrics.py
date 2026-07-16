"""
metric_simulator.py
Simulates the collection of "Deep Observability" metrics (Internal DB stuff)
and "CheckMK" external metrics, pushing them to MongoDB.
"""

import sys
import os
import json
import random
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from orchestrator.core.mongo_proxy import MongoProxy

class MetricSimulator:
    def __init__(self):
        self.mongo = MongoProxy()
        self.targets = ["M-DN-ORACLE-CAIRO-PRIMARY", "M-DN-PG-MILANO-PROD"]

    def generate_oracle_metrics(self):
        return {
            "tablespaces": [
                {"name": "SYSTEM", "size_gb": 10, "used_gb": 8.5, "status": "ONLINE"},
                {"name": "SYSAUX", "size_gb": 15, "used_gb": 12.0, "status": "ONLINE"},
                {"name": "USERS", "size_gb": 100, "used_gb": 85.0, "autoextend": True},
                {"name": "DATA_APP", "size_gb": 500, "used_gb": 320.0, "autoextend": True}
            ],
            "asm_diskgroups": [
                {"name": "DATA", "redundancy": "EXTERNAL", "total_mb": 204800, "free_mb": 45000},
                {"name": "RECO", "redundancy": "EXTERNAL", "total_mb": 102400, "free_mb": 80000}
            ],
            "fra_usage_pct": random.randint(20, 60),
            "blocking_sessions": []
        }

    def generate_dataguard_metrics(self):
        return {
            "status": "LOG_APPLY_ON",
            "protection_mode": "MAX_AVAILABILITY",
            "transport_lag_seconds": random.randint(0, 5),
            "apply_lag_seconds": random.randint(0, 10),
            "last_applied_log": 45021
        }

    def generate_rman_metrics(self):
        return {
             "last_backup_status": "COMPLETED",
             "last_backup_time": datetime.now().isoformat(),
             "input_type": "DB FULL",
             "duration_sec": 3600
        }

    def update_db(self, db_name):
        print(f"💉 Injecting Deep Metrics for {db_name}...")
        
        deep_obs = {
            "last_update": "new Date()",
            "oracle_internals": self.generate_oracle_metrics(),
            "data_protection": {
                "rman": self.generate_rman_metrics(),
                "dataguard": self.generate_dataguard_metrics()
            },
            "performance_metrics": {
                "cpu_load": random.uniform(1.0, 5.0),
                "db_time_wait": 120,
                "top_events": ["db file sequential read", "CPU"]
            },
            "external_metrics": {
                "checkmk": {
                    "host_state": "UP",
                    "cpu_util": random.randint(10, 80),
                    "mem_used_pct": random.randint(40, 90),
                    "notes": "Imported from CheckMK Bridge"
                }
            }
        }
        
        # Construct update query
        # Using json.dumps to stringify python dicts, but need to handle the new Date()
        # manual construction or placeholder replacement
        
        json_str = json.dumps(deep_obs)
        json_str = json_str.replace('"new Date()"', "new Date()") 
        
        js_cmd = f"""
        db.inventory_databases.updateOne(
            {{ "identity.db_unique_name": "{db_name}" }},
            {{ $set: {{ "deep_observability": {json_str} }} }}
        )
        """
        
        self.mongo.execute_eval(js_cmd)
        print("   ✅ Injection Complete")

    def run(self):
        for t in self.targets:
            self.update_db(t)

if __name__ == "__main__":
    sim = MetricSimulator()
    sim.run()
