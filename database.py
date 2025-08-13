from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Your MySQL connection string
SQL_DB_URL = "mysql+pymysql://root:dial%40mas123@172.12.10.22/hrms_db?charset=utf8mb4"



# SQLAlchemy engine with echo for debugging
engine = create_engine(SQL_DB_URL, echo=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for potential future models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()