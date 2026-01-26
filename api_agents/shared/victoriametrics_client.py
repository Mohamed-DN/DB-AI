"""
VictoriaMetrics Client - Query and write time-series data.
Supports PromQL queries for historical data and Graphite write for ingestion.

Used by the Sentinel Engine for predictive analytics.
"""
import os
import socket
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

import httpx

logger = logging.getLogger("VictoriaMetricsClient")


class VictoriaMetricsClient:
    """
    Client for VictoriaMetrics time-series database.
    Supports PromQL queries and Graphite write protocol.

    Configuration via environment:
        - VICTORIAMETRICS_URL: Query endpoint (default: http://localhost:8428)
        - GRAPHITE_HOST: Write endpoint host (default: localhost)
        - GRAPHITE_PORT: Write endpoint port (default: 2003)
    """

    def __init__(
        self,
        query_url: Optional[str] = None,
        graphite_host: Optional[str] = None,
        graphite_port: Optional[int] = None
    ):
        self.query_url = query_url or os.getenv("VICTORIAMETRICS_URL", "http://localhost:8428")
        self.graphite_host = graphite_host or os.getenv("GRAPHITE_HOST", "localhost")
        self.graphite_port = graphite_port or int(os.getenv("GRAPHITE_PORT", "2003"))

    def query_instant(self, query: str) -> List[Dict]:
        """
        Execute instant PromQL query.

        Args:
            query: PromQL query string (e.g., 'cpu_usage{db_name="PROD"}')

        Returns:
            List of result dictionaries with metric and value
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(
                    f"{self.query_url}/api/v1/query",
                    params={"query": query}
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "success":
                    logger.warning(f"Query returned non-success status: {data}")
                    return []

                return data.get("data", {}).get("result", [])

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error querying VictoriaMetrics: {e}")
            return []
        except Exception as e:
            logger.error(f"Error querying VictoriaMetrics: {e}")
            return []

    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> List[Tuple[float, float]]:
        """
        Execute range PromQL query for historical data.

        Args:
            query: PromQL query string
            start: Start datetime (UTC)
            end: End datetime (UTC)
            step: Query resolution (e.g., "5m", "1h")

        Returns:
            List of (timestamp, value) tuples
        """
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.get(
                    f"{self.query_url}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": start.isoformat() + "Z",
                        "end": end.isoformat() + "Z",
                        "step": step
                    }
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "success":
                    logger.warning(f"Range query returned non-success: {data}")
                    return []

                results = data.get("data", {}).get("result", [])
                if not results:
                    return []

                # Return first result's values as (timestamp, value) tuples
                return [(float(v[0]), float(v[1])) for v in results[0].get("values", [])]

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in range query: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in range query: {e}")
            return []

    def query_range_multi(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Dict[str, List[Tuple[float, float]]]:
        """
        Execute range query returning multiple series.

        Returns:
            Dict mapping metric labels to [(timestamp, value), ...]
        """
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.get(
                    f"{self.query_url}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": start.isoformat() + "Z",
                        "end": end.isoformat() + "Z",
                        "step": step
                    }
                )
                resp.raise_for_status()
                data = resp.json()

                results = data.get("data", {}).get("result", [])
                output = {}

                for result in results:
                    # Build label key from metric labels
                    metric = result.get("metric", {})
                    label_key = "_".join(f"{k}={v}" for k, v in sorted(metric.items()))
                    values = [(float(v[0]), float(v[1])) for v in result.get("values", [])]
                    output[label_key] = values

                return output

        except Exception as e:
            logger.error(f"Error in multi range query: {e}")
            return {}

    def write_graphite(self, metrics: List[Tuple[str, float, int]]) -> bool:
        """
        Write metrics via Graphite plaintext protocol.

        Args:
            metrics: List of (metric_path, value, unix_timestamp)

        Returns:
            True if write succeeded
        """
        if not metrics:
            return True

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10.0)
                sock.connect((self.graphite_host, self.graphite_port))

                payload = ""
                for path, value, ts in metrics:
                    # Sanitize path (no spaces, valid chars only)
                    safe_path = path.replace(" ", "_").replace(":", "_")
                    payload += f"{safe_path} {value} {ts}\n"

                sock.sendall(payload.encode("utf-8"))
                logger.debug(f"Wrote {len(metrics)} metrics to Graphite")
                return True

        except socket.timeout:
            logger.error("Graphite write timed out")
            return False
        except ConnectionRefusedError:
            logger.error(f"Graphite connection refused at {self.graphite_host}:{self.graphite_port}")
            return False
        except Exception as e:
            logger.error(f"Graphite write failed: {e}")
            return False

    def write_prometheus(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Write metrics via VictoriaMetrics import API (Prometheus format).

        Args:
            metrics: List of {"metric": "name", "labels": {...}, "value": float, "timestamp": int}

        Returns:
            True if write succeeded
        """
        if not metrics:
            return True

        try:
            # Build Prometheus text format
            lines = []
            for m in metrics:
                name = m["metric"]
                labels = m.get("labels", {})
                value = m["value"]
                ts = m.get("timestamp", int(datetime.utcnow().timestamp() * 1000))

                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f"{name}{{{label_str}}} {value} {ts}")
                else:
                    lines.append(f"{name} {value} {ts}")

            payload = "\n".join(lines)

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.query_url}/api/v1/import/prometheus",
                    content=payload,
                    headers={"Content-Type": "text/plain"}
                )
                resp.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Prometheus import failed: {e}")
            return False

    def health_check(self) -> bool:
        """Check if VictoriaMetrics is reachable"""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.query_url}/health")
                return resp.status_code == 200
        except Exception:
            return False


# Convenience singleton
_vm_client: Optional[VictoriaMetricsClient] = None


def get_victoriametrics_client() -> VictoriaMetricsClient:
    """Get singleton VictoriaMetrics client"""
    global _vm_client
    if _vm_client is None:
        _vm_client = VictoriaMetricsClient()
    return _vm_client
