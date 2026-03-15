"""
Pydantic models for location validation and highlights (Pipeline Stages 3-4).
"""
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0


class PrimaryDestination(BaseModel):
    country: str = ""
    region: str = ""
    city: str = ""


class ValidatedPlace(BaseModel):
    name: str
    place_id: str = ""
    formatted_address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    rating: float | None = None
    total_ratings: int | None = None
    price_level: int | None = None  # 0-4 (Google's scale)
    photo_url: str | None = None
    photo_reference: str | None = None
    types: list[str] = Field(default_factory=list)
    website: str | None = None
    opening_hours: dict | None = None
    source: str = "video_detected"  # "video_detected" | "nearby_attraction" | "nearby_restaurant" | "nearby_hotel"


class PlaceHighlight(BaseModel):
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
    source: str = "video_detected"  # "video_detected" | "nearby_attraction" | etc.


class LocationResult(BaseModel):
    primary_destination: PrimaryDestination = Field(default_factory=PrimaryDestination)
    primary_country: str = ""
    primary_region: str = ""
    primary_city: str = ""
    city_latitude: float | None = None
    city_longitude: float | None = None
    validated_places: list[ValidatedPlace] = Field(default_factory=list)
    nearby_attractions: list[ValidatedPlace] = Field(default_factory=list)
    nearby_restaurants: list[ValidatedPlace] = Field(default_factory=list)
    nearby_hotels: list[ValidatedPlace] = Field(default_factory=list)
    highlights: list[PlaceHighlight] = Field(default_factory=list)
    city_coordinates: Coordinates = Field(default_factory=Coordinates)
    processed_at: str = ""
