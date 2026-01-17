"""
Tasks Router - Celery task management endpoints
"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from orchestrator.celery_app import app as celery_app
from orchestrator.tasks import (
    collect_database_metrics,
    discover_databases,
    batch_collect_metrics,
    scheduled_metrics_collection
)

router = APIRouter()


@router.post("/tasks/collect/{db_name}")
async def trigger_metrics_collection(db_name: str):
    """Trigger metrics collection for a specific database"""
    task = collect_database_metrics.delay(db_name)
    return {
        "task_id": task.id,
        "status": "submitted",
        "db_name": db_name
    }


@router.post("/tasks/collect-all")
async def trigger_all_metrics_collection():
    """Trigger metrics collection for all databases"""
    task = scheduled_metrics_collection.delay()
    return {
        "task_id": task.id,
        "status": "submitted",
        "message": "Batch collection started"
    }


@router.post("/tasks/discover")
async def trigger_discovery():
    """Trigger database discovery"""
    task = discover_databases.delay()
    return {
        "task_id": task.id,
        "status": "submitted"
    }


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a Celery task"""
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state == 'PENDING':
        response = {
            "task_id": task_id,
            "state": task.state,
            "status": "Task is waiting in queue"
        }
    elif task.state == 'STARTED':
        response = {
            "task_id": task_id,
            "state": task.state,
            "status": "Task is running"
        }
    elif task.state == 'SUCCESS':
        response = {
            "task_id": task_id,
            "state": task.state,
            "result": task.result
        }
    elif task.state == 'FAILURE':
        response = {
            "task_id": task_id,
            "state": task.state,
            "error": str(task.info)
        }
    else:
        response = {
            "task_id": task_id,
            "state": task.state
        }
    
    return response


@router.get("/tasks/stats")
async def get_celery_stats():
    """Get Celery worker statistics"""
    try:
        inspect = celery_app.control.inspect()
        
        stats = {
            "active": inspect.active(),
            "scheduled": inspect.scheduled(),
            "reserved": inspect.reserved(),
            "stats": inspect.stats()
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve stats: {str(e)}")


@router.get("/tasks/queues")
async def get_queue_lengths():
    """Get queue lengths"""
    from celery import current_app
    
    try:
        with current_app.connection_or_acquire() as conn:
            queues = ['default', 'metrics', 'alerts', 'discovery']
            lengths = {}
            
            for queue_name in queues:
                try:
                    queue = conn.SimpleQueue(queue_name)
                    lengths[queue_name] = queue.qsize()
                    queue.close()
                except:
                    lengths[queue_name] = -1
            
            return lengths
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
