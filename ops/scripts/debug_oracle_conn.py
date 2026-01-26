"""
Oracle Connection Diagnostic Tool
=================================
Tests connection and permissions for specific monitoring queries.
"""
import sys
import time
import re

try:
    import oracledb
except ImportError:
    print("❌ oracledb not installed. Run: pip install oracledb")
    sys.exit(1)

# Configuration for VM1
CONFIG = {
    "host": "127.0.0.1",
    "port": 2521,
    "sid": "ORCL",
    "service_name": "",
    "user": "system",
    "password": "root"
}

# Queries to test
QUERIES = {
    "Basic Connection": "SELECT 1 FROM DUAL",
    "Instance Status": "SELECT INSTANCE_NAME, STATUS FROM V$INSTANCE",
    "Database Info": "SELECT NAME, OPEN_MODE FROM V$DATABASE",
    "Tablespace": "SELECT tablespace_name FROM dba_data_files FETCH FIRST 1 ROWS ONLY",
    "Sessions": "SELECT COUNT(*) FROM V$SESSION",
    "System Waits": "SELECT COUNT(*) FROM V$SYSTEM_WAIT_CLASS",
    "SGA Stats": "SELECT COUNT(*) FROM V$SGASTAT",
    "PGA Stats": "SELECT COUNT(*) FROM V$PGASTAT",
    "Sys Stats": "SELECT COUNT(*) FROM V$SYSSTAT"
}

def main():
    dsn = f"{CONFIG['host']}:{CONFIG['port']}/{CONFIG['sid']}"
    print(f"🔌 Connecting to {dsn} as {CONFIG['user']}...")
    
    try:
        conn = oracledb.connect(
            user=CONFIG['user'],
            password=CONFIG['password'],
            dsn=dsn
        )
        print("✅ Connection Established!")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    print("\n🔍 Testing Permissions on Views:")
    print("-" * 40)
    
    cursor = conn.cursor()
    success_count = 0
    
    for name, query in QUERIES.items():
        print(f"Testing {name}...", end=" ")
        try:
            cursor.execute(query)
            cursor.fetchone()
            print("✅ OK")
            success_count += 1
        except Exception as e:
            print(f"❌ FAILED")
            print(f"  Error: {e}")
    
    cursor.close()
    conn.close()
    
    print("-" * 40)
    print(f"Summary: {success_count}/{len(QUERIES)} checks passed.")

if __name__ == "__main__":
    main()
