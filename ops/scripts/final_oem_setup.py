"""Final attempt - execute everything via SFTP SQL file"""
import paramiko
import time

VM = {'host': '127.0.0.1', 'port': 2200}

# Complete SQL script
SETUP_SQL = """
-- Reset password and create SYSMAN
ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER USER system IDENTIFIED BY root;

-- Drop and recreate SYSMAN
BEGIN EXECUTE IMMEDIATE 'DROP USER sysman CASCADE'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
CREATE USER sysman IDENTIFIED BY sysman123;
GRANT DBA, CREATE SESSION TO sysman;
ALTER USER sysman DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;

-- Create tables as SYSMAN
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1

CREATE TABLE mgmt_target (target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY, target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256));
CREATE TABLE mgmt_os_hw_summary (host_name VARCHAR2(256) PRIMARY KEY, mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10));
CREATE TABLE mgmt_metric_current (target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE TABLE mgmt_metric_hourly (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
CREATE TABLE mgmt_metric_daily (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);

-- Views
CREATE OR REPLACE VIEW "mgmt$target" AS SELECT * FROM mgmt_target;
CREATE OR REPLACE VIEW "mgmt$os_hw_summary" AS SELECT * FROM mgmt_os_hw_summary;
CREATE OR REPLACE VIEW "mgmt$metric_current" AS SELECT * FROM mgmt_metric_current;
CREATE OR REPLACE VIEW "mgmt$metric_hourly" AS SELECT * FROM mgmt_metric_hourly;
CREATE OR REPLACE VIEW "mgmt$metric_daily" AS SELECT * FROM mgmt_metric_daily;

-- Data
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.m-dn.local');
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.m-dn.local');
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003'), 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.m-dn.local');

INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.m-dn.local', 65536, 32, 4, 16, 32, 'NO');
INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.m-dn.local', 131072, 64, 8, 32, 64, 'NO');
INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.m-dn.local', 32768, 16, 2, 8, 16, 'YES');

INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'tbspAllocation', 'spaceUsed', 'USERS', '15360', SYSTIMESTAMP);
INSERT INTO mgmt_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'tbspAllocation', 'spaceAllocated', 'USERS', '20480', SYSTIMESTAMP);

INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5);
INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512);
INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8);
INSERT INTO mgmt_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024);

INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 1, 35.5, 10, 75);
INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 1, 55.2, 20, 90);
INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 2, 36.1, 12, 78);
INSERT INTO mgmt_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 2, 58.4, 22, 92);

COMMIT;

SELECT 'Targets: ' || COUNT(*) FROM mgmt_target;
SELECT 'Hosts: ' || COUNT(*) FROM mgmt_os_hw_summary;
SELECT 'Current Metrics: ' || COUNT(*) FROM mgmt_metric_current;
SELECT 'Hourly Metrics: ' || COUNT(*) FROM mgmt_metric_hourly;
SELECT 'Daily Metrics: ' || COUNT(*) FROM mgmt_metric_daily;

EXIT;
"""

print("🚀 Final OEM Setup Attempt...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root')
print("✅ SSH connected")

# Upload SQL
sftp = ssh.open_sftp()
with sftp.open('/tmp/final_setup.sql', 'w') as f:
    f.write(SETUP_SQL)
sftp.close()
print("✅ SQL uploaded")

# Execute
print("🔧 Executing SQL (this takes ~30s)...")
stdin, stdout, stderr = ssh.exec_command('sqlplus / as sysdba @/tmp/final_setup.sql', timeout=120)
out = stdout.read().decode('utf-8', errors='ignore')

# Check for success indicators
if 'created' in out.lower():
    print("✅ User created!")
if 'row created' in out.lower() or '1 row' in out.lower():
    print("✅ Data inserted!")

# Show counts
for line in out.split('\n'):
    if 'Targets:' in line or 'Hosts:' in line or 'Metrics:' in line:
        print(f"  📊 {line.strip()}")

# Check for errors
errors = [l for l in out.split('\n') if 'ORA-' in l]
if errors:
    print("⚠️ Errors:")
    for e in errors[:5]:
        print(f"  {e[:80]}")

ssh.close()
print("\n✅ Setup complete!")
print("\n🧪 Test: python ops/scripts/oem_repository_collector.py --oem-host 127.0.0.1 --oem-port 2521 --oem-service FREEPDB1 --oem-user sysman --oem-pass sysman123 --once")
