"""
Create SYSMAN using Python oracledb directly
=============================================
Uses Python connection which we know works (system/root on FREEPDB1)
"""
import oracledb

DSN = "127.0.0.1:2521/FREEPDB1"

print("🚀 Creating OEM Repository Simulation via Python...")

# Connect as SYS to create user
try:
    conn = oracledb.connect(user="sys", password="root", dsn=DSN, mode=oracledb.SYSDBA)
    print("✅ Connected as SYS/SYSDBA")
except Exception as e:
    print(f"❌ SYS connection failed: {e}")
    print("Trying SYSTEM...")
    conn = oracledb.connect(user="system", password="root", dsn=DSN)
    print("✅ Connected as SYSTEM")

cursor = conn.cursor()

# Drop existing user
print("  🔧 Dropping existing SYSMAN if exists...")
try:
    cursor.execute("DROP USER sysman CASCADE")
    print("  ✅ Dropped old SYSMAN")
except:
    print("  ℹ️ SYSMAN did not exist")

# Create new user
print("  🔧 Creating SYSMAN user...")
cursor.execute("CREATE USER sysman IDENTIFIED BY sysman123 DEFAULT TABLESPACE users QUOTA UNLIMITED ON users")
cursor.execute("GRANT DBA TO sysman")
cursor.execute("GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW TO sysman")
print("  ✅ SYSMAN user created")

cursor.close()
conn.close()

# Now connect as SYSMAN and create tables
print("\n📦 Creating OEM tables...")
conn = oracledb.connect(user="sysman", password="sysman123", dsn=DSN)
print("✅ Connected as SYSMAN")
cursor = conn.cursor()

# Create tables
tables_sql = [
    """CREATE TABLE mgmt_target (
        target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY,
        target_name VARCHAR2(256),
        target_type VARCHAR2(64),
        type_qualifier3 VARCHAR2(64),
        host_name VARCHAR2(256)
    )""",
    """CREATE TABLE mgmt_os_hw_summary (
        host_name VARCHAR2(256) PRIMARY KEY,
        mem NUMBER,
        cpu_count NUMBER,
        physical_cpu_count NUMBER,
        total_cpu_cores NUMBER,
        logical_cpu_count NUMBER,
        virtual VARCHAR2(10)
    )""",
    """CREATE TABLE mgmt_metric_current (
        target_guid RAW(16),
        metric_name VARCHAR2(128),
        metric_column VARCHAR2(128),
        key_value VARCHAR2(256),
        value VARCHAR2(256),
        collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP
    )""",
    """CREATE TABLE mgmt_metric_hourly (
        target_guid RAW(16),
        target_name VARCHAR2(256),
        metric_name VARCHAR2(128),
        metric_column VARCHAR2(128),
        key_value VARCHAR2(256),
        rollup_timestamp TIMESTAMP,
        average NUMBER,
        minimum NUMBER,
        maximum NUMBER
    )""",
    """CREATE TABLE mgmt_metric_daily (
        target_guid RAW(16),
        target_name VARCHAR2(256),
        metric_name VARCHAR2(128),
        metric_column VARCHAR2(128),
        key_value VARCHAR2(256),
        rollup_timestamp TIMESTAMP,
        average NUMBER,
        minimum NUMBER,
        maximum NUMBER
    )"""
]

for sql in tables_sql:
    try:
        cursor.execute(sql)
        table_name = sql.split('TABLE ')[1].split(' ')[0]
        print(f"  ✅ Created table {table_name}")
    except Exception as e:
        if 'ORA-00955' in str(e):  # Already exists
            print(f"  ℹ️ Table already exists")
        else:
            print(f"  ❌ Error: {e}")

# Create views with $
print("\n📊 Creating mgmt$ views...")
views_sql = [
    ('mgmt$target', 'mgmt_target'),
    ('mgmt$os_hw_summary', 'mgmt_os_hw_summary'),
    ('mgmt$metric_current', 'mgmt_metric_current'),
    ('mgmt$metric_hourly', 'mgmt_metric_hourly'),
    ('mgmt$metric_daily', 'mgmt_metric_daily')
]

for view_name, table_name in views_sql:
    try:
        cursor.execute(f'CREATE OR REPLACE VIEW "{view_name}" AS SELECT * FROM {table_name}')
        print(f"  ✅ Created view {view_name}")
    except Exception as e:
        print(f"  ❌ View {view_name}: {e}")

# Insert sample data
print("\n📈 Inserting sample data...")

# Targets
cursor.execute("DELETE FROM mgmt_target")
cursor.execute("INSERT INTO mgmt_target (target_guid, target_name, target_type, type_qualifier3, host_name) VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.nexi.local')")
cursor.execute("INSERT INTO mgmt_target (target_guid, target_name, target_type, type_qualifier3, host_name) VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.nexi.local')")
cursor.execute("INSERT INTO mgmt_target (target_guid, target_name, target_type, type_qualifier3, host_name) VALUES (HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003'), 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.nexi.local')")
print("  ✅ 3 targets inserted")

# Hosts
cursor.execute("DELETE FROM mgmt_os_hw_summary")
cursor.execute("INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.nexi.local', 65536, 32, 4, 16, 32, 'NO')")
cursor.execute("INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.nexi.local', 131072, 64, 8, 32, 64, 'NO')")
cursor.execute("INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.nexi.local', 32768, 16, 2, 8, 16, 'YES')")
print("  ✅ 3 hosts inserted")

# Current metrics
cursor.execute("DELETE FROM mgmt_metric_current")
metrics = [
    ("HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001')", 'memory_usage_sga_pga', 'sga_total', 'NULL', '4096'),
    ("HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001')", 'memory_usage_sga_pga', 'pga_total', 'NULL', '1024'),
    ("HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002')", 'memory_usage_sga_pga', 'sga_total', 'NULL', '8192'),
    ("HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002')", 'memory_usage_sga_pga', 'pga_total', 'NULL', '2048'),
    ("HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001')", 'instance_throughput', 'avg_active_sessions', 'NULL', '45'),
    ("HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002')", 'instance_throughput', 'avg_active_sessions', 'NULL', '82'),
    ("HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001')", 'tbspAllocation', 'spaceUsed', "'USERS'", '15360'),
    ("HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001')", 'tbspAllocation', 'spaceAllocated', "'USERS'", '20480'),
]
for guid, mname, mcol, kv, val in metrics:
    cursor.execute(f"INSERT INTO mgmt_metric_current (target_guid, metric_name, metric_column, key_value, value) VALUES ({guid}, '{mname}', '{mcol}', {kv}, '{val}')")
print("  ✅ 8 current metrics inserted")

# Hourly metrics
cursor.execute("DELETE FROM mgmt_metric_hourly")
cursor.execute("INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5)")
cursor.execute("INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512)")
cursor.execute("INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8)")
cursor.execute("INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024)")
print("  ✅ 4 hourly metrics inserted")

# Daily CPU metrics
cursor.execute("DELETE FROM mgmt_metric_daily")
for i in range(1, 8):
    cursor.execute(f"INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - {i}, 35.5, 10, 75)")
    cursor.execute(f"INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - {i}, 55.2, 20, 90)")
print("  ✅ 14 daily metrics inserted (7 days x 2 DBs)")

conn.commit()
cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ OEM Repository Simulation COMPLETE!")
print("="*60)
print("\n📊 Data Summary:")
print("  - 3 database targets (PRODDB1, PRODDB2, DEVDB1)")
print("  - 3 hosts with hardware info")
print("  - 8 current metrics (SGA, PGA, sessions, tablespace)")
print("  - 4 hourly metrics (DB size)")
print("  - 14 daily metrics (CPU usage)")
print("\n🚀 Test with:")
print("python ops/scripts/oem_repository_collector.py --oem-host 127.0.0.1 --oem-port 2521 --oem-service FREEPDB1 --oem-user sysman --oem-pass sysman123 --once")
