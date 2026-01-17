"""
Shared Dependencies for API Gateway
Provides MongoProxy singleton, validators, and common utilities.
"""
import sys
import os
import re
from fastapi import HTTPException

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from orchestrator.core.mongo_proxy import MongoProxy

# =============================================================================
# Validation
# =============================================================================
SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._/\-]+$")

def validate_identifier(value: str, label: str) -> str:
    """Validate identifiers to prevent injection attacks."""
    if not value or not SAFE_IDENTIFIER_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value

# =============================================================================
# MongoProxy Singleton
# =============================================================================
_mongo_instance = None

def get_mongo() -> MongoProxy:
    """Get or create MongoProxy singleton."""
    global _mongo_instance
    if _mongo_instance is None:
        try:
            _mongo_instance = MongoProxy()
            print("[DEPS] MongoProxy initialized")
        except Exception as e:
            print(f"[DEPS] MongoProxy failed: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    return _mongo_instance

# Initialize on import
try:
    _mongo_instance = MongoProxy()
    print("[DEPS] MongoProxy connected")
except Exception as e:
    print(f"[DEPS] MongoProxy connection failed: {e}")
    _mongo_instance = None
