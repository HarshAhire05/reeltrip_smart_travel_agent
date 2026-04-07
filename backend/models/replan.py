"""
Pydantic models for the itinerary re-plan feature.
"""
from pydantic import BaseModel, Field
from models.preferences import UserPreferences
from models.itinerary import TripItinerary


class ReplanRequest(BaseModel):
    """Request payload for re-planning an itinerary."""
    session_id: str
    original_params: UserPreferences
    updated_params: UserPreferences
    changed_fields: list[str] = Field(
        default_factory=list,
        description="List of field names that changed (e.g., ['total_budget', 'accommodation_tier'])"
    )
    existing_itinerary: TripItinerary
    selected_cities: list[str] = Field(
        default_factory=list,
        description="List of destination cities (for destination override)"
    )


class ReplanResponse(BaseModel):
    """Response payload for a completed re-plan."""
    updated_itinerary: TripItinerary
    changed_sections: list[str] = Field(
        default_factory=list,
        description="List of itinerary sections that were updated (e.g., ['flights', 'hotels', 'budget_breakdown'])"
    )
    version: int = Field(
        default=1,
        description="Version number of this itinerary (increments with each re-plan)"
    )
    summary: str = Field(
        default="",
        description="Brief summary of what changed (e.g., 'Updated flights and hotels based on new budget')"
    )


class AgentSkipDecision(BaseModel):
    """Decision map for which agents to run during re-plan."""
    skip_agents: list[str] = Field(
        default_factory=list,
        description="List of agent names to skip (e.g., ['activity', 'weather', 'safety'])"
    )
    run_agents: list[str] = Field(
        default_factory=list,
        description="List of agent names to run (e.g., ['flight', 'hotel', 'budget', 'assembler'])"
    )
    reason: str = Field(
        default="",
        description="Explanation of why these agents were selected"
    )
