import sys
import os
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

mongo = MongoProxy()
print("Resetting config...")
mongo.execute_eval("db.system_config.updateOne({key: 'scout_interval'}, {$set: {value: 60}}, {upsert: true})")
mongo.execute_eval("db.system_config.updateOne({key: 'criticalalert_interval'}, {$set: {value: 30}}, {upsert: true})")
print("Config reset: scout_interval=60, criticalalert_interval=30")
