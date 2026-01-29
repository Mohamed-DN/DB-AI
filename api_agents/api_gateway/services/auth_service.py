
import os
from datetime import datetime, timedelta
from typing import Optional, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.user import (
    UserCreate, UserResponse, UserRole, 
    TokenData, get_default_permissions
)
from ..models.sql_models import User, Profile
from .postgres_service import get_postgres_service
from .casbin_service import get_casbin_service

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nexi-dba-ai-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for authentication operations (PostgreSQL + Casbin)"""
    
    def __init__(self):
        self.pg_service = get_postgres_service()
        self.casbin_service = get_casbin_service()
    
    # Password methods
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def get_password_hash(self, password: str) -> str:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Token methods
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None:
                return None
            return TokenData(username=username, role=UserRole(role) if role else None)
        except JWTError:
            return None
    
    def _map_user_to_response(self, user: User, role: str = None) -> UserResponse:
        """Map SQL User model to Pydantic Response"""
        # Get role from Casbin if not provided
        if not role:
            roles = self.casbin_service.get_roles_for_user(user.username)
            role = roles[0] if roles else UserRole.VIEWER
            
        return UserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=role,
            databases_scope=["*"], # TODO: Implement DB scopes in Postgres/Casbin
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.profile.last_login if user.profile else None,
            permissions=get_default_permissions(UserRole(role))
        )

    # User methods
    def get_user(self, username: str) -> Optional[UserResponse]:
        """Get a user by username"""
        db = next(self.pg_service.get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            return self._map_user_to_response(user)
        finally:
            db.close()

    def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """Authenticate a user"""
        db = next(self.pg_service.get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            if not self.verify_password(password, user.hashed_password):
                return None
            if not user.is_active:
                return None
            
            # Update last login
            if user.profile:
                user.profile.last_login = datetime.utcnow()
                db.commit()
            
            return self._map_user_to_response(user)
        finally:
            db.close()
    
    def create_user(self, user_create: UserCreate) -> UserResponse:
        """Create a new user"""
        db = next(self.pg_service.get_db())
        try:
            # Check existing
            existing = db.query(User).filter(
                (User.username == user_create.username) | (User.email == user_create.email)
            ).first()
            if existing:
                raise ValueError("Username or email already exists")
            
            # Create User
            db_user = User(
                username=user_create.username,
                email=user_create.email,
                full_name=user_create.full_name,
                hashed_password=self.get_password_hash(user_create.password),
                is_active=user_create.is_active,
                created_at=datetime.utcnow()
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Create Profile
            profile = Profile(user_id=db_user.id)
            db.add(profile)
            db.commit()

            # Assign Role in Casbin
            self.casbin_service.add_role_for_user(db_user.username, user_create.role.value)
            
            return self._map_user_to_response(db_user, user_create.role.value)
        except IntegrityError:
            db.rollback()
            raise ValueError("Database integrity error")
        finally:
            db.close()

    def ensure_admin_exists(self, instance_id: str = None):
        """Ensure admin exists"""
        db = next(self.pg_service.get_db())
        try:
            user = db.query(User).filter(User.username == "admin").first()
            if not user:
                print("⚡ Creating default admin user (Postgres)...")
                self.create_user(UserCreate(
                    username="admin",
                    email="admin@nexi.lab",
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    password="NexiAdmin2024!",
                    is_active=True
                ))
                print("✅ Admin created!")
        finally:
            db.close()
    
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        db = next(self.pg_service.get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.hashed_password = self.get_password_hash(new_password)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        db = next(self.pg_service.get_db())
        try:
            users = db.query(User).offset(skip).limit(limit).all()
            return [self._map_user_to_response(u) for u in users]
        finally:
            db.close()
    
    def delete_user(self, username: str) -> bool:
        db = next(self.pg_service.get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            if user:
                db.delete(user)
                db.commit()
                # Remove from Casbin
                self.casbin_service.enforcer.delete_user(username)
                return True
            return False
        finally:
            db.close()

# Singleton instance
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
