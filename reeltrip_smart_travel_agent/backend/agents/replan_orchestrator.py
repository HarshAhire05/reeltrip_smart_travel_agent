"""
Re-plan Orchestrator — selective agent execution for itinerary re-planning.

This orchestrator determines which agents to re-run based on changed preference fields,
executes only those agents, and merges results with the existing itinerary.
"""
import asyncio
import logging
from typing import AsyncGenerator

from agents.state import TravelPlannerState
from agents.orchestrator import run_travel_planner_streaming
from utils.itinerary_merger import get_agents_to_rerun, merge_itinerary, calculate_minimum_viable_budget
from models.preferences import UserPreferences
from models.itinerary import TripItinerary
from models.replan import AgentSkipDecision

logger = logging.getLogger(__name__)


async def run_replan_orchestrator(
    session_id: str,
    original_params: UserPreferences,
    updated_params: UserPreferences,
    changed_fields: list[str],
    existing_itinerary: TripItinerary,
    location_result: dict,
    highlights: list[dict],
    selected_cities: list[str],
) -> AsyncGenerator[dict, None]:
    """
    Run selective re-plan based on changed fields.
    
    Args:
        session_id: Session identifier
        original_params: Original user preferences before edit
        updated_params: New user preferences after edit
        changed_fields: List of field names that changed
        existing_itinerary: Current itinerary to selectively update
        location_result: Location metadata (destination, coordinates, etc.)
        highlights: Place highlights from original processing
        selected_cities: List of selected destination cities
    
    Yields:
        SSE events for progress tracking and final itinerary
    """
    logger.info(f"Re-plan orchestrator starting for session {session_id}")
    logger.info(f"Changed fields: {changed_fields}")
    
    # Determine which agents to skip vs run
    skip_decision = get_agents_to_rerun(changed_fields)
    logger.info(f"Agent decision: skip={skip_decision.skip_agents}, run={skip_decision.run_agents}")
    
    # Yield initial status
    yield {
        "event": "replan_start",
        "data": {
            "changed_fields": changed_fields,
            "skip_agents": skip_decision.skip_agents,
            "run_agents": skip_decision.run_agents,
            "reason": skip_decision.reason,
        }
    }
    
    # Check for low budget warning
    if "total_budget" in changed_fields or "number_of_travelers" in changed_fields or "trip_duration_days" in changed_fields:
        min_budget = calculate_minimum_viable_budget(
            destination_country=existing_itinerary.destination_country,
            number_of_travelers=updated_params.number_of_travelers,
            trip_duration_days=updated_params.trip_duration_days,
            currency=updated_params.budget_currency,
        )
        
        if updated_params.total_budget < min_budget:
            yield {
                "event": "warning",
                "data": {
                    "type": "low_budget",
                    "message": f"Your new budget may limit available flights/hotels. Showing best options within {updated_params.budget_currency} {updated_params.total_budget:.0f}. Minimum recommended: {updated_params.budget_currency} {min_budget:.0f}.",
                    "minimum_budget": min_budget,
                    "current_budget": updated_params.total_budget,
                }
            }
    
    # Prepare state for agent execution
    state: TravelPlannerState = {
        "location_result": location_result,
        "user_preferences": updated_params.model_dump(),
        "highlights": highlights,
        "selected_cities": selected_cities,
        # Pre-populate with existing agent outputs (for skipped agents)
        "flight_data": _extract_flight_data(existing_itinerary) if "flight" in skip_decision.skip_agents else None,
        "hotel_data": _extract_hotel_data(existing_itinerary) if "hotel" in skip_decision.skip_agents else None,
        "weather_data": _extract_weather_data(existing_itinerary) if "weather" in skip_decision.skip_agents else None,
        "safety_data": _extract_safety_data(existing_itinerary) if "safety" in skip_decision.skip_agents else None,
        "activity_data": _extract_activity_data(existing_itinerary) if "activity" in skip_decision.skip_agents else None,
        "transport_data": _extract_transport_data(existing_itinerary) if "transport" in skip_decision.skip_agents else None,
        "budget_analysis": _extract_budget_data(existing_itinerary) if "budget" in skip_decision.skip_agents else None,
        "itinerary": None,
        "agent_errors": [],
        "progress_updates": [],
    }
    
    # Run the orchestrator with skip list
    agent_run_count = 0
    async for event in run_travel_planner_streaming(state, skip_agents=skip_decision.skip_agents):
        # Forward all events from orchestrator
        yield event
        
        # Track which agents actually ran
        if event.get("event") == "agent_progress" and event.get("data", {}).get("status") == "complete":
            agent_run_count += 1
    
    # Extract final itinerary
    final_itinerary = state.get("itinerary")
    
    if not final_itinerary:
        yield {
            "event": "error",
            "data": {"message": "Re-plan failed: could not generate updated itinerary"}
        }
        return
    
    # Determine changed sections
    changed_sections = []
    if "flight" in skip_decision.run_agents:
        changed_sections.append("flights")
    if "hotel" in skip_decision.run_agents:
        changed_sections.append("hotels")
    if "activity" in skip_decision.run_agents:
        changed_sections.append("daily_activities")
    if "weather" in skip_decision.run_agents:
        changed_sections.append("weather_summary")
    if "safety" in skip_decision.run_agents:
        changed_sections.append("cultural_tips")
    if "budget" in skip_decision.run_agents:
        changed_sections.append("budget_breakdown")
    
    # Generate summary
    summary = _generate_summary(changed_fields, changed_sections, updated_params)
    
    # Yield final itinerary
    yield {
        "event": "itinerary",
        "data": {
            "itinerary": final_itinerary,
            "changed_sections": changed_sections,
            "version": 2,  # Will be incremented by endpoint
        }
    }
    
    # Yield completion
    yield {
        "event": "complete",
        "data": {
            "session_id": session_id,
            "summary": summary,
            "agents_run": len(skip_decision.run_agents),
            "agents_skipped": len(skip_decision.skip_agents),
        }
    }
    
    logger.info(f"Re-plan complete: {agent_run_count} agents executed, summary: {summary}")


def _extract_flight_data(itinerary: TripItinerary) -> dict:
    """Extract flight data from existing itinerary for re-use."""
    return {
        "flights": [flight.model_dump() for flight in itinerary.flights] if itinerary.flights else []
    }


def _extract_hotel_data(itinerary: TripItinerary) -> dict:
    """Extract hotel data from existing itinerary for re-use."""
    return {
        "hotels": [hotel.model_dump() for hotel in itinerary.hotels] if itinerary.hotels else []
    }


def _extract_weather_data(itinerary: TripItinerary) -> dict:
    """Extract weather data from existing itinerary for re-use."""
    return {
        "weather_summary": itinerary.weather_summary.model_dump() if itinerary.weather_summary else {},
        "packing_suggestions": itinerary.packing_suggestions or []
    }


def _extract_safety_data(itinerary: TripItinerary) -> dict:
    """Extract safety data from existing itinerary for re-use."""
    return {
        "cultural_tips": itinerary.cultural_tips or [],
        "emergency_info": itinerary.emergency_info.model_dump() if itinerary.emergency_info else {}
    }


def _extract_activity_data(itinerary: TripItinerary) -> dict:
    """Extract activity data from existing itinerary for re-use."""
    return {
        "days": [day.model_dump() for day in itinerary.days] if itinerary.days else []
    }


def _extract_transport_data(itinerary: TripItinerary) -> dict:
    """Extract transport data from existing itinerary for re-use."""
    # Transport is embedded in activities, so we extract from days
    # This is a placeholder - actual implementation depends on how transport is stored
    return {
        "inter_city_routes": []  # Would extract from activities with type="transport"
    }


def _extract_budget_data(itinerary: TripItinerary) -> dict:
    """Extract budget data from existing itinerary for re-use."""
    return {
        "budget_breakdown": itinerary.budget_breakdown.model_dump() if itinerary.budget_breakdown else {}
    }


def _generate_summary(changed_fields: list[str], changed_sections: list[str], updated_params: UserPreferences) -> str:
    """Generate a human-readable summary of what changed."""
    field_descriptions = {
        "total_budget": f"budget to {updated_params.budget_currency} {updated_params.total_budget:.0f}",
        "accommodation_tier": f"accommodation to {updated_params.accommodation_tier}",
        "number_of_travelers": f"travelers to {updated_params.number_of_travelers}",
        "start_date": f"dates to {updated_params.start_date} - {updated_params.end_date}",
        "end_date": "travel dates",
        "month_of_travel": f"travel month to {updated_params.month_of_travel}",
        "dietary_preferences": f"dietary preferences to {', '.join(updated_params.dietary_preferences)}",
        "travel_styles": f"travel style to {', '.join(updated_params.travel_styles)}",
        "must_include_places": "bucket list",
        "additional_notes": "special requests",
    }
    
    # Get descriptions for changed fields
    changes = []
    for field in changed_fields[:3]:  # Max 3 for brevity
        if field in field_descriptions:
            changes.append(field_descriptions[field])
    
    if not changes:
        return "Itinerary updated based on your changes"
    
    change_text = ", ".join(changes)
    if len(changed_fields) > 3:
        change_text += f", and {len(changed_fields) - 3} more"
    
    # Build section summary
    section_text = ", ".join(changed_sections[:3])
    
    return f"Updated {change_text}. Modified sections: {section_text}."
