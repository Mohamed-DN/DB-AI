-- monitor_metrics.sql
SET PAGESIZE 0
SET LINESIZE 32000
SET LONG 2000000000
SET FEEDBACK OFF
SET VERIFY OFF

WITH session_load AS (
    SELECT 
        COUNT(*) as current_sessions,
        (SELECT value FROM v$parameter WHERE name = 'sessions') as max_sessions,
        SUM(CASE WHEN status = 'ACTIVE' AND type != 'BACKGROUND' THEN 1 ELSE 0 END) as active_user_sessions
    FROM v$session
),
waits_summary AS (
    -- Top 3 Wait Class negli ultimi 60 secondi (approssimativo tramite wait_class_metric)
    SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'wait_class' VALUE wait_class,
                'avg_wait_ms' VALUE ROUND(average_waiter_wait_time/10, 2),
                'db_time_pct' VALUE ROUND(db_time_percent, 2)
            )
        ) as top_waits
    FROM (
        SELECT wait_class, average_waiter_wait_time, db_time_percent 
        FROM v$wait_class_metric 
        WHERE wait_class != 'Idle' 
        ORDER BY db_time_percent DESC 
    ) WHERE ROWNUM <= 3
)
SELECT JSON_OBJECT(
    'timestamp' VALUE SYSTIMESTAMP AT TIME ZONE 'UTC',
    'host'      VALUE (SELECT host_name FROM v$instance),
    'db_name'   VALUE (SELECT name FROM v$database),
    'metrics'   VALUE JSON_OBJECT(
        'sessions' VALUE JSON_OBJECT(
            'total'  VALUE s.current_sessions,
            'active' VALUE s.active_user_sessions,
            'limit'  VALUE s.max_sessions,
            'pct_used' VALUE ROUND((s.current_sessions / TO_NUMBER(s.max_sessions)) * 100, 2)
        ),
        'waits' VALUE w.top_waits FORMAT JSON
    )
) 
FROM session_load s, waits_summary w;