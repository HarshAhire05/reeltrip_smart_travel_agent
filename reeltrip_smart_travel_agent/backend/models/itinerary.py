"""
Pydantic models for the final itinerary output (Pipeline Stage 7).
"""
from pydantic import BaseModel, Field


class FlightReservation(BaseModel):
    type: str = "international"  # "international" | "domestic"
    from_city: str = ""
    from_airport_code: str = ""  # IATA code
    to_city: str = ""
    to_airport_code: str = ""
    departure_datetime: str = ""
    arrival_datetime: str = ""
    duration: str = ""
    estimated_price: float = 0.0
    price_currency: str = "INR"
    booking_url: str = ""  # Link to Google Flights search
    notes: str | None = None
    day_number: int = 1


class HotelReservation(BaseModel):
    hotel_name: str = ""
    city: str = ""
    address: str = ""
    check_in_date: str = ""
    check_out_date: str = ""
    nights: int = 0
    price_per_night: float = 0.0
    total_price: float = 0.0
    price_currency: str = "INR"
    rating: float = 0.0
    photo_url: str | None = None
    why_recommended: str = ""  # 1-2 sentences
    booking_url: str = ""  # Link to Google Hotels or Booking.com search
    latitude: float = 0.0
    longitude: float = 0.0


class Activity(BaseModel):
    time: str = ""  # "08:00" format
    title: str = ""
    type: str = "attraction"  # "flight" | "checkin" | "checkout" | "meal" | "attraction" | "activity" | "transport" | "free_time"
    venue_name: str | None = None
    venue_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    photo_url: str | None = None
    rating: float | None = None
    duration_minutes: int = 0
    estimated_cost: float = 0.0
    cost_currency: str = "INR"
    description: str = ""  # 1-2 sentence description
    practical_tip: str | None = None  # Insider tip
    booking_url: str | None = None  # Booking link where available
    google_maps_url: str | None = None
    # Transport-specific
    transport_mode: str | None = None  # "flight" | "car" | "metro" | "taxi" | "walk"
    transport_from: str | None = None
    transport_to: str | None = None


class ItineraryDay(BaseModel):
    day_number: int = 1
    date: str = ""
    city: str = ""
    theme: str = ""  # e.g., "Dubai Iconic Landmarks"
    activities: list[Activity] = Field(default_factory=list)


class BudgetBreakdown(BaseModel):
    flights_total: float = 0.0
    accommodation_total: float = 0.0
    food_total: float = 0.0
    activities_total: float = 0.0
    transportation_total: float = 0.0
    miscellaneous_buffer: float = 0.0
    grand_total: float = 0.0
    currency: str = "INR"
    budget_status: str = "within_budget"  # "within_budget" | "over_budget" | "under_budget"
    savings_tips: list[str] | None = None  # If over budget, suggest savings


class VisaInfo(BaseModel):
    required: bool = False
    visa_type: str = ""  # e.g., "Tourist Visa on Arrival"
    processing_time: str = ""
    estimated_cost: str = ""
    documents_needed: list[str] = Field(default_factory=list)
    notes: str = ""


class WeatherSummary(BaseModel):
    overview: str = ""
    avg_high_celsius: float = 0.0
    avg_low_celsius: float = 0.0
    precipitation_chance: str = "low"
    pack_suggestions: list[str] = Field(default_factory=list)


class CurrencyInfo(BaseModel):
    local_currency: str = ""  # e.g., "AED"
    local_currency_name: str = ""  # e.g., "UAE Dirham"
    exchange_rate: str = ""  # e.g., "1 USD = 3.67 AED"
    tips: list[str] = Field(default_factory=list)


class EmergencyInfo(BaseModel):
    police: str = ""
    ambulance: str = ""
    fire: str = ""
    tourist_police: str = ""
    embassy_phone: str = ""
    emergency_notes: list[str] = Field(default_factory=list)


class TripItinerary(BaseModel):
    trip_title: str = ""
    destination_country: str = ""
    destination_cities: list[str] = Field(default_factory=list)
    start_date: str = ""  # e.g., "March 7, 2026"
    end_date: str = ""
    total_days: int = 0
    total_travelers: int = 0

    # Reservations
    flights: list[FlightReservation] = Field(default_factory=list)
    hotels: list[HotelReservation] = Field(default_factory=list)

    # Day-by-day plan
    days: list[ItineraryDay] = Field(default_factory=list)

    # Budget
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)

    # Miscellaneous
    visa_requirements: VisaInfo | None = None
    weather_summary: WeatherSummary = Field(default_factory=WeatherSummary)
    packing_suggestions: list[str] = Field(default_factory=list)
    cultural_tips: list[str] = Field(default_factory=list)
    emergency_info: EmergencyInfo = Field(default_factory=EmergencyInfo)
    currency_info: CurrencyInfo = Field(default_factory=CurrencyInfo)
