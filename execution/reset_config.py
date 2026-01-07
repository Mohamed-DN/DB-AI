import sys
import os
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

mongo = MongoProxy()
print("Resetting config...")
mongo.execute_eval("db.system_config.updateOne({key: 'scout_interval'}, {$set: {value: 60}}, {upsert: true})")
mongo.execute_eval("db.system_config.updateOne({key: 'check_interval'}, {$set: {value: 30}}, {upsert: true})")
print("Config reset to 60s/30s")
