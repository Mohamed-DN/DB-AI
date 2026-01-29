
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from casbin_sqlalchemy_adapter import CasbinRule

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role})>"

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSON, default={})
    last_login = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="profile")

# CasbinRule is imported from the adapter, but typically we don't need to subclass it specifically 
# unless we want to customize the table name, which defaults to 'casbin_rule'.
