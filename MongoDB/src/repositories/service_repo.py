"""Repository for business_services collection"""
from typing import List, Optional, Dict
from pymongo.results import InsertOneResult, UpdateResult
from ..connection import get_collection


class ServiceRepository:
    """Repository for business_services CRUD operations"""

    def __init__(self):
        self.collection = get_collection("business_services")

    def find_by_service_now_id(self, snow_id: str) -> Optional[Dict]:
        """Find service by ServiceNow ID"""
        return self.collection.find_one({"service_info.service_now_id": snow_id})

    def find_by_database(self, db_unique_name: str) -> List[Dict]:
        """Find all services using a specific database"""
        return list(self.collection.find({
            "technical_mapping.db_unique_name": db_unique_name
        }))

    def find_by_schema(self, schema_name: str) -> List[Dict]:
        """Find services by schema name"""
        return list(self.collection.find({
            "technical_mapping.schemas.schema_name": schema_name
        }))

    def get_bao_for_database(self, db_unique_name: str) -> Optional[Dict]:
        """Get BAO contact for a database"""
        service = self.collection.find_one(
            {"technical_mapping.db_unique_name": db_unique_name},
            {"contacts.bao": 1}
        )
        return service.get("contacts", {}).get("bao") if service else None

    def insert(self, service: Dict) -> InsertOneResult:
        """Insert a new service"""
        return self.collection.insert_one(service)

    def upsert(self, snow_id: str, service: Dict) -> UpdateResult:
        """Upsert service by ServiceNow ID"""
        return self.collection.update_one(
            {"service_info.service_now_id": snow_id},
            {"$set": service},
            upsert=True
        )

    def get_all(self, limit: int = 100) -> List[Dict]:
        """Get all services with limit"""
        return list(self.collection.find().limit(limit))
