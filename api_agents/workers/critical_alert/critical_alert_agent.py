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
        self.smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST") or "smtp.gmail.com"
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
    
    def send_alert(self, to_email: str, subject: str, body: str) -> bool:
        """Send an alert email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email or ""
            msg['Subject'] = f"Nexi DBA AI Alert: {subject}"

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #ff4444; color: white; padding: 20px; text-align: center;">
                    <h1>CRITICAL DATABASE ALERT</h1>
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

            email_sent = False
            if to_email and self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                print(f"EMAIL SENT: {to_email}")
                email_sent = True
            else:
                if not to_email:
                    print("No alert email configured; skipping SMTP send.")
                else:
                    print(f"SIMULATED EMAIL: {to_email}")
                    print(f"Subject: {subject}")
                    print(f"Body: {body[:100]}...")
                email_sent = bool(to_email)

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
                print(f"Email saved to: {filename}")
            except Exception as e:
                print(f"Failed to save email to file: {e}")

            return email_sent

        except Exception as e:
            print(f"Failed to send email: {e}")
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
        self.default_pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.default_pg_password = os.getenv("POSTGRES_PASSWORD", "nexi2024")
        self.default_pg_db = os.getenv("POSTGRES_DB", "postgres")
        
        # Connect to MongoDB via SyncMongoService
        try:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
            from api_agents.shared.sync_mongo_service import SyncMongoService
            self.mongo = SyncMongoService.get_instance()
            print("Connected to MongoDB (SyncMongoService)")
            
            # Load targets from Inventory
            self.load_targets_from_inventory()
        except Exception as e:
            print(f"MongoDB SyncMongoService Setup Failed: {e}")
            self.mongo = None

    def load_targets_from_inventory(self):
        """Fetch active databases from MongoDB Inventory"""
        if not self.mongo:
            print("MongoDB not available; skipping inventory load.")
            return

        print("Fetching targets from inventory...")
        try:
            dbs = self.mongo.get_postgres_databases()
            targets = []
            for db in dbs or []:
                identity = db.get('identity', {})
                config = db.get('configuration', {})
                name = identity.get('db_unique_name', 'UNKNOWN')
                host = identity.get('host', '127.0.0.1')
                port = config.get('port') or identity.get('port') or 5432
                targets.append(PostgresChecker(
                    host=host,
                    port=int(port),
                    user=self.default_pg_user,
                    password=self.default_pg_password,
                    database=self.default_pg_db,
                    name=name
                ))

            self.databases = targets
            if targets:
                print(f"Loaded {len(targets)} targets from inventory.")
            else:
                print("No targets found in inventory.")
        except Exception as e:
            print(f"Failed to load targets: {e}")

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
    
    def check_for_active_alert(self, db_name: str, alert_type: str) -> bool:
        """Check if an unprocessed alert already exists for this db and type"""
        if not self.mongo: return False
        try:
            return self.mongo.check_active_alert(db_name, alert_type)
        except:
            return False

    def resolve_alerts(self, db_name: str):
        """Mark alerts as processed when issue is resolved"""
        if not self.mongo: return
        try:
            count = self.mongo.resolve_alerts_for_db(db_name)
            if count > 0:
                print(f"    Resolved {count} active alerts for {db_name}")
        except Exception as e:
            print(f"    Failed to resolve alerts: {e}")

    def run_once(self):
        """Run one check cycle and send alerts"""
        print(f"\n{'='*60}")
        print(f"CriticalAlert Agent Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Check all databases
        current_status = self.check_all()
        # alerts list contains only NEW problems detected this cycle
        
        # Logic: 
        # 1. Iterate over all monitored databases (self.databases)
        # 2. If DB is DOWN in current_status -> Check if already alerted. 
        #    If YES -> Skip email. 
        #    If NO -> Send Email + Insert.
        # 3. If DB is OK -> Check if there are pending alerts. If YES -> Resolve them.

        # Transform alerts list to map for easy lookup
        current_problems = {alert['database']: alert for alert in current_status}
        
        for db in self.databases:
            if db.name in current_problems:
                # PROBLEM DETECTED
                problem = current_problems[db.name]
                if problem['severity'] == 'CRITICAL':
                    # Check duplication
                    if self.check_for_active_alert(db.name, problem['type']):
                        print(f"  [SUPPRESSED] Alert already active for {db.name}. No email sent.")
                    else:
                        print(f"  [NEW] {db.name}: {problem['type']}")
                        # Send Email
                        self.email_sender.send_alert(
                            self.alert_email, 
                            f"{problem['type']} - {db.name}", 
                            problem['message']
                        )
                        # Insert into DB
                        if self.mongo:
                            self.mongo.insert_alert(problem)
            else:
                # DB IS OK (or at least not in critical list)
                # Try to resolve any pending critical alerts
                self.resolve_alerts(db.name)
        
        print("Check cycle complete.")
        return current_status
    
    def get_interval(self, default_value: int = 30) -> int:
        if not self.mongo:
            return default_value
        try:
            interval = self.mongo.get_config('criticalalert_interval')
            if interval:
                return int(interval)
        except Exception:
            pass
        return default_value

    def check_pause(self):
        """Check if system is globally paused"""
        try:
            if not self.mongo: return False
            status = self.mongo.get_config('global_status')
            if status == 'PAUSED':
                return True
        except:
            pass
        return False

    def run_continuous(self, interval_seconds: int = 30):
        """Run continuous monitoring"""
        print("Starting CriticalAlert Agent")
        
        while True:
            try:
                if self.check_pause():
                    print("System global pause active. Alert Agent sleeping...")
                    time.sleep(10)
                    continue

                # Reload targets dynamically
                self.load_targets_from_inventory()
                
                self.run_once()
                
                # Dynamic Interval
                actual_wait = self.get_interval(interval_seconds)
                print(f"Sleeping for {actual_wait}s...")
                time.sleep(actual_wait)
            except KeyboardInterrupt:
                print("\nAgent stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CriticalAlert Agent")
    parser.add_argument("--email", help="Email for alerts (optional)")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    email = args.email or os.getenv("ALERT_EMAIL") or os.getenv("SMTP_USER") or ""
    if not email:
        print("No alert email configured; alerts will be logged only.")

    agent = CriticalAlertAgent(email)
    
    # Add Docker lab databases - REMOVED, now using dynamic loading
    # agent.add_database("localhost", 5433, "postgres", "nexi2024", "payments_dev", "PG-Milano-DEV")
    # agent.add_database("localhost", 5434, "postgres", "nexi2024", "cards_dev", "PG-Bratislava-DEV")
    
    if args.once:
        agent.run_once()
    else:
        agent.run_continuous(args.interval)


if __name__ == "__main__":
    main()
