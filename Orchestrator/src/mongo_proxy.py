import subprocess
import json
import os

class MongoProxy:
    """Proxy to interact with MongoDB via Docker CLI when PyMongo fails"""
    
    def __init__(self):
        # V2 Support: Read from environment or use defaults
        # V1 defaults: nexi-cmdb-mongo / nexi_cmdb / admin / admin123
        # V2 values:   nexi-mongodb2 / nexi_cmdb_v2 / admin / nexi2024
        self.container = os.environ.get("MONGO_CONTAINER", "nexi-cmdb-mongo")
        self.database = os.environ.get("MONGODB_DB", "nexi_cmdb")
        mongo_user = os.environ.get("MONGO_USERNAME", "admin")
        mongo_pass = os.environ.get("MONGO_PASSWORD", "admin123")
        self.auth_args = ["--username", mongo_user, "--password", mongo_pass, "--authenticationDatabase", "admin"]
    
    def execute_eval(self, eval_js):
        cmd = [
            "docker", "exec", self.container, 
            "mongosh", self.database
        ] + self.auth_args + ["--quiet", "--eval", f"JSON.stringify({eval_js})"]
        
        try:
            # print(f"Executing: {eval_js}")
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8')
            print(f"MongoProxy Result: {result}")
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

    def get_pending_alerts(self):
        # Fetch both CRITICAL and WARNING
        js_cmd = 'db.monitoring_alerts.find({state: {$in: ["CRITICAL", "WARNING"]}, processed: {$ne: true}}).toArray()'
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

    def get_inventory(self):
        js = "db.inventory_databases.find().toArray()"
        return self.execute_eval(js) or []

    def update_metrics(self, db_name, metrics):
        m_json = json.dumps(metrics)
        js = f"db.inventory_databases.updateOne({{ 'identity.db_unique_name': '{db_name}' }}, {{ $set: {{ 'state.metrics': {m_json}, 'state.last_metric_update': new Date() }} }})"
        return self.execute_eval(js)

    def upsert_database(self, db_doc):
        # Handle datetime serialization
        doc_json = json.dumps(db_doc, default=str)
        name = db_doc.get('identity', {}).get('db_unique_name')
        if not name: return None
        
        js_cmd = f"db.inventory_databases.updateOne({{ 'identity.db_unique_name': '{name}' }}, {{ $set: {doc_json} }}, {{ upsert: true }})"
        return self.execute_eval(js_cmd)

    def update_status(self, db_name, status):
        """Update just the status field"""
        js = f"db.inventory_databases.updateOne({{ 'identity.db_unique_name': '{db_name}' }}, {{ $set: {{ 'state.status': '{status}', 'state.last_check': new Date() }} }})"
        return self.execute_eval(js)
