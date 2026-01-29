
import os
import casbin
from casbin_sqlalchemy_adapter import Adapter
from .postgres_service import get_postgres_service

class CasbinService:
    _instance = None

    def __init__(self):
        pg_service = get_postgres_service()
        self.adapter = Adapter(pg_service.engine)
        
        config_path = os.path.join(os.path.dirname(__file__), "../config/rbac_model.conf")
        self.enforcer = casbin.Enforcer(config_path, self.adapter)
        
        print("[CasbinService] Enforcer initialized with Postgres Adapter")

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = CasbinService()
        return cls._instance

    def enforce(self, sub, obj, act):
        return self.enforcer.enforce(sub, obj, act)

    def add_policy(self, sub, obj, act):
        return self.enforcer.add_policy(sub, obj, act)

    def add_role_for_user(self, user, role):
        return self.enforcer.add_grouping_policy(user, role)

    def get_roles_for_user(self, user):
        return self.enforcer.get_roles_for_user(user)

def get_casbin_service() -> CasbinService:
    return CasbinService.get_instance()
