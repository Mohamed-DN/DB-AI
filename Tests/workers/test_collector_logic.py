
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mock dependencies before importing CollectorAgent
sys.modules['api_agents.shared.sync_mongo_service'] = MagicMock()
sys.modules['api_agents.shared.redis_client'] = MagicMock()
sys.modules['src.extractors'] = MagicMock()
sys.modules['src.cmdb_updater'] = MagicMock()
sys.modules['dotenv'] = MagicMock() # Mock dotenv

# Import CollectorAgent
from api_agents.workers.Collector.collector_agent import CollectorAgent

class TestCollectorNameResolution(unittest.TestCase):
    def setUp(self):
        self.agent = CollectorAgent()
        # Re-mock these because __init__ might have overwritten them with real instances if mocking wasn't perfect,
        # but here we mocked the modules so it should be fine.
        # However, CollectorAgent calls SyncMongoService.get_instance()
        self.agent.mongo = MagicMock()
        self.agent.redis = MagicMock()
        self.agent.cmdb_updater = MagicMock()

        # Mock methods we don't want to actually run
        self.agent.collect_docker_metrics = MagicMock(return_value={})

        # We will use this to capture the container name
        self.captured_names = []
        self.agent.is_container_running = MagicMock(side_effect=self.capture_name)

    def capture_name(self, name):
        self.captured_names.append(name)
        return True # Pretend it's running so we continue logic

    def test_name_resolution_priority(self):
        # 1. Connection container name (Highest priority)
        # 2. Identity db_name
        # 3. Identity db_unique_name (lower case)

        test_cases = [
            # Case 1: All present -> should use connection.container
            {
                "identity": {"db_unique_name": "DB_UNIQUE", "db_name": "db_identity_name"},
                "connection": {"container": "container_connection_name", "type": "LOCAL"},
                "_expected": "container_connection_name"
            },
            # Case 2: Connection container missing -> should use identity.db_name
            {
                "identity": {"db_unique_name": "DB_UNIQUE", "db_name": "db_identity_name"},
                "connection": {"type": "LOCAL"},
                "_expected": "db_identity_name"
            },
             # Case 3: Both missing -> should use db_unique_name lowercased
            {
                "identity": {"db_unique_name": "DB_UNIQUE"},
                "connection": {"type": "LOCAL"},
                "_expected": "db_unique"
            },
        ]

        self.agent.mongo.get_inventory.return_value = test_cases

        self.agent.run_once()

        self.assertEqual(len(self.captured_names), 3)
        self.assertEqual(self.captured_names[0], "container_connection_name")
        self.assertEqual(self.captured_names[1], "db_identity_name")
        self.assertEqual(self.captured_names[2], "db_unique")

    def test_connection_none_crash(self):
        # Case 4: Connection is explicitly None
        test_cases = [
            {
                "identity": {"db_unique_name": "DB_UNIQUE_NONE"},
                "connection": None,
                "_expected": "db_unique_none" # fallback
            }
        ]

        self.agent.mongo.get_inventory.return_value = test_cases
        self.captured_names = [] # reset

        # This should NOT raise AttributeError anymore
        try:
            self.agent.run_once()
        except Exception as e:
            self.fail(f"Caught unexpected exception: {type(e)} {e}")

        # Verify it fell back to unique name
        self.assertEqual(len(self.captured_names), 1)
        self.assertEqual(self.captured_names[0], "db_unique_none")

if __name__ == '__main__':
    unittest.main()
