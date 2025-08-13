from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Database configuration - using your actual database URL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:dial%40mas123@172.12.10.22/hrms_db?charset=utf8mb4"

# Create engine with additional MySQL-specific options
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=True  # Set to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 