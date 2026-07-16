"""
MongoDB Schema and Index Management for M-DN DBA AI
Optimized for 3000+ database scale in banking environment.

Run this script to initialize/update MongoDB schema validation and indexes.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://admin:pippopippo_1234@localhost:28017")
DB_NAME = os.getenv("MONGODB_DB", "m-dn_cmdb_v2")


# =============================================================================
# SCHEMA DEFINITIONS - Optimized for 3000+ databases
# =============================================================================

INVENTORY_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["identity", "state"],
        "properties": {
            "identity": {
                "bsonType": "object",
                "required": ["db_unique_name", "engine"],
                "properties": {
                    "db_unique_name": {
                        "bsonType": "string",
                        "description": "Unique identifier for the database"
                    },
                    "engine": {
                        "enum": ["POSTGRES", "ORACLE", "MYSQL", "SQLSERVER", "MONGODB"],
                        "description": "Database engine type"
                    },
                    "version": {"bsonType": "string"},
                    "host": {"bsonType": "string"},
                    "port": {"bsonType": "int"},
                    "gateway": {"bsonType": "string"},
                    "datacenter": {"bsonType": "string"},
                    "environment": {
                        "enum": ["PROD", "STAGING", "DEV", "TEST", "DR"],
                        "description": "Environment type"
                    }
                }
            },
            "state": {
                "bsonType": "object",
                "properties": {
                    "status": {
                        "enum": ["UP", "DOWN", "UNKNOWN", "MAINTENANCE", "DEGRADED"],
                        "description": "Current status"
                    },
                    "last_check": {"bsonType": "date"},
                    "metrics": {"bsonType": "object"}
                }
            },
            "configuration": {"bsonType": "object"},
            "topology": {"bsonType": "object"},
            "deep_observability": {"bsonType": "object"},
            "credentials_ref": {
                "bsonType": "string",
                "description": "Reference to encrypted credentials (vault key)"
            },
            "owner": {"bsonType": "string"},
            "tags": {
                "bsonType": "array",
                "items": {"bsonType": "string"}
            },
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"}
        }
    }
}

ALERTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["alert_id", "severity", "db_name", "created_at"],
        "properties": {
            "alert_id": {"bsonType": "string"},
            "severity": {
                "enum": ["CRITICAL", "WARNING", "INFO"],
                "description": "Alert severity level"
            },
            "db_name": {"bsonType": "string"},
            "message": {"bsonType": "string"},
            "details": {"bsonType": "object"},
            "status": {
                "enum": ["PENDING", "ACKNOWLEDGED", "RESOLVED", "EXPIRED"],
                "description": "Alert status"
            },
            "acknowledged_by": {"bsonType": "string"},
            "resolved_at": {"bsonType": "date"},
            "created_at": {"bsonType": "date"},
            "expires_at": {"bsonType": "date"}
        }
    }
}

USERS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["username", "password_hash", "role"],
        "properties": {
            "username": {
                "bsonType": "string",
                "minLength": 3,
                "maxLength": 50
            },
            "email": {"bsonType": "string"},
            "full_name": {"bsonType": "string"},
            "password_hash": {"bsonType": "string"},
            "role": {
                "enum": ["admin", "operator", "viewer"],
                "description": "User role for RBAC"
            },
            "databases_scope": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "List of databases user can access (* = all)"
            },
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "last_login": {"bsonType": "date"}
        }
    }
}


# =============================================================================
# INDEX DEFINITIONS - Critical for 3000+ database performance
# =============================================================================

INVENTORY_INDEXES = [
    # Primary lookup - UNIQUE
    {
        "keys": [("identity.db_unique_name", 1)],
        "options": {"unique": True, "name": "idx_db_unique_name"}
    },
    # Engine filter - common query
    {
        "keys": [("identity.engine", 1)],
        "options": {"name": "idx_engine"}
    },
    # Status filter - for monitoring dashboards
    {
        "keys": [("state.status", 1)],
        "options": {"name": "idx_status"}
    },
    # Environment filter
    {
        "keys": [("identity.environment", 1)],
        "options": {"name": "idx_environment"}
    },
    # Datacenter + Status compound (common query)
    {
        "keys": [("identity.datacenter", 1), ("state.status", 1)],
        "options": {"name": "idx_datacenter_status"}
    },
    # Gateway filter
    {
        "keys": [("identity.gateway", 1)],
        "options": {"name": "idx_gateway"}
    },
    # Last check time (for stale detection)
    {
        "keys": [("state.last_check", -1)],
        "options": {"name": "idx_last_check"}
    },
    # Tags (for flexible querying)
    {
        "keys": [("tags", 1)],
        "options": {"name": "idx_tags"}
    },
    # Text search on db_unique_name
    {
        "keys": [("identity.db_unique_name", "text")],
        "options": {"name": "idx_db_name_text"}
    }
]

ALERTS_INDEXES = [
    # Primary lookup
    {
        "keys": [("alert_id", 1)],
        "options": {"unique": True, "name": "idx_alert_id"}
    },
    # Status filter - most common query
    {
        "keys": [("status", 1)],
        "options": {"name": "idx_alert_status"}
    },
    # Severity + Status compound
    {
        "keys": [("severity", 1), ("status", 1)],
        "options": {"name": "idx_severity_status"}
    },
    # Database lookup
    {
        "keys": [("db_name", 1), ("status", 1)],
        "options": {"name": "idx_db_alert_status"}
    },
    # Creation time (for pagination)
    {
        "keys": [("created_at", -1)],
        "options": {"name": "idx_created_at"}
    },
    # TTL index - auto-expire resolved alerts after 30 days
    {
        "keys": [("resolved_at", 1)],
        "options": {"name": "idx_ttl_resolved", "expireAfterSeconds": 2592000}  # 30 days
    }
]

USERS_INDEXES = [
    # Primary lookup - UNIQUE
    {
        "keys": [("username", 1)],
        "options": {"unique": True, "name": "idx_username"}
    },
    # Email lookup - UNIQUE (sparse for null emails)
    {
        "keys": [("email", 1)],
        "options": {"unique": True, "sparse": True, "name": "idx_email"}
    },
    # Role filter
    {
        "keys": [("role", 1)],
        "options": {"name": "idx_role"}
    }
]


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

async def apply_schema_validation(db, collection_name: str, schema: dict):
    """Apply JSON schema validation to a collection"""
    try:
        # Check if collection exists
        collections = await db.list_collection_names()
        
        if collection_name in collections:
            # Modify existing collection
            await db.command({
                "collMod": collection_name,
                "validator": schema,
                "validationLevel": "moderate",  # Allow existing docs that don't match
                "validationAction": "warn"  # Warn on validation failure, don't reject
            })
            print(f"  ✅ Updated schema validation for '{collection_name}'")
        else:
            # Create new collection with validation
            await db.create_collection(
                collection_name,
                validator=schema,
                validationLevel="moderate",
                validationAction="warn"
            )
            print(f"  ✅ Created collection '{collection_name}' with schema validation")
            
    except Exception as e:
        print(f"  ⚠️ Schema validation for '{collection_name}': {e}")


async def create_indexes(db, collection_name: str, indexes: list):
    """Create indexes for a collection"""
    collection = db[collection_name]
    
    for idx in indexes:
        try:
            await collection.create_index(idx["keys"], **idx["options"])
            print(f"  ✅ Index '{idx['options']['name']}' on '{collection_name}'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ℹ️ Index '{idx['options']['name']}' already exists")
            else:
                print(f"  ⚠️ Index '{idx['options']['name']}': {e}")


async def run_migration():
    """Run full schema and index migration"""
    print("=" * 60)
    print("🏦 M-DN DBA AI - MongoDB Schema Migration")
    print(f"📅 {datetime.now().isoformat()}")
    print(f"🎯 Target: {DB_NAME}")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("\n✅ Connected to MongoDB\n")
        
        # Apply schemas
        print("📋 Applying Schema Validation...")
        await apply_schema_validation(db, "inventory_databases", INVENTORY_SCHEMA)
        await apply_schema_validation(db, "monitoring_alerts", ALERTS_SCHEMA)
        await apply_schema_validation(db, "users", USERS_SCHEMA)
        
        # Create indexes
        print("\n📊 Creating Performance Indexes...")
        await create_indexes(db, "inventory_databases", INVENTORY_INDEXES)
        await create_indexes(db, "monitoring_alerts", ALERTS_INDEXES)
        await create_indexes(db, "users", USERS_INDEXES)
        
        # Print stats
        print("\n📈 Collection Statistics:")
        for coll in ["inventory_databases", "monitoring_alerts", "users"]:
            count = await db[coll].count_documents({})
            print(f"  • {coll}: {count} documents")
        
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
