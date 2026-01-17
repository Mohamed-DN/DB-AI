"""
Alerts Router - Alert management endpoints (Async with Motor)
"""
from fastapi import APIRouter, HTTPException
from ..services.mongo_service import get_mongo_service

router = APIRouter()


@router.get("/alerts")
async def get_alerts():
    """Get recent alerts"""
    try:
        mongo = get_mongo_service()
        return await mongo.get_alerts(limit=50)
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/ai")
async def get_alerts_with_ai_analysis():
    """Get alerts that have AI analysis attached"""
    try:
        mongo = get_mongo_service()
        return await mongo.get_alerts_with_ai_analysis(limit=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/clear_alerts")
async def clear_alerts():
    """Mark all pending alerts as processed"""
    try:
        mongo = get_mongo_service()
        count = await mongo.clear_alerts()
        return {"status": "All Pending Alerts Cleared", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
