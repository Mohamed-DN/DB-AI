"""
Final attempt - create everything as SYSDBA using ALTER SESSION SET CURRENT_SCHEMA
"""
import paramiko

VM = {'host': '127.0.0.1', 'port': 2200}

FINAL_SQL = """
ALTER SESSION SET CONTAINER=FREEPDB1;

-- Drop and create SYSMAN
BEGIN EXECUTE IMMEDIATE 'DROP USER sysman CASCADE'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
CREATE USER sysman IDENTIFIED BY sysman123;
GRANT DBA, RESOURCE, CONNECT TO sysman;
ALTER USER sysman QUOTA UNLIMITED ON users;

-- Switch to SYSMAN schema for object creation
ALTER SESSION SET CURRENT_SCHEMA = sysman;

-- Create tables
CREATE TABLE mgmt_target (target_guid RAW(16), target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256));
CREATE TABLE mgmt_os_hw_summary (host_name VARCHAR2(256), mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10));
CREATE TABLE mgmt_metric_current (target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE TABLE mgmt_metric_hourly (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
CREATE TABLE mgmt_metric_daily (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);

-- Create views with $
CREATE OR REPLACE VIEW "mgmt$target" AS SELECT * FROM mgmt_target;
CREATE OR REPLACE VIEW "mgmt$os_hw_summary" AS SELECT * FROM mgmt_os_hw_summary;
CREATE OR REPLACE VIEW "mgmt$metric_current" AS SELECT * FROM mgmt_metric_current;
CREATE OR REPLACE VIEW "mgmt$metric_hourly" AS SELECT * FROM mgmt_metric_hourly;
CREATE OR REPLACE VIEW "mgmt$metric_daily" AS SELECT * FROM mgmt_metric_daily;

-- Grant to SYSMAN
GRANT SELECT ON "mgmt$target" TO sysman;
GRANT SELECT ON "mgmt$os_hw_summary" TO sysman;
GRANT SELECT ON "mgmt$metric_current" TO sysman;
GRANT SELECT ON "mgmt$metric_hourly" TO sysman;
GRANT SELECT ON "mgmt$metric_daily" TO sysman;

-- Insert data
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.nexi.local');
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.nexi.local');
INSERT INTO mgmt_target VALUES (HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003'), 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.nexi.local');

INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.nexi.local', 65536, 32, 4, 16, 32, 'NO');
INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.nexi.local', 131072, 64, 8, 32, 64, 'NO');
INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.nexi.local', 32768, 16, 2, 8, 16, 'YES');

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

COMMIT;

-- Verify
SELECT 'TARGETS: ' || COUNT(*) FROM sysman.mgmt_target;
SELECT 'HOSTS: ' || COUNT(*) FROM sysman.mgmt_os_hw_summary;
SELECT 'CURRENT: ' || COUNT(*) FROM sysman.mgmt_metric_current;
SELECT 'HOURLY: ' || COUNT(*) FROM sysman.mgmt_metric_hourly;
SELECT 'DAILY: ' || COUNT(*) FROM sysman.mgmt_metric_daily;

EXIT;
"""

print("🚀 FINAL OEM Setup...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root')
print("✅ SSH connected")

# Upload and execute
sftp = ssh.open_sftp()
with sftp.open('/tmp/final.sql', 'w') as f:
    f.write(FINAL_SQL)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('sqlplus / as sysdba @/tmp/final.sql', timeout=90)
out = stdout.read().decode('utf-8', errors='ignore')

# Parse output
for line in out.split('\n'):
    if 'TARGETS:' in line or 'HOSTS:' in line or 'CURRENT:' in line or 'HOURLY:' in line or 'DAILY:' in line:
        print(f"  📊 {line.strip()}")
    if 'User created' in line:
        print("  ✅ SYSMAN user created")

ssh.close()
print("\n✅ DONE!")
