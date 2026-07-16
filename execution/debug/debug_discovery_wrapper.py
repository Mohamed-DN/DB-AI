
import sys
import os
import io

# Force utf-8
sys.stdout.reconfigure(encoding='utf-8')

from api_agents.workers.discovery.discovery_agent import DiscoveryAgent

def main():
    log_file = "c:\\AI-M-DN\\M-DN_DB_AI\\discovery_agent_debug.log"
    print(f"Redirecting output to {log_file}")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        # Redirect stdout/stderr
        sys.stdout = f
        sys.stderr = f
        
        print("--- START DIAGONSTICS ---")
        try:
            agent = DiscoveryAgent()
            agent.run_once()
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
