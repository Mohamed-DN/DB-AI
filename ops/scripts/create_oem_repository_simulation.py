"""
Create Simulated OEM Repository on VirtualBox VM
================================================
Creates SYSMAN schema with mgmt$* tables and sample data
to test the OEM Repository Collector.
"""
import paramiko
import time

VM = {'host': '127.0.0.1', 'port': 2200}

CREATE_SCHEMA_SQL = """
-- Create SYSMAN user
CREATE USER sysman IDENTIFIED BY sysman123 DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE SEQUENCE TO sysman;
GRANT SELECT_CATALOG_ROLE TO sysman;

-- Connect as SYSMAN to create tables
ALTER SESSION SET CURRENT_SCHEMA = sysman;

-- mgmt$target - OEM targets
CREATE TABLE sysman.mgmt_target (
    target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY,
    target_name VARCHAR2(256),
    target_type VARCHAR2(64),
    type_qualifier3 VARCHAR2(64),
    host_name VARCHAR2(256),
    display_name VARCHAR2(256)
);

CREATE OR REPLACE VIEW sysman.mgmt\$target AS SELECT * FROM sysman.mgmt_target;

-- mgmt$os_hw_summary - Host hardware info
CREATE TABLE sysman.mgmt_os_hw_summary (
    host_name VARCHAR2(256) PRIMARY KEY,
    mem NUMBER,
    cpu_count NUMBER,
    physical_cpu_count NUMBER,
    total_cpu_cores NUMBER,
    logical_cpu_count NUMBER,
    virtual VARCHAR2(10)
);

CREATE OR REPLACE VIEW sysman.mgmt\$os_hw_summary AS SELECT * FROM sysman.mgmt_os_hw_summary;

-- mgmt$metric_current - Current metrics
CREATE TABLE sysman.mgmt_metric_current (
    target_guid RAW(16),
    metric_name VARCHAR2(128),
    metric_column VARCHAR2(128),
    key_value VARCHAR2(256),
    value VARCHAR2(256),
    collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE OR REPLACE VIEW sysman.mgmt\$metric_current AS SELECT * FROM sysman.mgmt_metric_current;

-- mgmt$metric_hourly - Hourly aggregated metrics
CREATE TABLE sysman.mgmt_metric_hourly (
    target_guid RAW(16),
    target_name VARCHAR2(256),
    metric_name VARCHAR2(128),
    metric_column VARCHAR2(128),
    key_value VARCHAR2(256),
    rollup_timestamp TIMESTAMP,
    average NUMBER,
    minimum NUMBER,
    maximum NUMBER
);

CREATE OR REPLACE VIEW sysman.mgmt\$metric_hourly AS SELECT * FROM sysman.mgmt_metric_hourly;

-- mgmt$metric_daily - Daily aggregated metrics
CREATE TABLE sysman.mgmt_metric_daily (
    target_guid RAW(16),
    target_name VARCHAR2(256),
    metric_name VARCHAR2(128),
    metric_column VARCHAR2(128),
    key_value VARCHAR2(256),
    rollup_timestamp TIMESTAMP,
    average NUMBER,
    minimum NUMBER,
    maximum NUMBER
);

CREATE OR REPLACE VIEW sysman.mgmt\$metric_daily AS SELECT * FROM sysman.mgmt_metric_daily;

-- mgmt$rac_memberships (optional)
CREATE TABLE sysman.mgmt_rac_memberships (
    composite_target_name VARCHAR2(256),
    member_target_guid RAW(16)
);

CREATE OR REPLACE VIEW sysman.mgmt\$rac_memberships AS SELECT * FROM sysman.mgmt_rac_memberships;

-- mgmt$group_derived_memberships (optional)
CREATE TABLE sysman.mgmt_group_memberships (
    composite_target_name VARCHAR2(256),
    composite_target_guid RAW(16),
    member_target_guid RAW(16),
    member_target_type VARCHAR2(64)
);

CREATE OR REPLACE VIEW sysman.mgmt\$group_derived_memberships AS SELECT * FROM sysman.mgmt_group_memberships;

COMMIT;
EXIT;
"""

INSERT_SAMPLE_DATA_SQL = """
ALTER SESSION SET CURRENT_SCHEMA = sysman;

-- Sample targets
DECLARE
    v_guid1 RAW(16) := SYS_GUID();
    v_guid2 RAW(16) := SYS_GUID();
    v_guid3 RAW(16) := SYS_GUID();
BEGIN
    -- Database targets
    INSERT INTO mgmt_target VALUES (v_guid1, 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.m-dn.local', 'Production DB 1');
    INSERT INTO mgmt_target VALUES (v_guid2, 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.m-dn.local', 'Production DB 2');
    INSERT INTO mgmt_target VALUES (v_guid3, 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.m-dn.local', 'Development DB');

    -- Host hardware
    INSERT INTO mgmt_os_hw_summary VALUES ('dbserver1.m-dn.local', 65536, 32, 4, 16, 32, 'NO');
    INSERT INTO mgmt_os_hw_summary VALUES ('dbserver2.m-dn.local', 131072, 64, 8, 32, 64, 'NO');
    INSERT INTO mgmt_os_hw_summary VALUES ('devserver1.m-dn.local', 32768, 16, 2, 8, 16, 'YES');

    -- Current metrics - SGA/PGA
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid3, 'memory_usage_sga_pga', 'sga_total', NULL, '2048', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid3, 'memory_usage_sga_pga', 'pga_total', NULL, '512', SYSTIMESTAMP);

    -- Active sessions
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid3, 'instance_throughput', 'avg_active_sessions', NULL, '12', SYSTIMESTAMP);

    -- Tablespace metrics
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceUsed', 'USERS', '15360', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceAllocated', 'USERS', '20480', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceUsed', 'SYSTEM', '2048', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceAllocated', 'SYSTEM', '4096', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'tbspAllocation', 'spaceUsed', 'USERS', '45000', SYSTIMESTAMP);
    INSERT INTO mgmt_metric_current VALUES (v_guid2, 'tbspAllocation', 'spaceAllocated', 'USERS', '51200', SYSTIMESTAMP);

    -- Hourly metrics - DATABASE_SIZE
    INSERT INTO mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 256.5);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 512);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 512.8);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 1024);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid3, 'DEVDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 64.2);
    INSERT INTO mgmt_metric_hourly VALUES (v_guid3, 'DEVDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP - 1/24, NULL, NULL, 128);

    -- Daily metrics - CPU usage
    FOR i IN 1..7 LOOP
        INSERT INTO mgmt_metric_daily VALUES (v_guid1, 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 35.5 + DBMS_RANDOM.VALUE(-5, 5), 10, 75 + DBMS_RANDOM.VALUE(-10, 10));
        INSERT INTO mgmt_metric_daily VALUES (v_guid2, 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 55.2 + DBMS_RANDOM.VALUE(-5, 5), 20, 90 + DBMS_RANDOM.VALUE(-5, 5));
        INSERT INTO mgmt_metric_daily VALUES (v_guid3, 'DEVDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 15.8 + DBMS_RANDOM.VALUE(-5, 5), 5, 45 + DBMS_RANDOM.VALUE(-10, 10));
    END LOOP;

    COMMIT;
END;
/
EXIT;
"""

def execute_sql(ssh, sql, desc):
    """Execute SQL via SSH"""
    print(f"  🔧 {desc}...")
    
    # Escape single quotes for shell
    sql_escaped = sql.replace("'", "'\"'\"'")
    cmd = f"echo '{sql_escaped}' | sqlplus -s / as sysdba"
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if 'ORA-' in output or 'SP2-' in output:
        # Check for expected errors (like "user already exists")
        if 'ORA-01920' not in output:  # User already exists is OK
            print(f"    ⚠️ Some errors (may be expected): {output[:200]}")
    else:
        print(f"    ✅ Done")
    
    return output

def main():
    print("🏗️ Creating Simulated OEM Repository...")
    print("=" * 50)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root', timeout=15)
        print("✅ SSH connected to VM")
        
        # Step 1: Switch to CDB and create schema
        print("\n📦 Step 1: Creating SYSMAN schema...")
        cdb_sql = """
ALTER SESSION SET CONTAINER=CDB\$ROOT;
""" + CREATE_SCHEMA_SQL
        
        execute_sql(ssh, CREATE_SCHEMA_SQL, "Creating tables and views")
        
        time.sleep(2)
        
        # Step 2: Insert sample data
        print("\n📊 Step 2: Inserting sample data...")
        execute_sql(ssh, INSERT_SAMPLE_DATA_SQL, "Inserting sample metrics")
        
        ssh.close()
        
        print("\n" + "=" * 50)
        print("✅ OEM Repository simulation created!")
        print("\n📊 Sample data includes:")
        print("  - 3 database targets (PRODDB1, PRODDB2, DEVDB1)")
        print("  - 3 hosts with hardware info")
        print("  - SGA/PGA metrics")
        print("  - Active sessions")
        print("  - Tablespace usage")
        print("  - Database size (hourly)")
        print("  - CPU usage (7 days)")
        
        print("\n🚀 Test command:")
        print("python ops/scripts/oem_repository_collector.py --oem-host 127.0.0.1 --oem-port 2521 --oem-service FREEPDB1 --oem-user sysman --oem-pass sysman123 --once")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
