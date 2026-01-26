"""Test SYSMAN connection"""
import oracledb

configs = [
    ("sysman", "sysman123"),
    ("system", "root"),
    ("SYSMAN", "sysman123"),
]

for user, pwd in configs:
    try:
        conn = oracledb.connect(user=user, password=pwd, dsn="127.0.0.1:2521/FREEPDB1")
        print(f"✅ {user}/{pwd} - CONNECTED!")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM user_tables")
        print(f"   Tables: {cur.fetchone()[0]}")
        conn.close()
        break
    except Exception as e:
        print(f"❌ {user}/{pwd}: {str(e)[:60]}")
