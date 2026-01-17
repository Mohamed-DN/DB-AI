import sys
import os
sys.path.append(os.getcwd())
from api_agents.workers.AIAssistant.main import tools

print("Available Tools:")
for t in tools:
    print(f"- {t.name}: {t.description[:50]}...")
