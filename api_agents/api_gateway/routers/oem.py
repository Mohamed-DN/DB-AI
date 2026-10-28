"""
OEM (Oracle Enterprise Manager) Router
API endpoints for OEM database monitoring and metrics.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class OEMInstanceConfig(BaseModel):
    """OEM instance configuration for registration"""
    name: str
    url: str
    username: str
    password: str
    verify_ssl: bool = False


class OEMInstanceResponse(BaseModel):
    """OEM instance response (no password)"""
    name: str
    url: str
    username: str
    is_connected: bool = False
    last_check: Optional[datetime] = None


class OEMDatabaseTarget(BaseModel):
    """Database target from OEM"""
    name: str
    target_type: str
    status: str
    host: Optional[str] = None
    port: Optional[int] = None


class OEMMetricData(BaseModel):
    """Metric data point"""
    metric_name: str
    value: float
    unit: str = ""
    timestamp: datetime


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/oem/instances")
async def get_oem_instances() -> List[OEMInstanceResponse]:
    """
    Get all configured OEM instances.
    Returns list of OEM instances without sensitive data.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        # Get OEM configs from MongoDB
        configs = await db["oem_instances"].find().to_list(100)
        
        instances = []
        for cfg in configs:
            instances.append(OEMInstanceResponse(
                name=cfg.get("name", "Unknown"),
                url=cfg.get("url", ""),
                username=cfg.get("username", ""),
                is_connected=cfg.get("is_connected", False),
                last_check=cfg.get("last_check")
            ))
        
        return instances
        
    except Exception as e:
        print(f"Error fetching OEM instances: {e}")
        # Return empty list if no configs
        return []


@router.post("/oem/instances")
async def add_oem_instance(instance: OEMInstanceConfig) -> Dict[str, Any]:
    """
    Add a new OEM instance configuration.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        # Check if already exists
        existing = await db["oem_instances"].find_one({"url": instance.url})
        if existing:
            raise HTTPException(status_code=400, detail="OEM instance already configured")
        
        # Insert new config
        doc = {
            "name": instance.name,
            "url": instance.url,
            "username": instance.username,
            "password": instance.password,  # TODO: Encrypt in production
            "verify_ssl": instance.verify_ssl,
            "is_connected": False,
            "created_at": datetime.utcnow()
        }
        
        result = await db["oem_instances"].insert_one(doc)
        
        return {
            "status": "success",
            "message": f"OEM instance '{instance.name}' added",
            "id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/oem/instances/{instance_name}")
async def delete_oem_instance(instance_name: str) -> Dict[str, Any]:
    """
    Delete an OEM instance configuration.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        result = await db["oem_instances"].delete_one({"name": instance_name})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="OEM instance not found")
        
        return {"status": "success", "message": f"OEM instance '{instance_name}' deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oem/targets")
async def get_oem_targets() -> List[Dict[str, Any]]:
    """
    Get all database targets discovered by OEM.
    Returns databases from the inventory that have OEM metrics.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        # Get databases with OEM metrics
        filter_query = {"oem_metrics": {"$exists": True}}
        
        databases = await db["databases"].find(filter_query, {
            "identity.db_unique_name": 1,
            "identity.engine": 1,
            "state.status": 1,
            "connection.host": 1,
            "connection.port": 1,
            "oem_metrics": 1,
            "oem_last_collected": 1
        }).to_list(500)
        
        targets = []
        for db_doc in databases:
            identity = db_doc.get("identity", {})
            targets.append({
                "name": identity.get("db_unique_name", "Unknown"),
                "engine": identity.get("engine", "ORACLE"),
                "status": db_doc.get("state", {}).get("status", "UNKNOWN"),
                "host": db_doc.get("connection", {}).get("host"),
                "port": db_doc.get("connection", {}).get("port"),
                "metrics": db_doc.get("oem_metrics", {}),
                "last_collected": db_doc.get("oem_last_collected")
            })
        
        return targets
        
    except Exception as e:
        print(f"Error fetching OEM targets: {e}")
        return []


@router.get("/oem/targets/{target_name}/metrics")
async def get_target_metrics(target_name: str) -> Dict[str, Any]:
    """
    Get detailed metrics for a specific OEM target.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        # Get database from inventory
        database = await db["databases"].find_one({
            "identity.db_unique_name": {"$regex": f"^{target_name}$", "$options": "i"}
        })
        
        if not database:
            raise HTTPException(status_code=404, detail=f"Database '{target_name}' not found")
        
        oem_metrics = database.get("oem_metrics", {})
        
        return {
            "target_name": target_name,
            "last_collected": database.get("oem_last_collected"),
            "metrics": oem_metrics,
            "metric_list": [
                {"name": k, "value": v} for k, v in oem_metrics.items()
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oem/collect")
async def trigger_oem_collection() -> Dict[str, Any]:
    """
    Manually trigger an OEM collection cycle.
    This will fetch latest metrics from all configured OEM instances.
    """
    try:
        from api_agents.workers.oem_collector.oem_collector import OEMCollectorAgent
        from api_agents.shared.sync_mongo_service import SyncMongoService
        
        # Run collection
        mongo = SyncMongoService.get_instance()
        agent = OEMCollectorAgent(mongo_service=mongo)
        
        result = await agent.run_once()
        
        return {
            "status": "success",
            "instances_checked": result.get("instances_checked", 0),
            "metrics_collected": result.get("metrics_collected", 0),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oem/status")
async def get_oem_status() -> Dict[str, Any]:
    """
    Get overall OEM integration status.
    """
    from ..services.mongo_service import get_mongo_service
    
    try:
        mongo = get_mongo_service()
        db = mongo._get_db()
        
        # Count instances
        instance_count = await db["oem_instances"].count_documents({})
        
        # Count targets with OEM data
        target_count = await db["databases"].count_documents({"oem_metrics": {"$exists": True}})
        
        # Get last collection time
        last_db = await db["databases"].find_one(
            {"oem_last_collected": {"$exists": True}},
            sort=[("oem_last_collected", -1)]
        )
        
        last_collection = last_db.get("oem_last_collected") if last_db else None
        
        return {
            "configured_instances": instance_count,
            "monitored_targets": target_count,
            "last_collection": last_collection,
            "status": "active" if instance_count > 0 else "not_configured"
        }
        
    except Exception as e:
        return {
            "configured_instances": 0,
            "monitored_targets": 0,
            "last_collection": None,
            "status": "error",
            "error": str(e)
        }
