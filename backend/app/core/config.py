"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Security
    TRADE_MASTER_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Delta Exchange
    DELTA_SANDBOX_URL: str = "https://api-sandbox.delta.exchange/v2"
    DELTA_LIVE_URL: str = "https://api.delta.exchange/v2"
    DELTA_WS_SANDBOX_URL: str = "wss://api-sandbox.delta.exchange/v2"
    DELTA_WS_LIVE_URL: str = "wss://api.delta.exchange/v2"
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Worker
    WORKER_CONCURRENCY: int = 4
    WORKER_HEARTBEAT_INTERVAL: int = 30
    
    # Safety
    GLOBAL_KILL_SWITCH: bool = False
    MAX_DRAWDOWN_PERCENT: float = 20.0
    MAX_POSITION_SIZE: float = 100000.0
    
    # Logging
    LOG_DIR: str = "./logs"
    LOG_MAX_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: int = 5
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def delta_base_url(self) -> str:
        """Get Delta Exchange base URL based on environment."""
        # This will be determined per profile
        return self.DELTA_LIVE_URL
    
    @property
    def delta_ws_url(self) -> str:
        """Get Delta Exchange WebSocket URL based on environment."""
        # This will be determined per profile
        return self.DELTA_WS_LIVE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

