"""
Pydantic models for all agent outputs (Pipeline Stage 6).
"""
from pydantic import BaseModel, Field


# --- FLIGHT AGENT ---


class FlightOption(BaseModel):
    airline: str = ""
    from_airport: str = ""  # IATA code
    to_airport: str = ""  # IATA code
    departure_time: str = ""  # Approximate
    arrival_time: str = ""
    duration: str = ""
    stops: int = 0
    estimated_price: float = 0.0
    price_currency: str = "USD"
    source: str = ""  # Where the price came from


class FlightResearchOutput(BaseModel):
    flights_needed: bool = True
    route_type: str = "international"  # "international" | "domestic" | "none"
    outbound_options: list[FlightOption] = Field(default_factory=list)
    return_options: list[FlightOption] = Field(default_factory=list)
    recommended_outbound: FlightOption | None = None
    recommended_return: FlightOption | None = None
    inter_city_flights: list[FlightOption] = Field(default_factory=list)
    booking_search_url: str = ""  # Google Flights pre-filled URL


# --- HOTEL AGENT ---


class HotelOption(BaseModel):
    name: str = ""
    city: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    rating: float = 0.0
    price_per_night_estimate: float = 0.0
    currency: str = "USD"
    photo_url: str | None = None
    why_recommended: str = ""
    traveler_type_match: str = ""  # "family" | "couple" | "solo" | "friends"
    booking_search_url: str = ""
    amenities: list[str] = Field(default_factory=list)


class HotelResearchOutput(BaseModel):
    recommended_hotels: list[HotelOption] = Field(default_factory=list)  # 1 per city
    alternative_hotels: list[HotelOption] = Field(default_factory=list)  # 2-3 alternatives per city


# --- WEATHER AGENT ---


class WeatherResearchOutput(BaseModel):
    destination_city: str = ""
    travel_month: str = ""
    avg_high_celsius: float = 0.0
    avg_low_celsius: float = 0.0
    precipitation_chance: str = "low"  # "low" | "moderate" | "high"
    weather_description: str = ""  # "Warm and sunny with occasional humidity"
    warnings: list[str] = Field(default_factory=list)  # e.g., ["Extreme heat expected"]
    recommendations: list[str] = Field(default_factory=list)  # e.g., ["Schedule outdoor for morning"]
    best_time_for_outdoor: str = ""  # "early morning and evening"
    pack_suggestions: list[str] = Field(default_factory=list)  # ["sunscreen", "hat"]


# --- SAFETY AGENT ---


class SafetyResearchOutput(BaseModel):
    overall_safety_rating: str = "safe"  # "very safe" | "safe" | "moderate" | "use caution" | "avoid"
    travel_advisory_summary: str = ""
    specific_warnings: list[str] = Field(default_factory=list)
    health_advisories: list[str] = Field(default_factory=list)
    emergency_numbers: dict[str, str] = Field(default_factory=dict)  # {"police": "999", "ambulance": "998"}
    cultural_etiquette: list[str] = Field(default_factory=list)
    scam_warnings: list[str] = Field(default_factory=list)
    areas_to_avoid: list[str] = Field(default_factory=list)


# --- ACTIVITY AGENT ---


class PlannedActivity(BaseModel):
    name: str = ""
    type: str = "attraction"  # "attraction" | "experience" | "show" | "tour"
    city: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    photo_url: str | None = None
    rating: float | None = None
    suggested_day: int | None = None  # Which day this fits best
    suggested_time_slot: str = "morning"  # "morning" | "afternoon" | "evening"
    duration_minutes: int = 60
    estimated_cost_per_person: float = 0.0
    currency: str = "USD"
    booking_url: str | None = None
    description: str = ""
    tip: str | None = None
    weather_dependent: bool = False  # True for outdoor activities


class RestaurantRecommendation(BaseModel):
    name: str = ""
    cuisine: str = ""
    city: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    photo_url: str | None = None
    rating: float | None = None
    price_range: str = "$$"  # "$" to "$$$$"
    estimated_cost_per_person: float = 0.0
    currency: str = "USD"
    signature_dishes: list[str] = Field(default_factory=list)
    dietary_suitable: list[str] = Field(default_factory=list)  # ["vegetarian", "halal", etc.]
    meal_type: str = "lunch"  # "breakfast" | "lunch" | "dinner"
    booking_url: str | None = None
    google_maps_url: str = ""


class ActivityResearchOutput(BaseModel):
    planned_activities: list[PlannedActivity] = Field(default_factory=list)
    restaurant_recommendations: list[RestaurantRecommendation] = Field(default_factory=list)


# --- TRANSPORT AGENT ---


class InterCityTransport(BaseModel):
    from_city: str = ""
    to_city: str = ""
    mode: str = "car"  # "car" | "bus" | "train" | "flight"
    duration: str = ""
    estimated_cost: float = 0.0
    currency: str = "USD"
    recommended: bool = False
    notes: str = ""


class AirportTransfer(BaseModel):
    airport: str = ""
    hotel: str = ""
    recommended_mode: str = "taxi"  # "taxi" | "metro" | "shuttle"
    estimated_cost: float = 0.0
    estimated_duration: str = ""


class LocalTransportSummary(BaseModel):
    city: str = ""
    best_option: str = "taxi"  # "metro" | "taxi" | "ride_hailing" | "walking"
    metro_available: bool = False
    ride_hailing_apps: list[str] = Field(default_factory=list)  # ["Uber", "Careem"]
    avg_taxi_cost_per_km: float = 0.0
    daily_transport_budget: float = 0.0
    tips: list[str] = Field(default_factory=list)


class TransportResearchOutput(BaseModel):
    inter_city_options: list[InterCityTransport] = Field(default_factory=list)
    airport_transfers: list[AirportTransfer] = Field(default_factory=list)
    local_transport_summary: list[LocalTransportSummary] = Field(default_factory=list)


# --- BUDGET AGENT ---


class BudgetAnalysisOutput(BaseModel):
    total_estimated_cost: float = 0.0
    currency: str = "INR"
    user_budget: float = 0.0
    budget_status: str = "within"  # "within" | "over" | "under"
    breakdown: dict[str, float] = Field(default_factory=dict)  # Category -> total cost
    exchange_rate_used: float | None = None
    optimization_suggestions: list[str] = Field(default_factory=list)  # If over budget
    potential_savings: float = 0.0  # How much could be saved
