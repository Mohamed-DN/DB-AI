"""
MongoDB Connection Helper for CMDB
"""
import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_client() -> MongoClient:
    """Get MongoDB client (singleton)"""
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)
    return _client


def get_database() -> Database:
    """Get MongoDB database"""
    global _db
    if _db is None:
        db_name = os.getenv("MONGO_DB", "nexi_cmdb")
        _db = get_client()[db_name]
    return _db


def close_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


# Collection names
COLLECTIONS = {
    "inventory_databases": "inventory_databases",
    "business_services": "business_services",
    "gateways": "gateways",
    "discovery_queue": "discovery_queue",
    "agent_runs": "agent_runs",
    "rag_knowledge_base": "rag_knowledge_base",
    "monitoring_alerts": "monitoring_alerts",
    "baselines": "baselines",
    "compliance_reports": "compliance_reports",
}


def get_collection(name: str):
    """Get a collection by name"""
    if name not in COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}")
    return get_database()[COLLECTIONS[name]]
