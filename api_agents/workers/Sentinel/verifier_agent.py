"""
Verifier Agent - LLM-based decision maker for predicted alerts.
Determines if predictions are real issues or false alarms using AI reasoning.

Part of the Sentinel Engine Multi-Agent System.
"""
import os
import sys
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger("VerifierAgent")


class AlertClassification(Enum):
    """Classification outcomes for verified alerts"""
    REAL_CRITICAL = "real_critical"      # Immediate action required
    REAL_WARNING = "real_warning"        # Action needed but not urgent
    FALSE_ALARM = "false_alarm"          # Prediction unlikely to materialize
    NEEDS_INVESTIGATION = "needs_investigation"  # Unclear, requires human review


@dataclass
class VerifiedAlert:
    """Output of the Verifier Agent"""
    prediction_alert: Any  # PredictionAlert from predictor
    classification: AlertClassification
    confidence: float  # 0.0 - 1.0
    reasoning: str
    similar_incidents: List[Dict] = field(default_factory=list)
    recommended_action: str = ""
    fix_procedure: Optional[str] = None  # From repository knowledge base
    auto_fixable: bool = False
    tool_execution: Optional[Dict] = None # RALPH Loop Action
    verified_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "prediction": self.prediction_alert.to_dict() if hasattr(self.prediction_alert, 'to_dict') else str(self.prediction_alert),
            "classification": self.classification.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "similar_incidents": self.similar_incidents,
            "recommended_action": self.recommended_action,
            "fix_procedure": self.fix_procedure,
            "auto_fixable": self.auto_fixable,
            "tool_execution": self.tool_execution,
            "verified_at": self.verified_at.isoformat()
        }





class VerifierAgent:
    """
    Analyzes predictions and classifies them as real or false alarms.

    Uses:
    - LLM reasoning for classification (DeepSeek R1 or fallback)
    - RAG lookup for similar past incidents
    - Real-time database status comparison

    Features:
    - Multi-factor analysis (prediction + real-time + history)
    - Confidence scoring
    - Automatic procedure lookup from knowledge base
    """

    def __init__(
        self,
        mongo_service=None,
        qdrant_url: Optional[str] = None,
        llm_model: str = "deepseek-r1:8b"
    ):
        """
        Initialize the Verifier Agent.

        Args:
            mongo_service: MongoDB service for inventory and config
            qdrant_url: Qdrant vector DB URL for RAG
            llm_model: Ollama model to use for reasoning
        """
        self.mongo = mongo_service

        # Initialize Qdrant client
        qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:7333")
        try:
            from qdrant_client import QdrantClient
            self.qdrant = QdrantClient(url=qdrant_url)
            self.qdrant_available = True
        except ImportError:
            logger.warning("Qdrant client not installed, RAG disabled")
            self.qdrant = None
            self.qdrant_available = False
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")
            self.qdrant = None
            self.qdrant_available = False

        # Initialize LLM
        self.llm_model = llm_model
        try:
            self.llm = ChatOllama(
                model=llm_model,
                temperature=0.1,
                num_predict=1024
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None

        self.collection_name = "nexi_sop_knowledge"

    def get_realtime_status(self, db_name: str) -> Dict[str, Any]:
        """
        Fetch current database status from MongoDB.

        Args:
            db_name: Database unique name

        Returns:
            Dict with current status, metrics, and last seen time
        """
        if not self.mongo:
            return {"status": "UNKNOWN", "error": "MongoDB not available"}

        try:
            db = self.mongo.get_database(db_name)
            if not db:
                return {"status": "NOT_FOUND"}

            return {
                "status": db.get("state", {}).get("status", "UNKNOWN"),
                "last_metrics": db.get("last_metrics", {}),
                "last_seen": db.get("last_seen"),
                "engine": db.get("identity", {}).get("engine", "UNKNOWN"),
                "datacenter": db.get("datacenter", "UNKNOWN")
            }
        except Exception as e:
            logger.error(f"Error fetching status for {db_name}: {e}")
            return {"status": "ERROR", "error": str(e)}

    def search_similar_incidents(
        self,
        anomaly_type: str,
        db_engine: str
    ) -> List[Dict]:
        """
        RAG lookup for similar past incidents and procedures.

        Args:
            anomaly_type: Type of anomaly (e.g., "oom_risk")
            db_engine: Database engine (e.g., "ORACLE", "POSTGRES")

        Returns:
            List of similar incidents with text and relevance score
        """
        if not self.qdrant_available or not self.qdrant:
            return []

        query = f"{anomaly_type} {db_engine} resolution procedure fix"

        try:
            # Generate embedding (placeholder - should use actual embedding model)
            embedding = self._generate_embedding(query)

            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=3
            )

            return [
                {
                    "text": r.payload.get("text", ""),
                    "source": r.payload.get("source", "unknown"),
                    "score": r.score
                }
                for r in results
            ]

        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ollama.
        """
        try:
            if not self.llm:
                 return [0.0] * 384
            
            # Use the ollama client that LangChain uses or a direct request
            # For simplicity with the existing import, we can try to use a standard Ollama call if available,
            # but since we are using ChatOllama, we might need a separate embedding client.
            
            # We will use requests to hit the Ollama API directly for embeddings as it's lighter
            # than importing another LangChain class if not already there.
            import requests
            
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama2:11434")
            if "localhost" in ollama_base_url and os.path.exists("/.dockerenv"):
                 ollama_base_url = "http://ollama2:11434"

            response = requests.post(
                f"{ollama_base_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text", # Standard embedding model often pulled with Ollama
                    "prompt": text
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [0.0] * 384)
            
            # Fallback if model not found, try 'llama3' or whatever is being used
            logger.warning(f"Embedding failed with nomic-embed-text, trying {self.llm_model}")
            response = requests.post(
                f"{ollama_base_url}/api/embeddings",
                json={
                    "model": self.llm_model.split(":")[0], # Strip tag
                    "prompt": text
                },
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("embedding", [0.0] * 384)
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            
        return [0.0] * 384  # Fallback

    def _build_verification_prompt(
        self,
        prediction: Any,
        realtime: Dict,
        similar: List[Dict]
    ) -> str:
        """
        Build the RALPH LOOP prompt.
        """
        past_attempts = [] # Placeholder for now, could be passed in arguments later

        # Format input data for the agent
        input_data = {
            "alert": {
                "db": prediction.db_name,
                "error": prediction.anomaly_type.value,
                "details": f"Prob: {prediction.probability:.0%}, Trend: {prediction.trend_direction}, Val: {prediction.predicted_value}",
                "timestamp": datetime.utcnow().isoformat()
            },
            "rag_knowledge": [ 
                {"text": s.get('text', '')[:300], "relevance": f"{s.get('score', 0):.2f}"} 
                for s in similar[:3] 
            ],
            "system_state": realtime,
            "past_attempts": past_attempts
        }

        return f"""
# MISSION
You are **Nexi-Sentinel**, the Autonomous Database Administrator Agent for the Nexi DBA AI fleet. 
Your operational mode is the **RALPH LOOP**: A stateless, iterative, infinite remediation cycle.

# OPERATIONAL CONSTRAINTS
1.  **NO CHIT-CHAT**: Do not greet, do not explain "what you are going to do". Output **ONLY** valid JSON.
2.  **STATELESSNESS**: You have no memory of previous prompts. You rely **exclusively** on the `input_context` provided in this message.
3.  **SAFETY FIRST**: If an action is "High Risk" (e.g., `DROP`, `RESTART`, `DELETE`) and `confidence_score` is below 0.9, you MUST escalate to a human instead of executing.
4.  **LOOP PREVENTION**: Check the `past_attempts` array in the input. If an action was already tried and failed, **DO NOT** repeat it. Try the next logical step in the SOP.

# AVAILABLE TOOLS (The "Hands")
You have access to the `ops/scripts/` library via the `run_script` tool. Common capabilities include:
- `kill_blocking_session`: Terminates specific PIDs causing locks.
- `expand_disk`: Triggers cloud volume expansion.
- `restart_service`: Restarts DB services (Postgres/Oracle/MySQL).
- `flush_logs`: Rotates or archives logs to free space.
- `gather_diagnostics`: Runs deep-dive SQL queries for analysis.
- `mongo_runner`: Executes scripts stored in MongoDB.

# INPUT DATA STRUCTURE
{json.dumps(input_data, indent=2, default=str)}

# REASONING FRAMEWORK (Chain of Thought)
Before deciding, perform this internal analysis:
1.  **Analyze**: Decode the error code. Is it a False Positive?
2.  **Correlate**: Does `rag_knowledge` provide a known fix?
3.  **Evaluate**: Look at `past_attempts`. What didn't work?
4.  **Decide**: Select the precise Python script or Escalation.

# OUTPUT FORMAT (STRICT JSON)
You must reply with this EXACT JSON structure. No markdown formatting outside the JSON block.

{{
  "analysis": {{
    "root_cause": "Brief technical explanation of the issue.",
    "severity_assessment": "CRITICAL|WARNING|INFO",
    "confidence_score": 0.0 to 1.0
  }},
  "decision": {{
    "action_type": "EXECUTE_SCRIPT" or "ESCALATE" or "MARK_RESOLVED",
    "rationale": "Why this specific action was chosen."
  }},
  "tool_execution": {{
    "script_name": "name_of_script.py",
    "arguments": {{
      "target_host": "db-prod-01",
      "param1": "value1"
    }}
  }},
  "next_state_hint": "Brief note for the next Ralph Loop iteration if this fails."
}}
"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response, handling thinking tokens and markdown."""
        content = response_text

        # Strip DeepSeek thinking tokens
        if "</think>" in content:
            content = content.split("</think>")[-1]

        # Strip markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            data = json.loads(content)
            
            # Map RALPH output to internal structure
            analysis = data.get("analysis", {})
            decision = data.get("decision", {})
            tool = data.get("tool_execution", {})
            
            return {
                "classification": "REAL_CRITICAL" if analysis.get("severity_assessment") == "CRITICAL" else "NEEDS_INVESTIGATION",
                "confidence": analysis.get("confidence_score", 0.5),
                "reasoning": analysis.get("root_cause", "No reasoning provided"),
                "recommended_action": f"{decision.get('action_type')}: {decision.get('rationale')}",
                "auto_fixable": decision.get("action_type") == "EXECUTE_SCRIPT",
                "tool_execution": tool # Pass this through
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nContent: {content[:500]}")
            return {
                "classification": "NEEDS_INVESTIGATION",
                "confidence": 0.5,
                "reasoning": f"Parse error: {str(e)}",
                "recommended_action": "Manual review required",
                "auto_fixable": False
            }

    def verify_prediction(self, prediction) -> VerifiedAlert:
        """
        Main entry point: verify a single prediction alert.

        Args:
            prediction: PredictionAlert from the Predictor Agent

        Returns:
            VerifiedAlert with classification and recommendations
        """

        # 1. Get real-time status
        realtime = self.get_realtime_status(prediction.db_name)

        # 2. Search for similar incidents (RAG)
        similar = self.search_similar_incidents(
            prediction.anomaly_type.value,
            realtime.get("engine", "ORACLE")
        )

        # 3. LLM reasoning
        if self.llm:
            try:
                prompt = self._build_verification_prompt(prediction, realtime, similar)

                response = self.llm.invoke([
                    SystemMessage(content="You are an expert DBA assistant. Respond only with valid JSON."),
                    HumanMessage(content=prompt)
                ])

                result = self._parse_llm_response(response.content)

            except Exception as e:
                logger.error(f"LLM verification failed: {e}")
                result = {
                    "classification": "NEEDS_INVESTIGATION",
                    "confidence": 0.5,
                    "reasoning": f"LLM error: {str(e)}",
                    "recommended_action": "Manual review required",
                    "auto_fixable": False
                }
        else:
            # Fallback: rule-based classification
            result = self._rule_based_classification(prediction, realtime)

        # 4. Map classification string to enum
        try:
            classification = AlertClassification[result["classification"].upper().replace(" ", "_")]
        except KeyError:
            classification = AlertClassification.NEEDS_INVESTIGATION

        # 5. Extract fix procedure if available
        fix_procedure = None
        if similar and classification in [AlertClassification.REAL_CRITICAL, AlertClassification.REAL_WARNING]:
            fix_procedure = similar[0].get("text")

        return VerifiedAlert(
            prediction_alert=prediction,
            classification=classification,
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "No reasoning provided"),
            similar_incidents=similar,
            recommended_action=result.get("recommended_action", "Review manually"),
            fix_procedure=fix_procedure,
            auto_fixable=result.get("auto_fixable", False),
            tool_execution=result.get("tool_execution"),
            verified_at=datetime.utcnow()
        )

    def _rule_based_classification(
        self,
        prediction,
        realtime: Dict
    ) -> Dict[str, Any]:
        """
        Fallback rule-based classification when LLM is unavailable.
        """
        prob = prediction.probability
        trend = prediction.trend_direction
        current_status = realtime.get("status", "UNKNOWN")

        # If database is already DOWN, this is critical
        if current_status == "DOWN":
            return {
                "classification": "REAL_CRITICAL",
                "confidence": 0.95,
                "reasoning": "Database is already DOWN",
                "recommended_action": "Immediate investigation required",
                "auto_fixable": False
            }

        # High probability + rising trend = critical
        if prob >= 0.8 and trend == "rising":
            return {
                "classification": "REAL_CRITICAL",
                "confidence": prob,
                "reasoning": f"High probability ({prob:.0%}) with rising trend",
                "recommended_action": "Apply automated memory optimization", # Changed for demo
                "auto_fixable": True # Enabled for demo/test
            }

        # Medium-high probability
        if prob >= 0.6:
            return {
                "classification": "REAL_WARNING",
                "confidence": prob,
                "reasoning": f"Medium-high probability ({prob:.0%})",
                "recommended_action": "Monitor closely, prepare contingency",
                "auto_fixable": False
            }

        # Falling trend suggests recovery
        if trend == "falling":
            return {
                "classification": "FALSE_ALARM",
                "confidence": 0.7,
                "reasoning": f"Trend is falling, issue likely resolving",
                "recommended_action": "Continue monitoring",
                "auto_fixable": False
            }

        # Default to needs investigation
        return {
            "classification": "NEEDS_INVESTIGATION",
            "confidence": 0.5,
            "reasoning": "Inconclusive, requires human analysis",
            "recommended_action": "Review metrics manually",
            "auto_fixable": False
        }

    def verify_all(self, predictions: List) -> List[VerifiedAlert]:
        """
        Verify a batch of predictions.

        Args:
            predictions: List of PredictionAlert objects

        Returns:
            List of VerifiedAlert objects
        """
        verified = []
        for prediction in predictions:
            try:
                result = self.verify_prediction(prediction)
                verified.append(result)
            except Exception as e:
                logger.error(f"Error verifying prediction for {prediction.db_name}: {e}")

        logger.info(f"✅ Verified {len(verified)} alerts")
        return verified


if __name__ == "__main__":
    # CLI entry point for testing
    from api_agents.shared.sync_mongo_service import SyncMongoService

    logging.basicConfig(level=logging.INFO)

    mongo = SyncMongoService.get_instance()
    verifier = VerifierAgent(mongo_service=mongo)

    # Test with a mock prediction
    from predictor_agent import PredictionAlert, AnomalyType

    mock_prediction = PredictionAlert(
        db_name="NEXI_PG_MILANO_PROD",
        anomaly_type=AnomalyType.CPU_SPIKE,
        probability=0.85,
        predicted_at=datetime.utcnow(),
        horizon_minutes=30,
        current_value=75.0,
        predicted_value=95.0,
        threshold=90.0,
        trend_direction="rising"
    )

    result = verifier.verify_prediction(mock_prediction)
    print(f"Classification: {result.classification.value}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Action: {result.recommended_action}")
