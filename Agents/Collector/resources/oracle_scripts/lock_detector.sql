SET PAGESIZE 0
SET LINESIZE 32000
SET LONG 2000000000
SET FEEDBACK OFF
SET VERIFY OFF

WITH 
-- A. IDENTITÀ (Questa parte restituisce sempre 1 riga)
identity_map AS (
    SELECT 
        d.name AS db_name,
        i.host_name,
        i.instance_name,
        SYS_CONTEXT('USERENV', 'CON_NAME') as current_container -- Dice se sei in CDB$ROOT o altrove
    FROM v$database d, v$instance i
),
-- B. LOGICA LOCK (Questa parte può essere vuota)
waiters AS (
    SELECT 
        s.inst_id, s.sid, s.serial#, s.username, 
        s.blocking_instance, s.blocking_session,
        s.seconds_in_wait, s.event, s.sql_id,
        s.con_id, s.machine
    FROM gv$session s
    WHERE s.blocking_session IS NOT NULL
),
lock_tree AS (
    SELECT 
        w.inst_id AS w_inst,
        w.sid AS w_sid,
        w.serial# AS w_serial,
        w.username AS w_user,
        w.machine AS w_machine,
        w.con_id,
        w.seconds_in_wait,
        w.event,
        b.inst_id AS b_inst,
        b.sid AS b_sid,
        b.serial# AS b_serial,
        b.username AS b_user,
        b.program AS b_program,
        b.sql_id AS b_sql_id
    FROM waiters w
    LEFT JOIN gv$session b 
        ON w.blocking_instance = b.inst_id 
        AND w.blocking_session = b.sid
),
enriched_locks AS (
    SELECT 
        lt.*,
        c.name AS target_pdb_name -- PDB dove avviene il lock
    FROM lock_tree lt
    LEFT JOIN gv$containers c ON lt.con_id = c.con_id AND lt.w_inst = c.inst_id
),
-- C. AGGREGAZIONE LOCK IN JSON (Gestisce il caso vuoto)
json_locks AS (
    SELECT 
        COUNT(*) as lock_count,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'target_pdb' VALUE target_pdb_name,
                'waiter' VALUE JSON_OBJECT(
                    'sid' VALUE w_sid,
                    'user' VALUE w_user,
                    'sec' VALUE seconds_in_wait
                ),
                'blocker' VALUE JSON_OBJECT(
                    'sid' VALUE b_sid,
                    'inst' VALUE b_inst,
                    'user' VALUE b_user
                )
            )
        ) as details_array
    FROM enriched_locks
)
-- D. UNIONE FINALE (CROSS JOIN garantisce che l'identità ci sia sempre)
SELECT JSON_OBJECT(
    'timestamp' VALUE SYSTIMESTAMP AT TIME ZONE 'UTC',
    'identity' VALUE JSON_OBJECT(
        'host'      VALUE id.host_name,
        'cdb_name'  VALUE id.db_name,
        'instance'  VALUE id.instance_name,
        'container' VALUE id.current_container
    ),
    'status' VALUE JSON_OBJECT(
        'lock_detected' VALUE (CASE WHEN jl.lock_count > 0 THEN 'YES' ELSE 'NO' END),
        'count'         VALUE NVL(jl.lock_count, 0),
        'details'       VALUE jl.details_array FORMAT JSON
    )
)
FROM identity_map id
CROSS JOIN json_locks jl;