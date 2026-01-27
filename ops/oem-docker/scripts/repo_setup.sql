-- ============================================================================
-- PREPARE REPOSITORY DATABASE FOR OEM 13c
-- Run this on your 'ol7-orcl' container (Oracle 19c)
-- ============================================================================

-- 1. Check/Set System Parameters
-- OEM requires specific SPFILE parameters.
ALTER SYSTEM SET processes=600 SCOPE=SPFILE;
ALTER SYSTEM SET session_cached_cursors=200 SCOPE=SPFILE;
ALTER SYSTEM SET job_queue_processes=20 SCOPE=SPFILE;
ALTER SYSTEM SET open_cursors=600 SCOPE=SPFILE;
-- Needed for 19c
ALTER SYSTEM SET "_allow_insert_with_update_check"=TRUE SCOPE=SPFILE;

-- Restart Database to apply changes
-- SHUTDOWN IMMEDIATE;
-- STARTUP;

-- 2. Create Repository User (Optional, Installer can do this, but recommended pre-check)
-- The installer usually creates SYSMAN. You need to provide SYS credentials.

-- 3. Create Tablespaces (Optional - Installer can auto-create if you select 'Small' deployment)
-- But for "Production" level:
/*
CREATE TABLESPACE mgmt_ecm_depot_ts DATAFILE 'mgmt_ecm_depot01.dbf' SIZE 1G AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED;
CREATE TABLESPACE mgmt_tablespace DATAFILE 'mgmt.dbf' SIZE 2G AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED;
CREATE TABLESPACE mgmt_ad4j_ts DATAFILE 'mgmt_ad4j.dbf' SIZE 1G AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED;
*/

-- 4. Verify Temp Tablespace
ALTER DATABASE TEMPFILE '/opt/oracle/oradata/ORCLCDB/temp01.dbf' AUTOEXTEND ON MAXSIZE UNLIMITED;

-- ============================================================================
-- END
-- ============================================================================
