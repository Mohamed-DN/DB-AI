-- OEM Repository Simulation Setup Script
-- Run this as SYSDBA on the Oracle database

ALTER SESSION SET CONTAINER=FREEPDB1;

-- Drop existing user if any
BEGIN
  EXECUTE IMMEDIATE 'DROP USER sysman CASCADE';
EXCEPTION
  WHEN OTHERS THEN NULL;
END;
/

-- Create SYSMAN user
CREATE USER sysman IDENTIFIED BY sysman123
  DEFAULT TABLESPACE users
  QUOTA UNLIMITED ON users;

GRANT DBA TO sysman;
GRANT CREATE SESSION TO sysman;
GRANT CREATE TABLE TO sysman;
GRANT CREATE VIEW TO sysman;

-- Create mgmt$ tables
CREATE TABLE sysman.mgmt_target (
    target_guid RAW(16) DEFAULT SYS_GUID() PRIMARY KEY,
    target_name VARCHAR2(256),
    target_type VARCHAR2(64),
    type_qualifier3 VARCHAR2(64),
    host_name VARCHAR2(256)
);

CREATE TABLE sysman.mgmt_os_hw_summary (
    host_name VARCHAR2(256) PRIMARY KEY,
    mem NUMBER,
    cpu_count NUMBER,
    physical_cpu_count NUMBER,
    total_cpu_cores NUMBER,
    logical_cpu_count NUMBER,
    virtual VARCHAR2(10)
);

CREATE TABLE sysman.mgmt_metric_current (
    target_guid RAW(16),
    metric_name VARCHAR2(128),
    metric_column VARCHAR2(128),
    key_value VARCHAR2(256),
    value VARCHAR2(256),
    collection_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP
);

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

-- Create views with dollar sign names
CREATE OR REPLACE VIEW sysman."mgmt$target" AS SELECT * FROM sysman.mgmt_target;
CREATE OR REPLACE VIEW sysman."mgmt$os_hw_summary" AS SELECT * FROM sysman.mgmt_os_hw_summary;
CREATE OR REPLACE VIEW sysman."mgmt$metric_current" AS SELECT * FROM sysman.mgmt_metric_current;
CREATE OR REPLACE VIEW sysman."mgmt$metric_hourly" AS SELECT * FROM sysman.mgmt_metric_hourly;
CREATE OR REPLACE VIEW sysman."mgmt$metric_daily" AS SELECT * FROM sysman.mgmt_metric_daily;

-- Insert sample data
DECLARE
    v_guid1 RAW(16) := HEXTORAW('A1B2C3D4E5F60001A1B2C3D4E5F60001');
    v_guid2 RAW(16) := HEXTORAW('A1B2C3D4E5F60002A1B2C3D4E5F60002');
    v_guid3 RAW(16) := HEXTORAW('A1B2C3D4E5F60003A1B2C3D4E5F60003');
BEGIN
    -- Database targets
    INSERT INTO sysman.mgmt_target VALUES (v_guid1, 'PRODDB1', 'oracle_database', 'SINGLE', 'dbserver1.nexi.local');
    INSERT INTO sysman.mgmt_target VALUES (v_guid2, 'PRODDB2', 'oracle_database', 'SINGLE', 'dbserver2.nexi.local');
    INSERT INTO sysman.mgmt_target VALUES (v_guid3, 'DEVDB1', 'oracle_database', 'SINGLE', 'devserver1.nexi.local');

    -- Host hardware
    INSERT INTO sysman.mgmt_os_hw_summary VALUES ('dbserver1.nexi.local', 65536, 32, 4, 16, 32, 'NO');
    INSERT INTO sysman.mgmt_os_hw_summary VALUES ('dbserver2.nexi.local', 131072, 64, 8, 32, 64, 'NO');
    INSERT INTO sysman.mgmt_os_hw_summary VALUES ('devserver1.nexi.local', 32768, 16, 2, 8, 16, 'YES');

    -- SGA/PGA metrics
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'sga_total', NULL, '4096', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid1, 'memory_usage_sga_pga', 'pga_total', NULL, '1024', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'sga_total', NULL, '8192', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid2, 'memory_usage_sga_pga', 'pga_total', NULL, '2048', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid3, 'memory_usage_sga_pga', 'sga_total', NULL, '2048', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid3, 'memory_usage_sga_pga', 'pga_total', NULL, '512', SYSTIMESTAMP);

    -- Active sessions
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid1, 'instance_throughput', 'avg_active_sessions', NULL, '45', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid2, 'instance_throughput', 'avg_active_sessions', NULL, '82', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid3, 'instance_throughput', 'avg_active_sessions', NULL, '12', SYSTIMESTAMP);

    -- Tablespace metrics
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceUsed', 'USERS', '15360', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid1, 'tbspAllocation', 'spaceAllocated', 'USERS', '20480', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid2, 'tbspAllocation', 'spaceUsed', 'USERS', '45000', SYSTIMESTAMP);
    INSERT INTO sysman.mgmt_metric_current VALUES (v_guid2, 'tbspAllocation', 'spaceAllocated', 'USERS', '51200', SYSTIMESTAMP);

    -- Hourly DB size
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 256.5);
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid1, 'PRODDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512);
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 512.8);
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid2, 'PRODDB2', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 1024);
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid3, 'DEVDB1', 'DATABASE_SIZE', 'USED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 64.2);
    INSERT INTO sysman.mgmt_metric_hourly VALUES (v_guid3, 'DEVDB1', 'DATABASE_SIZE', 'ALLOCATED_GB', NULL, SYSTIMESTAMP, NULL, NULL, 128);

    -- Daily CPU usage (7 days)
    FOR i IN 1..7 LOOP
        INSERT INTO sysman.mgmt_metric_daily VALUES (v_guid1, 'PRODDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 35.5, 10, 75);
        INSERT INTO sysman.mgmt_metric_daily VALUES (v_guid2, 'PRODDB2', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 55.2, 20, 90);
        INSERT INTO sysman.mgmt_metric_daily VALUES (v_guid3, 'DEVDB1', 'instance_efficiency', 'cpuusage_ps', NULL, TRUNC(SYSDATE) - i, 15.8, 5, 45);
    END LOOP;

    COMMIT;
END;
/

-- Verify
SELECT 'Targets: ' || COUNT(*) FROM sysman.mgmt_target;
SELECT 'Hosts: ' || COUNT(*) FROM sysman.mgmt_os_hw_summary;
SELECT 'Current Metrics: ' || COUNT(*) FROM sysman.mgmt_metric_current;
SELECT 'Hourly Metrics: ' || COUNT(*) FROM sysman.mgmt_metric_hourly;
SELECT 'Daily Metrics: ' || COUNT(*) FROM sysman.mgmt_metric_daily;

EXIT;
