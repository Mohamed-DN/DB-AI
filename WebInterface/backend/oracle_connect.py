"""
Oracle Interactive SQL Console
Usage: python oracle_connect.py <host> <port> <service> <user> <password>
"""
import sys
import os

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 6:
    print("Usage: python oracle_connect.py <host> <port> <service> <user> <password>")
    sys.exit(1)

host = sys.argv[1]
port = sys.argv[2]
service = sys.argv[3]
user = sys.argv[4]
password = sys.argv[5]

try:
    import oracledb
    
    dsn = f"{host}:{port}/{service}"
    print(f"\n🔌 Connecting to Oracle: {dsn}")
    print(f"   User: {user}")
    
    # Determine if SYSDBA mode needed
    mode = oracledb.AUTH_MODE_SYSDBA if user.lower() == 'sys' else 0
    
    conn = oracledb.connect(user=user, password=password, dsn=dsn, mode=mode)
    cursor = conn.cursor()
    
    # Get connection info
    cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
    banner = cursor.fetchone()[0]
    cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CON_NAME') FROM dual")
    container = cursor.fetchone()[0]
    cursor.execute("SELECT USER FROM dual")
    current_user = cursor.fetchone()[0]
    
    print(f"\n✅ CONNECTED!")
    print(f"   Oracle: {banner}")
    print(f"   Container: {container}")
    print(f"   User: {current_user}")
    print("\n" + "="*60)
    print("NEXI AI - Oracle Interactive SQL Console")
    print("Type SQL commands (end with ;) or 'exit' to quit")
    print("Special commands: tables, users, pdbs, sessions")
    print("="*60 + "\n")
    
    # Interactive SQL loop
    while True:
        try:
            sql = input(f"{container}> ").strip()
            
            if not sql:
                continue
                
            if sql.lower() == 'exit' or sql.lower() == 'quit':
                print("Goodbye!")
                break
            
            # Special commands
            if sql.lower() == 'tables':
                sql = "SELECT table_name FROM user_tables ORDER BY table_name"
            elif sql.lower() == 'users':
                sql = "SELECT username, account_status FROM dba_users ORDER BY username"
            elif sql.lower() == 'pdbs':
                sql = "SELECT name, open_mode FROM v$pdbs"
            elif sql.lower() == 'sessions':
                sql = "SELECT sid, serial#, username, status FROM v$session WHERE username IS NOT NULL"
            elif sql.lower() == 'help':
                print("\nSpecial commands:")
                print("  tables   - List user tables")
                print("  users    - List database users")
                print("  pdbs     - List pluggable databases")
                print("  sessions - List active sessions")
                print("  exit     - Close connection\n")
                continue
            
            # Remove trailing semicolon for Python execution
            if sql.endswith(';'):
                sql = sql[:-1]
            
            cursor.execute(sql)
            
            # Check if it's a SELECT query
            if cursor.description:
                # Print column headers
                columns = [col[0] for col in cursor.description]
                print("-" * 80)
                print(" | ".join(f"{col[:15]:15}" for col in columns))
                print("-" * 80)
                
                # Print rows
                rows = cursor.fetchall()
                for row in rows:
                    print(" | ".join(f"{str(val)[:15]:15}" if val else "NULL           " for val in row))
                print(f"\n{len(rows)} rows returned.\n")
            else:
                conn.commit()
                print(f"Statement executed. Rows affected: {cursor.rowcount}\n")
                
        except oracledb.DatabaseError as e:
            print(f"❌ Oracle Error: {e}\n")
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    cursor.close()
    conn.close()
    
except ImportError:
    print("❌ oracledb module not installed!")
    print("   Run: pip install oracledb")
    input("\nPress Enter to close...")
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    input("\nPress Enter to close...")
