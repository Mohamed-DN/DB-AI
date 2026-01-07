"""
Script to insert PDBs as separate inventory entries in MongoDB
"""
import sys
import os

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))

from mongo_proxy import MongoProxy

mongo = MongoProxy()

# Get RAC databases with PDBs
print("🔍 Scanning for PDBs in RAC databases...")

rac_dbs = mongo.execute_eval("""
    db.inventory_databases.find({
        'configuration.oracle_specific.pdbs': { $exists: true, $ne: [] }
    }).toArray()
""")

if not rac_dbs:
    print("No RAC databases with PDBs found.")
    exit()

print(f"Found {len(rac_dbs)} databases with PDBs")

for db in rac_dbs:
    cdb_name = db.get('identity', {}).get('db_unique_name')
    conn = db.get('connection', {})
    pdbs = db.get('configuration', {}).get('oracle_specific', {}).get('pdbs', [])
    
    print(f"\n📦 CDB: {cdb_name} has {len(pdbs)} PDBs")
    
    for pdb in pdbs:
        pdb_name = pdb.get('name')
        pdb_status = pdb.get('status', 'UNKNOWN')
        
        # Create unique name for PDB
        pdb_unique_name = f"{cdb_name}/{pdb_name}"
        
        pdb_doc = {
            "identity": {
                "db_unique_name": pdb_unique_name,
                "db_name": pdb_name,
                "engine": "ORACLE",
                "environment": db.get('identity', {}).get('environment', 'DEV'),
                "topology": "PDB",
                "parent_cdb": cdb_name,
                "host": conn.get('host', 'N/A'),
                "port": conn.get('port', 1521)
            },
            "connection": {
                "type": "REMOTE",
                "host": conn.get('host'),
                "port": conn.get('port', 1521),
                "service_name": pdb_name,  # PDB name as service
                "user": conn.get('user', 'sys'),
                "password": conn.get('password')
            },
            "state": {
                "status": "UP" if pdb_status in ['NORMAL', 'READ WRITE'] else 'UNKNOWN'
            },
            "configuration": {
                "version": db.get('configuration', {}).get('version', 'Unknown'),
                "port": conn.get('port', 1521)
            }
        }
        
        # Upsert PDB
        result = mongo.upsert_database(pdb_doc)
        print(f"   ✅ Created/Updated PDB: {pdb_unique_name} (Status: {pdb_status})")

print("\n✅ PDB Inventory Sync Complete!")
