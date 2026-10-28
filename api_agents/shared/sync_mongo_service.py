"""
Sync MongoDB Service - PyMongo client for background agent workers.
Replaces the subprocess-based MongoProxy with native Python driver.
"""
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Pattern for safe identifiers
SAFE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_\-\.]+$')


def sanitize_identifier(value: str, field_name: str = "value") -> str:
    """Validate and sanitize identifiers to prevent injection attacks."""
    if not value or not isinstance(value, str):
        raise ValueError(f"Invalid {field_name}: must be a non-empty string")
    if len(value) > 128:
        raise ValueError(f"Invalid {field_name}: too long (max 128 chars)")
    if not SAFE_ID_PATTERN.match(value):
        raise ValueError(f"Invalid {field_name}: contains unsafe characters")
    return value


class SyncMongoService:
    """Synchronous MongoDB service using PyMongo driver for agent workers."""
    
    _instance: Optional["SyncMongoService"] = None
    
    def __init__(self):
        # Build connection string from environment
        mongo_url = os.getenv("MONGODB_URL")
        
        if mongo_url:
            self.connection_string = mongo_url
        else:
            host = os.getenv("MONGODB_HOST", "localhost")
            port = os.getenv("MONGODB_PORT", "28017")
            user = os.getenv("MONGO_USERNAME", "admin")
            password = os.getenv("MONGO_PASSWORD", "pippopippo_1234")
            self.connection_string = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
            
        self.db_name = os.getenv("MONGODB_DB", "m-dn_cmdb_v2")
        
        # Create sync client
        self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
        self.db = self.client[self.db_name]
        
        display_url = mongo_url or f"{host}:{port}"
        print(f"[SyncMongoService] Connected to {display_url}/{self.db_name}")
    
    @classmethod
    def get_instance(cls) -> "SyncMongoService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = SyncMongoService()
        return cls._instance
    
    # =========================================================================
    # Inventory Operations
    # =========================================================================
    
    def get_inventory(self) -> List[Dict[str, Any]]:
        """Get all databases from inventory."""
        cursor = self.db.inventory_databases.find({}, {"_id": 0})
        return list(cursor)
    
    def get_database(self, db_name: str) -> Optional[Dict[str, Any]]:
        """Get a single database by unique name."""
        db_name = sanitize_identifier(db_name, "db_name")
        return self.db.inventory_databases.find_one(
            {"identity.db_unique_name": db_name},
            {"_id": 0}
        )
    
    def upsert_database(self, db_doc: Dict[str, Any]) -> bool:
        """Upsert a database document."""
        name = db_doc.get("identity", {}).get("db_unique_name")
        if not name:
            return False
        name = sanitize_identifier(name, "db_unique_name")
        
        result = self.db.inventory_databases.update_one(
            {"identity.db_unique_name": name},
            {"$set": db_doc},
            upsert=True
        )
        return result.acknowledged
    
    def bulk_write_inventory(self, operations: List[Any]) -> bool:
        """Execute bulk write operations on inventory_databases."""
        if not operations:
            return True
        try:
            result = self.db.inventory_databases.bulk_write(operations, ordered=False)
            return result.acknowledged
        except Exception as e:
            print(f"Bulk write error: {e}")
            return False

    def update_status(self, db_name: str, status: str) -> bool:
        """Update database status."""
        db_name = sanitize_identifier(db_name, "db_name")
        status = sanitize_identifier(status, "status")
        
        result = self.db.inventory_databases.update_one(
            {"identity.db_unique_name": db_name},
            {"$set": {
                "state.status": status,
                "state.last_check": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    def update_metrics(self, db_name: str, metrics: Dict[str, Any]) -> bool:
        """Update database metrics."""
        db_name = sanitize_identifier(db_name, "db_name")
        
        result = self.db.inventory_databases.update_one(
            {"identity.db_unique_name": db_name},
            {"$set": {
                "state.metrics": metrics,
                "state.last_metric_update": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    def get_existing_databases(self) -> Dict[str, str]:
        """Get existing databases with their status for Scout comparison."""
        cursor = self.db.inventory_databases.find(
            {},
            {"identity.db_unique_name": 1, "state.status": 1}
        )
        result = {}
        for doc in cursor:
            name = doc.get("identity", {}).get("db_unique_name")
            status = doc.get("state", {}).get("status", "UNKNOWN")
            if name:
                result[name] = status
        return result
    
    def get_remote_databases(self) -> List[str]:
        """Get list of remote database names (excluded from Docker scan)."""
        cursor = self.db.inventory_databases.find(
            {"connection.type": "REMOTE"},
            {"identity.db_unique_name": 1}
        )
        return [doc.get("identity", {}).get("db_unique_name") for doc in cursor if doc.get("identity", {}).get("db_unique_name")]
    
    def update_last_seen(self, db_name: str, status: str = "UP") -> bool:
        """Update database status and last_seen timestamp."""
        db_name = sanitize_identifier(db_name, "db_name")
        status = sanitize_identifier(status, "status")
        
        result = self.db.inventory_databases.update_one(
            {"identity.db_unique_name": db_name},
            {"$set": {
                "state.status": status,
                "state.last_seen": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    # =========================================================================
    # Storage Operations
    # =========================================================================
    
    def upsert_storage(self, db_name: str, engine: str, storage_items: List[Dict]) -> bool:
        """Upsert storage data."""
        db_name = sanitize_identifier(db_name, "db_name")
        engine = sanitize_identifier(engine, "engine")
        
        result = self.db.inventory_storage.update_one(
            {"db_ref": db_name},
            {"$set": {
                "db_ref": db_name,
                "engine": engine,
                "items": storage_items,
                "last_updated": datetime.utcnow()
            }},
            upsert=True
        )
        return result.acknowledged
    
    # =========================================================================
    # Alert Operations
    # =========================================================================
    
    def get_pending_alerts(self) -> List[Dict[str, Any]]:
        """Get pending critical/warning alerts."""
        cursor = self.db.monitoring_alerts.find({
            "state": {"$in": ["CRITICAL", "WARNING"]},
            "processed": {"$ne": True}
        })
        alerts = list(cursor)
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    
    def get_pending_critical_alerts(self) -> List[Dict[str, Any]]:
        """Get pending critical alerts only."""
        cursor = self.db.monitoring_alerts.find({
            "state": "CRITICAL",
            "processed": {"$ne": True}
        })
        alerts = list(cursor)
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    
    def insert_alert(self, alert: Dict[str, Any]) -> bool:
        """Insert a new alert."""
        alert["timestamp"] = datetime.utcnow()
        result = self.db.monitoring_alerts.insert_one(alert)
        return result.acknowledged
    
    def bulk_write_alerts(self, operations: List[Any]) -> bool:
        """Execute bulk write operations on monitoring_alerts."""
        if not operations:
            return True
        try:
            result = self.db.monitoring_alerts.bulk_write(operations, ordered=False)
            return result.acknowledged
        except Exception as e:
            print(f"Bulk write alerts error: {e}")
            return False

    def get_postgres_databases(self) -> List[Dict[str, Any]]:
        """Get PostgreSQL databases from inventory for CriticalAlert."""
        cursor = self.db.inventory_databases.find(
            {"identity.engine": "POSTGRES"},
            {"_id": 0}
        )
        return list(cursor)
    
    def check_active_alert(self, db_name: str, alert_type: str) -> bool:
        """Check if an unprocessed alert already exists for this db and type."""
        result = self.db.monitoring_alerts.find_one({
            "database": db_name,
            "type": alert_type,
            "processed": False,
            "state": "CRITICAL"
        })
        return result is not None
    
    def resolve_alerts_for_db(self, db_name: str) -> int:
        """Mark alerts as processed when issue is resolved."""
        result = self.db.monitoring_alerts.update_many(
            {"database": db_name, "processed": False, "state": "CRITICAL"},
            {"$set": {"processed": True, "resolved_at": datetime.utcnow()}}
        )
        return result.modified_count
    
    def mark_as_processed(self, alert_id: str, analysis: Dict[str, Any]) -> bool:
        """Mark an alert as processed with AI analysis."""
        from bson import ObjectId
        alert_id = sanitize_identifier(alert_id, "alert_id")
        
        result = self.db.monitoring_alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "processed": True,
                "ai_analysis": analysis
            }}
        )
        return result.modified_count > 0
    
    # =========================================================================
    # System Config
    # =========================================================================
    
    def get_config(self, key: str) -> Optional[Any]:
        """Get a system config value."""
        doc = self.db.system_config.find_one({"key": key})
        return doc.get("value") if doc else None
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set a system config value."""
        result = self.db.system_config.update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True
        )
        return result.acknowledged
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    def ping(self) -> bool:
        """Check MongoDB connection."""
        try:
            self.client.admin.command("ping")
            return True
        except ConnectionFailure:
            return False


# Convenience function
def get_sync_mongo_service() -> SyncMongoService:
    """Get SyncMongoService singleton."""
    return SyncMongoService.get_instance()
