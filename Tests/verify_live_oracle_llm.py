
import os
import sys
import json
import logging
from datetime import datetime

# Add root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LiveVerification")

try:
    import oracledb
except ImportError:
    logger.error("❌ oracledb module not found. Please install it: pip install oracledb")
    sys.exit(1)

from api_agents.workers.Sentinel.verifier_agent import VerifierAgent, VerifiedAlert
from api_agents.workers.Sentinel.predictor_agent import PredictionAlert, AnomalyType

# Configuration from .env match
ORACLE_HOST = "localhost"
ORACLE_PORT = 2521
ORACLE_SID = "JUPITER"
ORACLE_USER = "system" # Using system to access v$ metrics
ORACLE_PASS = "nexi2024"

def verify_oracle_connection():
    """Connect to Oracle and get active session count."""
    dsn = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SID}"
    logger.info(f"🔌 Connecting to Oracle: {dsn} as {ORACLE_USER}...")
    
    try:
        conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=dsn)
        cursor = conn.cursor()
        
        # Get Session Count
        cursor.execute("SELECT count(*) FROM v$session")
        session_count = cursor.fetchone()[0]
        
        # Get DB Name
        cursor.execute("SELECT name FROM v$database")
        db_name = cursor.fetchone()[0]
        
        logger.info(f"✅ Oracle Connected! DB: {db_name}, Active Sessions: {session_count}")
        conn.close()
        return session_count, db_name
        
    except Exception as e:
        logger.error(f"❌ Oracle Connection Failed: {e}")
        return None, None

def run_live_test():
    """Run the end-to-end test."""
    
    # 1. Get Live Data
    session_count, db_name = verify_oracle_connection()
    if session_count is None:
        logger.warning("⚠️ Skipping Oracle part due to connection failure. Testing LLM only with mock data.")
        session_count = 150 # Simulated high load
        db_name = "JUPITER (Simulated)"

    # Enable Debug Logging for Verifier
    logging.getLogger("VerifierAgent").setLevel(logging.DEBUG)

    # 2. Simulate a Prediction based on this data
    import random
    unique_id = f"test_{random.randint(1000, 9999)}"
    # Let's pretend 150 sessions is high
    predicted_sessions = session_count + 50
    
    prediction = PredictionAlert(
        db_name=f"NEXI_ORACLE_{db_name}_{unique_id}", # Unique name to bust cache
        anomaly_type=AnomalyType.SESSION_OVERFLOW,
        probability=0.88,
        predicted_at=datetime.utcnow(),
        horizon_minutes=20,
        current_value=float(session_count),
        predicted_value=float(predicted_sessions),
        threshold=200.0,
        trend_direction="rising"
    )

    # 3. Initialize Verifier with Real LLM
    logger.info("🧠 Initializing Verifier Agent with Local LLM...")
    # passing mongo_service=None for simplicity, focusing on LLM
    verifier = VerifierAgent(mongo_service=None, llm_model="deepseek-r1:8b") 
    
    if not verifier.llm:
        logger.error("❌ LLM Initialization failed. Is Ollama running?")
        sys.exit(1)

    # 4. Verify
    logger.info("🤔 Asking LLM for verification (RALPH Mode)...")
    result = verifier.verify_prediction(prediction)
    
    # 5. Output Results
    logger.info("\n" + "="*50)
    logger.info("🦅 RALPH RESULT")
    logger.info("="*50)
    logger.info(f"Classification: {result.classification.value}")
    logger.info(f"Confidence:     {result.confidence:.2%}")
    logger.info(f"Reasoning:      {result.reasoning}")
    logger.info(f"Action:         {result.recommended_action}")
    logger.info(f"Auto-Fixable:   {result.auto_fixable}")
    
    if result.tool_execution:
        logger.info(f"🛠️ Tool Decision: {json.dumps(result.tool_execution, indent=2)}")
    else:
        logger.info("🛠️ Tool Decision: None (Escalate or Monitor)")
        
    logger.info("="*50)

    if result.classification.value != "needs_investigation":
         logger.info("✅ Live Test PASSED: LLM produced a definitive classification.")
    else:
         logger.warning("⚠️ Live Test INCONCLUSIVE: LLM returned 'needs_investigation'.")

if __name__ == "__main__":
    run_live_test()
