"""
CriticalAlert Agent - Real-time monitoring and email alerts
"""
import os
import time
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class EmailSender:
    """Send email alerts via SMTP"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
    
    def send_alert(self, to_email: str, subject: str, body: str) -> bool:
        """Send an alert email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"🚨 DBA AI ALERT: {subject}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #ff4444; color: white; padding: 20px; text-align: center;">
                    <h1>⚠️ CRITICAL DATABASE ALERT</h1>
                </div>
                <div style="padding: 20px;">
                    <h2>{subject}</h2>
                    <p style="font-size: 16px;">{body}</p>
                    <hr>
                    <p style="color: gray; font-size: 12px;">
                        Sent by Nexi DBA AI CriticalAlert Agent<br>
                        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            if self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                print(f"✅ [REAL EMAIL] Sent to {to_email}")
            else:
                # Simulate email if no SMTP configured
                print(f"📧 [SIMULATED EMAIL] To: {to_email}")
                print(f"   Subject: {subject}")
                print(f"   Body: {body[:100]}...")

            # Save to file for verification
            try:
                # Assuming running from Agents/CriticalAlert/ or root, try to find root
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                emails_dir = os.path.join(base_dir, 'emails')
                if not os.path.exists(emails_dir):
                    os.makedirs(emails_dir)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                clean_subject = "".join([c if c.isalnum() else "_" for c in subject])[:30]
                filename = os.path.join(emails_dir, f"email_{timestamp}_{clean_subject}.html")
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html_body)
                print(f"    💾 Email saved to: {filename}")
            except Exception as e:
                print(f"    ❌ Failed to save email to file: {e}")

            return True
                
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


class PostgresChecker:
    """Check PostgreSQL database status"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str, name: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.name = name
    
    def check_connection(self) -> Dict:
        """Check if database is accessible"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=5
            )
            conn.close()
            return {"status": "OK", "name": self.name}
        except Exception as e:
            return {"status": "DOWN", "name": self.name, "error": str(e)}
    
    def check_storage(self) -> Dict:
        """Check database storage usage"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=5
            )
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("SELECT pg_database_size(current_database());")
            db_size_bytes = cursor.fetchone()[0]
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            # Get tablespace usage (simulated threshold)
            # In real scenario, check disk space
            cursor.execute("SELECT count(*) FROM pg_stat_user_tables;")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "OK",
                "name": self.name,
                "size_mb": round(db_size_mb, 2),
                "table_count": table_count
            }
        except Exception as e:
            return {"status": "ERROR", "name": self.name, "error": str(e)}


class CriticalAlertAgent:
    """Main CriticalAlert agent"""
    
    def __init__(self, alert_email: str):
        self.alert_email = alert_email
        self.email_sender = EmailSender()
        self.databases = []
        self.alerts_sent = []
        
        # Connect to MongoDB via Proxy
        try:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
            from Orchestrator.src.mongo_proxy import MongoProxy
            self.mongo_proxy = MongoProxy()
            print("✅ Connected to MongoDB (Proxy)")
            
            # Load targets from Inventory
            self.load_targets_from_inventory()
        except Exception as e:
            print(f"❌ MongoDB Proxy Setup Failed: {e}")
            self.mongo_proxy = None

    def load_targets_from_inventory(self):
        """Fetch active databases from MongoDB Inventory"""
        print("🔄 Fetching targets from Inventory...")
        try:
            # Query inventory
            dbs = self.mongo_proxy.execute_eval("db.inventory_databases.find({'identity.engine': 'POSTGRES'}).toArray()")
            if dbs:
                count = 0
                for db in dbs:
                    identity = db.get('identity', {})
                    config = db.get('configuration', {})
                    name = identity.get('db_unique_name', 'UNKNOWN')
                    host = identity.get('host', '127.0.0.1')
                    port = config.get('port', 5432)
                    
                    # Add to monitoring list if not exists or update?
                    # For simplicity, we just append or recreating list logic
                    # Just add standard credentials for now (In real world, fetch from Vault)
                    self.add_database(host, port, "postgres", "nexi2024", "postgres", name)
                    count += 1
                print(f"✅ Loaded {count} targets from Inventory.")
            else:
                print("⚠️ No targets found in Inventory.")
        except Exception as e:
            print(f"❌ Failed to load targets: {e}")

    def add_database(self, host: str, port: int, user: str, password: str, database: str, name: str):
        """Add a database to monitor"""
        self.databases.append(PostgresChecker(host, port, user, password, database, name))
    
    def check_all(self) -> List[Dict]:
        """Check all databases and return alerts"""
        alerts = []
        
        for db in self.databases:
            # Check connection
            conn_result = db.check_connection()
            if conn_result["status"] == "DOWN":
                alert = {
                    "severity": "CRITICAL",
                    "type": "DATABASE_DOWN",
                    "database": db.name,
                    "host_name": db.host,
                    "service": f"PostgreSQL-{db.name}",
                    "message": f"Database {db.name} is DOWN! Error: {conn_result.get('error', 'Unknown')}",
                    "output": f"Database {db.name} is DOWN! Error: {conn_result.get('error', 'Unknown')}",
                    "state": "CRITICAL",
                    "timestamp": datetime.now(),
                    "processed": False
                }
                alerts.append(alert)
            else:
                # Check storage
                storage_result = db.check_storage()
                if storage_result["status"] == "OK":
                    # Check if storage is high (simulate with size > 100MB for demo)
                    if storage_result["size_mb"] > 100:
                        alert = {
                            "severity": "WARNING",
                            "type": "STORAGE_HIGH",
                            "database": db.name,
                            "service": f"PostgreSQL-{db.name}",
                            "host_name": db.host,
                            "output": f"Database {db.name} storage is HIGH: {storage_result['size_mb']}MB",
                             "state": "WARNING",
                            "message": f"Database {db.name} storage is HIGH: {storage_result['size_mb']}MB",
                            "timestamp": datetime.now(),
                            "processed": False
                        }
                        alerts.append(alert)
        
        return alerts
    
    def run_once(self):
        """Run one check cycle and send alerts"""
        print(f"\n{'='*60}")
        print(f"🔍 CriticalAlert Agent Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        alerts = self.check_all()
        
        if alerts:
            print(f"\n🚨 Found {len(alerts)} alert(s)!")
            for alert in alerts:
                print(f"  [{alert['severity']}] {alert['database']}: {alert['type']}")
                
                # Save to MongoDB
                if self.mongo_proxy is not None:
                    try:
                        self.mongo_proxy.insert_alert(alert)
                        print("    💾 Alert saved to MongoDB")
                    except Exception as e:
                        print(f"    ❌ Failed to save to MongoDB: {e}")

                # Send email for CRITICAL alerts (Directly OR handled by Orchestrator? 
                # User asked for Orchestrator to do it. But agent also has logic. 
                # I'll disable direct email here if Orchestrator is supposed to do it, 
                # OR keep it as redundant backup. I'll comment it out to let Orchestrator demonstrate.)
                
                # if alert['severity'] == 'CRITICAL':
                #     self.email_sender.send_alert(...)
        else:
            print("✅ All databases OK")
        
        return alerts
    
    def get_interval(self):
        try:
             cmd = "db.system_config.findOne({key: 'check_interval'})"
             doc = self.mongo_proxy.execute_eval(cmd)
             if doc and 'value' in doc:
                 return int(doc['value'])
        except:
             pass
        return 30

    def run_continuous(self, interval_seconds: int = 30):
        """Run continuous monitoring"""
        print(f"🚀 Starting CriticalAlert Agent")
        
        while True:
            try:
                # Reload targets dynamically
                self.load_targets_from_inventory()
                
                self.run_once()
                
                # Dynamic Interval
                actual_wait = self.get_interval()
                print(f"💤 Sleeping for {actual_wait}s...")
                time.sleep(actual_wait)
            except KeyboardInterrupt:
                print("\n⏹️ Agent stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CriticalAlert Agent")
    parser.add_argument("--email", required=True, help="Email for alerts")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    agent = CriticalAlertAgent(args.email)
    
    # Add Docker lab databases - REMOVED, now using dynamic loading
    # agent.add_database("localhost", 5433, "postgres", "nexi2024", "payments_dev", "PG-Milano-DEV")
    # agent.add_database("localhost", 5434, "postgres", "nexi2024", "cards_dev", "PG-Bratislava-DEV")
    
    if args.once:
        agent.run_once()
    else:
        agent.run_continuous(args.interval)


if __name__ == "__main__":
    main()
