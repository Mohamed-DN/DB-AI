"""
Auto-discover Oracle SID by testing common variants
"""
import sys

try:
    import oracledb
except ImportError:
    print("❌ oracledb not installed")
    sys.exit(1)

TEST_SIDS = ['FREE', 'FREEPDB1', 'CDB', 'XEPDB1', 'ORCLPDB1', 'ORCL', 'XE']
VMS = [
    {'name': 'VM1', 'host': '127.0.0.1', 'port': 2521},
    {'name': 'VM2', 'host': '127.0.0.1', 'port': 2522}
]

USER = 'system'
PASSWORD = 'root'

def test_connection(host, port, sid, user, password):
    """Test Oracle connection with given SID"""
    dsn = f'{host}:{port}/{sid}'
    try:
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute("SELECT NAME, OPEN_MODE, DATABASE_ROLE FROM V$DATABASE")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return True, {"db_name": row[0], "open_mode": row[1], "role": row[2]}
    except Exception as e:
        err_str = str(e)
        if 'ORA-12514' in err_str:
            return False, "SID not found"
        elif 'ORA-01017' in err_str:
            return False, "Wrong password"
        else:
            return False, str(e)[:80]

def main():
    print("🔍 Auto-discovering Oracle SID on VirtualBox VMs...")
    print("=" * 60)
    
    discovered = {}
    
    for vm in VMS:
        print(f"\n📡 Testing {vm['name']} ({vm['host']}:{vm['port']})")
        print("-" * 40)
        
        found = False
        for sid in TEST_SIDS:
            success, info = test_connection(vm['host'], vm['port'], sid, USER, PASSWORD)
            
            if success:
                print(f"✅ SUCCESS: {sid}")
                print(f"   DB_NAME: {info['db_name']}")
                print(f"   OPEN_MODE: {info['open_mode']}")
                print(f"   ROLE: {info['role']}")
                discovered[vm['name']] = {
                    'host': vm['host'],
                    'port': vm['port'],
                    'sid': sid,
                    'info': info
                }
                found = True
                break
            else:
                print(f"❌ {sid}: {info}")
        
        if not found:
            print(f"⚠️  No working SID found for {vm['name']}")
    
    print("\n" + "=" * 60)
    if discovered:
        print("✅ Discovery Complete! Working configurations:")
        for vm_name, config in discovered.items():
            print(f"\n{vm_name}:")
            print(f"  Host: {config['host']}")
            print(f"  Port: {config['port']}")
            print(f"  SID: {config['sid']}")
            print(f"  DB Name: {config['info']['db_name']}")
        
        print("\n🔧 Update ops/scripts/seed_virtualbox_vms.py with the correct SIDs")
        return 0
    else:
        print("❌ No working Oracle connections found")
        print("   Check if Oracle listener is running on the VMs")
        return 1

if __name__ == "__main__":
    sys.exit(main())
