import os
import secrets
from pydantic_settings import BaseSettings  # type: ignore
from pydantic import ConfigDict, field_validator  # type: ignore

class Settings(BaseSettings):
    PROJECT_NAME: str = "HARSH TRADER AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment & Logs
    ENVIRONMENT: str = "development"  # development | production | test
    LOG_LEVEL: str = "INFO"
    
    # Database & Redis
    DATABASE_URL: str = "sqlite:///./harshtrader.db"  # Fallback to SQLite for easy local dev if Postgres unavailable
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    
    # Provider selection
    MARKET_DATA_PROVIDER: str = "MOCK"  # MOCK | YFINANCE | LIVE
    MARKET_DATA_API_KEY: str = ""
    
    # WhatsApp
    WHATSAPP_PROVIDER: str = "MOCK"  # MOCK | OFFICIAL
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_TARGET_PHONE: str = ""
    WHATSAPP_CHANNEL_URL: str = "https://whatsapp.com/channel/0029VbBGFGjBPzjaNPem3p0J"
    
    # Security
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Thresholds
    MIN_DATA_QUALITY_SCORE: float = 85.0
    DEFAULT_INTRADAY_MIN_RR: float = 2.0
    DEFAULT_SWING_MIN_RR: float = 2.0
    
    # Live Market Data Ingestion & Polling Configuration
    LIVE_DATA_MODE: str = "API"  # API | SCRAPER | HYBRID
    LIVE_COLLECTOR_ENABLED: bool = False
    LIVE_MARKET_POLL_INTERVAL_SECONDS: int = 5
    MARKET_DATA_TIMEOUT_SECONDS: float = 10.0
    MARKET_DATA_MAX_RETRIES: int = 3
    MARKET_DATA_STALE_AFTER_SECONDS: int = 15
    SCRAPER_ENABLED: bool = False
    SCRAPER_POLL_INTERVAL_SECONDS: int = 10
    
    # Scanner & Scheduler Configuration
    SCANNER_ENABLED: bool = False
    POSITION_MONITOR_ENABLED: bool = False
    SCANNER_INTERVAL_MINUTES: int = 15
    POSITION_MONITOR_INTERVAL_SECONDS: int = 30
    MIN_SIGNAL_CONFIDENCE: float = 80.0
    MARKET_TIMEZONE: str = "Asia/Kolkata"
    MARKET_OPEN: str = "09:15"
    MARKET_CLOSE: str = "15:30"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

    @field_validator("JWT_SECRET", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        if not v or v == "super-secret-jwt-key-harsh-trader-ai-2026":
            # For development, generate a safe volatile secret if not set
            env = os.environ.get("ENVIRONMENT", "development")
            if env == "production":
                raise ValueError("JWT_SECRET must be explicitly set in production environment!")
            return secrets.token_hex(32)
        return v

settings = Settings()
