"""
User Models for Authentication System
Pydantic models for user management and JWT tokens.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class UserPermissions(BaseModel):
    """Granular permissions for a user"""
    can_start_stop: bool = False
    can_execute_sql: bool = False
    can_use_llm: bool = False
    can_manage_users: bool = False
    can_delete_databases: bool = False


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    databases_scope: List[str] = Field(default=["*"])  # "*" means all
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    """User model as stored in MongoDB"""
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class UserResponse(UserBase):
    """User model for API responses (no password)"""
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: UserPermissions

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Data encoded in the JWT token"""
    username: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request body"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# Default permissions based on role
def get_default_permissions(role: UserRole) -> UserPermissions:
    """Returns default permissions for a given role"""
    if role == UserRole.ADMIN:
        return UserPermissions(
            can_start_stop=True,
            can_execute_sql=True,
            can_use_llm=True,
            can_manage_users=True,
            can_delete_databases=True
        )
    elif role == UserRole.OPERATOR:
        return UserPermissions(
            can_start_stop=True,
            can_execute_sql=True,
            can_use_llm=True,
            can_manage_users=False,
            can_delete_databases=False
        )
    else:  # VIEWER
        return UserPermissions(
            can_start_stop=False,
            can_execute_sql=False,
            can_use_llm=True,  # Can chat but not execute actions
            can_manage_users=False,
            can_delete_databases=False
        )
