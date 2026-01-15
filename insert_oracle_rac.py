"""Insert Oracle RAC nodes and PDBs into MongoDB inventory"""
from pymongo import MongoClient
from datetime import datetime

c = MongoClient('localhost', 28017, username='admin', password='nexi2024')
db = c['nexi_cmdb_v2']

# First, clear any old Oracle entries
db.inventory_databases.delete_many({"identity.family": "ORACLE"})
print("Cleared old Oracle entries")

# RAC Node 1
rac1 = {
    "metadata": {
        "extraction_timestamp": datetime.now().isoformat(),
        "agent_version": "2.0.0",
        "db_technology": "ORACLE",
        "environment": "LAB"
    },
    "infrastructure": {
        "host": {
            "alias": "ol7-19-rac1",
            "ip_address": "192.168.56.101",
            "vip": "192.168.56.103",
            "os": "Oracle Linux 7"
        }
    },
    "database_core": {
        "identity": {
            "db_name": "cdbrac",
            "db_unique_name": "cdbrac",
            "instance_name": "cdbrac1"
        },
        "version_info": {
            "full_version": "19.0.0.0.0"
        },
        "configuration": {
            "type": "CDB"
        }
    },
    "ha_dr": {
        "cluster_type": "RAC",
        "cluster_nodes": [
            {"instance": "cdbrac1", "node": "ol7-19-rac1", "status": "OPEN"},
            {"instance": "cdbrac2", "node": "ol7-19-rac2", "status": "OPEN"}
        ]
    },
    "identity": {
        "db_unique_name": "CDBRAC_RAC1",
        "db_name": "cdbrac",
        "family": "ORACLE",
        "engine": "ORACLE",
        "role": "PRIMARY",
        "environment": "LAB",
        "host": "192.168.56.101"
    },
    "connection": {
        "port": 1521,
        "service_name": "cdbrac",
        "type": "RAC"
    },
    "state": {
        "status": "UP",
        "last_seen": datetime.now().isoformat()
    },
    "created_at": datetime.now()
}

# RAC Node 2
rac2 = {
    "metadata": {
        "extraction_timestamp": datetime.now().isoformat(),
        "agent_version": "2.0.0",
        "db_technology": "ORACLE",
        "environment": "LAB"
    },
    "infrastructure": {
        "host": {
            "alias": "ol7-19-rac2",
            "ip_address": "192.168.56.102",
            "vip": "192.168.56.104",
            "os": "Oracle Linux 7"
        }
    },
    "database_core": {
        "identity": {
            "db_name": "cdbrac",
            "db_unique_name": "cdbrac",
            "instance_name": "cdbrac2"
        },
        "version_info": {
            "full_version": "19.0.0.0.0"
        },
        "configuration": {
            "type": "CDB"
        }
    },
    "ha_dr": {
        "cluster_type": "RAC",
        "cluster_nodes": [
            {"instance": "cdbrac1", "node": "ol7-19-rac1", "status": "OPEN"},
            {"instance": "cdbrac2", "node": "ol7-19-rac2", "status": "OPEN"}
        ]
    },
    "identity": {
        "db_unique_name": "CDBRAC_RAC2",
        "db_name": "cdbrac",
        "family": "ORACLE",
        "engine": "ORACLE",
        "role": "PRIMARY",
        "environment": "LAB",
        "host": "192.168.56.102"
    },
    "connection": {
        "port": 1521,
        "service_name": "cdbrac",
        "type": "RAC"
    },
    "state": {
        "status": "UP",
        "last_seen": datetime.now().isoformat()
    },
    "created_at": datetime.now()
}

# PDBs
pdbs = [
    {
        "name": "pdb1",
        "unique_name": "PDB1_CDBRAC"
    },
    {
        "name": "luna",
        "unique_name": "LUNA_CDBRAC"
    },
    {
        "name": "sole",
        "unique_name": "SOLE_CDBRAC"
    }
]

pdb_docs = []
for pdb in pdbs:
    pdb_doc = {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": "ORACLE",
            "environment": "LAB"
        },
        "database_core": {
            "identity": {
                "pdb_name": pdb["name"],
                "parent_cdb": "cdbrac"
            },
            "configuration": {
                "type": "PDB"
            }
        },
        "identity": {
            "db_unique_name": pdb["unique_name"],
            "db_name": pdb["name"],
            "family": "ORACLE",
            "engine": "ORACLE",
            "role": "PDB",
            "environment": "LAB",
            "host": "192.168.56.101"
        },
        "connection": {
            "port": 1521,
            "service_name": pdb["name"],
            "type": "PDB"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        },
        "created_at": datetime.now()
    }
    pdb_docs.append(pdb_doc)

# Insert all
result = db.inventory_databases.insert_one(rac1)
print(f"Inserted RAC1: {result.inserted_id}")

result = db.inventory_databases.insert_one(rac2)
print(f"Inserted RAC2: {result.inserted_id}")

for doc in pdb_docs:
    result = db.inventory_databases.insert_one(doc)
    print(f"Inserted PDB {doc['identity']['db_name']}: {result.inserted_id}")

print(f"\nTotal Oracle entries: {db.inventory_databases.count_documents({'identity.family': 'ORACLE'})}")
