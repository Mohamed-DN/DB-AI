"""
Metrics Router - Database metrics and deep observability endpoints
"""
from fastapi import APIRouter, HTTPException
from ..dependencies import get_mongo, validate_identifier

router = APIRouter()


@router.get("/metrics")
def get_database_metrics():
    """Get aggregated database metrics for the metrics dashboard"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        dbs = mongo.execute_eval("db.inventory_databases.find().toArray()") or []
        
        # Aggregate summary
        summary = {
            "buffer_hit": 0.0,
            "tps": 0,
            "storage_gb": 0,
            "total_connections": 0,
            "avg_query_ms": 0,
            "active_alerts": 0
        }
        
        connections_by_db = []
        pg_databases = []
        oracle_tablespaces = []
        
        buffer_hit_count = 0
        query_ms_count = 0
        total_query_ms = 0
        
        for db in dbs:
            identity = db.get('identity', {})
            db_name = identity.get('db_unique_name', 'UNKNOWN')
            engine = identity.get('engine', 'UNKNOWN').upper()
            state = db.get('state', {})
            metrics = state.get('metrics', {})
            deep = db.get('deep_observability', {})
            
            # Connections
            active = metrics.get('active_connections', 0)
            idle = metrics.get('idle_connections', 0)
            summary["total_connections"] += active + idle
            
            if active > 0 or idle > 0:
                connections_by_db.append({
                    "name": db_name,
                    "active": active,
                    "idle": idle,
                    "engine": engine
                })
            
            # Buffer hit ratio
            if 'buffer_hit_ratio' in metrics:
                summary["buffer_hit"] += float(metrics.get('buffer_hit_ratio', 0))
                buffer_hit_count += 1
            
            # TPS
            summary["tps"] += int(metrics.get('commits_per_sec', 0) or metrics.get('tps', 0))
            
            # Storage
            size_gb = float(metrics.get('db_size_gb', 0) or metrics.get('used_gb', 0))
            summary["storage_gb"] += size_gb
            
            # PostgreSQL specific
            if engine == 'POSTGRES' and size_gb > 0:
                pg_databases.append({
                    "name": db_name,
                    "size_gb": round(size_gb, 2),
                    "connections": active + idle
                })
            
            # Oracle specific - tablespaces
            if engine == 'ORACLE':
                internals = deep.get('oracle_internals', {})
                tbls = internals.get('tablespaces_usage', [])
                for ts in tbls:
                    oracle_tablespaces.append({
                        "name": f"{db_name}:{ts.get('tablespace_name', 'UNKNOWN')}",
                        "used_pct": ts.get('used_pct', 0),
                        "used_gb": ts.get('used_gb', 0),
                        "max_gb": ts.get('max_gb', 0)
                    })
            
            # Query time
            if 'avg_query_time_ms' in metrics:
                total_query_ms += float(metrics.get('avg_query_time_ms', 0))
                query_ms_count += 1
        
        # Calculate averages
        if buffer_hit_count > 0:
            summary["buffer_hit"] = round(summary["buffer_hit"] / buffer_hit_count, 2)
        if query_ms_count > 0:
            summary["avg_query_ms"] = round(total_query_ms / query_ms_count, 2)
        
        summary["storage_gb"] = round(summary["storage_gb"], 2)
        
        # Active alerts
        alerts = mongo.execute_eval("db.monitoring_alerts.find({state: {$in: ['CRITICAL', 'WARNING']}, processed: {$ne: true}}).toArray()") or []
        summary["active_alerts"] = len(alerts)
        
        return {
            "summary": summary,
            "connections_by_db": connections_by_db,
            "pg_databases": pg_databases,
            "oracle_tablespaces": oracle_tablespaces,
            "database_count": len(dbs)
        }
    except Exception as e:
        print(f"Error in get_database_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/deep")
def get_deep_metrics():
    """Get deep dive metrics for advanced dashboard"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        dbs = mongo.execute_eval("db.inventory_databases.find().toArray()") or []
        
        databases = []
        for db in dbs:
            identity = db.get('identity', {})
            db_name = identity.get('db_unique_name', 'UNKNOWN')
            engine = identity.get('engine', 'UNKNOWN').upper()
            state = db.get('state', {})
            status = state.get('status', 'UNKNOWN')
            metrics = state.get('metrics', {})
            deep = db.get('deep_observability', {})
            config = db.get('configuration', {})
            
            # Build database entry
            entry = {
                "name": db_name,
                "engine": engine,
                "status": status,
                "version": config.get('version', 'Unknown'),
                "metrics": {
                    "connections": {
                        "active": metrics.get('active_connections', 0),
                        "idle": metrics.get('idle_connections', 0),
                        "max": metrics.get('max_connections', 0)
                    },
                    "performance": {
                        "buffer_hit_ratio": metrics.get('buffer_hit_ratio', 0),
                        "tps": metrics.get('commits_per_sec', 0) or metrics.get('tps', 0),
                        "avg_query_ms": metrics.get('avg_query_time_ms', 0)
                    },
                    "storage": {
                        "size_gb": metrics.get('db_size_gb', 0) or metrics.get('used_gb', 0),
                        "growth_mb_day": metrics.get('growth_mb_day', 0)
                    }
                },
                "deep_observability": deep
            }
            
            databases.append(entry)
        
        return {
            "databases": databases,
            "count": len(databases)
        }
    except Exception as e:
        print(f"Error in get_deep_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/{db_name}/deep")
def get_deep_observability(db_name: str):
    """Get deep observability data for a specific database"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        db_name = validate_identifier(db_name, "database")
        db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
        
        if not db_info:
            raise HTTPException(status_code=404, detail="Database not found")
        
        deep_obs = db_info.get('deep_observability', {})
        
        return {
            "db_name": db_name,
            "engine": db_info.get('identity', {}).get('engine', 'UNKNOWN'),
            "status": db_info.get('state', {}).get('status', 'UNKNOWN'),
            "deep_observability": deep_obs,
            "has_oracle_internals": 'oracle_internals' in deep_obs,
            "has_pg_internals": 'pg_internals' in deep_obs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
