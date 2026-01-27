import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import sys
import os
import asyncio

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api_agents.workers.OEM_Collector.oem_collector import OEMClient, OEMInstance, OEMMetric

class TestOEMCollector(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.instance = OEMInstance(
            name="TEST_OEM",
            url="https://test-oem:7803/em",
            username="user",
            password="pass"
        )
        self.client = OEMClient(self.instance)

    @patch('httpx.AsyncClient')
    async def test_get_targets_success(self, mock_client_cls):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"name": "DB1", "targetType": "oracle_database"},
                {"name": "DB2", "targetType": "oracle_database"}
            ]
        }
        
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)

        # Test
        targets = await self.client.get_targets()
        self.assertEqual(len(targets), 2)
        self.assertEqual(targets[0]['name'], "DB1")

    @patch('httpx.AsyncClient')
    async def test_get_target_metrics_success(self, mock_client_cls):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "metricColumn": "cpu_usage",
                    "value": "45.5",
                    "unit": "%"
                }
            ]
        }
        
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)

        # Test
        metrics = await self.client.get_target_metrics("DB1")
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].metric_name, "cpu_usage")
        self.assertEqual(metrics[0].value, 45.5)

if __name__ == '__main__':
    unittest.main()
