
import oracledb
import sys

def debug_oracle():
    print("🔌 Debugging Oracle Connection to 192.168.56.101...")
    
    ip = "192.168.56.101"
    port = 1521
    services = ["cdbrac", "pdb1", "ORCL", "XE"]
    users = [("sys", "root", oracledb.AUTH_MODE_SYSDBA), ("c##aiauto", "root", oracledb.DEFAULT_AUTH)]
    
    for user, pwd, mode in users:
        print(f"\n👤 User: {user}")
        for service in services:
            dsn = f"{ip}:{port}/{service}"
            print(f"   Trying {dsn}...", end="")
            try:
                conn = oracledb.connect(
                    user=user,
                    password=pwd,
                    dsn=dsn,
                    mode=mode
                )
                print(" ✅ SUCCESS!")
                
                cursor = conn.cursor()
                cursor.execute("SELECT NAME, DB_UNIQUE_NAME FROM V$DATABASE")
                print(f"   Database: {cursor.fetchone()}")
                
                cursor.execute("SELECT INSTANCE_NAME, HOST_NAME FROM V$INSTANCE")
                print(f"   Instance: {cursor.fetchone()}")
                
                conn.close()
                return # Stop on first success
            except Exception as e:
                print(f" ❌ Failed: {e}")

if __name__ == "__main__":
    debug_oracle()
