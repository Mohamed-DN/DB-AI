import subprocess
import sys

with open("error_log_graph.txt", "w", encoding="utf-8") as f:
    subprocess.run([sys.executable, "-m", "api_agents.workers.AIAssistant.main"], stdout=f, stderr=f)
