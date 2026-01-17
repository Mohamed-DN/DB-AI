"""
Connection Router - Database terminal connection endpoints (Async with Motor)
"""
import os
import subprocess
from fastapi import APIRouter, HTTPException
from ..services.mongo_service import get_mongo_service
from ..dependencies import validate_identifier, SAFE_IDENTIFIER_RE

router = APIRouter()


@router.post("/action/connect/{db_name:path}")
async def connect_db(db_name: str, mode: str = "sql"):
    """Open a terminal connection to the DB. Mode: 'sql', 'bash', or 'sysdba'. db_name can be CDB or CDB/PDB"""
    try:
        db_name = validate_identifier(db_name, "database")
        if mode not in {"sql", "bash", "sysdba"}:
            raise HTTPException(status_code=400, detail="Invalid connection mode")
        
        mongo = get_mongo_service()
        
        # Handle PDB paths (e.g., "ORCLCDB/ORCLPDB1")
        pdb_name = None
        if "/" in db_name:
            parent_name, pdb_name = db_name.split("/", 1)
            print(f"DEBUG: Connecting to PDB {pdb_name} of {parent_name}")
            db_info = await mongo.get_database(parent_name)
        else:
            print(f"DEBUG: Connecting to DB {db_name}")
            db_info = await mongo.get_database(db_name)

        if not db_info:
            print(f"ERROR: Database not found: {db_name}")
            raise HTTPException(status_code=404, detail=f"Database not found: {db_name}")
        
        container = (
            db_info.get('connection', {}).get('container') or
            db_info.get('identity', {}).get('db_name') or
            db_info.get('identity', {}).get('host') or
            db_info.get('identity', {}).get('db_unique_name', '').lower()
        )
        if not container:
            raise HTTPException(status_code=404, detail="Container name not found for database")
        
        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()
        conn_type = db_info.get('connection', {}).get('type', 'DOCKER')

        if hasattr(conn_type, 'upper') and conn_type.upper() == "REMOTE":
            # Remote Connection (VirtualBox)
            conn = db_info.get('connection', {})
            host = conn.get('host')
            port = conn.get('port', 1521)
            service = conn.get('service_name')
            user = 'c##aiauto'
            password = 'root'
            
            if pdb_name:
                service = pdb_name
                user = 'aiauto'
            
            sqlplus_container = "nexi-oracle-cairo-primary"
            
            if mode == "bash":
                cmd = f'start powershell -NoExit -Command "Write-Host \'Opening shell on Oracle Gateway ({sqlplus_container})...\' -ForegroundColor Cyan; docker exec -it {sqlplus_container} bash"'
            elif mode == "sysdba":
                pdb_label = f" (PDB: {pdb_name})" if pdb_name else ""
                connect_str = f"sys/root@//{host}:{port}/{service} as sysdba"
                cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to Oracle {host}{pdb_label} as SYSDBA...\' -ForegroundColor Yellow; docker exec -it {sqlplus_container} sqlplus {connect_str}"'
            else:
                pdb_label = f" (PDB: {pdb_name})" if pdb_name else ""
                connect_str = f"{user}/{password}@//{host}:{port}/{service}"
                cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to Oracle {host}{pdb_label} as {user} via SQLPlus...\' -ForegroundColor Green; docker exec -it {sqlplus_container} sqlplus {connect_str}"'
            
        else:
            # Docker Container Connection
            db_port = db_info.get('configuration', {}).get('port', 5432)
            
            if mode == "bash":
                cmd = f'start powershell -NoExit -Command "Write-Host \'Opening shell on {container}...\' -ForegroundColor Cyan; docker exec -it {container} /bin/bash"'
            elif mode == "sysdba":
                if engine == 'ORACLE':
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Oracle Console as SYSDBA...\' -ForegroundColor Yellow; docker exec -it {container} sqlplus / as sysdba"'
                else:
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to PostgreSQL ({container}) as POSTGRES (superuser)...\' -ForegroundColor Yellow; docker exec -it {container} psql -U postgres"'
            else:
                if engine == 'ORACLE':
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Oracle Console as SYSDBA (Enforced)...\'-ForegroundColor Yellow; docker exec -it {container} sqlplus / as sysdba"'
                else:
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to PostgreSQL ({container}) as AIAUTO...\' -ForegroundColor Green; docker exec -e PGPASSWORD=root -it {container} psql -U aiauto -d postgres"'
        
        subprocess.Popen(cmd, shell=True)
        return {"status": f"Terminal ({mode}) opened for {container}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
