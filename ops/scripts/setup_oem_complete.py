"""
Reset SYSTEM password and create SYSMAN via Python
"""
import paramiko
import time
import oracledb

VM = {'host': '127.0.0.1', 'port': 2200}
DSN = "127.0.0.1:2521/FREEPDB1"

print("🔧 Step 1: Reset SYSTEM password via SSH/SYSDBA...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root')

# Write SQL to file and execute
reset_sql = """ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER USER system IDENTIFIED BY root;
DROP USER sysman CASCADE;
CREATE USER sysman IDENTIFIED BY sysman123;
GRANT DBA TO sysman;
EXIT;
"""

# Write to temp file
sftp = ssh.open_sftp()
with sftp.open('/tmp/reset_pwd.sql', 'w') as f:
    f.write(reset_sql)
sftp.close()

# Execute via sqlplus
stdin, stdout, stderr = ssh.exec_command('sqlplus / as sysdba @/tmp/reset_pwd.sql', timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"  SQL output: {'User altered' if 'altered' in out.lower() else 'executed'}")
ssh.close()

time.sleep(2)

print("\n🔧 Step 2: Create OEM tables via Python...")

try:
    conn = oracledb.connect(user="sysman", password="sysman123", dsn=DSN)
    print("✅ SYSMAN connected!")
except Exception as e:
    print(f"❌ SYSMAN failed: {e}")
    print("Trying system...")
    conn = oracledb.connect(user="system", password="root", dsn=DSN)
    print("✅ SYSTEM connected, creating SYSMAN...")
    cur = conn.cursor()
    try:
        cur.execute("DROP USER sysman CASCADE")
    except:
        pass
    cur.execute("CREATE USER sysman IDENTIFIED BY sysman123 DEFAULT TABLESPACE users QUOTA UNLIMITED ON users")
    cur.execute("GRANT DBA TO sysman")
    conn.commit()
    cur.close()
    conn.close()
    conn = oracledb.connect(user="sysman", password="sysman123", dsn=DSN)
    print("✅ SYSMAN connected!")

cursor = conn.cursor()

# Create tables
tables = {
    'mgmt_target': '(target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY, target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256))',
    'mgmt_os_hw_summary': '(host_name VARCHAR2(256) PRIMARY KEY, mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10))',
    'mgmt_metric_current': '(target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP)',
    'mgmt_metric_hourly': '(target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER)',
    'mgmt_metric_daily': '(target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER)'
}

for tbl, cols in tables.items():
    try:
        cursor.execute(f'DROP TABLE {tbl}')
    except:
        pass
    cursor.execute(f'CREATE TABLE {tbl} {cols}')
    cursor.execute(f'CREATE OR REPLACE VIEW "mgmt${tbl.replace("mgmt_","")}" AS SELECT * FROM {tbl}')
    print(f"  ✅ Created {tbl}")

# Insert data
print("\n📊 Inserting sample data...")
data_sql = [
    "INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.nexi.local')",
    "INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.nexi.local')",
    "INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003'), 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.nexi.local')",
    "INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.nexi.local', 65536, 32, 4, 16, 32, 'NO')",
    "INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.nexi.local', 131072, 64, 8, 32, 64, 'NO')",
    "INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.nexi.local', 32768, 16, 2, 8, 16, 'YES')",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'tbspAllocation', 'spaceUsed', 'USERS', '15360', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'tbspAllocation', 'spaceAllocated', 'USERS', '20480', SYSTIMESTAMP)",
    "INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5)",
    "INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512)",
    "INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8)",
    "INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024)",
]

for sql in data_sql:
    cursor.execute(sql)
print(f"  ✅ {len(data_sql)} rows inserted")

# Add daily CPU data
for i in range(1, 8):
    cursor.execute(f"INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - {i}, 35.5, 10, 75)")
    cursor.execute(f"INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - {i}, 55.2, 20, 90)")
print("  ✅ 14 daily CPU metrics inserted")

conn.commit()
cursor.close()
conn.close()

print("\n" + "="*60)
print("🎉 OEM REPOSITORY SIMULATION COMPLETE!")
print("="*60)
