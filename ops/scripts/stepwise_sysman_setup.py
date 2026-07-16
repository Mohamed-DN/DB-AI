"""
Step by step SYSMAN setup with verification
"""
import paramiko
import time

VM = {'host': '127.0.0.1', 'port': 2200}

print("🔧 Step-by-step SYSMAN creation...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root')

def run_sql(sql, desc):
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/step.sql', 'w') as f:
        f.write(sql)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('sqlplus / as sysdba @/tmp/step.sql', timeout=60)
    out = stdout.read().decode('utf-8', errors='ignore')
    
    success = 'error' not in out.lower() or 'ORA-01918' in out  # User doesn't exist is OK for drop
    print(f"  {desc}: {'✅' if success else '❌'}")
    if 'ORA-' in out and 'ORA-01918' not in out and 'ORA-01920' not in out:
        for line in out.split('\n'):
            if 'ORA-' in line:
                print(f"    {line[:60]}")
    return out

# Step 1: Switch container and reset SYSTEM
run_sql("""
ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER USER system IDENTIFIED BY root;
EXIT;
""", "Reset SYSTEM password")

# Step 2: Drop SYSMAN
run_sql("""
ALTER SESSION SET CONTAINER=FREEPDB1;
DROP USER sysman CASCADE;
EXIT;
""", "Drop old SYSMAN")

# Step 3: Create SYSMAN
out = run_sql("""
ALTER SESSION SET CONTAINER=FREEPDB1;
CREATE USER sysman IDENTIFIED BY sysman123;
GRANT DBA TO sysman;
ALTER USER sysman QUOTA UNLIMITED ON users;
EXIT;
""", "Create SYSMAN")

if 'created' in out.lower():
    print("  ✅ SYSMAN user confirmed created")

# Step 4: Test SYSMAN connection internally
out = run_sql("""
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1
SELECT 'SYSMAN_OK' FROM DUAL;
EXIT;
""", "Test SYSMAN connection")

if 'SYSMAN_OK' in out:
    print("  ✅ SYSMAN can connect!")

# Step 5: Create tables as SYSMAN
run_sql("""
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1
CREATE TABLE mgmt_target (target_guid RAW(16), target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256));
CREATE TABLE mgmt_os_hw_summary (host_name VARCHAR2(256), mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10));
CREATE TABLE mgmt_metric_current (target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE TABLE mgmt_metric_hourly (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
CREATE TABLE mgmt_metric_daily (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
EXIT;
""", "Create tables")

# Step 6: Create views
run_sql("""
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1
CREATE OR REPLACE VIEW "mgmt$target" AS SELECT * FROM mgmt_target;
CREATE OR REPLACE VIEW "mgmt$os_hw_summary" AS SELECT * FROM mgmt_os_hw_summary;
CREATE OR REPLACE VIEW "mgmt$metric_current" AS SELECT * FROM mgmt_metric_current;
CREATE OR REPLACE VIEW "mgmt$metric_hourly" AS SELECT * FROM mgmt_metric_hourly;
CREATE OR REPLACE VIEW "mgmt$metric_daily" AS SELECT * FROM mgmt_metric_daily;
EXIT;
""", "Create views")

# Step 7: Insert data
run_sql("""
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.m-dn.local');
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.m-dn.local');
INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.m-dn.local', 65536, 32, 4, 16, 32, 'NO');
INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.m-dn.local', 131072, 64, 8, 32, 64, 'NO');
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5);
INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512);
INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 1, 35.5, 10, 75);
COMMIT;
SELECT COUNT(*) || ' rows in mgmt_target' FROM mgmt_target;
SELECT COUNT(*) || ' rows in mgmt_metric_current' FROM mgmt_metric_current;
EXIT;
""", "Insert sample data")

ssh.close()
print("\n✅ Setup steps complete!")
print("🧪 Test with: python ops/scripts/oem_repository_collector.py --oem-host 127.0.0.1 --oem-port 2521 --oem-service FREEPDB1 --oem-user sysman --oem-pass sysman123 --once")
