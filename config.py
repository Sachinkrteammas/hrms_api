from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///hrms.db")
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "sachinkr78276438@gmail.com"
    SMTP_PASSWORD: str = "efsn ryss yjin kwgr"
    FROM_EMAIL: str = "sachinkr78276438@gmail.com"
    
    # Frontend settings
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Verification API settings
    VERIFICATION_API_BASE_URL: str = "https://api.verification.com"
    VERIFICATION_API_KEY: str = "your-api-key"
    
    # AWS S3 settings (for file uploads)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "hrms-uploads"
    
    # Redis settings (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379"
    
    # App settings
    APP_NAME: str = "HRMS API"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Database configuration
DATABASE_CONFIG = {
    "url": settings.DATABASE_URL,
    "echo": settings.DEBUG,
}

# JWT configuration
JWT_CONFIG = {
    "secret_key": settings.SECRET_KEY,
    "algorithm": settings.ALGORITHM,
    "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
}

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": settings.SMTP_SERVER,
    "smtp_port": settings.SMTP_PORT,
    "smtp_username": settings.SMTP_USERNAME,
    "smtp_password": settings.SMTP_PASSWORD,
    "from_email": settings.FROM_EMAIL,
}

# AWS configuration
AWS_CONFIG = {
    "access_key_id": settings.AWS_ACCESS_KEY_ID,
    "secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    "region": settings.AWS_REGION,
    "s3_bucket": settings.AWS_S3_BUCKET,
} 