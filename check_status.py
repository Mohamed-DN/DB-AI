from Orchestrator.src.mongo_proxy import MongoProxy
try:
    m = MongoProxy()
    print("Attempting updateOne...")
    res = m.execute_eval("db.system_config.updateOne({key: 'global_status'}, {$set: {value: 'PAUSED'}}, {upsert: true})")
    print(f"Result: {res}")
    
    print("Verifying...")
    print(m.execute_eval("db.system_config.findOne({key: 'global_status'})"))
except Exception as e:
    print(f"Error: {e}")
