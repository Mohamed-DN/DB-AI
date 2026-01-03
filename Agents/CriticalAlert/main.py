"""
CriticalAlert Agent - Real-time monitoring and email alerts
"""
import os
import time
import smtplib
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
                print(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                # Simulate email if no SMTP configured
                print(f"📧 [SIMULATED EMAIL] To: {to_email}")
                print(f"   Subject: {subject}")
                print(f"   Body: {body}")
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
                    "message": f"Database {db.name} is DOWN! Error: {conn_result.get('error', 'Unknown')}",
                    "timestamp": datetime.now()
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
                            "message": f"Database {db.name} storage is HIGH: {storage_result['size_mb']}MB",
                            "timestamp": datetime.now()
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
                
                # Send email for CRITICAL alerts
                if alert['severity'] == 'CRITICAL':
                    self.email_sender.send_alert(
                        self.alert_email,
                        f"{alert['type']} - {alert['database']}",
                        alert['message']
                    )
                    self.alerts_sent.append(alert)
        else:
            print("✅ All databases OK")
        
        return alerts
    
    def run_continuous(self, interval_seconds: int = 30):
        """Run continuous monitoring"""
        print(f"🚀 Starting CriticalAlert Agent (checking every {interval_seconds}s)")
        print(f"📧 Alerts will be sent to: {self.alert_email}")
        
        while True:
            try:
                self.run_once()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n⏹️ Agent stopped")
                break


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CriticalAlert Agent")
    parser.add_argument("--email", required=True, help="Email for alerts")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    agent = CriticalAlertAgent(args.email)
    
    # Add Docker lab databases
    agent.add_database("localhost", 5433, "postgres", "nexi2024", "payments_dev", "PG-Milano-DEV")
    agent.add_database("localhost", 5434, "postgres", "nexi2024", "cards_dev", "PG-Bratislava-DEV")
    
    if args.once:
        agent.run_once()
    else:
        agent.run_continuous(args.interval)


if __name__ == "__main__":
    main()
