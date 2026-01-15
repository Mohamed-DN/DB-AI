"""
Template Loader Utility for CMDB JSON Templates
Provides functions to load and populate database templates for Scout/Collector agents.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Template directory path (relative to this file)
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../mongo/schemas/json/templates'))

def get_template_path(engine: str) -> str:
    """Get the path to the template file for a given database engine."""
    engine_map = {
        'ORACLE': 'oracle_template.json',
        'POSTGRES': 'postgresql_template.json',
        'POSTGRESQL': 'postgresql_template.json',
        'MONGODB': 'postgresql_template.json',  # Use Postgres as base for now
        'REDIS': 'postgresql_template.json',
        'QDRANT': 'postgresql_template.json'
    }
    template_file = engine_map.get(engine.upper(), 'postgresql_template.json')
    return os.path.join(TEMPLATES_DIR, template_file)

def load_template(engine: str) -> Dict[str, Any]:
    """Load the JSON template for a given database engine."""
    template_path = get_template_path(engine)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Template not found: {template_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in template {template_path}: {e}")
        return {}

def build_postgres_document(container_name: str, port: int, environment: str, gateway_ref: str = None) -> Dict[str, Any]:
    """
    Build a hierarchical document for PostgreSQL databases.
    Based on postgresql_template.json structure.
    """
    return {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": "POSTGRESQL",
            "environment": environment
        },
        "cluster_identity": {
            "system_identifier": None,  # Will be populated by Collector
            "timeline_id": None,
            "cluster_name": container_name,
            "version_major": None,
            "version_full": None,
            "uptime_seconds": None
        },
        "instance_details": {
            "role": "UNKNOWN",  # Will be populated by Collector
            "inet_server_addr": "127.0.0.1",
            "inet_server_port": port,
            "is_in_recovery": None
        },
        "resource_config": {
            "connections": {
                "max_connections": None,
                "current_active": None
            },
            "memory": {
                "shared_buffers": None,
                "effective_cache_size": None,
                "work_mem": None,
                "maintenance_work_mem": None
            },
            "wal": {
                "wal_level": None,
                "max_wal_size": None
            }
        },
        "replication_ha": {
            "manager": None,
            "sync_standby_names": None,
            "replication_slots": []
        },
        "storage_info": {
            "database_size_bytes": None,
            "temp_file_limit": None,
            "tablespaces": []
        },
        "extensions_installed": [],
        # Legacy fields for backward compatibility
        "identity": {
            "db_unique_name": container_name.upper(),
            "db_name": container_name,
            "family": "POSTGRESQL",
            "engine": "POSTGRES",
            "role": "DEV" if "dev" in container_name.lower() else ("STAGING" if "stg" in container_name.lower() else "PRIMARY"),
            "environment": environment,
            "host": "127.0.0.1",
            "gateway_ref": gateway_ref
        },
        "connection": {
            "port": port,
            "container": container_name,
            "type": "DOCKER"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        }
    }

def build_oracle_document(container_name: str, port: int, environment: str, gateway_ref: str = None) -> Dict[str, Any]:
    """
    Build a hierarchical document for Oracle databases.
    Based on oracle_template.json structure.
    """
    return {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": "ORACLE",
            "environment": environment
        },
        "infrastructure": {
            "host": {
                "alias": container_name,
                "ip_address": "127.0.0.1",
                "os": "Docker/Linux",
                "cloud_provider": None,
                "tenant": None
            },
            "hardware": {
                "type": "Docker Container",
                "resources": {
                    "cpu_sockets": None,
                    "cores": None,
                    "ram_gb": None
                }
            }
        },
        "database_core": {
            "identity": {
                "dbid": None,
                "db_name": container_name,
                "db_unique_name": container_name.upper(),
                "service_name": None,
                "instance_name": None
            },
            "version_info": {
                "full_version": None,
                "patch_level": None,
                "compatibility": None
            },
            "configuration": {
                "type": None,  # CDB/non-CDB
                "pdb_status": None,
                "charset": None,
                "performance_mode": None
            }
        },
        "network": {
            "listeners": [
                {"port": port, "protocol": "TCP"}
            ],
            "cluster_interconnect": {
                "scan_name": None,
                "scan_ips": [],
                "node_vips": []
            }
        },
        "ha_dr": {
            "cluster_roles": [],
            "dataguard": {
                "role": None,
                "target": None,
                "transport_type": None
            }
        },
        # Legacy fields for backward compatibility
        "identity": {
            "db_unique_name": container_name.upper(),
            "db_name": container_name,
            "family": "ORACLE",
            "engine": "ORACLE",
            "role": "PRIMARY" if "primary" in container_name.lower() else ("REPLICA" if "replica" in container_name.lower() else "UNKNOWN"),
            "environment": environment,
            "host": "127.0.0.1",
            "gateway_ref": gateway_ref
        },
        "connection": {
            "port": port,
            "container": container_name,
            "service_name": "ORCL",
            "type": "DOCKER"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        }
    }

def build_document(engine: str, container_name: str, port: int, environment: str, gateway_ref: str = None) -> Dict[str, Any]:
    """
    Build a hierarchical document based on the database engine.
    Dispatcher function that calls the appropriate builder.
    """
    engine_upper = engine.upper()
    
    if engine_upper == 'ORACLE':
        return build_oracle_document(container_name, port, environment, gateway_ref)
    elif engine_upper in ['POSTGRES', 'POSTGRESQL']:
        return build_postgres_document(container_name, port, environment, gateway_ref)
    else:
        # Generic fallback using Postgres template
        doc = build_postgres_document(container_name, port, environment, gateway_ref)
        doc['metadata']['db_technology'] = engine_upper
        doc['identity']['family'] = engine_upper
        doc['identity']['engine'] = engine_upper
        return doc
