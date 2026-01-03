"""Repository for inventory_databases collection"""
from typing import List, Optional, Dict, Any
from pymongo.results import InsertOneResult, UpdateResult
from ..connection import get_collection


class InventoryRepository:
    """Repository for inventory_databases CRUD operations"""

    def __init__(self):
        self.collection = get_collection("inventory_databases")

    def find_by_unique_name(self, db_unique_name: str) -> Optional[Dict]:
        """Find database by unique name"""
        return self.collection.find_one({"identity.db_unique_name": db_unique_name})

    def find_by_gateway(self, gateway_ref: str) -> List[Dict]:
        """Find all databases using a specific gateway"""
        return list(self.collection.find({"identity.gateway_ref": gateway_ref}))

    def find_by_engine(self, engine: str) -> List[Dict]:
        """Find all databases by engine type"""
        return list(self.collection.find({"identity.engine": engine}))

    def find_by_environment(self, environment: str) -> List[Dict]:
        """Find all databases by environment"""
        return list(self.collection.find({"identity.environment": environment}))

    def find_with_tablespace_above_threshold(self, threshold: int = 90) -> List[Dict]:
        """Find databases with tablespace usage above threshold"""
        return list(self.collection.find({
            "storage.tablespaces.used_pct": {"$gte": threshold}
        }))

    def insert(self, database: Dict) -> InsertOneResult:
        """Insert a new database"""
        return self.collection.insert_one(database)

    def upsert(self, db_unique_name: str, database: Dict) -> UpdateResult:
        """Upsert database by unique name"""
        return self.collection.update_one(
            {"identity.db_unique_name": db_unique_name},
            {"$set": database},
            upsert=True
        )

    def update_storage(self, db_unique_name: str, storage: Dict) -> UpdateResult:
        """Update storage information for a database"""
        return self.collection.update_one(
            {"identity.db_unique_name": db_unique_name},
            {"$set": {"storage": storage}}
        )

    def count_by_engine(self) -> Dict[str, int]:
        """Count databases by engine type"""
        pipeline = [
            {"$group": {"_id": "$identity.engine", "count": {"$sum": 1}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in result}

    def get_all(self, limit: int = 100) -> List[Dict]:
        """Get all databases with limit"""
        return list(self.collection.find().limit(limit))
