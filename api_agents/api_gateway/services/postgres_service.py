
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..models.sql_models import Base

class PostgresService:
    _instance = None

    def __init__(self):
        # Default credentials from docker run command if not in env
        user = os.getenv("POSTGRES_USER", "admin")
        password = os.getenv("POSTGRES_PASSWORD", "nexi2024")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "nexi_auth_db")

        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        print(f"[PostgresService] Creating tables on {self.database_url}...")
        try:
            Base.metadata.create_all(bind=self.engine)
            print("[PostgresService] Tables created.")
        except Exception as e:
            print(f"[PostgresService] ERROR creating tables: {e}")
            raise e

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PostgresService()
        return cls._instance

    def get_db(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

def get_postgres_service() -> PostgresService:
    return PostgresService.get_instance()
