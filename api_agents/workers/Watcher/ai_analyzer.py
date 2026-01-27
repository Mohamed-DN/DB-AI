"""
Forensic AI Analyzer - Processes Watcher Alerts with RAG
Monitors DB_FORENSICS alerts and generates AI-powered root cause analysis.
"""

import sys
import os

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

import time
import json
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Orchestrator.core.mongo_proxy import MongoProxy
from Orchestrator.rag.rag_pipeline import RAGPipeline


class ForensicAnalyzer:
    """
    Analyzes DB_FORENSICS alerts using the RAG pipeline.
    
    Workflow:
    1. Poll MongoDB for unprocessed DB_FORENSICS alerts
    2. Extract forensic_context (log lines)
    3. Send to RAG for diagnosis
    4. Update alert with ai_analysis field
    """
    
    def __init__(self, poll_interval: int = 30):
        self.mongo = MongoProxy()
        self.rag = RAGPipeline()
        self.poll_interval = poll_interval
        self.running = True
        
    def get_pending_forensics(self):
        """Fetch unprocessed DB_FORENSICS alerts"""
        js_query = """
        db.monitoring_alerts.find({
            type: "DB_FORENSICS",
            processed: false,
            ai_analysis: {$exists: false}
        }).toArray()
        """
        return self.mongo.execute_eval(js_query) or []
    
    def analyze_alert(self, alert: dict) -> dict:
        """
        Run RAG analysis on a forensic alert.
        
        Returns analysis dict with diagnosis, confidence, etc.
        """
        error_line = alert.get("full_error") or alert.get("message", "Unknown Error")
        context = alert.get("forensic_context", [])
        db_name = alert.get("db_unique_name", "UNKNOWN")
        
        print(f"   🔬 Analyzing: {error_line[:60]}...")
        
        result = self.rag.diagnose_error(
            error_line=error_line,
            log_context=context,
            additional_info={
                "db_name": db_name,
                "engine": "ORACLE" if "ORA-" in error_line or "TNS-" in error_line else "POSTGRES",
                "timestamp": alert.get("timestamp", "Unknown")
            }
        )
        
        return {
            "diagnosis": result.get("diagnosis", "Analysis failed"),
            "confidence": result.get("confidence", 0),
            "sources_used": [d.get("source") for d in result.get("retrieved_docs", [])],
            "analyzed_at": datetime.now().isoformat(),
            "analyzer_version": "1.0"
        }
    
    def update_alert_with_analysis(self, alert_id: str, analysis: dict) -> bool:
        """Update the alert document with AI analysis"""
        analysis_json = json.dumps(analysis)
        
        js_cmd = f"""
        db.monitoring_alerts.updateOne(
            {{_id: ObjectId("{alert_id}")}},
            {{$set: {{
                ai_analysis: {analysis_json},
                processed: true,
                processed_at: new Date()
            }}}}
        )
        """
        
        result = self.mongo.execute_eval(js_cmd)
        return result is not None
    
    def run_once(self) -> int:
        """Single analysis cycle. Returns count of analyzed alerts."""
        print(f"🧠 Forensic Analyzer: Checking for pending alerts...")
        
        alerts = self.get_pending_forensics()
        
        if not alerts:
            print("   No pending forensic alerts.")
            return 0
        
        print(f"   Found {len(alerts)} alerts to analyze")
        
        analyzed = 0
        for alert in alerts:
            alert_id = alert.get("_id", {}).get("$oid") or str(alert.get("_id"))
            
            try:
                analysis = self.analyze_alert(alert)
                
                if self.update_alert_with_analysis(alert_id, analysis):
                    print(f"   ✅ Alert {alert_id[:8]}... analyzed (Confidence: {analysis['confidence']})")
                    analyzed += 1
                else:
                    print(f"   ⚠️ Failed to update alert {alert_id[:8]}...")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing alert: {e}")
        
        return analyzed
    
    def run_continuous(self):
        """Continuous monitoring loop"""
        print(f"🧠 Forensic AI Analyzer started (Poll interval: {self.poll_interval}s)")
        
        # Initial setup: Seed knowledge base
        print("📚 Ensuring Knowledge Base is seeded...")
        count = self.rag.seed_knowledge_base()
        print(f"   KB ready with {count} seed documents")
        
        while self.running:
            try:
                self.run_once()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                print("\n⏹️ Analyzer stopped")
                break
            except Exception as e:
                print(f"❌ Error in analysis loop: {e}")
                time.sleep(10)
    
    def check_dependencies(self) -> dict:
        """Check all required services are available"""
        return {
            "mongodb": self.mongo.execute_eval("1") == 1,
            "ollama": self.rag.llm.health_check(),
            "qdrant": self.rag.vector_db.health_check()
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Forensic AI Analyzer")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")
    args = parser.parse_args()
    
    analyzer = ForensicAnalyzer(poll_interval=args.interval)
    
    if args.check:
        print("🔍 Checking Dependencies...")
        deps = analyzer.check_dependencies()
        for service, status in deps.items():
            print(f"   {service}: {'✅' if status else '❌'}")
        return
    
    if args.once:
        count = analyzer.run_once()
        print(f"\n📊 Analyzed {count} alerts")
    else:
        analyzer.run_continuous()


if __name__ == "__main__":
    main()
