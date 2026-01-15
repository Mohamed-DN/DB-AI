import sys
import os
import json
import datetime
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from orchestrator.core.mongo_proxy import MongoProxy

class DailyAuditAgent:
    def __init__(self):
        try:
            self.mongo = MongoProxy()
            print("[OK] Connected to MongoDB")
        except Exception as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
            sys.exit(1)
            
    def parse_size(self, size_str):
        """Parse size string (e.g. '1.5GB', '500MB') to GB"""
        if not size_str or size_str == "N/A": return 0.0
        
        # Remove / and second part if present (e.g. "1.5GB / 10GB")
        if "/" in size_str:
            size_str = size_str.split("/")[0].strip()
            
        units = {'B': 1e-9, 'KB': 1e-6, 'MB': 1e-3, 'GB': 1, 'TB': 1000}
        unit = "".join([c for c in size_str if c.isalpha()]).upper()
        if unit == "IB": unit = "B" # Fix for MiB?
        if unit.endswith("IB"): unit = unit[:-2] + "B" # MiB -> MB logic approx? 
        # Actually MiB is 1024 based, but let's approximate
        
        # Regex for number
        val_match = re.search(r"([\d\.]+)", size_str)
        if not val_match: return 0.0
        val = float(val_match.group(1))
        
        # Simple suffix mapping
        if 'T' in size_str: mult = 1000
        elif 'G' in size_str: mult = 1
        elif 'M' in size_str: mult = 0.001
        elif 'K' in size_str: mult = 0.000001
        else: mult = 1e-9
        
        return val * mult

    def check_compliance(self):
        print("[INFO] Starting Daily Audit...")
        
        dbs = self.mongo.execute_eval("db.inventory_databases.find().toArray()")
        services = self.mongo.execute_eval("db.business_services.find().toArray()")
        
        report_items = []
        
        for db in dbs:
            name = db.get('identity', {}).get('db_unique_name', 'Unknown')
            engine = db.get('identity', {}).get('engine', 'Unknown')
            version = db.get('configuration', {}).get('version', 'Unknown')
            
            # 1. Licensing / Obsolescence Check
            eol_status = "OK"
            if engine == 'POSTGRES' and version.startswith('11'):
                eol_status = "WARNING: EOL Soon"
            if engine == 'ORACLE' and '11' in version:
                eol_status = "CRITICAL: EOL"
                
            # 2. Capacity Check
            metrics = db.get('state', {}).get('metrics', {})
            disk_str = metrics.get('disk_io', '0B') # Often formatted as "Used / Total" or just IO? 
            # Actually Collector puts "disk_io" as I/O rate, NOT storage usage.
            # We don't have storage usage in current collector!
            # We need to query 'df -h' inside container.
            # For now, we mock/skip or rely on 'ram_usage' as proxy for liveness.
            # Let's mark Capacity as "Not Monitored" for now.
            capacity_status = "NOT MONITORED (Agent update required)"
            
            # 3. Best Practices
            # Mock: Check connection count
            best_practice_issues = []
            if db.get('connection', {}).get('type') == 'DOCKER':
                 best_practice_issues.append("Running in Container (Non-Prod Best Practice?)")

            report_items.append({
                "name": name,
                "engine": engine,
                "version": version,
                "eol": eol_status,
                "capacity": capacity_status,
                "issues": best_practice_issues
            })

        self.generate_report(report_items)

    def generate_report(self, items):
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .critical { color: red; font-weight: bold; }
                .warning { color: orange; }
            </style>
        </head>
        <body>
            <h2>Daily Database Audit Report</h2>
            <p>Generated at: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <table>
                <tr>
                    <th>Database</th>
                    <th>Engine</th>
                    <th>Version</th>
                    <th>Obsolescence</th>
                    <th>Capacity</th>
                    <th>Best Practices</th>
                </tr>
        """
        
        for item in items:
            eol_class = "critical" if "CRITICAL" in item['eol'] else ("warning" if "WARNING" in item['eol'] else "ok")
            
            html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item['engine']}</td>
                    <td>{item['version']}</td>
                    <td class="{eol_class}">{item['eol']}</td>
                    <td>{item['capacity']}</td>
                    <td>{", ".join(item['issues'])}</td>
                </tr>
            """
            
        html += """
            </table>
            <p>To configure policies, contact the Global DBA Team.</p>
        </body>
        </html>
        """
        
        # Save locally
        filename = f"Audit_Report_{datetime.datetime.now().strftime('%Y%m%d')}.html"
        path = os.path.join(os.path.dirname(__file__), '../../emails', filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"[OK] Report generated: {path}")

if __name__ == "__main__":
    agent = DailyAuditAgent()
    agent.check_compliance()
