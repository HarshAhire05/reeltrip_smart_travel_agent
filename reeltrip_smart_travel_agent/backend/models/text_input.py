"""
Pydantic models for text-based travel intent input (Alternative to video pipeline).
"""
from pydantic import BaseModel, Field
from typing import Literal


class TextInputRequest(BaseModel):
    """Request body for POST /api/v1/process-text"""
    text: str = Field(..., min_length=3, description="User's free-text travel intent")
    session_id: str | None = None  # Optional; will be generated if not provided


class DestinationInfo(BaseModel):
    """Extracted destination information from natural language"""
    primary: str = ""  # Main destination city/country
    country: str = ""
    region: str = ""  # Geographic region (e.g., "Middle East", "Southeast Asia")
    secondary: list[str] = Field(default_factory=list)  # Additional destinations mentioned


class IntentClassification(BaseModel):
    """Result of analyzing user's travel intent from natural language"""
    intent_type: Literal[
        "SPECIFIC_DESTINATION",      # User mentions a clear place (e.g., "Dubai")
        "EXPERIENCE_BASED",           # User describes an experience (e.g., "beach vacation")
        "THEME_BASED",                # User mentions a theme (e.g., "adventure travel")
        "MULTI_DESTINATION",          # User mentions multiple cities/countries
        "NON_TRAVEL"                  # Input is not travel-related
    ]
    destination: DestinationInfo = Field(default_factory=DestinationInfo)
    travel_theme: str = ""  # e.g., "luxury", "adventure", "cultural", "beach", "food"
    confidence: Literal["high", "medium", "low"] = "medium"
    needs_clarification: bool = False
    clarification_options: list[str] = Field(default_factory=list)  # Suggested destinations if vague
    clarification_message: str = ""  # Message to show user
    error_message: str = ""  # Error message if NON_TRAVEL


class ClarificationOption(BaseModel):
    """A suggested destination when user's intent is vague"""
    destination_name: str
    country: str
    region: str
    description: str  # Brief 1-line description
    image_url: str | None = None  # Optional destination image


class TextProcessingResult(BaseModel):
    """Final result from text-based processing pipeline - matches LocationResult structure"""
    session_id: str
    input_mode: Literal["text"] = "text"
    raw_text_input: str
    intent_classification: IntentClassification
    
    # These fields mirror LocationResult to ensure compatibility with existing flow
    primary_destination: dict = Field(default_factory=dict)  # {"country": "", "region": "", "city": ""}
    primary_country: str = ""
    primary_region: str = ""
    primary_city: str = ""
    city_latitude: float | None = None
    city_longitude: float | None = None
    
    highlights: list[dict] = Field(default_factory=list)  # List of PlaceHighlight dicts
    highlights_summary: str = ""  # 3-4 line excitement paragraph about destination
    
    # Additional metadata
    processed_at: str = ""
    travel_theme: str = ""
    needs_clarification: bool = False
    clarification_options: list[ClarificationOption] = Field(default_factory=list)


class TextHighlightPlace(BaseModel):
    """
    Place information for text-based highlights.
    Mirrors PlaceHighlight structure from location.py
    """
    place_name: str
    place_id: str = ""
    photo_url: str | None = None
    latitude: float = 0.0
    longitude: float = 0.0
    formatted_address: str = ""
    rating: float | None = None
    description: str = ""
    vibe_tags: list[str] = Field(default_factory=list)  # Exactly 3 tags
    signature_experiences: list[str] = Field(default_factory=list)  # 2-3 experiences
    best_time_to_visit: str = ""
    know_more: str = ""
    estimated_visit_duration: str = ""
    estimated_cost_usd: float = 0.0
    google_maps_url: str = ""
    source: str = "text_generated"  # Always "text_generated" for text mode
    category: str = ""  # "landmark", "nature", "food", "adventure", "cultural", etc.


class DestinationEnrichmentResult(BaseModel):
    """Result from enriching a destination with places and highlights"""
    destination_name: str
    country: str
    region: str
    city_coordinates: dict = Field(default_factory=dict)  # {"latitude": 0.0, "longitude": 0.0}
    places: list[TextHighlightPlace] = Field(default_factory=list)
    highlights_summary: str = ""
    travel_theme: str = ""
