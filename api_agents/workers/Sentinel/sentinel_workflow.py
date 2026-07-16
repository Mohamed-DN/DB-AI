"""
Sentinel Workflow - LangGraph orchestration for the Predictor → Verifier → Action pipeline.
Coordinates the multi-agent system for autonomous database monitoring.

Part of the Sentinel Engine Multi-Agent System.
"""
import os
import sys
import uuid
import logging
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Add root path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from langgraph.graph import StateGraph, END

# Handle imports for both module and standalone execution
try:
    from api_agents.workers.sentinel.predictor_agent import PredictorAgent, PredictionAlert
    from api_agents.workers.sentinel.verifier_agent import VerifierAgent, VerifiedAlert, AlertClassification
except ImportError:
    from predictor_agent import PredictorAgent, PredictionAlert
    from verifier_agent import VerifierAgent, VerifiedAlert, AlertClassification

logger = logging.getLogger("SentinelWorkflow")



class SentinelState(TypedDict):
    """State for the Sentinel workflow"""
    # Identifiers
    run_id: str
    started_at: datetime

    # Intermediate results
    predictions: List[PredictionAlert]
    verified_alerts: List[VerifiedAlert]

    # Output counters
    urgent_emails_sent: int
    status_reports_sent: int
    auto_fixes_triggered: int

    # Error tracking
    errors: List[str]


class EmailTemplate(Enum):
    """Email template types"""
    URGENT_ALERT = "urgent_alert"
    STATUS_REPORT = "status_report"
    DAILY_SUMMARY = "daily_summary"


class SentinelEmailSender:
    """
    Extended email sender for Sentinel alerts.
    Uses Jinja2 templates for rich HTML emails.
    """

    def __init__(self):
        """Initialize email sender with SMTP settings from env."""
        self.smtp_server = os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST") or "smtp.gmail.com"
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)

        # Default recipients
        self.urgent_recipients = os.getenv("DBA_URGENT_EMAIL", "dba-team@m-dn.it").split(",")
        self.report_recipients = os.getenv("DBA_REPORT_EMAIL", "dba-reports@m-dn.it").split(",")

    def _build_urgent_html(self, alert: VerifiedAlert) -> str:
        """Build HTML for urgent alert email."""
        pred = alert.prediction_alert
        fix_section = ""
        if alert.fix_procedure:
            fix_section = f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 15px;">
                <h3 style="color: #28a745; margin-top: 0;">📋 Fix Procedure</h3>
                <pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto;">{alert.fix_procedure}</pre>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>🚨 Critical Database Alert</title>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: #ffffff; border-radius: 10px; padding: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: #dc3545; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 CRITICAL: Predicted Database Issue</h1>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 150px;">Database</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-size: 18px;">{pred.db_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Issue Type</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; color: #dc3545;">{pred.anomaly_type.value.replace('_', ' ').upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Probability</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.probability:.0%}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Expected In</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; color: #fd7e14; font-weight: bold;">{pred.horizon_minutes} minutes</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Current Value</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.current_value:.1f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Predicted Value</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; color: #dc3545;">{pred.predicted_value:.1f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Threshold</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.threshold:.1f}</td>
                    </tr>
                </table>

                <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <h3 style="color: #856404; margin-top: 0;">🧠 AI Analysis</h3>
                    <p style="color: #856404; margin-bottom: 5px;"><strong>Confidence:</strong> {alert.confidence:.0%}</p>
                    <p style="color: #856404; margin-bottom: 0;">{alert.reasoning}</p>
                </div>

                <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #155724; margin-top: 0;">✅ Recommended Action</h3>
                    <p style="color: #155724; margin-bottom: 0;">{alert.recommended_action}</p>
                </div>

                {fix_section}

                <p style="color: #6c757d; font-size: 12px; margin-top: 20px; text-align: center;">
                    Generated by M-DN DBA Sentinel Engine at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    <br>Run ID: {os.getenv('SENTINEL_RUN_ID', 'N/A')}
                </p>
            </div>
        </body>
        </html>
        """

    def _build_status_html(self, alert: VerifiedAlert) -> str:
        """Build HTML for status report email."""
        pred = alert.prediction_alert
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>📊 Database Status Report</title>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: #ffffff; border-radius: 10px; padding: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: #28a745; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">📊 Status Report: Prediction Cleared</h1>
                </div>

                <p style="color: #333; font-size: 16px;">
                    A potential issue was predicted but determined to be a <strong style="color: #28a745;">false alarm</strong>.
                </p>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; width: 150px;">Database</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.db_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Predicted Issue</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.anomaly_type.value.replace('_', ' ').title()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Prediction Probability</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{pred.probability:.0%}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Status</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; color: #28a745; font-weight: bold;">✅ Healthy</td>
                    </tr>
                </table>

                <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <h3 style="color: #155724; margin-top: 0;">Analysis</h3>
                    <p style="color: #155724; margin-bottom: 0;">{alert.reasoning}</p>
                </div>

                <div style="background-color: #cce5ff; border: 1px solid #007bff; padding: 15px; border-radius: 5px;">
                    <h3 style="color: #004085; margin-top: 0;">💡 Optimization Tips</h3>
                    <p style="color: #004085; margin-bottom: 0;">{alert.recommended_action}</p>
                </div>

                <p style="color: #6c757d; font-size: 12px; margin-top: 20px; text-align: center;">
                    Generated by M-DN DBA Sentinel Engine at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </p>
            </div>
        </body>
        </html>
        """

    def send_urgent_alert(self, alert: VerifiedAlert) -> bool:
        """Send urgent email for critical alerts."""
        subject = f"🚨 CRITICAL: {alert.prediction_alert.db_name} - {alert.prediction_alert.anomaly_type.value}"
        body = self._build_urgent_html(alert)
        return self._send_email(self.urgent_recipients, subject, body)

    def send_status_report(self, alert: VerifiedAlert) -> bool:
        """Send status report for false alarms."""
        subject = f"📊 Status Report: {alert.prediction_alert.db_name}"
        body = self._build_status_html(alert)
        return self._send_email(self.report_recipients, subject, body)

    def _send_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """Send an HTML email."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)

            html_part = MIMEText(body, "html", "utf-8")
            msg.attach(html_part)

            # Save to file for debugging
            email_dir = os.path.join(os.path.dirname(__file__), "../../../emails")
            os.makedirs(email_dir, exist_ok=True)
            filename = f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{subject[:30].replace(' ', '_')}.html"
            filepath = os.path.join(email_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
            logger.info(f"📧 Saved email to {filepath}")

            # Send via SMTP if configured
            if self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, recipients, msg.as_string())
                logger.info(f"📧 Sent email: {subject}")
            else:
                logger.info(f"📧 SMTP not configured, email saved locally only")

            return True

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


# =============================================================================
# LangGraph Workflow Nodes
# =============================================================================

def prediction_node(state: SentinelState) -> dict:
    """Run the Predictor Agent on all databases."""
    logger.info("🔮 Running Predictor Agent...")

    try:
        from api_agents.shared.victoriametrics_client import get_victoriametrics_client
        from api_agents.shared.sync_mongo_service import SyncMongoService

        vm = get_victoriametrics_client()
        mongo = SyncMongoService.get_instance()
        predictor = PredictorAgent(vm_client=vm, mongo_service=mongo)

        predictions = predictor.run_once()

        logger.info(f"🔮 Generated {len(predictions)} predictions")
        return {"predictions": predictions}

    except Exception as e:
        logger.error(f"Prediction node failed: {e}")
        return {
            "predictions": [],
            "errors": state.get("errors", []) + [f"Predictor error: {e}"]
        }


def verification_node(state: SentinelState) -> dict:
    """Run the Verifier Agent on all predictions."""
    logger.info("✅ Running Verifier Agent...")

    predictions = state.get("predictions", [])
    if not predictions:
        logger.info("No predictions to verify")
        return {"verified_alerts": []}

    try:
        from api_agents.shared.sync_mongo_service import SyncMongoService

        mongo = SyncMongoService.get_instance()
        verifier = VerifierAgent(mongo_service=mongo)

        verified = verifier.verify_all(predictions)

        logger.info(f"✅ Verified {len(verified)} alerts")
        return {"verified_alerts": verified}

    except Exception as e:
        logger.error(f"Verification node failed: {e}")
        return {
            "verified_alerts": [],
            "errors": state.get("errors", []) + [f"Verifier error: {e}"]
        }


def action_node(state: SentinelState) -> dict:
    """Execute actions based on verified alerts."""
    logger.info("⚡ Executing Actions...")

    verified_alerts = state.get("verified_alerts", [])
    if not verified_alerts:
        logger.info("No alerts to act on")
        return {
            "urgent_emails_sent": 0,
            "status_reports_sent": 0,
            "auto_fixes_triggered": 0
        }

    email_sender = SentinelEmailSender()
    urgent_count = 0
    status_count = 0
    auto_fix_count = 0

    for alert in verified_alerts:
        try:
            if alert.classification == AlertClassification.REAL_CRITICAL:
                # Send urgent email with fix procedure
                if email_sender.send_urgent_alert(alert):
                    urgent_count += 1

                # Log to MongoDB
                try:
                    from api_agents.shared.sync_mongo_service import SyncMongoService
                    mongo = SyncMongoService.get_instance()
                    mongo.insert_alert({
                        "type": "SENTINEL_CRITICAL",
                        "source": "SentinelWorkflow",
                        "db_name": alert.prediction_alert.db_name,
                        "data": alert.to_dict(),
                        "created_at": datetime.utcnow(),
                        "processed": False
                    })
                except Exception as e:
                    logger.warning(f"Failed to log alert to MongoDB: {e}")

            elif alert.classification == AlertClassification.REAL_WARNING:
                # Send warning (less urgent)
                if email_sender.send_urgent_alert(alert):
                    urgent_count += 1

            elif alert.classification == AlertClassification.FALSE_ALARM:
                # Send status report with optimization tips
                if email_sender.send_status_report(alert):
                    status_count += 1

            # Auto-fix if applicable (future implementation)
            if alert.auto_fixable:
                logger.info(f"🤖 Auto-fix available for {alert.prediction_alert.db_name} (not implemented)")
                # TODO: Integrate with LangGraph remediation workflow
                # auto_fix_count += 1

        except Exception as e:
            logger.error(f"Error processing alert for {alert.prediction_alert.db_name}: {e}")

    logger.info(f"⚡ Actions complete: {urgent_count} urgent, {status_count} status reports")
    return {
        "urgent_emails_sent": urgent_count,
        "status_reports_sent": status_count,
        "auto_fixes_triggered": auto_fix_count
    }


# =============================================================================
# LangGraph Workflow Construction
# =============================================================================

def build_sentinel_workflow():
    """Construct the LangGraph workflow."""
    workflow = StateGraph(SentinelState)

    # Add nodes
    workflow.add_node("predict", prediction_node)
    workflow.add_node("verify", verification_node)
    workflow.add_node("act", action_node)

    # Linear flow: predict → verify → act
    workflow.set_entry_point("predict")
    workflow.add_edge("predict", "verify")
    workflow.add_edge("verify", "act")
    workflow.add_edge("act", END)

    return workflow.compile()


# Global compiled workflow
sentinel_workflow = build_sentinel_workflow()


def run_sentinel_cycle() -> Dict[str, Any]:
    """
    Execute one full sentinel cycle.

    Returns:
        Dict with cycle results (alerts sent, etc.)
    """
    run_id = str(uuid.uuid4())
    os.environ["SENTINEL_RUN_ID"] = run_id

    initial_state: SentinelState = {
        "run_id": run_id,
        "started_at": datetime.utcnow(),
        "predictions": [],
        "verified_alerts": [],
        "urgent_emails_sent": 0,
        "status_reports_sent": 0,
        "auto_fixes_triggered": 0,
        "errors": []
    }

    logger.info(f"🏁 Starting Sentinel cycle (Run ID: {run_id})")

    try:
        result = sentinel_workflow.invoke(initial_state)

        logger.info(
            f"🏁 Sentinel cycle complete: "
            f"{result['urgent_emails_sent']} urgent, "
            f"{result['status_reports_sent']} status reports, "
            f"{len(result.get('errors', []))} errors"
        )

        return {
            "run_id": run_id,
            "predictions_count": len(result.get("predictions", [])),
            "verified_count": len(result.get("verified_alerts", [])),
            "urgent_emails_sent": result["urgent_emails_sent"],
            "status_reports_sent": result["status_reports_sent"],
            "auto_fixes_triggered": result["auto_fixes_triggered"],
            "errors": result.get("errors", []),
            "duration_seconds": (datetime.utcnow() - initial_state["started_at"]).total_seconds()
        }

    except Exception as e:
        logger.error(f"Sentinel cycle failed: {e}")
        return {
            "run_id": run_id,
            "error": str(e),
            "predictions_count": 0,
            "verified_count": 0,
            "urgent_emails_sent": 0,
            "status_reports_sent": 0,
            "auto_fixes_triggered": 0
        }


def run_continuous(interval_seconds: int = 300):
    """
    Run the sentinel workflow continuously.

    Args:
        interval_seconds: Seconds between cycles (default: 5 minutes)
    """
    import time

    logger.info(f"🛡️ Sentinel Engine starting (interval: {interval_seconds}s)")

    while True:
        try:
            result = run_sentinel_cycle()
            logger.info(f"Cycle result: {result}")
        except Exception as e:
            logger.error(f"Cycle error: {e}")

        logger.info(f"💤 Sleeping {interval_seconds}s until next cycle...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Sentinel Engine Workflow")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Cycle interval in seconds")
    args = parser.parse_args()

    if args.once:
        result = run_sentinel_cycle()
        print(f"\n📊 Sentinel Cycle Results:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        run_continuous(args.interval)
