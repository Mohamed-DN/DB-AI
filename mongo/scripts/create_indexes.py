"""
Create indexes for all CMDB collections
"""
import sys
sys.path.append('..')

from src.connection import get_database


def create_indexes():
    """Create all indexes for CMDB collections"""
    db = get_database()

    # inventory_databases indexes
    print("Creating inventory_databases indexes...")
    db.inventory_databases.create_index(
        [("identity.db_unique_name", 1)],
        unique=True,
        name="idx_unique_dbname"
    )
    db.inventory_databases.create_index(
        [("nodes.hostname", 1), ("nodes.host_ip", 1)],
        name="idx_nodes_lookup"
    )
    db.inventory_databases.create_index(
        [("identity.gateway_ref", 1)],
        name="idx_gateway_ref"
    )
    db.inventory_databases.create_index(
        [("identity.engine", 1), ("identity.environment", 1)],
        name="idx_monitoring_dashboard"
    )

    # business_services indexes
    print("Creating business_services indexes...")
    db.business_services.create_index(
        [("technical_mapping.db_unique_name", 1)],
        name="idx_tech_mapping_db"
    )
    db.business_services.create_index(
        [("service_info.service_now_id", 1)],
        unique=True,
        name="idx_snow_id"
    )

    # discovery_queue indexes
    print("Creating discovery_queue indexes...")
    db.discovery_queue.create_index(
        [("status", 1), ("discovered_at", 1)],
        name="idx_pending_queue"
    )
    db.discovery_queue.create_index(
        [("target_host", 1), ("discovered_service", 1)],
        unique=True,
        name="idx_unique_target"
    )

    # monitoring_alerts indexes
    print("Creating monitoring_alerts indexes...")
    db.monitoring_alerts.create_index(
        [("host_name", 1), ("state", 1)],
        name="idx_host_state"
    )
    db.monitoring_alerts.create_index(
        [("cmdb_db_ref", 1)],
        name="idx_cmdb_link"
    )

    # baselines indexes
    print("Creating baselines indexes...")
    db.baselines.create_index(
        [("db_unique_name", 1), ("baseline_date", -1)],
        name="idx_db_baseline"
    )

    # compliance_reports indexes
    print("Creating compliance_reports indexes...")
    db.compliance_reports.create_index(
        [("report_date", -1)],
        name="idx_report_date"
    )
    db.compliance_reports.create_index(
        [("issues.db_unique_name", 1)],
        name="idx_issues_db"
    )

    # gateways indexes
    print("Creating gateways indexes...")
    db.gateways.create_index(
        [("info.hostname", 1)],
        unique=True,
        name="idx_gw_hostname"
    )
    db.gateways.create_index(
        [("location.datacenter", 1)],
        name="idx_gw_datacenter"
    )

    # agent_runs indexes
    print("Creating agent_runs indexes...")
    db.agent_runs.create_index(
        [("agent_type", 1), ("started_at", -1)],
        name="idx_agent_history"
    )
    db.agent_runs.create_index(
        [("status", 1)],
        name="idx_run_status"
    )

    # rag_knowledge_base indexes
    print("Creating rag_knowledge_base indexes...")
    db.rag_knowledge_base.create_index(
        [("text_chunk", "text")],
        name="idx_text_search"
    )
    db.rag_knowledge_base.create_index(
        [("metadata.db_engines", 1), ("metadata.tags", 1)],
        name="idx_metadata_filter"
    )
    db.rag_knowledge_base.create_index(
        [("source_path", 1), ("chunk_index", 1)],
        unique=True,
        name="idx_unique_chunk"
    )

    print("All indexes created successfully!")


if __name__ == "__main__":
    create_indexes()
