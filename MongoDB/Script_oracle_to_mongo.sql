SET PAGESIZE 0
SET LINESIZE 32000
SET LONG 2000000000
SET LONGCHUNKSIZE 32000
SET TRIMSPOOL ON
SET FEEDBACK OFF
SET ECHO OFF
SET HEADING OFF
SET VERIFY OFF

-- Attiva il salvataggio su file
SPOOL database_metadata.json

-- Esegui la query (versione corretta per l'export)
WITH db_info AS (
    SELECT 
        d.name AS db_name,
        d.dbid,
        TO_CHAR(d.created, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS created_date,
        d.log_mode,
        d.open_mode,
        d.database_role,
        d.platform_name,
        d.protection_mode,
        d.protection_level,
        i.instance_name,
        i.instance_number,
        i.thread#,
        i.version,
        i.host_name,
        TO_CHAR(i.startup_time, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS startup_time
    FROM v$database d, v$instance i
),
rac_info AS (
    SELECT 
        value AS cluster_database,
        (SELECT value FROM v$parameter WHERE name = 'cluster_database_instances') AS cluster_instances,
        (SELECT COUNT(*) FROM gv$instance) AS instance_count
    FROM v$parameter 
    WHERE name = 'cluster_database'
),
init_params AS (
    SELECT 
        JSON_OBJECTAGG(name VALUE value) AS params_json
    FROM v$parameter
    WHERE name IN (
        'db_block_size', 'compatible', 'sga_target', 'sga_max_size',
        'pga_aggregate_target', 'pga_aggregate_limit', 'processes',
        'sessions', 'transactions', 'memory_target', 'memory_max_target',
        'db_cache_size', 'shared_pool_size', 'large_pool_size',
        'java_pool_size', 'streams_pool_size', 'log_buffer'
    )
),
charset_info AS (
    SELECT 
        MAX(CASE WHEN parameter = 'NLS_CHARACTERSET' THEN value END) AS database_charset,
        MAX(CASE WHEN parameter = 'NLS_NCHAR_CHARACTERSET' THEN value END) AS nls_charset,
        MAX(CASE WHEN parameter = 'NLS_LANGUAGE' THEN value END) AS nls_language,
        MAX(CASE WHEN parameter = 'NLS_TERRITORY' THEN value END) AS nls_territory
    FROM nls_database_parameters
    WHERE parameter IN ('NLS_CHARACTERSET', 'NLS_NCHAR_CHARACTERSET', 'NLS_LANGUAGE', 'NLS_TERRITORY')
),
tablespaces_info AS (
    SELECT 
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'name' VALUE ts.tablespace_name,
                'size_gb' VALUE ROUND(SUM(df.bytes)/1024/1024/1024, 2),
                'used_gb' VALUE ROUND((SUM(df.bytes) - NVL(SUM(fs.bytes), 0))/1024/1024/1024, 2),
                'free_gb' VALUE ROUND(NVL(SUM(fs.bytes), 0)/1024/1024/1024, 2),
                'autoextend' VALUE MAX(df.autoextensible),
                'status' VALUE ts.status,
                'contents' VALUE ts.contents
            )
        ) AS tablespaces_json
    FROM dba_tablespaces ts
    LEFT JOIN dba_data_files df ON ts.tablespace_name = df.tablespace_name
    LEFT JOIN dba_free_space fs ON ts.tablespace_name = fs.tablespace_name
    WHERE ts.contents != 'TEMPORARY'
    GROUP BY ts.tablespace_name, ts.status, ts.contents
    UNION ALL
    SELECT 
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'name' VALUE ts.tablespace_name,
                'size_gb' VALUE ROUND(SUM(tf.bytes)/1024/1024/1024, 2),
                'used_gb' VALUE 0,
                'free_gb' VALUE 0,
                'autoextend' VALUE MAX(tf.autoextensible),
                'status' VALUE ts.status,
                'contents' VALUE ts.contents
            )
        ) AS tablespaces_json
    FROM dba_tablespaces ts
    JOIN dba_temp_files tf ON ts.tablespace_name = tf.tablespace_name
    WHERE ts.contents = 'TEMPORARY'
    GROUP BY ts.tablespace_name, ts.status, ts.contents
),
redo_logs_info AS (
    SELECT 
        (SELECT COUNT(*) FROM v$log) AS redo_groups,
        members AS members_per_group,
        ROUND(bytes/1024/1024, 0) AS size_mb
    FROM v$log
    WHERE ROWNUM = 1
),
database_size AS (
    SELECT 
        ROUND(SUM(bytes)/1024/1024/1024, 2) AS total_allocated_gb,
        ROUND((SUM(bytes) - SUM(NVL(free_space, 0)))/1024/1024/1024, 2) AS total_used_gb
    FROM (
        SELECT SUM(bytes) AS bytes, NULL AS free_space FROM dba_data_files
        UNION ALL
        SELECT SUM(bytes), NULL FROM dba_temp_files
        UNION ALL
        SELECT NULL, SUM(bytes) FROM dba_free_space
    )
),
security_info AS (
    SELECT 
        COUNT(*) AS total_users,
        SUM(CASE WHEN account_status = 'OPEN' THEN 1 ELSE 0 END) AS active_users,
        SUM(CASE WHEN account_status LIKE '%LOCKED%' THEN 1 ELSE 0 END) AS locked_users
    FROM dba_users
),
asm_info AS (
    SELECT 
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'name' VALUE name,
                'size_gb' VALUE ROUND(total_mb/1024, 2),
                'free_gb' VALUE ROUND(free_mb/1024, 2),
                'used_gb' VALUE ROUND((total_mb - free_mb)/1024, 2),
                'redundancy' VALUE type
            )
        ) AS asm_diskgroups_json
    FROM v$asm_diskgroup
),
services_info AS (
    SELECT 
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'name' VALUE name,
                'network_name' VALUE network_name,
                'goal' VALUE goal,
                'clb_goal' VALUE clb_goal
            )
        ) AS services_json
    FROM v$active_services
    WHERE name NOT LIKE 'SYS%'
),
edition_info AS (
    SELECT 
        banner AS version,
        CASE 
            WHEN banner LIKE '%Enterprise Edition%' THEN 'Enterprise'
            WHEN banner LIKE '%Standard Edition%' THEN 'Standard'
            ELSE 'Unknown'
        END AS edition
    FROM v$version
    WHERE banner LIKE 'Oracle Database%'
    AND ROWNUM = 1
),
audit_info AS (
    SELECT 
        p1.value AS audit_trail,
        p2.value AS audit_sys_operations
    FROM v$parameter p1, v$parameter p2
    WHERE p1.name = 'audit_trail'
    AND p2.name = 'audit_sys_operations'
)
SELECT 
    JSON_OBJECT(
        'collection_timestamp' VALUE SYSTIMESTAMP AT TIME ZONE 'UTC',
        'identity' VALUE JSON_OBJECT(
            'db_name' VALUE d.db_name,
            'dbid' VALUE d.dbid,
            'unique_name' VALUE d.db_name, 
            'platform' VALUE d.platform_name,
            'created' VALUE d.created_date,
            'role' VALUE d.database_role,
            'open_mode' VALUE d.open_mode,
            'log_mode' VALUE d.log_mode
        ),
        'instance' VALUE JSON_OBJECT(
            'name' VALUE d.instance_name,
            'host' VALUE d.host_name,
            'version' VALUE d.version,
            'edition' VALUE e.edition,
            'startup_time' VALUE d.startup_time,
            'rac_enabled' VALUE r.cluster_database,
            'rac_instances' VALUE r.instance_count
        ),
        'configuration' VALUE JSON_OBJECT(
            'nls' VALUE JSON_OBJECT(
                'charset' VALUE c.database_charset,
                'nchar_charset' VALUE c.nls_charset,
                'language' VALUE c.nls_language,
                'territory' VALUE c.nls_territory
            ),
            'audit' VALUE JSON_OBJECT(
                'trail' VALUE au.audit_trail,
                'sys_ops' VALUE au.audit_sys_operations
            ),
            'parameters' VALUE ip.params_json FORMAT JSON
        ),
        'storage' VALUE JSON_OBJECT(
            'summary' VALUE JSON_OBJECT(
                'allocated_gb' VALUE ds.total_allocated_gb,
                'used_gb' VALUE ds.total_used_gb
            ),
            'redo_logs' VALUE JSON_OBJECT(
                'groups' VALUE rl.redo_groups,
                'members_per_group' VALUE rl.members_per_group,
                'size_mb' VALUE rl.size_mb
            ),
            'tablespaces' VALUE (SELECT JSON_ARRAYAGG(t.tablespaces_json) FROM tablespaces_info t) FORMAT JSON,
            'asm_diskgroups' VALUE a.asm_diskgroups_json FORMAT JSON
        ),
        'security' VALUE JSON_OBJECT(
            'users_total' VALUE s.total_users,
            'users_active' VALUE s.active_users,
            'users_locked' VALUE s.locked_users
        ),
        'network' VALUE JSON_OBJECT(
            'services' VALUE sv.services_json FORMAT JSON
        )
    RETURNING CLOB) 
FROM db_info d
CROSS JOIN rac_info r
CROSS JOIN init_params ip
CROSS JOIN charset_info c
CROSS JOIN redo_logs_info rl
CROSS JOIN database_size ds
CROSS JOIN security_info s
CROSS JOIN asm_info a
CROSS JOIN services_info sv
CROSS JOIN edition_info e
CROSS JOIN audit_info au;

-- Chiudi e salva
SPOOL OFF