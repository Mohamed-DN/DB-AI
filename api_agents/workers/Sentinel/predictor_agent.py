"""
Predictor Agent - Time-series forecasting for database anomaly prediction.
Uses Prophet for seasonal patterns and Isolation Forest for anomaly detection.

Part of the Sentinel Engine Multi-Agent System.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

import pandas as pd

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

logger = logging.getLogger("PredictorAgent")


class AnomalyType(Enum):
    """Types of anomalies the Predictor can detect"""
    OOM_RISK = "oom_risk"
    LOCK_CONTENTION = "lock_contention"
    STORAGE_EXHAUSTION = "storage_exhaustion"
    CPU_SPIKE = "cpu_spike"
    SESSION_OVERFLOW = "session_overflow"
    IO_BOTTLENECK = "io_bottleneck"
    TABLESPACE_FULL = "tablespace_full"


@dataclass
class PredictionAlert:
    """Output of the Predictor Agent"""
    db_name: str
    anomaly_type: AnomalyType
    probability: float  # 0.0 - 1.0
    predicted_at: datetime
    horizon_minutes: int  # When the issue is expected to occur
    current_value: float
    predicted_value: float
    threshold: float
    trend_direction: str  # "rising", "falling", "stable"
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "db_name": self.db_name,
            "anomaly_type": self.anomaly_type.value,
            "probability": self.probability,
            "predicted_at": self.predicted_at.isoformat(),
            "horizon_minutes": self.horizon_minutes,
            "current_value": self.current_value,
            "predicted_value": self.predicted_value,
            "threshold": self.threshold,
            "trend_direction": self.trend_direction,
            "context": self.context
        }


class PredictorAgent:
    """
    Forecasts future anomalies using historical time-series data.

    Uses:
    - Prophet for time-series forecasting (seasonal patterns)
    - Isolation Forest for anomaly detection
    - Linear regression for simple trend analysis

    Features:
    - Configurable thresholds via MongoDB
    - Multi-metric analysis per database
    - Probabilistic alerting with confidence scores
    """

    # Default thresholds (can be overridden via MongoDB config)
    DEFAULT_THRESHOLDS = {
        "cpu_percent": 90.0,
        "memory_percent": 85.0,
        "storage_percent": 95.0,
        "active_sessions": 500,
        "tablespace_percent": 90.0,
        "io_wait_percent": 80.0,
    }

    # Metric to anomaly type mapping
    METRIC_MAP = [
        ("checkmk_cpu_usage_percent", AnomalyType.CPU_SPIKE, "cpu_percent"),
        ("checkmk_memory_usage_percent", AnomalyType.OOM_RISK, "memory_percent"),
        ("oracle_tablespace_used_percent", AnomalyType.TABLESPACE_FULL, "tablespace_percent"),
        ("postgres_storage_percent", AnomalyType.STORAGE_EXHAUSTION, "storage_percent"),
        ("db_active_sessions", AnomalyType.SESSION_OVERFLOW, "active_sessions"),
    ]

    def __init__(self, vm_client=None, mongo_service=None):
        """
        Initialize the Predictor Agent.

        Args:
            vm_client: VictoriaMetrics client for time-series queries
            mongo_service: MongoDB service for inventory and config
        """
        self.vm = vm_client
        self.mongo = mongo_service
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()

        # Try to load custom thresholds from MongoDB
        self._load_thresholds()

    def _load_thresholds(self):
        """Load custom thresholds from MongoDB config"""
        if self.mongo:
            try:
                config = self.mongo.get_config("sentinel_thresholds")
                if config:
                    self.thresholds.update(config)
                    logger.info(f"Loaded custom thresholds from MongoDB")
            except Exception as e:
                logger.debug(f"Using default thresholds: {e}")

    def fetch_historical_metrics(
        self,
        db_name: str,
        metric: str,
        hours: int = 24
    ) -> pd.DataFrame:
        """
        Fetch historical data from VictoriaMetrics.

        Args:
            db_name: Database unique name
            metric: Metric name to query
            hours: Hours of historical data to fetch

        Returns:
            DataFrame with 'ds' (datetime) and 'y' (value) columns for Prophet
        """
        if not self.vm:
            logger.warning("VictoriaMetrics client not available")
            return pd.DataFrame()

        # Build PromQL query
        query = f'{metric}{{db_name="{db_name}"}}'
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)

        try:
            # Query VictoriaMetrics
            data = self.vm.query_range(query, start, end, step="5m")

            if not data:
                return pd.DataFrame()

            # Convert to Prophet format (ds, y)
            df = pd.DataFrame(data, columns=["timestamp", "value"])
            df["ds"] = pd.to_datetime(df["timestamp"], unit="s")
            df["y"] = df["value"].astype(float)
            df = df[["ds", "y"]]

            return df

        except Exception as e:
            logger.error(f"Error fetching metrics for {db_name}: {e}")
            return pd.DataFrame()

    def forecast_metric(
        self,
        df: pd.DataFrame,
        horizon_hours: int = 4
    ) -> pd.DataFrame:
        """
        Forecast future values using available forecasting libraries.

        Tries in order:
        1. Prophet (if installed) - best for seasonal patterns
        2. ARIMA via statsmodels - good for trend detection
        3. Linear regression - simple fallback

        Args:
            df: Historical data in Prophet format (ds, y)
            horizon_hours: How many hours to forecast

        Returns:
            Forecast DataFrame with ds, yhat, yhat_lower, yhat_upper
        """
        if df.empty or len(df) < 10:
            return pd.DataFrame()

        # Try Prophet first (best for seasonal patterns)
        try:
            from prophet import Prophet

            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_mode='multiplicative'
            )
            model.fit(df)

            periods = horizon_hours * 12
            future = model.make_future_dataframe(periods=periods, freq="5min")
            forecast = model.predict(future)

            logger.debug("Using Prophet for forecasting")
            return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

        except ImportError:
            logger.debug("Prophet not installed, trying ARIMA")
        except Exception as e:
            logger.warning(f"Prophet forecast failed: {e}, trying ARIMA")

        # Try ARIMA via statsmodels (good for trend detection)
        try:
            return self._arima_forecast(df, horizon_hours)
        except Exception as e:
            logger.warning(f"ARIMA forecast failed: {e}, using linear fallback")

        # Final fallback: linear regression
        return self._linear_forecast(df, horizon_hours)

    def _arima_forecast(
        self,
        df: pd.DataFrame,
        horizon_hours: int
    ) -> pd.DataFrame:
        """ARIMA forecasting using statsmodels"""
        from statsmodels.tsa.arima.model import ARIMA
        import numpy as np

        if df.empty:
            return pd.DataFrame()

        # Prepare data
        y = df["y"].values
        
        # Fit ARIMA model (order 1,1,1 is robust for most time series)
        try:
            model = ARIMA(y, order=(1, 1, 1))
            fitted = model.fit()
        except Exception:
            # Simpler model if ARIMA(1,1,1) fails
            model = ARIMA(y, order=(1, 0, 0))
            fitted = model.fit()

        # Forecast
        periods = horizon_hours * 12
        forecast_result = fitted.get_forecast(steps=periods)
        predictions = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=0.2)  # 80% confidence

        # Generate future dates
        last_date = df["ds"].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(minutes=5),
            periods=periods,
            freq="5min"
        )

        forecast = pd.DataFrame({
            "ds": future_dates,
            "yhat": predictions,
            "yhat_lower": conf_int.iloc[:, 0] if len(conf_int.columns) >= 2 else predictions * 0.9,
            "yhat_upper": conf_int.iloc[:, 1] if len(conf_int.columns) >= 2 else predictions * 1.1
        })

        logger.debug("Using ARIMA for forecasting")
        return forecast


    def _linear_forecast(
        self,
        df: pd.DataFrame,
        horizon_hours: int
    ) -> pd.DataFrame:
        """Simple linear regression fallback for forecasting"""
        import numpy as np

        if df.empty:
            return pd.DataFrame()

        # Convert to numeric for regression
        x = np.arange(len(df))
        y = df["y"].values

        # Linear fit
        slope, intercept = np.polyfit(x, y, 1)

        # Forecast
        future_x = np.arange(len(df), len(df) + horizon_hours * 12)
        future_y = slope * future_x + intercept

        future_dates = pd.date_range(
            start=df["ds"].max() + timedelta(minutes=5),
            periods=len(future_x),
            freq="5min"
        )

        forecast = pd.DataFrame({
            "ds": future_dates,
            "yhat": future_y,
            "yhat_lower": future_y * 0.9,
            "yhat_upper": future_y * 1.1
        })

        return forecast

    def detect_anomalies_isolation_forest(self, df: pd.DataFrame) -> List[int]:
        """
        Use Isolation Forest to detect current anomalies.

        Args:
            df: Data with 'y' column

        Returns:
            List of indices where anomalies were detected
        """
        if df.empty or len(df) < 10:
            return []

        try:
            from pyod.models.iforest import IForest

            model = IForest(contamination=0.05, random_state=42)
            model.fit(df[["y"]])
            labels = model.predict(df[["y"]])

            return [i for i, label in enumerate(labels) if label == 1]

        except ImportError:
            logger.debug("PyOD not installed, skipping anomaly detection")
            return []
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate trend direction from recent data"""
        if df.empty or len(df) < 5:
            return "stable"

        recent = df["y"].tail(12).values  # Last hour (5-min intervals)
        if len(recent) < 2:
            return "stable"

        first_half = recent[:len(recent)//2].mean()
        second_half = recent[len(recent)//2:].mean()

        diff_percent = (second_half - first_half) / max(first_half, 1) * 100

        if diff_percent > 10:
            return "rising"
        elif diff_percent < -10:
            return "falling"
        return "stable"

    def analyze_database(self, db_name: str) -> List[PredictionAlert]:
        """
        Main entry point: analyze a database for potential future issues.

        Args:
            db_name: Unique database name from inventory

        Returns:
            List of PredictionAlert objects for detected issues
        """
        alerts = []

        for metric_name, anomaly_type, threshold_key in self.METRIC_MAP:
            try:
                # Fetch historical data (48 hours for better patterns)
                df = self.fetch_historical_metrics(db_name, metric_name, hours=48)

                if df.empty:
                    logger.debug(f"No data for {metric_name} on {db_name}")
                    continue

                # Calculate current trend
                trend = self._calculate_trend(df)

                # Forecast next 4 hours
                forecast = self.forecast_metric(df, horizon_hours=4)

                if forecast.empty:
                    continue

                # Check if forecast exceeds threshold
                threshold = self.thresholds.get(threshold_key, 90.0)
                future_rows = forecast[forecast["ds"] > datetime.utcnow()]

                for _, row in future_rows.iterrows():
                    if row["yhat"] >= threshold:
                        # Calculate probability based on confidence interval
                        current_val = df["y"].iloc[-1] if not df.empty else 0
                        predicted_val = row["yhat"]

                        # Probability increases as prediction approaches/exceeds threshold
                        prob = min(1.0, max(0.5,
                            (predicted_val - threshold * 0.8) / (threshold * 0.2)
                        ))

                        # Reduce probability if trend is falling
                        if trend == "falling":
                            prob *= 0.7

                        horizon_mins = int(
                            (row["ds"] - datetime.utcnow()).total_seconds() / 60
                        )

                        alerts.append(PredictionAlert(
                            db_name=db_name,
                            anomaly_type=anomaly_type,
                            probability=round(prob, 2),
                            predicted_at=datetime.utcnow(),
                            horizon_minutes=max(0, horizon_mins),
                            current_value=float(current_val),
                            predicted_value=float(predicted_val),
                            threshold=threshold,
                            trend_direction=trend,
                            context={
                                "metric": metric_name,
                                "data_points": len(df),
                                "forecast_confidence": row.get("yhat_upper", 0) - row.get("yhat_lower", 0)
                            }
                        ))
                        break  # One alert per metric type

            except Exception as e:
                logger.error(f"Error analyzing {metric_name} for {db_name}: {e}")

        return alerts

    def run_once(self) -> List[PredictionAlert]:
        """
        Analyze all databases in inventory.

        Returns:
            List of all prediction alerts across all databases
        """
        if not self.mongo:
            logger.error("MongoDB service not available")
            return []

        try:
            databases = self.mongo.get_inventory()
        except Exception as e:
            logger.error(f"Failed to get inventory: {e}")
            return []

        all_alerts = []

        for db in databases:
            db_name = db.get("identity", {}).get("db_unique_name")
            if not db_name:
                continue

            # Skip databases that are already DOWN
            status = db.get("state", {}).get("status", "UNKNOWN")
            if status == "DOWN":
                logger.debug(f"Skipping {db_name} (already DOWN)")
                continue

            try:
                alerts = self.analyze_database(db_name)
                all_alerts.extend(alerts)
            except Exception as e:
                logger.error(f"Error analyzing {db_name}: {e}")

        logger.info(f"🔮 Predictor: Generated {len(all_alerts)} prediction alerts")
        return all_alerts

    def run_continuous(self, interval_seconds: int = 300):
        """
        Run predictor continuously.

        Args:
            interval_seconds: Seconds between analysis cycles (default: 5 min)
        """
        import time

        logger.info(f"🔮 Predictor Agent starting (interval: {interval_seconds}s)")

        while True:
            try:
                alerts = self.run_once()

                # Store alerts in MongoDB for Verifier to process
                if alerts and self.mongo:
                    for alert in alerts:
                        self.mongo.insert_alert({
                            "type": "PREDICTION",
                            "source": "PredictorAgent",
                            "data": alert.to_dict(),
                            "created_at": datetime.utcnow(),
                            "processed": False
                        })

            except Exception as e:
                logger.error(f"Predictor cycle error: {e}")

            time.sleep(interval_seconds)


if __name__ == "__main__":
    # CLI entry point for testing
    from api_agents.shared.sync_mongo_service import SyncMongoService
    from api_agents.shared.victoriametrics_client import get_victoriametrics_client

    logging.basicConfig(level=logging.INFO)

    mongo = SyncMongoService.get_instance()
    vm = get_victoriametrics_client()

    agent = PredictorAgent(vm_client=vm, mongo_service=mongo)

    import sys
    if "--once" in sys.argv:
        alerts = agent.run_once()
        for a in alerts:
            print(f"⚠️ {a.db_name}: {a.anomaly_type.value} (P={a.probability:.0%}) in {a.horizon_minutes}min")
    else:
        agent.run_continuous()
