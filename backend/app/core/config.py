"""
Helpuvio Backend Configuration
Loads environment variables and provides app settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/helpuvio"
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    # JWT Authentication
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Paystack
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""
    
    # File Storage (R2/S3)
    R2_ENDPOINT: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: str = "helpuvio-datasets"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Email
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@helpuvio.com"

    # SMTP Email Verification
    SMTP_VERIFY_FROM_EMAIL: str = "verify@helpuvio.com"
    SMTP_VERIFY_DOMAIN: str = "helpuvio.com"
    SMTP_VERIFY_TIMEOUT: int = 30
    SMTP_VERIFY_MAX_WORKERS: int = 3
    SMTP_VERIFY_MAX_CONCURRENT: int = 10
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Admin defaults
    ADMIN_DEFAULT_EMAIL: str = "admin@helpuvio.com"
    ADMIN_DEFAULT_PASSWORD: str = "changeme123"
    
    # Pricing (in cents/kobo)
    # Phone only datasets are cheaper
    PHONE_ONLY_PRICE_MULTIPLIER: float = 1.0
    # Email + Phone datasets are more expensive
    EMAIL_AND_PHONE_PRICE_MULTIPLIER: float = 2.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
