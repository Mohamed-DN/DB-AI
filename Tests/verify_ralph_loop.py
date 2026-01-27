
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# Add root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from api_agents.workers.Sentinel.verifier_agent import VerifierAgent, VerifiedAlert, AlertClassification
from api_agents.workers.Sentinel.sentinel_workflow import AutoFixer

class TestRalphLoop(unittest.TestCase):

    def setUp(self):
        self.mock_mongo = MagicMock()
        self.verifier = VerifierAgent(mongo_service=self.mock_mongo, qdrant_url=None, llm_model="mock")
        # Mock LLM
        self.verifier.llm = MagicMock()

    def test_brain_decision_making(self):
        """Test that VerifierAgent correctly parses RALPH JSON into VerifiedAlert"""
        
        # 1. Mock LLM Response (RALPH Format)
        ralph_response = {
            "analysis": {
                "root_cause": "Blocking session detected on PID 123",
                "severity_assessment": "CRITICAL",
                "confidence_score": 0.95
            },
            "decision": {
                "action_type": "EXECUTE_SCRIPT",
                "rationale": "Terminating blocker to restore service"
            },
            "tool_execution": {
                "script_name": "kill_blocking_session.py",
                "arguments": {
                    "target_host": "NEXI_PG_TEST",
                    "pid": "123"
                }
            },
            "next_state_hint": "Check if session is gone"
        }
        
        # Mock invoke return value
        mock_msg = MagicMock()
        mock_msg.content = json.dumps(ralph_response)
        self.verifier.llm.invoke.return_value = mock_msg
        
        # Mock inputs
        mock_prediction = MagicMock()
        mock_prediction.db_name = "NEXI_PG_TEST"
        mock_prediction.probability = 0.9
        
        # Run Verification
        verified_alert = self.verifier.verify_prediction(mock_prediction)
        
        # Assertions
        print(f"\n🧠 BRAIN TEST: Classification={verified_alert.classification}, AutoFix={verified_alert.auto_fixable}")
        self.assertEqual(verified_alert.classification, AlertClassification.REAL_CRITICAL)
        self.assertTrue(verified_alert.auto_fixable)
        self.assertIsNotNone(verified_alert.tool_execution)
        self.assertEqual(verified_alert.tool_execution["script_name"], "kill_blocking_session.py")
        
        return verified_alert

    @patch('subprocess.run')
    def test_hands_execution(self, mock_subprocess):
        """Test that AutoFixer executes the script defined in verified_alert"""
        
        # Create a mock alert with tool execution
        alert = VerifiedAlert(
            prediction_alert=MagicMock(),
            classification=AlertClassification.REAL_CRITICAL,
            confidence=0.9,
            reasoning="Test",
            auto_fixable=True,
            tool_execution={
                "script_name": "kill_blocking_session.py",
                "arguments": {"target_host": "NEXI_PG_TEST", "pid": "123"}
            }
        )
        alert.prediction_alert.db_name = "NEXI_PG_TEST"
        
        # Setup mock subprocess
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Killed PID 123"
        
        # Run AutoFixer
        fixer = AutoFixer()
        result = fixer.execute_fix(alert)
        
        # Assertions
        print(f"\n✋ HANDS TEST: Result={result}")
        self.assertTrue(result)
        
        # Verify the command called
        called_args = mock_subprocess.call_args[0][0]
        print(f"   Command Executed: {called_args}")
        self.assertIn("mongo_runner.py", called_args[1]) # [python, mongo_runner.py, script_name...]
        self.assertIn("kill_blocking_session.py", called_args[2])
        self.assertIn("pid=123", called_args)

if __name__ == '__main__':
    unittest.main()
