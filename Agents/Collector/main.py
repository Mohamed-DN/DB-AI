"""
SADA Collector Agent
Main entry point for the Collector agent.
"""
import argparse
import logging
from typing import List, Dict

from src.ssh_connection import GatewayConnection, DirectConnection
from src.extractors import OracleDataCollector, SystemDataCollector
from src.cmdb_updater import CMDBUpdater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("collector")


class CollectorAgent:
    """SADA Collector Agent"""

    def __init__(self, gateway_config: Dict = None):
        self.gateway_config = gateway_config
        self.cmdb = CMDBUpdater()
        self.errors = []

    def collect_oracle_database(self, target_host: str, gateway_ref: str, use_gateway: bool = True) -> Dict:
        """Collect data from a single Oracle database host"""
        logger.info(f"Collecting from {target_host}...")
        
        try:
            # Setup SSH connection
            if use_gateway and self.gateway_config:
                conn = GatewayConnection(**self.gateway_config)
                executor = lambda cmd: conn.execute_on_target(target_host, cmd)
            else:
                conn = DirectConnection(target_host, user="oracle")
                executor = conn.execute

            # Collect system data
            system_collector = SystemDataCollector(executor)
            system_data = system_collector.collect_all()
            logger.info(f"  System: {system_data.get('hostname')}")

            # Collect Oracle data
            oracle_collector = OracleDataCollector(executor)
            oracle_data = oracle_collector.collect_all()
            logger.info(f"  Oracle: {oracle_data.get('db_info', [{}])[0].get('DB_UNIQUE_NAME', 'N/A')}")

            # Transform and update CMDB
            cmdb_doc = self.cmdb.transform_oracle_data(oracle_data, system_data, gateway_ref)
            db_name = self.cmdb.upsert_database(cmdb_doc)
            logger.info(f"  Updated CMDB: {db_name}")

            conn.close()
            return {"status": "success", "db_unique_name": db_name}

        except Exception as e:
            logger.error(f"  Error: {e}")
            self.errors.append({"target": target_host, "error": str(e)})
            return {"status": "error", "error": str(e)}

    def collect_from_discovery_queue(self):
        """Process targets from discovery queue"""
        # TODO: Read from discovery_queue collection
        pass

    def run(self, targets: List[str], gateway_ref: str = "dbgec2"):
        """Run collection for multiple targets"""
        logger.info(f"Starting collection for {len(targets)} targets...")
        
        results = []
        for target in targets:
            result = self.collect_oracle_database(target, gateway_ref)
            results.append(result)

        # Log agent run
        success_count = sum(1 for r in results if r.get("status") == "success")
        status = "SUCCESS" if not self.errors else "PARTIAL"
        self.cmdb.log_agent_run("COLLECTOR", len(targets), status, self.errors)

        logger.info(f"Collection complete: {success_count}/{len(targets)} successful")
        return results


def main():
    parser = argparse.ArgumentParser(description="SADA Collector Agent")
    parser.add_argument("--targets", nargs="+", help="Target hosts to collect from")
    parser.add_argument("--gateway", default="dbgec2", help="Gateway reference")
    parser.add_argument("--no-gateway", action="store_true", help="Direct connection (no gateway)")
    
    args = parser.parse_args()

    if args.targets:
        agent = CollectorAgent()
        agent.run(args.targets, args.gateway)
    else:
        print("No targets specified. Use --targets to specify hosts.")
        print("Example: python main.py --targets host1.local host2.local")


if __name__ == "__main__":
    main()
