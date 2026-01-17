"""
Services Package - Business logic layer
"""
from .mongo_service import MongoService, get_mongo_service

__all__ = ["MongoService", "get_mongo_service"]
