"""
The Watcher - Real-Time Log Forensics Agent
Monitors database logs via Docker, maintains separate buffers for each container,
and captures "context" (history) when critical errors occur.
"""

import sys
import os
import time
import subprocess
import threading
import re
import json
from collections import deque
from datetime import datetime

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Orchestrator.src.mongo_proxy import MongoProxy

class LogStreamer(threading.Thread):
    """Thread to tail a single container's log and detect errors"""
    
    def __init__(self, container_name, log_path, mongo_proxy):
        super().__init__()
        self.container_name = container_name
        self.log_path = log_path
        self.mongo = mongo_proxy
        self.running = True
        self.buffer = deque(maxlen=100) # Sliding window of last 100 lines
        
        # Regex patterns for critical DB errors
        self.patterns = [
            r"ORA-\d+",           # Oracle Errors
            r"TNS-\d+",           # Oracle Network
            r"FATAL",             # Generic Fatal
            r"PANIC",             # Postgres Panic
            r"Corrupt",           # Corruption
            r"Deadlock"           # Deadlocks
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def run(self):
        print(f"   Update: Started Watcher on {self.container_name} ({self.log_path})")
        
        # Determine command: Docker Exec Tail
        # Adjust command based on container type/OS if needed
        cmd = ["docker", "exec", "-t", self.container_name, "tail", "-f", self.log_path]
        
        try:
            # Popen with pipe to read stdout line by line
            # bufsize=1 means line buffered
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)
            
            while self.running:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        print(f"❌ Stream ended for {self.container_name}")
                        break
                    continue
                
                line = line.strip()
                if not line: continue
                
                # Add to buffer
                self.buffer.append(line)
                
                # Analyze
                self.analyze_line(line)
                
        except Exception as e:
            print(f"❌ Error streaming {self.container_name}: {e}")

    def analyze_line(self, line):
        for pattern in self.compiled_patterns:
            if pattern.search(line):
                print(f"🔥 DETECTED in {self.container_name}: {line}")
                self.trigger_forensic_alert(line)
                break # Only fire once per line

    def trigger_forensic_alert(self, error_line):
        """Create a detailed forensic alert with context"""
        context = list(self.buffer)
        
        alert = {
            "severity": "CRITICAL",
            "state": "CRITICAL",
            "type": "DB_FORENSICS",
            "db_unique_name": self.container_name.upper(), # Mapping assumption
            "host_name": self.container_name,
            "service": f"Watcher-{self.container_name}",
            "message": f"Critical Log Event: {error_line[:100]}",
            "full_error": error_line,
            "forensic_context": context, # The secret sauce: sending the history
            "timestamp": "NOW",
            "processed": False
        }
        
        # Insert into MongoDB
        self.mongo.insert_alert(alert)
        print(f"    📤 Forensic Data pushed for {self.container_name}")


class TheWatcher:
    def __init__(self):
        self.mongo = MongoProxy()
        self.streams = {} # container_name -> LogStreamer
        
        # Configuration: Define where to look for logs in different images
        self.log_locations = {
            "oracle": "/opt/oracle/diag/rdbms/*/*/trace/alert_*.log", # Wildcard handling needed
            "postgres": "/var/lib/postgresql/data/log/*.log",
            "mongo": "/var/log/mongodb/mongod.log"
        }

    def discover_targets(self):
        """Find active DB containers and start streams"""
        # For prototype simplicity: Hardcode or simple scan
        # Real implementation: Query Inventory or Docker labels
        
        targets = []
        try:
            cmd = ["docker", "ps", "--format", "{{.Names}}|{{.Image}}"]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            for line in output.split('\n'):
                if not line: continue
                name, image = line.split('|')
                
                log_file = None
                
                # Heuristic for Log Path
                if "oracle" in image or "oracle" in name:
                    # In standard Oracle containers, finding the exact alert log path is tricky without exec
                    # For demo, we'll try a common path or rely on stdout if configured?
                    # Ideally, Oracle logs to stdout in Docker too.
                    # If Docker logs driver is json-file, we can tail docker logs f <container>
                    # Let's switch to `docker logs -f` which is more universal!
                    pass 
                
                # Actually, best practice for Docker is reading `docker logs`.
                # File tailing is only for internal files not sending to stdout.
                # Let's assume we want to tail the DOCKER STDOUT/STDERR flow as it contains the logs.
                targets.append(name)
                
        except Exception as e:
            print(f"Discovery Error: {e}")
            
        return targets

    def run(self):
        print("👁️ 'The Watcher' started - Deep Log Forensics")
        
        # Hardcoded verification target for the demo
        target = "nexi-oracle-cairo-primary" 
        
        # For `docker logs -f`, we simply spawn the thread.
        # Note: `docker logs` combines stdout/stderr.
        
        if target not in self.streams:
            # Create a streamer that uses `docker logs -f`
            # This works for generic containers compliant with 12-factor apps
            streamer = LogStreamer(target, "STD", self.mongo)
            
            # Override run method logic slightly for docker logs
            # Actually LogStreamer uses `docker exec tail`.
            # Let's change LogStreamer to use `docker logs -f` for universality
            
            streamer.start()
            self.streams[target] = streamer
            
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("Watcher stopping...")

# Redefine Streamer for 'docker logs' to be robust
class DockerLogStreamer(LogStreamer):
    def run(self):
        print(f"   👁️ Watching logs for {self.container_name}")
        cmd = ["docker", "logs", "-f", "--tail", "10", self.container_name]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)
            
            while self.running:
                # Docker logs output might drift to stderr for logs
                # We need to read both? complex. Let's read stdout for now.
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                    
                line = line.strip()
                if not line: continue
                
                self.buffer.append(line)
                self.analyze_line(line)
        except Exception as e:
            print(f"Stream Error: {e}")

if __name__ == "__main__":
    watcher = TheWatcher()
    
    # Manually attach the specialized Docker Streamer
    # In a full dynamic version, this would be in the discovery loop
    target_name = "nexi-oracle-cairo-primary"
    streamer = DockerLogStreamer(target_name, "DOCKER_API", watcher.mongo)
    streamer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
