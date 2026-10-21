"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Literal


class ProcessRequest(BaseModel):
    """Request body for POST /api/v1/process"""
    url: str
    input_mode: Literal["url", "text"] = "url"  # Support for dual input mode


class PreferenceRequest(BaseModel):
    """Request body for POST /api/v1/itinerary/preferences"""
    session_id: str
    preferences: dict  # UserPreferences as dict
    selected_cities: list[str] = Field(default_factory=list)


class CustomizeRequest(BaseModel):
    """Request body for POST /api/v1/itinerary/customize"""
    session_id: str
    itinerary_id: str
    request: str  # User's customization request in natural language


class CityRequest(BaseModel):
    """Request body for city selection"""
    session_id: str
    selected_cities: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response for GET /health"""
    status: str = "ok"
    service: str = "reeltrip-api"


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str | None = None


class SessionResponse(BaseModel):
    """Response for GET /api/v1/session/{session_id}"""
    id: str
    url: str | None = None
    input_mode: Literal["url", "text"] = "url"  # Track which input mode was used
    raw_text_input: str | None = None  # Store original text input if text mode
    stage: str = "processing"
    preferences: dict | None = None
    selected_cities: list[str] = Field(default_factory=list)
    itinerary_id: str | None = None
