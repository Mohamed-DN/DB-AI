"""
Alerts Router - Alert management endpoints
"""
from fastapi import APIRouter, HTTPException
from ..dependencies import get_mongo

router = APIRouter()


@router.get("/alerts")
def get_alerts():
    """Get recent alerts"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        # Fetch alerts, sort by timestamp desc, limit 50
        alerts = mongo.execute_eval(
            "db.monitoring_alerts.find().sort({timestamp: -1}).limit(50).toArray()"
        ) or []
        
        # Convert _id to string
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/ai")
def get_alerts_with_ai_analysis():
    """Get alerts that have AI analysis attached"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        alerts = mongo.execute_eval(
            "db.monitoring_alerts.find({ai_analysis: {$exists: true}}).sort({timestamp: -1}).limit(20).toArray()"
        ) or []
        
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/clear_alerts")
def clear_alerts():
    """Mark all pending alerts as processed"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        mongo.execute_eval(
            "db.monitoring_alerts.updateMany({processed: false}, {$set: {processed: true}})"
        )
        return {"status": "All Pending Alerts Cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
