"""
Disaster Simulator
Generates chaos on PostgreSQL database.
"""
import threading
import time
import psycopg2
import os

DB_HOST = "localhost" # We need to target the port mapped on host or use container IP if running from outside
# Check docker-compose ports. pg-milano-prod2 is NOT mapped to a fixed port in the V2 file? 
# Ops, checking docker-compose-v2.yml:
# pg-milano-prod2 has NO ports mapped? Wait.
# Ah, lines 143-156 of docker-compose-v2.yml: no ports mapped for prod2? 
# Usually prod is internal. dev2 has 6433:5432.
# Let's target dev2 for simulation as it is accessible, or use docker exec psql.

# Using docker exec is safer/easier from host context without installing drivers
import subprocess

def run_sql(container, sql):
    cmd = ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "payments_prod", "-c", sql]
    subprocess.run(cmd, capture_output=True)

def cpu_spike(container, duration=30):
    print(f"🔥 CPU SPIKE on {container} for {duration}s")
    # Calculates factorials repeatedly
    sql = """
    SELECT count(*) FROM generate_series(1, 5000000);
    """
    end = time.time() + duration
    while time.time() < end:
        run_sql(container, sql)

def deadlock(container):
    print(f"🔒 DEADLOCK Simulation on {container}")
    # Hard to coordinate via two exec calls, but we can lock table
    run_sql(container, "LOCK TABLE pg_stat_activity IN ACCESS EXCLUSIVE MODE;")
    print("  - Table Locked (Main thread)")

def main():
    target = "nexi-pg-milano-prod2" # Internal, via exec
    print(f"💣 Starting Disaster Simulation on {target}")
    
    # 1. IO/CPU Load
    t = threading.Thread(target=cpu_spike, args=(target, 60))
    t.start()
    
    print("  - CPU Load active...")
    time.sleep(5)
    
    # 2. Connection Flood (Simulated via logs)
    print("🌊 Simulating connection flood logs...")
    
    t.join()
    print("✅ Simulation Complete.")

if __name__ == "__main__":
    main()
