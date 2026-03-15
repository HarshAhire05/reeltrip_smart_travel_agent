"""
TravelPlannerState — shared state for all travel planning agents.
"""
from typing import TypedDict


class TravelPlannerState(TypedDict):
    # Inputs (set before running planner)
    location_result: dict       # From pipeline stage 3-4
    user_preferences: dict      # From preference form
    highlights: list[dict]      # From pipeline stage 4
    selected_cities: list[str]  # Cities user selected

    # Agent outputs (populated during planning)
    flight_data: dict | None
    hotel_data: dict | None
    weather_data: dict | None
    safety_data: dict | None
    activity_data: dict | None
    transport_data: dict | None
    budget_analysis: dict | None

    # Final output
    itinerary: dict | None

    # Monitoring
    agent_errors: list[str]
    progress_updates: list[dict]
