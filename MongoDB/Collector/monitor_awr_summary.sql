/*
-------------------------------------------------------------------------------------
   NOME SCRIPT: monitor_awr_summary.sql
   DESCRIZIONE: AWR Mini-Summary (Ultimo Intervallo)
   
   REQUISITI:
   Richiede licenza Oracle Diagnostics Pack (uso di DBA_HIST_* views).
   
   OBIETTIVO:
   Estrarre un "Health Pulse" storico del database basato sull'ultimo snapshot AWR.
   A differenza delle viste V$ (Real-time), questo script calcola il DELTA 
   tra gli ultimi due snapshot per mostrare il carico reale dell'ultimo intervallo 
   (solitamente l'ultima ora).

   METRICHE ESTRATTE (DELTA):
   1. DB Time (microsecondi): Il tempo totale speso dal DB a lavorare.
   2. Physical Reads: Letture da disco (indice di stress I/O).
   3. Execute Count: Numero di statement eseguiti (indice di carico transazionale).
   4. User Commits: Numero di transazioni confermate (indice di throughput).

   LOGICA TECNICA:
   - Identifica automaticamente DBID e Instance locale.
   - Recupera gli ultimi 2 Snapshot ID.
   - Usa la funzione analitica LAG() per sottrarre il valore precedente a quello attuale
     (trasforma i contatori cumulativi in valori di intervallo).
   - Genera un JSON unico con Identità + Metriche.

   OUTPUT:
   Un singolo documento JSON CLOB.
-------------------------------------------------------------------------------------
*/

-- Configurazione ambiente SQL*Plus per output JSON puro
SET PAGESIZE 0
SET LINESIZE 32000
SET LONG 2000000000
SET FEEDBACK OFF
SET VERIFY OFF
SET TRIMSPOOL ON

WITH 
-- 1. Identifica il contesto locale (DBID e Instance Number)
params AS (
    SELECT 
        (SELECT dbid FROM v$database) AS dbid,
        (SELECT instance_number FROM v$instance) AS inst 
    FROM dual
),
-- 2. Trova gli ultimi 2 Snapshot completati
last_snaps AS (
    SELECT snap_id, begin_interval_time, end_interval_time 
    FROM (
        SELECT s.snap_id, s.begin_interval_time, s.end_interval_time 
        FROM dba_hist_snapshot s 
        JOIN params p ON p.dbid = s.dbid AND p.inst = s.instance_number 
        ORDER BY s.snap_id DESC
    ) 
    FETCH FIRST 2 ROWS ONLY
),
-- 3. Estrai i dati grezzi da SYSSTAT (Letture, Esecuzioni, Commit)
raw_sysstat AS (
    SELECT 
        s.snap_id,
        sn.name AS stat_name,
        s.value
    FROM dba_hist_sysstat s
    JOIN params p ON p.dbid = s.dbid AND p.inst = s.instance_number
    JOIN last_snaps ls ON ls.snap_id = s.snap_id
    -- Join con V$STATNAME per garanzia sui nomi (opzionale ma robusto)
    JOIN v$statname sn ON sn.statistic# = s.stat_id
    WHERE sn.name IN ('physical reads', 'execute count', 'user commits')
),
-- 4. Estrai i dati grezzi dal Time Model (DB Time)
raw_timemodel AS (
    SELECT 
        t.snap_id,
        tm.stat_name,
        t.value
    FROM dba_hist_sys_time_model t
    JOIN params p ON p.dbid = t.dbid AND p.inst = t.instance_number
    JOIN last_snaps ls ON ls.snap_id = t.snap_id
    JOIN v$sys_time_model tm ON tm.stat_id = t.stat_id
    WHERE tm.stat_name = 'DB time'
),
-- 5. Unisci le metriche grezze
raw_metrics AS (
    SELECT * FROM raw_sysstat 
    UNION ALL 
    SELECT * FROM raw_timemodel
),
-- 6. Calcolo del DELTA (Valore Attuale - Valore Precedente)
calculated_deltas AS (
    SELECT 
        snap_id,
        stat_name,
        value - LAG(value) OVER (PARTITION BY stat_name ORDER BY snap_id) AS delta_value
    FROM raw_metrics
),
-- 7. Pivot finale: tieni solo l'ultimo snap e ruota le righe in colonne
final_metrics AS (
    SELECT 
        d.snap_id,
        ls.begin_interval_time,
        ls.end_interval_time,
        NVL(MAX(CASE WHEN stat_name = 'DB time' THEN delta_value END), 0) AS db_time_micro,
        NVL(MAX(CASE WHEN stat_name = 'physical reads' THEN delta_value END), 0) AS physical_reads,
        NVL(MAX(CASE WHEN stat_name = 'execute count' THEN delta_value END), 0) AS executes,
        NVL(MAX(CASE WHEN stat_name = 'user commits' THEN delta_value END), 0) AS commits
    FROM calculated_deltas d
    JOIN last_snaps ls ON ls.snap_id = d.snap_id
    WHERE d.delta_value IS NOT NULL -- Rimuove la riga "vecchia" usata solo per la sottrazione
    GROUP BY d.snap_id, ls.begin_interval_time, ls.end_interval_time
),
-- 8. Identità Host/DB
identity_map AS (
    SELECT d.name AS db_name, i.host_name 
    FROM v$database d, v$instance i
)
-- 9. Costruzione JSON
SELECT JSON_OBJECT(
    'type'      VALUE 'awr_summary',
    'timestamp' VALUE (SYSTIMESTAMP AT TIME ZONE 'UTC'),
    'identity'  VALUE JSON_OBJECT(
        'host'    VALUE i.host_name,
        'db_name' VALUE i.db_name
    ),
    'snapshot'  VALUE JSON_OBJECT(
        'id'      VALUE f.snap_id,
        'start'   VALUE TO_CHAR(f.begin_interval_time, 'YYYY-MM-DD HH24:MI'),
        'end'     VALUE TO_CHAR(f.end_interval_time, 'YYYY-MM-DD HH24:MI'),
        'metrics' VALUE JSON_OBJECT(
            'db_time_micro'  VALUE f.db_time_micro,
            'physical_reads' VALUE f.physical_reads,
            'executes'       VALUE f.executes,
            'commits'        VALUE f.commits
        )
    )
    RETURNING CLOB
) AS json_payload
FROM final_metrics f
CROSS JOIN identity_map i;