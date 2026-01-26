"""
Test Oracle PDB Service Names
"""
import oracledb

# Test configurations - trying common PDB names
test_configs = [
    ('VM1', '127.0.0.1', 2521, 'FREEPDB1'),
    ('VM1', '127.0.0.1', 2521, 'cdbrac1PDB1'),
    ('VM1', '127.0.0.1', 2521, 'ORCLPDB1'),
    ('VM1', '127.0.0.1', 2521, 'PDB1'),
    ('VM1', '127.0.0.1', 2521, 'FREE'),
]

for name, host, port, service in test_configs:
    dsn = f'{host}:{port}/{service}'
    
    try:
        conn = oracledb.connect(user='system', password='root', dsn=dsn)
        print(f'✅ SUCCESS: {service}')
        
        cursor = conn.cursor()
        cursor.execute('SELECT NAME, OPEN_MODE FROM V$DATABASE')
        row = cursor.fetchone()
        print(f'   DB_NAME={row[0]}, MODE={row[1]}')
        
        cursor.close()
        conn.close()
        
        print(f'\n🎉 FOUND WORKING SERVICE: {service}')
        print(f'   Update seed script with service_name="{service}"')
        break
        
    except Exception as e:
        err = str(e)
        if 'DPY-6001' in err or 'ORA-12514' in err:
            print(f'❌ {service}: Not available')
        elif 'DPY-6005' in err:
            print(f'⚠️  {service}: Connection issue')
        else:
            print(f'❌ {service}: {err[:80]}')

print('\nIf none worked, the Oracle database may not be started.')
