"""
CMDB Updater
Transforms extracted data into CMDB format and updates MongoDB.
"""
import sys
from datetime import datetime
from typing import Dict, List, Optional

import os

# Add MongoDB src to path (pointing directly to src to avoid namespace collision)
mongo_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../MongoDB/src'))
if mongo_src_path not in sys.path:
    sys.path.insert(0, mongo_src_path)

from connection import get_collection


class CMDBUpdater:
    """Updates CMDB with collected data"""

    def __init__(self, mongo_proxy=None):
        self.mongo_proxy = mongo_proxy
        self.inventory = get_collection("inventory_databases")
        self.agent_runs = get_collection("agent_runs")

    def transform_oracle_data(self, oracle_data: Dict, system_data: Dict, gateway_ref: str) -> Dict:
        """Transform raw Oracle/System data into CMDB format"""
        
        db_info = oracle_data.get("db_info", [{}])[0]
        oracle_home = oracle_data.get("oracle_home", [{}])[0].get("ORACLE_HOME", "")
        
        # Build identity
        identity = {
            "db_unique_name": db_info.get("DB_UNIQUE_NAME", "UNKNOWN"),
            "db_name": db_info.get("DB_NAME", ""),
            "engine": "ORACLE",
            "topology": "RAC" if len(oracle_data.get("rac_nodes", [])) > 1 else "SINGLE",
            "environment": self._detect_environment(db_info.get("DB_UNIQUE_NAME", "")),
            "gateway_ref": gateway_ref
        }

        # Build nodes
        nodes = []
        for node in oracle_data.get("rac_nodes", [db_info]):
            node_data = {
                "node_name": node.get("INSTANCE_NAME", identity["db_unique_name"]),
                "hostname": system_data.get("hostname", node.get("HOST_NAME", "")),
                "host_ip": system_data.get("host_ip", ""),
                "role": "PRIMARY" if node.get("DATABASE_STATUS") != "MOUNTED" else "STANDBY",
                "status": node.get("STATUS", "UNKNOWN"),
                "host_specs": {
                    "os": system_data.get("os", {}),
                    "cpu": system_data.get("cpu", {}),
                    "memory": {
                        "total_gb": system_data.get("memory", {}).get("total_gb", 0),
                        "hugepages_configured": False,
                        "hugepages_size_gb": 0
                    }
                }
            }
            nodes.append(node_data)

        # Build configuration
        patches = [p.get("PATCH_ID", "") for p in oracle_data.get("patches", [])]
        configuration = {
            "version": db_info.get("VERSION", ""),
            "port": 1521,
            "oracle_home": oracle_home,
            "patches": patches,
            "oracle_specific": {
                "architecture": "CDB" if oracle_data.get("pdbs") else "NON-CDB",
                "pdbs": [
                    {
                        "name": p.get("PDB_NAME", ""), 
                        "status": p.get("STATUS", "UNKNOWN")
                    }
                    for p in oracle_data.get("pdbs", [])
                ]
            }
        }

        # Build licensing
        active_options = [opt.get("NAME", "") for opt in oracle_data.get("license_options", [])]
        licensing = {
            "product_edition": "ENTERPRISE" if "Real Application Clusters" in active_options else "STANDARD",
            "active_options": active_options
        }

        # Build storage
        diskgroups = [
            {
                "name": dg.get("NAME", ""),
                "total_gb": int(float(dg.get("TOTAL_GB", 0))),
                "used_pct": float(dg.get("USED_PCT", 0)),
                "state": dg.get("STATE", "")
            }
            for dg in oracle_data.get("diskgroups", [])
        ]
        
        tablespaces = [
            {
                "name": ts.get("TABLESPACE_NAME", ""),
                "used_pct": float(ts.get("USED_PCT", 0)),
                "autoextensible": ts.get("AUTOEXTENSIBLE", "NO"),
                "max_gb": int(float(ts.get("MAX_GB", 0)))
            }
            for ts in oracle_data.get("tablespaces", [])
        ]

        storage = {
            "last_check": datetime.utcnow(),
            "asm_diskgroups": diskgroups,
            "tablespaces": tablespaces
        }

        # Build Data Guard if present
        data_protection = {"backup": None, "replication": None}
        if oracle_data.get("dataguard"):
            data_protection["replication"] = {
                "is_active": True,
                "technology": "DATAGUARD",
                "oracle_dataguard": {
                    "destinations": [
                        {
                            "db_unique_name": dg.get("DB_UNIQUE_NAME", ""),
                            "status": dg.get("STATUS", "")
                        }
                        for dg in oracle_data.get("dataguard", [])
                    ]
                }
            }

        return {
            "identity": identity,
            "nodes": nodes,
            "configuration": configuration,
            "licensing": licensing,
            "storage": storage,
            "data_protection": data_protection,
            "state": {
                "status": "UP",
                "metrics": {
                    "hostname": system_data.get("hostname"),
                    "os": system_data.get("os"),
                    "cpu": system_data.get("cpu"),
                    "memory": system_data.get("memory")
                },
                "last_check": datetime.utcnow()
            }
        }

    def upsert_database(self, data: Dict):
        """Insert or Update database asset"""
        if self.mongo_proxy:
            # Use Proxy
            return self.mongo_proxy.upsert_database(data)
        
        # Fallback to PyMongo
        coll = get_collection("inventory_databases")
        unique_name = data.get("identity", {}).get("db_unique_name")
        
        if not unique_name:
            print("❌ Skipping upsert: No db_unique_name")
            return

        coll.update_one(
            {"identity.db_unique_name": unique_name},
            {"$set": data},
            upsert=True
        )
        
        return unique_name

    def log_agent_run(self, agent_type: str, targets_processed: int, status: str, errors: List = None):
        """Log agent execution"""
        self.agent_runs.insert_one({
            "agent_type": agent_type,
            "started_at": datetime.utcnow(),
            "finished_at": datetime.utcnow(),
            "status": status,
            "targets_processed": targets_processed,
            "errors": errors or []
        })

    @staticmethod
    def _detect_environment(db_name: str) -> str:
        """Detect environment from database name"""
        name_upper = db_name.upper()
        if any(x in name_upper for x in ["PROD", "PRD", "P01"]):
            return "PROD"
        elif any(x in name_upper for x in ["TEST", "TST", "T01"]):
            return "TEST"
        elif any(x in name_upper for x in ["DEV", "D01"]):
            return "DEV"
        return "UNKNOWN"
