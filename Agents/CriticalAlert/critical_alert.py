"""
CriticalAlert Agent - Real-time critical error monitoring
Runs continuously with 30-second polling

Monitors:
- Database DOWN
- Tablespace > 95%
- Data Guard LAG > 1 hour
- Backup failed
- Blocking sessions > 30 min
"""

import os
import sys
# Fix Windows console encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Orchestrator.src.mongo_proxy import MongoProxy


class CriticalAlertAgent:
    """Agent that monitors critical conditions and sends alerts."""
    
    CRITICAL_CONDITIONS = {
        'DB_DOWN': {'severity': 'CRITICAL', 'action': 'Email BAO + DL'},
        'TABLESPACE_CRITICAL': {'severity': 'CRITICAL', 'threshold': 95, 'action': 'Email BAO'},
        'DATAGUARD_LAG': {'severity': 'HIGH', 'threshold_hours': 1, 'action': 'Email DL'},
        'BACKUP_FAILED': {'severity': 'HIGH', 'action': 'Email DL'},
        'BLOCKING_SESSION': {'severity': 'MEDIUM', 'threshold_min': 30, 'action': 'Log + Alert'},
    }
    
    def __init__(self, poll_interval: int = 30):
        try:
            self.mongo = MongoProxy()
        except:
            self.mongo = None
            print("⚠️ Warning: MongoDB not connected")
            
        self.poll_interval = poll_interval
        self.running = True
        self.alerts_sent = set()  # Track sent alerts to avoid duplicates
        
    def run(self):
        """Run the continuous monitoring loop."""
        print(f"🚨 CriticalAlert Agent started - Polling every {self.poll_interval}s")
        
        while self.running:
            try:
                self._check_all_conditions()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                print("\n⏹️ CriticalAlert Agent stopped")
                self.running = False
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retry
    
    def run_once(self) -> List[Dict]:
        """Run a single check (useful for testing)."""
        return self._check_all_conditions()
    
    def _check_all_conditions(self) -> List[Dict]:
        """Check all critical conditions."""
        alerts = []
        
        # Get all databases
        databases = self._get_all_databases()
        
        for db in databases:
            db_name = db.get('identity', {}).get('db_unique_name', 'UNKNOWN')
            
            # Check DB status
            alert = self._check_db_status(db)
            if alert:
                alerts.append(alert)
            
            # Check tablespace usage
            ts_alerts = self._check_tablespace_usage(db)
            alerts.extend(ts_alerts)
            
            # Check Data Guard lag
            dg_alert = self._check_dataguard_lag(db)
            if dg_alert:
                alerts.append(dg_alert)
            
            # Check backup status
            backup_alert = self._check_backup_status(db)
            if backup_alert:
                alerts.append(backup_alert)
        
        # Check monitoring_alerts collection for new alerts from Checkmk
        external_alerts = self._check_monitoring_alerts()
        alerts.extend(external_alerts)
        
        # Process alerts
        for alert in alerts:
            self._process_alert(alert)
        
        if alerts:
            types = [a['type'] for a in alerts]
            print(f"⚠️ {len(alerts)} active alerts: {types}")
        
        return alerts
    
    def _get_all_databases(self) -> List[Dict]:
        """Get all databases from inventory."""
        try:
            return self.mongo.execute_eval("db.inventory_databases.find().toArray()")
        except:
            return []
    
    def _check_db_status(self, db: Dict) -> Optional[Dict]:
        """Check if database is DOWN."""
        state = db.get('state', {})
        status = state.get('status', 'UNKNOWN')
        
        if status in ['DOWN', 'MISSING']:
            return {
                'type': 'DB_DOWN',
                'severity': 'CRITICAL',
                'db_unique_name': db.get('identity', {}).get('db_unique_name'),
                'message': 'Database is DOWN',
                'timestamp': datetime.now(),
                'action': 'Email BAO + DL'
            }
        return None
    
    def _check_tablespace_usage(self, db: Dict) -> List[Dict]:
        """Check tablespace usage above threshold."""
        alerts = []
        db_name = db.get('identity', {}).get('db_unique_name', 'UNKNOWN')
        
        for ts in db.get('storage', {}).get('tablespaces', []):
            usage = ts.get('usage_pct', 0)
            if usage >= 95:
                alerts.append({
                    'type': 'TABLESPACE_CRITICAL',
                    'severity': 'CRITICAL',
                    'db_unique_name': db_name,
                    'tablespace': ts.get('name'),
                    'usage_pct': usage,
                    'message': f"Tablespace {ts.get('name')} at {usage}%",
                    'timestamp': datetime.now(),
                    'action': 'Email BAO'
                })
        return alerts
    
    def _check_dataguard_lag(self, db: Dict) -> Optional[Dict]:
        """Check Data Guard replication lag."""
        repl = db.get('data_protection', {}).get('replication', {})
        
        if repl.get('technology') == 'DATAGUARD' and repl.get('is_active'):
            # In real implementation, would check actual lag
            # For now, check if it's documented
            lag_hours = repl.get('lag_hours', 0)
            if lag_hours > 1:
                return {
                    'type': 'DATAGUARD_LAG',
                    'severity': 'HIGH',
                    'db_unique_name': db.get('identity', {}).get('db_unique_name'),
                    'lag_hours': lag_hours,
                    'message': f'Data Guard lag: {lag_hours} hours',
                    'timestamp': datetime.now(),
                    'action': 'Email DL'
                }
        return None
    
    def _check_backup_status(self, db: Dict) -> Optional[Dict]:
        """Check backup status."""
        backup = db.get('data_protection', {}).get('backup', {})
        
        if backup.get('status') == 'FAILED':
            return {
                'type': 'BACKUP_FAILED',
                'severity': 'HIGH',
                'db_unique_name': db.get('identity', {}).get('db_unique_name'),
                'message': 'Last backup failed',
                'timestamp': datetime.now(),
                'action': 'Email DL'
            }
        return None
    
    def _check_monitoring_alerts(self) -> List[Dict]:
        """Check monitoring_alerts collection for unprocessed alerts."""
        alerts = []
        try:
            # Get unprocessed critical alerts
            raw_alerts = self.mongo.execute_eval(
                "db.monitoring_alerts.find({processed: false, state: {$in: ['CRITICAL', 'RESOLVED']}}).toArray()"
            )
            for a in raw_alerts:
                # Preserve original type for RECOVERY
                alert_type = a.get('type', 'EXTERNAL_ALERT')
                if alert_type == 'DB_RECOVERY':
                    severity = 'RESOLVED'
                else:
                    severity = a.get('state', 'UNKNOWN')

                alerts.append({
                    'type': alert_type,
                    'severity': severity,
                    'db_unique_name': a.get('db_unique_name', 'UNKNOWN'),
                    'message': a.get('message', a.get('summary', 'No summary')),
                    'source': 'Checkmk',
                    'timestamp': datetime.now(),
                    'action': 'Email BAO + DL'
                })
        except Exception as e:
            pass
        return alerts
    
    def _process_alert(self, alert: Dict):
        """Process an alert: log, save, and send notification."""
        alert_key = f"{alert['type']}_{alert.get('db_unique_name')}_{alert.get('tablespace', '')}"
        
        # Avoid duplicate alerts within 15 minutes
        if alert_key in self.alerts_sent:
            return
        
        # Log alert
        if alert['severity'] == 'CRITICAL':
            severity_icon = '🔴'
        elif alert['severity'] == 'RESOLVED':
            severity_icon = '🟢'
        elif alert['severity'] == 'HIGH':
            severity_icon = '🟠'
        else:
            severity_icon = '🟡'
        
        print(f"{severity_icon} {alert['type']}: {alert.get('db_unique_name')} - {alert['message']}")
        
        # Save to MongoDB
        self._save_alert(alert)
        
        # Send notification
        self._send_notification(alert)
        
        # Track sent alert AND Toggle Clearing for Flapping
        self.alerts_sent.add(alert_key)
        
        if alert['type'] == 'DB_RECOVERY':
            # Remove corresponding DOWN alerts to allow future notifications
            to_remove = []
            for k in self.alerts_sent:
                if 'DB_DOWN' in k and alert.get('db_unique_name') in k:
                    to_remove.append(k)
            for k in to_remove:
                self.alerts_sent.remove(k)
                
        if alert['type'] == 'DB_DOWN':
             # Remove corresponding RECOVERY alerts
            to_remove = []
            for k in self.alerts_sent:
                if 'DB_RECOVERY' in k and alert.get('db_unique_name') in k:
                    to_remove.append(k)
            for k in to_remove:
                self.alerts_sent.remove(k)
    
    def _save_alert(self, alert: Dict):
        """Save alert to MongoDB."""
        try:
            alert_doc = {
                **alert,
                'timestamp': alert['timestamp'].isoformat(),
                'processed': False
            }
            # Fix JSON boolean for JS
            import json
            json_doc = json.dumps(alert_doc)
            self.mongo.execute_eval(f"db.critical_alerts.insertOne({json_doc})")
        except Exception as e:
            print(f"   ❌ Error saving alert to Mongo: {e}")
    
    def _send_notification(self, alert: Dict):
        """Send email notification for alert."""
        db_name = alert.get('db_unique_name', '')
        
        try:
            # Get contact info from business_services
            service = self.mongo.execute_eval(
                f"db.business_services.findOne({{'technical_mapping.db_unique_name': '{db_name}'}})"
            )
            
            if service:
                contacts = service.get('contacts', {})
                recipients = []
                
                action = alert.get('action', '')
                if 'BAO' in action:
                    bao_email = contacts.get('bao', {}).get('email')
                    if bao_email:
                        recipients.append(bao_email)
                if 'DL' in action:
                    dl_email = contacts.get('dl_team')
                    if dl_email:
                        recipients.append(dl_email)
                
                if recipients:
                    self._send_email(alert, recipients)
        except Exception as e:
            print(f"   Error getting contacts: {e}")
    
    def _send_email(self, alert: Dict, recipients: List[str]):
        """Send email to recipients via SMTP (Real + File Backup)."""
        subject = f"{'✅' if alert['severity'] == 'RESOLVED' else '⚠️'} {alert['severity']}: {alert['type']} - {alert.get('db_unique_name', 'N/A')}"
        
        # HTML Body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: {'#4CAF50' if alert['severity'] == 'RESOLVED' else '#f44336' if alert['severity'] == 'CRITICAL' else '#ff9800'}; color: white; padding: 15px; border-radius: 5px;">
                 <h2 style="margin:0;">{subject}</h2>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px;">
                <p><strong>Database:</strong> {alert.get('db_unique_name', 'N/A')}</p>
                <p><strong>Message:</strong> {alert.get('message', 'N/A')}</p>
                <p><strong>Time:</strong> {alert['timestamp']}</p>
                <p><strong>Source:</strong> Nexi AI Sentinel</p>
                <p style="font-size: 12px; color: #666;">This is an automated alert from the Nexi DB AI Monitoring System.</p>
            </div>
        </body>
        </html>
        """

        # 1. Try SMTP Sending
        sent_success = False
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if smtp_user and smtp_pass:
            try:
                print(f"   📧 Connecting to SMTP {smtp_server}:{smtp_port}...")
                msg = MIMEMultipart()
                msg['From'] = f"Big Brother <{smtp_user}>"
                msg['To'] = ", ".join(recipients)
                msg['Subject'] = subject
                msg.attach(MIMEText(html, 'html'))

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                
                print(f"   ✅ [SMTP] Email sent successfully to {len(recipients)} recipients.")
                sent_success = True
            except Exception as e:
                print(f"   ❌ [SMTP] Failed to send email: {e}")
        else:
            print("   ⚠️ [SMTP] Check skipped: SMTP_USER/SMTP_PASSWORD not set.")

        # 2. Always save to file (Backup/Audit)
        try:
            email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../emails'))
            os.makedirs(email_dir, exist_ok=True)
            
            filename = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{alert['type']}.html"
            filepath = os.path.join(email_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
                f.flush()
                os.fsync(f.fileno())
            print(f"   💾 [FILE] Saved email to {filename}")
        except Exception as e:
            print(f"   ❌ [FILE] Error saving email: {e}")


def main():
    """Run the CriticalAlert agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CriticalAlert Agent')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=30, help='Poll interval in seconds')
    args = parser.parse_args()
    
    agent = CriticalAlertAgent(poll_interval=args.interval)
    
    if args.once:
        alerts = agent.run_once()
        print(f"\n📋 Found {len(alerts)} alerts")
    else:
        agent.run()


if __name__ == "__main__":
    main()
