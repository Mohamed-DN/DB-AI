"""
AI Orchestrator - Main Brain
Monitors alerts and uses LLM to orchestrate response.
"""
import sys
import time
import json
from datetime import datetime
sys.path.append('../../')

from Orchestrator.src.mongo_proxy import MongoProxy
from Orchestrator.src.llm_client import LLMClient
from Agents.CriticalAlert.main import EmailSender

class AIOrchestrator:
    def __init__(self):
        # self.alerts_col = get_collection("monitoring_alerts")
        self.mongo_proxy = MongoProxy()
        
        self.llm = LLMClient()
        self.emailer = EmailSender()
        self.processed_ids = set()

    def check_new_alerts(self):
        """Check for new CRITICAL alerts"""
        # Use proxy to find
        alerts = self.mongo_proxy.get_pending_critical_alerts()
        # alerts is a list of dicts (parsed from JSON)
        return alerts if alerts else []

    def process_alert(self, alert):
        """Process a single alert with AI"""
        print(f"\n🤖 AI Processing Alert for: {alert.get('host_name')}...")
        
        # 1. Ask LLM to analyze
        analysis = self.llm.analyze_alert(alert)
        
        print(f"   🧠 LLM Analysis: {analysis.get('action', 'UNKNOWN')}")
        
        # 2. Execute Action
        if "EMAIL" in str(analysis.get('action', '')).upper() or "DOWN" in alert.get('output', ''):
            subject = analysis.get('email_subject', f"CRITICAL: {alert.get('host_name')} is DOWN")
            body = analysis.get('email_body', alert.get('output'))
            
            print(f"   📨 Sending Email to Mohamed...")
            self.emailer.send_alert(
                "mohamed.d.n.2002@gmail.com",
                subject,
                body
            )
            
            # Mark as processed
            alert_id = alert["_id"]
            self.mongo_proxy.mark_as_processed(alert_id, analysis)

    def run_loop(self):
        print("🧠 AI Orchestrator Started - Waiting for disasters...")
        while True:
            alerts = self.check_new_alerts()
            if alerts:
                print(f"⚠️ Detected {len(alerts)} new critical alerts!")
                for alert in alerts:
                    if str(alert["_id"]) not in self.processed_ids:
                        self.process_alert(alert)
                        self.processed_ids.add(str(alert["_id"]))
            
            time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once")
    args = parser.parse_args()
    
    orch = AIOrchestrator()
    if args.once:
        print("🧠 AI Orchestrator Running ONCE")
        count = 0
        alerts = orch.check_new_alerts()
        if alerts:
            print(f"⚠️ Detected {len(alerts)} new critical alerts!")
            for alert in alerts:
                if str(alert["_id"]) not in orch.processed_ids:
                    orch.process_alert(alert)
                    count += 1
        print(f"✅ Processed {count} alerts.")
    else:
        orch.run_loop()
