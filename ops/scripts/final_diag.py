
import os
import sys
from api_agents.api_gateway.config import ALLOWED_ORIGINS

print(f"DEBUG: MONGODB_PORT: {os.environ.get('MONGODB_PORT')}")
from api_agents.api_gateway.services.mongo_service import get_mongo_service
m = get_mongo_service()
print(f"DEBUG: SERVICE_URI: {m.connection_string}")
