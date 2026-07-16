"""
Authentication Service
Handles JWT token generation, password hashing, and user validation.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient

from ..models.user import (
    UserInDB, UserCreate, UserResponse, UserRole, 
    Token, TokenData, get_default_permissions
)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pippopippo_1234")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, mongo_uri: str = None, db_name: str = None):
        # Prioritize MONGODB_URI from environment, then build from components
        if mongo_uri:
            self.mongo_uri = mongo_uri
        else:
            self.mongo_uri = os.getenv("MONGODB_URI")
            if not self.mongo_uri:
                # Fallback: build from individual components
                user = os.getenv("MONGO_USERNAME", "admin")
                password = os.getenv("MONGO_PASSWORD", "pippopippo_1234")
                host = os.getenv("MONGODB_HOST", "localhost")
                port = os.getenv("MONGODB_PORT", "28017")
                self.mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
            
        self.db_name = db_name or os.getenv("MONGODB_DB", "m-dn_cmdb_v2")
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None
    
    async def _get_db(self):
        """Get MongoDB database connection"""
        if self._client is None:
            self._client = AsyncIOMotorClient(self.mongo_uri)
            self._db = self._client[self.db_name]
        return self._db
    
    async def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    # Password methods
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt directly"""
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt directly"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Token methods
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None:
                return None
            return TokenData(username=username, role=UserRole(role) if role else None)
        except JWTError:
            return None
    
    # User methods
    async def get_user(self, username: str) -> Optional[UserInDB]:
        """Get a user by username from MongoDB"""
        db = await self._get_db()
        user_doc = await db.users.find_one({"username": username})
        if user_doc:
            user_doc.pop("_id", None)
            return UserInDB(**user_doc)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get a user by email from MongoDB"""
        db = await self._get_db()
        user_doc = await db.users.find_one({"email": email})
        if user_doc:
            user_doc.pop("_id", None)
            return UserInDB(**user_doc)
        return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with username and password"""
        user = await self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        
        # Update last login
        db = await self._get_db()
        await db.users.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return user
    
    async def create_user(self, user_create: UserCreate) -> UserResponse:
        """Create a new user in MongoDB"""
        db = await self._get_db()
        
        # Check if user exists
        existing = await db.users.find_one({
            "$or": [
                {"username": user_create.username},
                {"email": user_create.email} if user_create.email else {"_id": None}
            ]
        })
        if existing:
            raise ValueError("Username or email already exists")
        
        # Create user document
        user_in_db = UserInDB(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            databases_scope=user_create.databases_scope,
            is_active=user_create.is_active,
            password_hash=self.get_password_hash(user_create.password),
            created_at=datetime.utcnow()
        )
        
        await db.users.insert_one(user_in_db.model_dump())
        
        return UserResponse(
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            role=user_in_db.role,
            databases_scope=user_in_db.databases_scope,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at,
            last_login=None,
            permissions=get_default_permissions(user_in_db.role)
        )
    
    async def update_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        db = await self._get_db()
        result = await db.users.update_one(
            {"username": username},
            {"$set": {"password_hash": self.get_password_hash(new_password)}}
        )
        return result.modified_count > 0
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """List all users"""
        db = await self._get_db()
        cursor = db.users.find({}).skip(skip).limit(limit)
        users = []
        async for doc in cursor:
            doc.pop("_id", None)
            doc.pop("password_hash", None)
            user = UserInDB(**{**doc, "password_hash": ""})
            users.append(UserResponse(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                databases_scope=user.databases_scope,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                permissions=get_default_permissions(user.role)
            ))
        return users
    
    async def delete_user(self, username: str) -> bool:
        """Delete a user"""
        db = await self._get_db()
        result = await db.users.delete_one({"username": username})
        return result.deleted_count > 0
    
    async def ensure_admin_exists(self):
        """Ensure at least one admin user exists (for initial setup)"""
        db = await self._get_db()
        admin = await db.users.find_one({"role": "admin"})
        if not admin:
            # Create default admin
            await self.create_user(UserCreate(
                username="admin",
                email="admin@m-dn.lab",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                password="M-DNAdmin2024!",  # Should be changed immediately
                databases_scope=["*"],
                is_active=True
            ))
            print("⚡ Created default admin user (username: admin, password: M-DNAdmin2024!)")
            print("⚠️  Please change the default password immediately!")


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get singleton AuthService instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
