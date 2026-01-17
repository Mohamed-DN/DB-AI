"""
Initialize MongoDB Tool Registry
Populates 'ai_tools' (dynamic SQL templates) and 'ai_system_tools' (enable/disable flags)
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "Nexi_DB_AI"

async def init_tools():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    print(f"🔌 Connecting to {MONGO_URI} / {DB_NAME}")

    # 1. System Tools Configuration
    # Whitelist of hardcoded python tools that should be enabled
    system_tools = [
        {"name": "search_inventory", "enabled": True, "category": "read"},
        {"name": "get_pdbs_info", "enabled": True, "category": "read"},
        {"name": "manage_container", "enabled": True, "category": "action"}, 
        {"name": "get_container_logs", "enabled": True, "category": "read"},
        {"name": "check_system_health", "enabled": True, "category": "read"},
        {"name": "execute_sql_query", "enabled": True, "category": "action"},
        {"name": "explain_query_plan", "enabled": True, "category": "read"},
        {"name": "get_table_schema", "enabled": True, "category": "read"},
        {"name": "run_agent", "enabled": True, "category": "admin"},
        {"name": "list_agents", "enabled": True, "category": "read"}
    ]
    
    await db['ai_system_tools'].delete_many({})
    await db['ai_system_tools'].insert_many(system_tools)
    print("✅ System tools configuration reset.")

    # 2. Dynamic SQL Tools
    # These are "virtual tools" created from SQL templates
    dynamic_tools = [
        {
            "name": "check_oracle_blocking_sessions",
            "description": "Finds blocking sessions in an Oracle database. Returns the blocker and the waiter.",
            "type": "sql_template",
            "enabled": True,
            "params": {"db_name": "string"}, # target_db context usually required
            "sql": """
                SELECT 
                    s1.username || '@' || s1.machine || ' (SID=' || s1.sid || ' )  is blocking ' || s2.username || '@' || s2.machine || ' (SID=' || s2.sid || ' )' AS blocking_status
                FROM v$lock l1, v$session s1, v$lock l2, v$session s2
                WHERE s1.sid=l1.sid AND s2.sid=l2.sid
                AND l1.BLOCK=1 AND l2.request > 0
                AND l1.id1 = l2.id1 AND l2.id2 = l2.id2
            """
        },
        {
            "name": "check_postgres_long_queries",
            "description": "Finds queries running longer than a specified duration in PostgreSQL.",
            "type": "sql_template",
            "enabled": True,
            "params": {"db_name": "string", "duration_seconds": "string"},
            "sql": "SELECT pid, user, state, query, duration FROM pg_stat_activity WHERE state != 'idle' AND extract(epoch from (now() - query_start)) > {duration_seconds}"
        },
         {
            "name": "get_oracle_tablespace_usage",
            "description": "Check tablespace usage percentage for Oracle DB.",
            "type": "sql_template",
            "enabled": True,
            "params": {"db_name": "string"},
            "sql": """
                SELECT df.tablespace_name "Tablespace",
                totalusedspace "Used MB",
                (df.totalspace - tu.totalusedspace) "Free MB",
                df.totalspace "Total MB",
                round(100 * ( (df.totalspace - tu.totalusedspace)/ df.totalspace)) "Pct. Free"
                FROM
                (SELECT tablespace_name,
                ROUND(SUM(bytes) / 1048576) TotalSpace
                FROM dba_data_files
                GROUP BY tablespace_name) df,
                (SELECT tablespace_name,
                ROUND(SUM(bytes)/(1024*1024)) totalusedspace
                FROM dba_segments
                GROUP BY tablespace_name) tu
                WHERE df.tablespace_name = tu.tablespace_name
            """
        }
    ]

    await db['ai_tools'].delete_many({})
    await db['ai_tools'].insert_many(dynamic_tools)
    print(f"✅ Registered {len(dynamic_tools)} dynamic SQL tools.")

if __name__ == "__main__":
    asyncio.run(init_tools())
