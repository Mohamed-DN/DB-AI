"""
Final Oracle Connection Test
"""
import oracledb

configs = [
    ('VM1', '127.0.0.1', 2521, 'cdbrac1'),
    ('VM2', '127.0.0.1', 2522, 'cdbrac1')
]

for name, host, port, sid in configs:
    print(f'\n🔌 Testing {name}: {host}:{port}/{sid}')
    dsn = f'{host}:{port}/{sid}'
    
    try:
        conn = oracledb.connect(user='system', password='root', dsn=dsn)
        print(f'  ✅ CONNECTED!')
        
        cursor = conn.cursor()
       
        # Test 1: Basic query
        cursor.execute('SELECT 1 FROM DUAL')
        cursor.fetchone()
        print(f'  ✅ DUAL query OK')
        
        # Test 2: V$INSTANCE access
        try:
            cursor.execute('SELECT COUNT(*) FROM V$INSTANCE')
            count = cursor.fetchone()[0]
            print(f'  ✅ V$INSTANCE accessible: {count} instance(s)')
        except Exception as e:
            print(f'  ❌ V$INSTANCE error: {e}')
        
        cursor.close()
        conn.close()
        print(f'  🎉 {name} is FULLY WORKING!')
        
    except Exception as e:
        print(f'  ❌ CONNECTION ERROR: {str(e)[:150]}')

print('\n' + '='*60)
print('Summary: Check results above')
