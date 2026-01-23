"""Test Oracle RAC with direct PDB connection and ASM"""
import oracledb

# Test with PDB services directly
tests = [
    ('192.168.56.101', 1521, 'pdb1', 'sys', 'root'),
    ('192.168.56.101', 1521, 'luna', 'sys', 'root'),
    ('192.168.56.101', 1521, 'sole', 'sys', 'root'),
    ('192.168.56.101', 1521, 'cdbrac', 'sys', 'root'),
]

for host, port, service, user, password in tests:
    try:
        dsn = f'{host}:{port}/{service}'
        print(f'\n=== Trying {user}@{dsn} ===')
        conn = oracledb.connect(
            user=user, 
            password=password, 
            dsn=dsn, 
            mode=oracledb.AUTH_MODE_SYSDBA
        )
        cursor = conn.cursor()
        
        # Basic info
        cursor.execute('SELECT NAME, DB_UNIQUE_NAME FROM V$DATABASE')
        row = cursor.fetchone()
        print(f'DB: {row[0]}, UNIQUE: {row[1]}')
        
        # Instance
        cursor.execute('SELECT INSTANCE_NAME, HOST_NAME, VERSION_FULL FROM V$INSTANCE')
        inst = cursor.fetchone()
        print(f'Instance: {inst[0]} on {inst[1]}, Version: {inst[2]}')
        
        # RAC instances (GV$ view)
        try:
            cursor.execute('SELECT INST_ID, INSTANCE_NAME, HOST_NAME, STATUS FROM GV$INSTANCE')
            print('RAC Instances:')
            for r in cursor.fetchall():
                print(f'  - Node {r[0]}: {r[1]} on {r[2]} ({r[3]})')
        except Exception as e:
            print(f'GV$INSTANCE: {str(e)[:40]}')
        
        # ASM from +ASM instance
        try:
            cursor.execute('SELECT NAME, TOTAL_MB, FREE_MB, STATE, TYPE FROM V$ASM_DISKGROUP')
            dgs = cursor.fetchall()
            if dgs:
                print('ASM Diskgroups:')
                for dg in dgs:
                    print(f'  - {dg[0]}: {dg[1]/1024:.1f}GB total, {dg[2]/1024:.1f}GB free, {dg[3]}, {dg[4]}')
        except Exception as e:
            print(f'V$ASM_DISKGROUP: {str(e)[:40]}')
        
        conn.close()
        print('SUCCESS!')
        break
    except Exception as e:
        print(f'FAILED: {str(e)[:80]}')

print("\n=== Test Complete ===")
