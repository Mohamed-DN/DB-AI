"""
Distributed Database Tasks
Celery tasks for scalable database operations.
"""
from orchestrator.celery_app import app
from orchestrator.core.mongo_proxy import MongoProxy
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


@app.task(bind=True, name='orchestrator.tasks.collect_metrics')
def collect_database_metrics(self, db_name: str):
    """
    Collect metrics for a single database.
    
    Args:
        db_name: Database unique name
        
    Returns:
        dict: Collected metrics
    """
    try:
        from api_agents.workers.Collector.collector_agent import CollectorAgent
        
        collector = CollectorAgent()
        result = collector.collect_for_database(db_name)
        
        return {
            "status": "success",
            "db_name": db_name,
            "metrics": result
        }
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@app.task(bind=True, name='orchestrator.tasks.discover_databases')
def discover_databases(self):
    """
    Discover all databases in the environment.
    
    Returns:
        dict: Discovery results
    """
    try:
        from api_agents.workers.Scout.scout_agent import ScoutAgent
        
        scout = ScoutAgent()
        discovered = scout.scan_all()
        
        return {
            "status": "success",
            "count": len(discovered),
            "databases": discovered
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@app.task(bind=True, name='orchestrator.tasks.validate_alert')
def validate_alert(self, alert_id: str):
    """
    Validate a CheckMK alert using AI.
    
    Args:
        alert_id: Alert ID
        
    Returns:
        dict: Validation result
    """
    try:
        mongo = MongoProxy()
        alert = mongo.execute_eval(f"db.monitoring_alerts.findOne({{_id: ObjectId('{alert_id}')}})")
        
        if not alert:
            return {"status": "not_found", "alert_id": alert_id}
        
        # TODO: LangGraph validation workflow
        # For now, simple validation
        is_valid = True  # Placeholder
        
        return {
            "status": "validated",
            "alert_id": alert_id,
            "is_valid": is_valid
        }
    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@app.task(name='orchestrator.tasks.batch_collect_metrics')
def batch_collect_metrics(db_names: list):
    """
    Collect metrics for multiple databases in parallel.
    
    Args:
        db_names: List of database names
        
    Returns:
        list: Task IDs
    """
    from celery import group
    
    # Create parallel tasks
    job = group(collect_database_metrics.s(db_name) for db_name in db_names)
    result = job.apply_async()
    
    return {
        "status": "submitted",
        "count": len(db_names),
        "group_id": result.id
    }


@app.task(name='orchestrator.tasks.scheduled_discovery')
def scheduled_discovery():
    """
    Scheduled task: Run discovery every hour.
    """
    return discover_databases.delay().id


@app.task(name='orchestrator.tasks.scheduled_metrics_collection')
def scheduled_metrics_collection():
    """
    Scheduled task: Collect metrics for all databases.
    """
    mongo = MongoProxy()
    dbs = mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
    
    db_names = [db.get('identity', {}).get('db_unique_name') for db in dbs if db.get('identity', {}).get('db_unique_name')]
    
    return batch_collect_metrics.delay(db_names).id
