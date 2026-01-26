"""Create SYSMAN in FREEPDB1 - simplified version"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('127.0.0.1', port=2200, username='oracle', password='root', timeout=15)
print("✅ SSH connected")

sql = """
ALTER SESSION SET CONTAINER=FREEPDB1;

-- Drop if exists
BEGIN EXECUTE IMMEDIATE 'DROP USER sysman CASCADE'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

-- Create user
CREATE USER sysman IDENTIFIED BY sysman123 DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT DBA TO sysman;
GRANT CREATE SESSION TO sysman;

-- Create tables
CREATE TABLE sysman.mgmt_target (target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY, target_name VARCHAR2(256), target_type VARCHAR2(64), type_qualifier3 VARCHAR2(64), host_name VARCHAR2(256));
CREATE TABLE sysman.mgmt_os_hw_summary (host_name VARCHAR2(256) PRIMARY KEY, mem NUMBER, cpu_count NUMBER, physical_cpu_count NUMBER, total_cpu_cores NUMBER, logical_cpu_count NUMBER, virtual VARCHAR2(10));
CREATE TABLE sysman.mgmt_metric_current (target_guid RAW(16), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), value VARCHAR2(256), collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE TABLE sysman.mgmt_metric_hourly (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);
CREATE TABLE sysman.mgmt_metric_daily (target_guid RAW(16), target_name VARCHAR2(256), metric_name VARCHAR2(128), metric_column VARCHAR2(128), key_value VARCHAR2(256), rollup_timestamp TIMESTAMP, average NUMBER, minimum NUMBER, maximum NUMBER);

COMMIT;
EXIT;
"""

cmd = f"sqlplus / as sysdba <<'EOF'\n{sql}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
print("✅ Done!")
