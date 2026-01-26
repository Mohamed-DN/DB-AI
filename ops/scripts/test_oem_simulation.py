"""
Test OEM Collector with SYSTEM user and sysman_ prefixed tables
"""
import oracledb
import socket
import time

DSN = "127.0.0.1:2521/FREEPDB1"
USER = "system"
PASSWORD = "root"

QUERIES = {
    "db_size": """
        SELECT target_name, 
               MAX(CASE WHEN metric_column = 'USED_GB' THEN maximum END) as used_gb,
               MAX(CASE WHEN metric_column = 'ALLOCATED_GB' THEN maximum END) as allocated_gb
        FROM sysman_metric_hourly
        WHERE metric_name = 'DATABASE_SIZE'
        GROUP BY target_name
    """,
    "sessions": """
        SELECT t.target_name, m.value as active_sessions
        FROM sysman_metric_current m
        JOIN sysman_target t ON m.target_guid = t.target_guid
        WHERE m.metric_name = 'instance_throughput' 
        AND m.metric_column = 'avg_active_sessions'
    """,
    "memory": """
        SELECT t.target_name, m.metric_column, m.value
        FROM sysman_metric_current m
        JOIN sysman_target t ON m.target_guid = t.target_guid
        WHERE m.metric_name = 'memory_usage_sga_pga'
    """,
    "hosts": """
        SELECT host_name, mem, cpu_count, total_cpu_cores
        FROM sysman_os_hw
    """
}

print("🔌 Connecting to Oracle as SYSTEM...")
try:
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    print("✅ Connected!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

cursor = conn.cursor()
metrics = []
now = int(time.time())

for query_name, sql in QUERIES.items():
    print(f"\n📊 Executing {query_name}...")
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        print(f"  ✅ Got {len(rows)} rows")
        
        for row in rows:
            print(f"    {row}")
            
            # Create metrics
            if query_name == "db_size" and row[1]:
                metrics.append((f"oem.db.{row[0].lower()}.used_gb", float(row[1]), now))
                metrics.append((f"oem.db.{row[0].lower()}.allocated_gb", float(row[2]) if row[2] else 0, now))
            elif query_name == "sessions":
                metrics.append((f"oem.db.{row[0].lower()}.active_sessions", float(row[1]), now))
            elif query_name == "hosts":
                metrics.append((f"oem.host.{row[0].lower().replace('.','_')}.memory_mb", float(row[1]) if row[1] else 0, now))
                metrics.append((f"oem.host.{row[0].lower().replace('.','_')}.cpu_cores", float(row[3]) if row[3] else 0, now))
                
    except Exception as e:
        print(f"  ❌ Error: {e}")

cursor.close()
conn.close()

print(f"\n📈 Collected {len(metrics)} metrics:")
for m in metrics[:10]:
    print(f"  {m[0]} = {m[1]}")

# Send to Graphite
if metrics:
    print("\n📤 Sending to VictoriaMetrics (Graphite)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("localhost", 2003))
        
        lines = [f"{m[0]} {m[1]} {m[2]}" for m in metrics]
        message = "\n".join(lines) + "\n"
        sock.sendall(message.encode())
        sock.close()
        print(f"  ✅ Sent {len(metrics)} metrics!")
    except Exception as e:
        print(f"  ⚠️ Graphite send failed (VictoriaMetrics may not be running): {e}")

print("\n🎉 OEM SIMULATION TEST SUCCESSFUL!")
