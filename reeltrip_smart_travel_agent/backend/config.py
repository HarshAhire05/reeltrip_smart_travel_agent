"""
Central configuration. Every service reads from here.
Never import os.environ directly in service files.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Required
    OPENAI_API_KEY: str
    GOOGLE_PLACES_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # Recommended (with defaults so app runs without them, but degraded)
    TAVILY_API_KEY: str = ""
    EXCHANGERATE_API_KEY: str = ""

    # Optional
    INSTAGRAM_COOKIES_PATH: str = ""
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_HOME_CITY: str = "Mumbai"
    MAX_FRAME_COUNT: int = 5

    # Model configuration — CRITICAL for cost control
    VISION_MODEL: str = "gpt-4o"
    REASONING_MODEL: str = "gpt-4o"
    FAST_MODEL: str = "gpt-4o-mini"
    WHISPER_MODEL: str = "whisper-1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Feature flags — useful for development/testing
    ENABLE_CACHE: bool = True
    ENABLE_VISION: bool = True
    ENABLE_TAVILY: bool = True
    ENABLE_WEATHER: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
