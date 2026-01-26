"""
Create OEM simulation tables under SYSTEM user instead of SYSMAN
"""
import paramiko

VM = {'host': '127.0.0.1', 'port': 2200}

# Create tables under SYSTEM user with sysman_ prefix
SQL = """
ALTER SESSION SET CONTAINER=FREEPDB1;

-- Drop existing tables
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sysman_target'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sysman_os_hw'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sysman_metric_current'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sysman_metric_hourly'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sysman_metric_daily'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

-- Create tables
CREATE TABLE sysman_target (target_guid RAW(16), target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256));
CREATE TABLE sysman_os_hw (host_name VARCHAR2(256), mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10));
CREATE TABLE sysman_metric_current (target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE TABLE sysman_metric_hourly (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
CREATE TABLE sysman_metric_daily (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);

-- Insert sample data
INSERT INTO sysman_target VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.nexi.local');
INSERT INTO sysman_target VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.nexi.local');
INSERT INTO sysman_target VALUES (HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003'), 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.nexi.local');

INSERT INTO sysman_os_hw VALUES ('dbserver1.nexi.local', 65536, 32, 4, 16, 32, 'NO');
INSERT INTO sysman_os_hw VALUES ('dbserver2.nexi.local', 131072, 64, 8, 32, 64, 'NO');
INSERT INTO sysman_os_hw VALUES ('devserver1.nexi.local', 32768, 16, 2, 8, 16, 'YES');

INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP);
INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP);
INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
INSERT INTO sysman_metric_current VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP);

INSERT INTO sysman_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5);
INSERT INTO sysman_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512);
INSERT INTO sysman_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8);
INSERT INTO sysman_metric_hourly VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024);

INSERT INTO sysman_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001'), 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 1, 35.5, 10, 75);
INSERT INTO sysman_metric_daily VALUES (HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002'), 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - 1, 55.2, 20, 90);

COMMIT;

-- Reset SYSTEM password
ALTER USER system IDENTIFIED BY root;

SELECT 'TARGETS: ' || COUNT(*) FROM sysman_target;
SELECT 'HOSTS: ' || COUNT(*) FROM sysman_os_hw;
SELECT 'CURRENT: ' || COUNT(*) FROM sysman_metric_current;
SELECT 'HOURLY: ' || COUNT(*) FROM sysman_metric_hourly;
SELECT 'DAILY: ' || COUNT(*) FROM sysman_metric_daily;

EXIT;
"""

print("🚀 Creating OEM simulation under SYSTEM user...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root')

sftp = ssh.open_sftp()
with sftp.open('/tmp/sys_oem.sql', 'w') as f:
    f.write(SQL)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('sqlplus / as sysdba @/tmp/sys_oem.sql', timeout=90)
out = stdout.read().decode('utf-8', errors='ignore')

for line in out.split('\n'):
    if 'TARGETS:' in line or 'HOSTS:' in line or 'CURRENT:' in line or 'HOURLY:' in line or 'DAILY:' in line:
        print(f"  📊 {line.strip()}")

ssh.close()
print("\n✅ Tables created under SYSTEM!")
print("\n🧪 Now update OEM collector to use SYSTEM user and modified table names")
