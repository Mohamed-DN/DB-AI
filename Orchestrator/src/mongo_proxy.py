import subprocess
import json
import os

class MongoProxy:
    """Proxy to interact with MongoDB via Docker CLI when PyMongo fails"""
    
    def __init__(self):
        self.container = "nexi-mongodb"
        self.auth_args = ["--username", "admin", "--password", "nexi2024", "--authenticationDatabase", "admin"]
    
    def execute_eval(self, eval_js):
        cmd = [
            "docker", "exec", self.container, 
            "mongosh", "nexi_cmdb"
        ] + self.auth_args + ["--quiet", "--eval", f"JSON.stringify({eval_js})"]
        
        try:
            # print(f"Executing: {eval_js}")
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8')
            return json.loads(result)
        except subprocess.CalledProcessError as e:
            print(f"MongoProxy Error: {e.stderr.decode('utf-8')}")
            return None
        except Exception as e:
            print(f"MongoProxy Exception: {e}")
            return None

    def insert_alert(self, alert_dict):
        # Handle datetime serialization
        alert_json = json.dumps(alert_dict, default=str)
        # We need to construct a JS object. Date objects are strings in JSON, 
        # but we might want real Dates. For now string is fine.
        js_cmd = f"db.monitoring_alerts.insertOne({alert_json})"
        return self.execute_eval(js_cmd)

    def get_pending_critical_alerts(self):
        js_cmd = 'db.monitoring_alerts.find({state: "CRITICAL", processed: {$ne: true}}).toArray()'
        return self.execute_eval(js_cmd)

    def mark_as_processed(self, alert_id, analysis):
        # alert_id from JSON is string if ObjectId. 
        # Need to wrap in ObjectId() if it's an ID.
        # But wait, find().toArray() returns _id as string? 
        # mongosh JSON.stringify might return specific format.
        # Let's assume input id is string.
        analysis_json = json.dumps(analysis)
        js_cmd = f"db.monitoring_alerts.updateOne({{_id: ObjectId('{alert_id}')}}, {{$set: {{processed: true, ai_analysis: {analysis_json}}}}})"
        return self.execute_eval(js_cmd)
