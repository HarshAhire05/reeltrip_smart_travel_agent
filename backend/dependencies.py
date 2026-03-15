"""
FastAPI dependencies.
Provides injectable dependencies for route handlers.
"""
from config import get_settings, Settings


def get_config() -> Settings:
    """Dependency that provides the application settings."""
    return get_settings()
