from pymongo import MongoClient
import datetime
import sys

try:
    client = MongoClient('localhost', 28017, username='admin', password='nexi2024')
    db = client.nexi_cmdb_v2
    collection = db.inventory_databases
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# RAC Configuration from User's /etc/hosts
rac1_ip = "192.168.56.101"
rac2_ip = "192.168.56.102"
rac1_vip = "192.168.56.103"
rac2_vip = "192.168.56.104"
service_name = "CDBRAC"

nodes = [
    {
        "name": "CDBRAC_RAC1",
        "host": rac1_ip,
        "hostname": "ol7-19-rac1",
        "vip": rac1_vip
    },
    {
        "name": "CDBRAC_RAC2",
        "host": rac2_ip,
        "hostname": "ol7-19-rac2",
        "vip": rac2_vip
    }
]

print("Configuring Oracle RAC Topology...")

# 1. Update/Insert Nodes
for node in nodes:
    doc = {
        "identity": {
            "db_unique_name": node['name'],
            "db_name": "CDBRAC",
            "sid": node['name'].replace("CDBRAC_", "CDBRAC"), # Usually SID=db_name+inst_num, e.g. CDBRAC1
            "engine": "ORACLE",
            "environment": "PRODUCTION",
            "topology": "RAC",
            "gateway_ref": "gateway-cairo",
            "host": node['host']
        },
        "connection": {
            "type": "REMOTE",
            "host": node['host'],
            "port": 1521,
            "service_name": service_name,
            "user": "system", 
            "password": "root" # Assuming generic pwd
        },
        "database_core": {
            "identity": {
                "db_unique_name": node['name'],
                "instance_name": node['name'].replace("CDBRAC_", "CDBRAC"),
                "is_rac": True,
                "cluster_name": "ol7-19-cluster"
            },
            "network": {
                "public_ip": node['host'],
                "vip_ip": node['vip'],
                "hostname": node['hostname']
            }
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.datetime.now().isoformat()
        }
    }
    
    # Upsert
    result = collection.update_one(
        {"identity.db_unique_name": node['name']},
        {"$set": doc},
        upsert=True
    )
    print(f"✅ Processed {node['name']}: {'Inserted' if result.upserted_id else 'Updated'}")

# 2. Update Cluster Entry (Scan/General access)
cluster_doc = {
    "identity": {
        "db_unique_name": "CDBRAC",
        "db_name": "CDBRAC",
        "engine": "ORACLE",
        "environment": "PRODUCTION",
        "topology": "RAC",
        "gateway_ref": "gateway-cairo",
        "host": rac1_ip # Default to Node 1 IP or SCAN if we had it
    },
    "connection": {
        "type": "REMOTE",
        "host": rac1_ip, 
        "port": 1521,
        "service_name": service_name
    },
    "ha_dr": {
        "cluster_nodes": [
            {"node": "ol7-19-rac1", "ip": rac1_ip, "vip": rac1_vip},
            {"node": "ol7-19-rac2", "ip": rac2_ip, "vip": rac2_vip}
        ],
        "interconnect": [
            {"node": "ol7-19-rac1", "ip": "192.168.1.101"},
            {"node": "ol7-19-rac2", "ip": "192.168.1.102"}
        ]
    }
}

collection.update_one(
    {"identity.db_unique_name": "CDBRAC"},
    {"$set": cluster_doc},
    upsert=True
)
print("✅ Updated Cluster CDBRAC configuration")
