/*
-------------------------------------------------------------------------------------
   NOME SCRIPT: monitor_top_sessions_safe.sql
   DESCRIZIONE: Modulo "Top 10 Consumers" (Safe Mode / Locale)
   
   OBIETTIVO:
   Identificare le 10 sessioni che stanno consumando più risorse (CPU e I/O) 
   in questo esatto momento sull'istanza locale.
   
   PERCHÉ "SAFE MODE"?
   Questa query interroga le viste locali (V$) invece di quelle globali (GV$).
   È progettata per essere eseguita dall'agente quando il Cluster RAC è instabile 
   (es. un nodo è in stato MOUNTED o non risponde). 
   A differenza della versione Globale, questa query NON si blocca (hang) se un 
   altro nodo del cluster è "morto", garantendo che il monitoraggio continui a funzionare.

   COSA FA:
   1. È "Locale": Interroga solo il nodo dove l'agente è connesso.
   2. Trova i "Mangiatori di Risorse": Filtra sessioni ACTIVE e somma:
      - CPU used by this session (Carico calcolo)
      - Physical reads (Stress disco/storage)
   3. Fa la Classifica (Ranking): Ordina per CPU decrescente (Top 10).
   4. Vede tutti i PDB: Risolve il CON_ID per mostrare se il carico è su CDB$ROOT o un PDB specifico.
   5. Genera JSON: Output pronto per MongoDB (Top Consumers + Identità Host).

   OUTPUT:
   Documento JSON singolo contenente timestamp, info host e array delle sessioni.
-------------------------------------------------------------------------------------
*/

-- Configurazione ambiente SQL*Plus per output JSON pulito
SET PAGESIZE 0
SET LINESIZE 32000
SET LONG 2000000000
SET FEEDBACK OFF
SET VERIFY OFF
SET TRIMSPOOL ON

WITH 
-- 1. Estrai Statistiche LOCALI (V$ invece di GV$)
-- Questo evita di chiedere dati al nodo bloccato
raw_stats AS (
    SELECT 
        s.sid, s.serial#, s.username, s.program, s.sql_id, s.event, 
        s.con_id, s.machine, s.seconds_in_wait,
        sn.name, st.value
    FROM v$session s
    JOIN v$sesstat st ON s.sid = st.sid
    JOIN v$statname sn ON st.statistic# = sn.statistic#
    WHERE s.type = 'USER' 
      AND s.status = 'ACTIVE'
      AND sn.name IN ('CPU used by this session', 'physical reads')
),
-- 2. Pivot dei dati (Cpu e Letture su colonne)
pivoted_sessions AS (
    SELECT 
        sid, serial#, username, program, sql_id, event, con_id, machine, seconds_in_wait,
        SUM(CASE WHEN name = 'CPU used by this session' THEN value ELSE 0 END) as cpu_value,
        SUM(CASE WHEN name = 'physical reads' THEN value ELSE 0 END) as io_reads
    FROM raw_stats
    GROUP BY sid, serial#, username, program, sql_id, event, con_id, machine, seconds_in_wait
    ORDER BY cpu_value DESC
    FETCH FIRST 10 ROWS ONLY
),
-- 3. Aggiungi nomi PDB e contesto istanza corrente
enriched_sessions AS (
    SELECT 
        ps.*,
        NVL(c.name, 'CDB$ROOT') as pdb_name,
        (SELECT instance_number FROM v$instance) as local_inst_id
    FROM pivoted_sessions ps
    LEFT JOIN v$containers c ON ps.con_id = c.con_id
),
-- 4. Creazione Blocco JSON (Isolato per evitare errori di gruppo ORA-00937)
json_sessions_block AS (
    SELECT 
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'rank'      VALUE ROWNUM,
                'location'  VALUE JSON_OBJECT(
                    'pdb'       VALUE pdb_name,
                    'inst_id'   VALUE local_inst_id -- Sarà sempre l'ID del nodo vivo
                ),
                'session'   VALUE JSON_OBJECT(
                    'sid_serial' VALUE sid || ',' || serial#,
                    'user'       VALUE username,
                    'program'    VALUE program,
                    'machine'    VALUE machine
                ),
                'activity'  VALUE JSON_OBJECT(
                    'sql_id'     VALUE sql_id,
                    'event'      VALUE event,
                    'wait_sec'   VALUE seconds_in_wait
                ),
                'resources' VALUE JSON_OBJECT(
                    'cpu_score'      VALUE cpu_value,
                    'physical_reads' VALUE io_reads
                )
            )
        ) as sessions_array
    FROM enriched_sessions
),
-- 5. Identità del DB
identity_map AS (
    SELECT d.name AS db_name, i.host_name, i.instance_name
    FROM v$database d, v$instance i
)
-- 6. Unione Finale
SELECT JSON_OBJECT(
    'timestamp' VALUE SYSTIMESTAMP AT TIME ZONE 'UTC',
    'type'      VALUE 'top_sessions_safe',
    'identity'  VALUE JSON_OBJECT(
        'host'      VALUE id.host_name,
        'db_name'   VALUE id.db_name,
        'instance'  VALUE id.instance_name
    ),
    'top_consumers' VALUE js.sessions_array FORMAT JSON
)
FROM identity_map id
CROSS JOIN json_sessions_block js;