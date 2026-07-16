"""Insert sample OEM data"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('127.0.0.1', port=2200, username='oracle', password='root', timeout=15)
print("✅ SSH connected")

sql = """
ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER SESSION SET CURRENT_SCHEMA=sysman;

-- Insert sample data
DECLARE
    v_guid1 RAW(16) := HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001');
    v_guid2 RAW(16) := HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002');
    v_guid3 RAW(16) := HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003');
BEGIN
    DELETE FROM mgmt_target;
    DELETE FROM mgmt_os_hw_summary;
    DELETE FROM mgmt_metric_current;
    DELETE FROM mgmt_metric_hourly;
    DELETE FROM mgmt_metric_daily;

    INSERT INTO mgmt_target VALUES (v_guid1, 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.m-dn.local');
    INSERT INTO mgmt_target VALUES (v_guid2, 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.m-dn.local');
    INSERT INTO mgmt_target VALUES (v_guid3, 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.m-dn.local');

    INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.m-dn.local', 65536, 32, 4, 16, 32, 'NO');
    INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.m-dn.local', 131072, 64, 8, 32, 64, 'NO');
    INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.m-dn.local', 32768, 16, 2, 8, 16, 'YES');

    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceUsed', 'USERS', '15360', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceAllocated', 'USERS', '20480', SYSTIMESTAMP);

    INSERT INTO mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024);

    INSERT INTO mgmt_metric_daily VALUES (v_guid1, 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE)-1, 35.5, 10, 75);
    INSERT INTO mgmt_metric_daily VALUES (v_guid2, 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE)-1, 55.2, 20, 90);

    COMMIT;
END;
/
EXIT;
"""

cmd = f"sqlplus / as sysdba <<'EOF'\n{sql}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
if 'PL/SQL procedure successfully completed' in out:
    print("✅ Sample data inserted!")
else:
    print(out[:500])
ssh.close()
