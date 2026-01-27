import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api_agents.workers.sentinel.predictor_agent import PredictorAgent, AnomalyType

class TestPredictorAgent(unittest.TestCase):

    def setUp(self):
        self.agent = PredictorAgent(vm_client=None, mongo_service=None)

    def test_calculate_trend_rising(self):
        # Create rising trend data
        y = np.linspace(10, 100, 20)
        df = pd.DataFrame({'y': y})
        
        trend = self.agent._calculate_trend(df)
        self.assertEqual(trend, "rising")

    def test_calculate_trend_falling(self):
        # Create falling trend data
        y = np.linspace(100, 10, 20)
        df = pd.DataFrame({'y': y})
        
        trend = self.agent._calculate_trend(df)
        self.assertEqual(trend, "falling")

    def test_linear_forecast(self):
        # Strict linear data
        now = datetime.utcnow()
        dates = [now + timedelta(minutes=5*i) for i in range(10)]
        y = [10 + i * 2 for i in range(10)] # 10, 12, 14...
        
        df = pd.DataFrame({'ds': dates, 'y': y})
        
        # Forecast 1 hour (12 steps)
        # Next value should be 10 + 10*2 = 30
        forecast = self.agent._linear_forecast(df, horizon_hours=1)
        
        self.assertFalse(forecast.empty)
        first_pred = forecast.iloc[0]['yhat']
        # Linear regression on perfect line should predict 30 loosely
        self.assertAlmostEqual(first_pred, 30.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
