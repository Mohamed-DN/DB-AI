import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
print(f"Path: {sys.path}")

print("Testing Orchestrator Import...")
try:
    from orchestrator.core.mongo_proxy import MongoProxy
    print("Objection! MongoProxy Imported Successfully!")
except Exception as e:
    print(f"CRITICAL: MongoProxy Import Failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting LLM Config Import...")
try:
    from llm.config.llm_config import LLM_MODELS
    print("Objection! LLM Config Imported Successfully!")
except Exception as e:
    print(f"CRITICAL: LLM Config Import Failed: {e}")
    import traceback
    traceback.print_exc()
