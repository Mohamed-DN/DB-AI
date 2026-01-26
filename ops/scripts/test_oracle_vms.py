"""
Test connessione Oracle alle VM VirtualBox
==========================================
Testa la connettività Oracle alle VM di sviluppo.

Usage:
    python test_oracle_vms.py
"""
import socket
import sys

# Configurazione VM
VMS = [
    {
        "name": "Oracle_VM1",
        "ssh_port": 2200,
        "oracle_port": 2521,  # Cambia se diverso nel port forwarding
        "checkmk_port": 2556
    },
    {
        "name": "Oracle_VM2", 
        "ssh_port": 2201,
        "oracle_port": 2522,
        "checkmk_port": 2557
    }
]

def test_port(host: str, port: int, timeout: int = 3) -> bool:
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("🔍 Testing VirtualBox Oracle VMs")
    print("=" * 50)
    
    for vm in VMS:
        print(f"\n📡 {vm['name']}")
        print("-" * 30)
        
        # Test SSH
        ssh_open = test_port("127.0.0.1", vm["ssh_port"])
        status = "✅ OPEN" if ssh_open else "❌ CLOSED"
        print(f"  SSH (:{vm['ssh_port']}): {status}")
        
        # Test Oracle
        ora_open = test_port("127.0.0.1", vm["oracle_port"])
        status = "✅ OPEN" if ora_open else "❌ CLOSED (check VirtualBox port forwarding)"
        print(f"  Oracle (:{vm['oracle_port']}): {status}")
        
        # Test CheckMK Agent
        cmk_open = test_port("127.0.0.1", vm["checkmk_port"])
        status = "✅ OPEN" if cmk_open else "⚠️ NOT FORWARDED"
        print(f"  CheckMK (:{vm['checkmk_port']}): {status}")
    
    print("\n" + "=" * 50)
    print("📋 ISTRUZIONI:")
    print("""
Se le porte Oracle sono CLOSED:
1. Apri VirtualBox
2. Seleziona la VM -> Settings -> Network -> Advanced -> Port Forwarding
3. Aggiungi regola:
   - Name: Oracle
   - Protocol: TCP
   - Host Port: 2521 (o 2522 per VM2)
   - Guest Port: 1521
4. Riavvia la VM
""")
    
    # Test Oracle connection if port is open
    for vm in VMS:
        if test_port("127.0.0.1", vm["oracle_port"]):
            print(f"\n🔧 Per testare Oracle su {vm['name']}:")
            print(f"   python ops/scripts/oem_scraper.py --oracle-host 127.0.0.1 --oracle-port {vm['oracle_port']} --oracle-sid ORCL --oracle-user system --oracle-pass root --once")

if __name__ == "__main__":
    main()
