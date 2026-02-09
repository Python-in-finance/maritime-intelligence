from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Maritime Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key"
    DATABASE_URL: str = "sqlite:///./maritime.db"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://me2lef2kyg5aq.ok.kimi.link"]
    AISSTREAM_API_KEY: str = "d16c1973c50998054d62f9e223a77b8cb1aec01a"

settings = Settings()
