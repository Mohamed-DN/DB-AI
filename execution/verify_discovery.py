from pymongo import MongoClient
try:
    c = MongoClient('localhost', 28017, username='admin', password='nexi2024')
    db = c['nexi_cmdb_v2']
    print(f'Total DBs: {db.inventory_databases.count_documents({})}')
    
    oracles = list(db.inventory_databases.find({'identity.family': 'ORACLE'}))
    print(f'Oracle DBs found: {len(oracles)}')
    
    for o in oracles:
        ident = o.get('identity', {})
        conn = o.get('connection', {})
        gw = o.get('gateway_ref') or conn.get('gateway_ref')
        print(f"- {ident.get('db_unique_name')} | Engine: {ident.get('engine')} | Gateway: {gw}")
except Exception as e:
    print(f"Error: {e}")
