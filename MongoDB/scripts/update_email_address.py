
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def update_email():
    mongo = MongoProxy()
    new_email = "MOHAMED.D.N.2002@GMAIL.COM"
    print(f"Updating Global BAO email to: {new_email}")

    # Update the Master Service contact
    mongo.execute_eval(f"""
    db.business_services.updateOne(
        {{ name: 'Global Operations (Master)' }},
        {{ $set: {{ "contacts.bao.email": "{new_email}" }} }}
    )
    """)
    
    # Verify
    svc = mongo.execute_eval("db.business_services.findOne({name: 'Global Operations (Master)'})")
    print(f"✅ Verified Update: {svc.get('contacts', {}).get('bao', {}).get('email')}")

if __name__ == "__main__":
    update_email()
