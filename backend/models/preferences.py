"""
Pydantic models for user travel preferences (Pipeline Stage 5).
"""
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    trip_duration_days: int = 3  # 1-14
    number_of_travelers: int = 2  # 1-10+
    traveling_with: str = "partner"  # "solo" | "partner" | "family" | "friends"
    month_of_travel: str = ""  # "January" - "December"
    total_budget: float = 0.0  # In user's local currency
    budget_currency: str = "INR"  # "INR", "USD", "EUR", etc.
    travel_styles: list[str] = Field(default_factory=list)  # ["adventure", "relaxation", "culture", ...]
    dietary_preferences: list[str] = Field(default_factory=list)  # ["vegetarian", "halal", "none", ...]
    accommodation_tier: str = "mid-range"  # "budget" | "mid-range" | "luxury" | "ultra-luxury"
    must_include_places: list[str] = Field(default_factory=list)  # From bucket list selection
    additional_notes: str = ""  # Free text special requests
    home_city: str = "Mumbai"  # For flight routing
    home_country: str = "India"  # For visa requirements
    
    # Optional fields for re-plan feature (override month_of_travel + trip_duration_days)
    start_date: str | None = None  # e.g., "2026-03-07" (ISO format)
    end_date: str | None = None  # e.g., "2026-03-14"
