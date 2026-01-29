"""
Inventory Router - Database inventory and storage endpoints (Async with Motor)
"""
from fastapi import APIRouter, HTTPException
from ..services.mongo_service import get_mongo_service
from ..dependencies import validate_identifier

router = APIRouter()


@router.get("/inventory")
async def get_inventory(skip: int = 0, limit: int = 1000, search: str = None, starts_with: str = None, filter_by: str = "name"):
    """Get paginated databases enriched with Business Service info"""
    try:
        mongo = get_mongo_service()
        
        # 1. Fetch Inventory (paginated)
        result = await mongo.get_inventory(skip=skip, limit=limit, search=search, starts_with=starts_with, filter_by=filter_by)
        dbs = result["items"]
        
        # 2. Fetch Business Services
        services = await mongo.get_business_services()
        
        # 3. Create Lookup Map (DB Name -> Service Info)
        service_map = {}
        default_svc = None
        for svc in services:
            svc_info_obj = svc.get('service_info', svc)
            service_entry = {
                "name": svc_info_obj.get("name"),
                "snow_group": svc_info_obj.get("snow_group"),
                "reperibility": svc.get("contacts", {}).get("reperibilita_number"),
                "contacts": svc.get("contacts")
            }
            
            mappings = svc.get('technical_mapping', [])
            if isinstance(mappings, dict):
                mappings = [mappings]
            
            for mapping in mappings:
                if isinstance(mapping, dict):
                    db_name = mapping.get('db_unique_name')
                    if db_name == "ALL":
                        default_svc = service_entry
                    elif db_name:
                        service_map[db_name.upper()] = service_entry
                elif isinstance(mapping, str):
                    if mapping == "ALL":
                        default_svc = service_entry
                    else:
                        service_map[mapping.upper()] = service_entry
        
        # 4. Normalize and Enrich DB objects
        for db in dbs:
            # Identity Normalization
            if 'identity' not in db:
                if 'cluster_identity' in db:
                    db['identity'] = db['cluster_identity']
                    if 'engine' not in db['identity']:
                        db['identity']['engine'] = 'POSTGRES'
                    if 'topology' not in db['identity']:
                        db['identity']['topology'] = 'CLUSTER'
                elif 'database_core' in db and 'identity' in db['database_core']:
                    db['identity'] = db['database_core']['identity']
                    if 'engine' not in db['identity']:
                        db['identity']['engine'] = 'ORACLE'
                    if 'topology' not in db['identity']:
                        db['identity']['topology'] = 'RAC' if db['identity'].get('is_rac') else 'SINGLE'
            
            # Connection Normalization
            if 'connection' not in db:
                if 'instance_details' in db:
                    db['connection'] = {
                        'host': db['instance_details'].get('inet_server_addr'),
                        'port': db['instance_details'].get('inet_server_port')
                    }
            
            # State/Status Normalization
            if 'state' not in db:
                db['state'] = {'status': 'UNKNOWN'}
            
            # Configuration Normalization
            if 'configuration' not in db:
                db['configuration'] = {}
            
            if 'version' not in db['configuration']:
                if 'database_core' in db and 'version_info' in db['database_core']:
                    db['configuration']['version'] = db['database_core']['version_info'].get('full_version')
                elif 'cluster_identity' in db:
                    db['configuration']['version'] = db['cluster_identity'].get('version_full')
            
            # Ensure minimal required fields
            if 'identity' not in db:
                db['identity'] = {'db_unique_name': 'UNKNOWN_DB', 'engine': 'UNKNOWN'}
            
            db_name = db.get('identity', {}).get('db_unique_name', '').upper()
            
            # Business Service Enrichment
            svc_info = service_map.get(db_name)
            if not svc_info and default_svc:
                svc_info = default_svc
            if svc_info:
                db['business_service'] = svc_info
        
        return {
            "items": dbs,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"]
        }
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def get_all_storage():
    """Get all storage inventory items"""
    try:
        mongo = get_mongo_service()
        return await mongo.get_all_storage()
    except Exception as e:
        print(f"Error fetching storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage/{db_name}")
async def get_storage_for_db(db_name: str):
    """Get storage inventory for a specific database"""
    try:
        mongo = get_mongo_service()
        db_name = validate_identifier(db_name, "database")
        storage = await mongo.get_storage_for_db(db_name)
        
        if not storage:
            raise HTTPException(status_code=404, detail=f"No storage found for {db_name}")
        return storage
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching storage for {db_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raw/{collection_name}")
async def get_raw_collection(collection_name: str):
    """Get raw collection data for Explorer"""
    try:
        mongo = get_mongo_service()
        return await mongo.get_raw_collection(collection_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error fetching raw collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/inventory/{db_name}")
async def delete_database(db_name: str):
    """Delete a database from inventory (does not stop container)"""
    try:
        mongo = get_mongo_service()
        
        # Check if exists
        exists = await mongo.get_database(db_name)
        if not exists:
            raise HTTPException(status_code=404, detail="Database not found")
        
        # Delete
        await mongo.delete_database(db_name)
        return {"status": f"Database {db_name} removed from inventory"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
