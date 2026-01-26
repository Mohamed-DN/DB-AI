"""Test con utente SYS"""
import oracledb

try:
    conn = oracledb.connect(
        user='sys',
        password='root',
        dsn='127.0.0.1:2521/FREEPDB1',
        mode=oracledb.SYSDBA
    )
    print('✅ Connected as SYS!')
    
    cursor = conn.cursor()
    cursor.execute('SELECT NAME, OPEN_MODE FROM V$DATABASE')
    row = cursor.fetchone()
    print(f'DB: {row[0]}, MODE: {row[1]}')
    
    # Test tablespace
    cursor.execute('SELECT COUNT(*) FROM DBA_TABLESPACES')
    count = cursor.fetchone()[0]
    print(f'Tablespaces: {count}')
    
    cursor.close()
    conn.close()
    
    print('\n🎉 Oracle FULLY working with FREEPDB1!')
    print('Update configuration to use: service_name="FREEPDB1", user="sys", mode=SYSDBA')
    
except Exception as e:
    print(f'❌ Error: {e}')
