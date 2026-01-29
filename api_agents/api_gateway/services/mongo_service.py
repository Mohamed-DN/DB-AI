"""
MongoDB Service - Async MongoDB client using Motor
Replaces the subprocess-based MongoProxy with native async driver.
"""
import os
import re
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

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


class MongoService:
    """Async MongoDB service using Motor driver."""
    
    _instance: Optional["MongoService"] = None
    
    def __init__(self):
        host = "localhost"
        port = "27017"
        db_name = "nexi_cmdb_v2"
        self.connection_string = f"mongodb://{host}:{port}/"
        self.db_name = db_name
        
        # Create async client
        self.client = AsyncIOMotorClient(self.connection_string)
        self.db = self.client[self.db_name]
        
        print(f"[DEBUG] [MongoService] Connection String: {self.connection_string}")
        print(f"[MongoService] Connected to {host}:{port}/{db_name}")

    def _get_db(self):
        """Helper for routers using older method name."""
        return self.db

    
    @classmethod
    def get_instance(cls) -> "MongoService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = MongoService()
        return cls._instance
    
    # =========================================================================
    # Inventory Operations
    # =========================================================================
    
    async def create_indexes(self):
        """Create indexes for performance."""
        # Unique Name Index for fast lookup and A-Z sorting
        await self.db.inventory_databases.create_index("identity.db_unique_name")
        # Host Index
        await self.db.inventory_databases.create_index("connection.host")
        print("[MongoService] Indexes ensured.")

    async def get_inventory(self, skip: int = 0, limit: int = 100, search: str = None, starts_with: str = None, filter_by: str = "name") -> Dict[str, Any]:
        """Get paginated databases from inventory with search/filter."""
        query = {}
        
        if starts_with:
            # Prefix search (A-Z Index)
            regex = f"^{re.escape(starts_with)}"
            if filter_by == "host":
                query["connection.host"] = {"$regex": regex, "$options": "i"}
            else:
                query["identity.db_unique_name"] = {"$regex": regex, "$options": "i"}
                
        elif search:
            # General fuzzy search
            query = {
                "$or": [
                    {"identity.db_unique_name": {"$regex": search, "$options": "i"}},
                    {"connection.host": {"$regex": search, "$options": "i"}},
                    {"identity.engine": {"$regex": search, "$options": "i"}}
                ]
            }

        total = await self.db.inventory_databases.count_documents(query)
        cursor = self.db.inventory_databases.find(query, {"_id": 0}).skip(skip).limit(limit)
        
        # Sort A-Z if browsing by letter
        if starts_with:
            sort_field = "connection.host" if filter_by == "host" else "identity.db_unique_name"
            cursor.sort(sort_field, 1)
            
        items = await cursor.to_list(length=limit)
        
        return {
            "items": items,
            "total": total,
            "page": (skip // limit) + 1,
            "limit": limit
        }
    
    async def get_database(self, db_name: str) -> Optional[Dict[str, Any]]:
        """Get a single database by unique name."""
        db_name = sanitize_identifier(db_name, "db_name")
        return await self.db.inventory_databases.find_one(
            {"identity.db_unique_name": db_name},
            {"_id": 0}
        )
    
    async def upsert_database(self, db_doc: Dict[str, Any]) -> bool:
        """Upsert a database document."""
        name = db_doc.get("identity", {}).get("db_unique_name")
        if not name:
            return False
        name = sanitize_identifier(name, "db_unique_name")
        
        result = await self.db.inventory_databases.update_one(
            {"identity.db_unique_name": name},
            {"$set": db_doc},
            upsert=True
        )
        return result.acknowledged
    
    async def delete_database(self, db_name: str) -> bool:
        """Delete a database from inventory."""
        db_name = sanitize_identifier(db_name, "db_name")
        result = await self.db.inventory_databases.delete_one(
            {"identity.db_unique_name": db_name}
        )
        return result.deleted_count > 0
    
    async def update_status(self, db_name: str, status: str) -> bool:
        """Update database status."""
        db_name = sanitize_identifier(db_name, "db_name")
        status = sanitize_identifier(status, "status")
        
        result = await self.db.inventory_databases.update_one(
            {"identity.db_unique_name": db_name},
            {"$set": {
                "state.status": status,
                "state.last_check": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    async def update_metrics(self, db_name: str, metrics: Dict[str, Any]) -> bool:
        """Update database metrics."""
        db_name = sanitize_identifier(db_name, "db_name")
        
        result = await self.db.inventory_databases.update_one(
            {"identity.db_unique_name": db_name},
            {"$set": {
                "state.metrics": metrics,
                "state.last_metric_update": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    async def count_databases(self) -> int:
        """Count total databases."""
        return await self.db.inventory_databases.count_documents({})
    
    # =========================================================================
    # Storage Operations
    # =========================================================================
    
    async def get_all_storage(self) -> List[Dict[str, Any]]:
        """Get all storage inventory items."""
        cursor = self.db.inventory_storage.find({})
        items = await cursor.to_list(length=None)
        for item in items:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        return items
    
    async def get_storage_for_db(self, db_name: str) -> Optional[Dict[str, Any]]:
        """Get storage for a specific database."""
        db_name = sanitize_identifier(db_name, "db_name")
        item = await self.db.inventory_storage.find_one({"db_ref": db_name})
        if item and "_id" in item:
            item["_id"] = str(item["_id"])
        return item
    
    async def upsert_storage(self, db_name: str, engine: str, storage_items: List[Dict]) -> bool:
        """Upsert storage data."""
        db_name = sanitize_identifier(db_name, "db_name")
        engine = sanitize_identifier(engine, "engine")
        
        result = await self.db.inventory_storage.update_one(
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
    
    async def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cursor = self.db.monitoring_alerts.find().sort("timestamp", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
            
            # Normalize Sentinel alerts for Frontend
            if "type" in a and a["type"].startswith("SENTINEL_"):
                # Map Sentinel Critical to Standard Critical
                if "state" not in a:
                    if "CRITICAL" in a["type"]:
                        a["state"] = "CRITICAL"
                    elif "WARNING" in a["type"]:
                        a["state"] = "WARNING"
                    else:
                        a["state"] = "UNKNOWN"
                
                # Map db_name to host_name if missing
                if "host_name" not in a and "db_name" in a:
                    a["host_name"] = a["db_name"]
                
                # Map service
                if "service" not in a:
                    a["service"] = "Sentinel AI"
                
                # Map message from data if missing
                if "message" not in a and "data" in a:
                    reasoning = a["data"].get("reasoning", "")
                    anomaly = a["data"].get("prediction_alert", {}).get("anomaly_type", "Anomaly")
                    a["message"] = f"{anomaly}: {reasoning}"
                    
                    # Add Auto-Fix flag to message for visibility
                    if a["data"].get("auto_fixable"):
                        a["message"] = f"[AUTO-FIXED] {a['message']}"

        return alerts
    
    async def get_pending_alerts(self) -> List[Dict[str, Any]]:
        """Get pending critical/warning alerts."""
        cursor = self.db.monitoring_alerts.find({
            "state": {"$in": ["CRITICAL", "WARNING"]},
            "processed": {"$ne": True}
        })
        alerts = await cursor.to_list(length=None)
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    
    async def get_alerts_with_ai_analysis(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get alerts that have AI analysis."""
        cursor = self.db.monitoring_alerts.find(
            {"ai_analysis": {"$exists": True}}
        ).sort("timestamp", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    
    async def count_critical_alerts(self) -> int:
        """Count unprocessed critical alerts."""
        return await self.db.monitoring_alerts.count_documents({
            "state": "CRITICAL",
            "processed": {"$ne": True}
        })
    
    async def insert_alert(self, alert: Dict[str, Any]) -> bool:
        """Insert a new alert."""
        alert["timestamp"] = datetime.utcnow()
        result = await self.db.monitoring_alerts.insert_one(alert)
        return result.acknowledged
    
    async def clear_alerts(self) -> int:
        """Mark all pending alerts as processed."""
        result = await self.db.monitoring_alerts.update_many(
            {"processed": False},
            {"$set": {"processed": True}}
        )
        return result.modified_count
    
    async def mark_alert_processed(self, alert_id: str, analysis: Dict[str, Any]) -> bool:
        """Mark an alert as processed with AI analysis."""
        from bson import ObjectId
        alert_id = sanitize_identifier(alert_id, "alert_id")
        
        result = await self.db.monitoring_alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "processed": True,
                "ai_analysis": analysis
            }}
        )
        return result.modified_count > 0
    
    # =========================================================================
    # Business Services
    # =========================================================================
    
    async def get_business_services(self) -> List[Dict[str, Any]]:
        """Get all business services."""
        cursor = self.db.business_services.find({}, {"_id": 0})
        return await cursor.to_list(length=None)
    
    # =========================================================================
    # System Config
    # =========================================================================
    
    async def get_config(self, key: str) -> Optional[Any]:
        """Get a system config value."""
        doc = await self.db.system_config.find_one({"key": key})
        return doc.get("value") if doc else None
    
    async def set_config(self, key: str, value: Any) -> bool:
        """Set a system config value."""
        result = await self.db.system_config.update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True
        )
        return result.acknowledged
    
    async def get_all_config(self) -> Dict[str, Any]:
        """Get all system config."""
        cursor = self.db.system_config.find({})
        docs = await cursor.to_list(length=None)
        return {doc["key"]: doc.get("value") for doc in docs}
    
    # =========================================================================
    # Raw Collection Access
    # =========================================================================
    
    async def get_raw_collection(self, collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get raw collection data for Explorer."""
        allowed = [
            "inventory_databases",
            "monitoring_alerts",
            "business_services",
            "system_config",
            "discovery_queue",
            "agent_runs",
            "baselines",
            "compliance_reports",
            "gateways",
            "rag_knowledge_base"
        ]
        
        if collection_name not in allowed:
            raise ValueError(f"Collection '{collection_name}' not allowed")
        
        collection = self.db[collection_name]
        cursor = collection.find().limit(limit)
        items = await cursor.to_list(length=limit)
        
        for item in items:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        
        return items
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    async def ping(self) -> bool:
        """Check MongoDB connection."""
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False


# Convenience function
def get_mongo_service() -> MongoService:
    """Get MongoService singleton."""
    return MongoService.get_instance()
