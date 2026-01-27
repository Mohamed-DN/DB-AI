import sys
import os
import time

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path to allow importing api_agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api_agents.workers.Watcher.watcher_agent import TheWatcher, DockerLogStreamer

def main():
    print("🚀 Watcher Agent Initializing...")
    try:
        watcher = TheWatcher()

        # Manually attach the specialized Docker Streamer
        # Allow configuration via environment variable for production flexibility
        target_name = os.getenv("WATCHER_TARGET", "nexi-oracle-cairo-primary")
        print(f"🎯 Target: {target_name}")

        streamer = DockerLogStreamer(target_name, "DOCKER_API", watcher.mongo)
        streamer.start()

        print("✅ Watcher Agent Running")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
        # Allow exit on critical error
        sys.exit(1)

if __name__ == "__main__":
    main()
