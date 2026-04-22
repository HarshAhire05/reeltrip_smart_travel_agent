"""
Utility for merging itinerary sections during re-plan operations.
"""
from typing import Any
from models.itinerary import TripItinerary, BudgetBreakdown, FlightReservation, HotelReservation, ItineraryDay
from models.replan import AgentSkipDecision


def merge_itinerary(
    existing_itinerary: TripItinerary,
    new_agent_outputs: dict[str, Any],
    changed_fields: list[str],
    skip_decision: AgentSkipDecision
) -> tuple[TripItinerary, list[str]]:
    """
    Merge new agent outputs with existing itinerary, preserving unchanged sections.
    
    Args:
        existing_itinerary: The current itinerary before re-plan
        new_agent_outputs: Dict with keys like 'flight_data', 'hotel_data', 'activity_data', etc.
        changed_fields: List of preference fields that changed (e.g., ['total_budget', 'accommodation_tier'])
        skip_decision: AgentSkipDecision indicating which agents ran vs skipped
    
    Returns:
        Tuple of (merged_itinerary, changed_sections)
        - merged_itinerary: New TripItinerary with selective updates
        - changed_sections: List of section names that were updated
    
    Example:
        If only budget changed:
        - Flight and hotel sections get replaced
        - Activities, weather, safety remain from existing_itinerary
        - Budget breakdown gets recalculated
        - Assembler runs to merge everything coherently
    """
    changed_sections = []
    
    # Start with a copy of existing itinerary data
    merged_data = existing_itinerary.model_dump()
    
    # Flight updates (if flight agent ran)
    if 'flight' not in skip_decision.skip_agents and new_agent_outputs.get('flight_data'):
        flight_data = new_agent_outputs['flight_data']
        if flight_data.get('flights'):
            merged_data['flights'] = flight_data['flights']
            changed_sections.append('flights')
    
    # Hotel updates (if hotel agent ran)
    if 'hotel' not in skip_decision.skip_agents and new_agent_outputs.get('hotel_data'):
        hotel_data = new_agent_outputs['hotel_data']
        if hotel_data.get('hotels'):
            merged_data['hotels'] = hotel_data['hotels']
            changed_sections.append('hotels')
    
    # Weather updates (if weather agent ran)
    if 'weather' not in skip_decision.skip_agents and new_agent_outputs.get('weather_data'):
        weather_data = new_agent_outputs['weather_data']
        if weather_data.get('weather_summary'):
            merged_data['weather_summary'] = weather_data['weather_summary']
            changed_sections.append('weather_summary')
        if weather_data.get('packing_suggestions'):
            merged_data['packing_suggestions'] = weather_data['packing_suggestions']
            changed_sections.append('packing_suggestions')
    
    # Safety updates (if safety agent ran)
    if 'safety' not in skip_decision.skip_agents and new_agent_outputs.get('safety_data'):
        safety_data = new_agent_outputs['safety_data']
        if safety_data.get('cultural_tips'):
            merged_data['cultural_tips'] = safety_data['cultural_tips']
            changed_sections.append('cultural_tips')
        if safety_data.get('emergency_info'):
            merged_data['emergency_info'] = safety_data['emergency_info']
            changed_sections.append('emergency_info')
    
    # Activity updates (if activity agent ran)
    if 'activity' not in skip_decision.skip_agents and new_agent_outputs.get('activity_data'):
        activity_data = new_agent_outputs['activity_data']
        # Activities are embedded in days - need to update carefully
        if activity_data.get('days'):
            # Replace entire day-by-day plan
            merged_data['days'] = activity_data['days']
            changed_sections.append('daily_activities')
    
    # Transport updates (if transport agent ran)
    if 'transport' not in skip_decision.skip_agents and new_agent_outputs.get('transport_data'):
        # Transport is usually embedded in activities, handled by assembler
        changed_sections.append('inter_city_transport')
    
    # Budget updates (if budget agent ran - almost always runs)
    if 'budget' not in skip_decision.skip_agents and new_agent_outputs.get('budget_analysis'):
        budget_data = new_agent_outputs['budget_analysis']
        if budget_data.get('budget_breakdown'):
            merged_data['budget_breakdown'] = budget_data['budget_breakdown']
            changed_sections.append('budget_breakdown')
    
    # Assembler output (ALWAYS runs - provides the final coherent itinerary)
    if new_agent_outputs.get('itinerary'):
        # The assembler has already merged everything intelligently
        # Use its output as the final merged itinerary
        assembler_output = new_agent_outputs['itinerary']
        
        # The assembler returns the complete coherent itinerary
        # Validate it has all required fields
        if isinstance(assembler_output, dict):
            merged_itinerary = TripItinerary(**assembler_output)
        elif isinstance(assembler_output, TripItinerary):
            merged_itinerary = assembler_output
        else:
            # Fallback: use our manual merge
            merged_itinerary = TripItinerary(**merged_data)
    else:
        # No assembler output - use our manual merge
        merged_itinerary = TripItinerary(**merged_data)
    
    return merged_itinerary, changed_sections


def get_agents_to_rerun(changed_fields: list[str]) -> AgentSkipDecision:
    """
    Determine which agents need to re-run based on changed preference fields.
    
    Args:
        changed_fields: List of UserPreferences field names that changed
    
    Returns:
        AgentSkipDecision with skip_agents, run_agents, and reason
    
    Decision Map:
        - total_budget or accommodation_tier changed → flight, hotel, budget
        - number_of_travelers changed → flight, hotel, budget
        - start_date, end_date, month_of_travel changed → flight, hotel, weather, budget
        - dietary_preferences changed → activity, budget
        - travel_styles changed → hotel, activity, budget
        - destination or selected_cities changed → ALL agents (full rebuild)
        - additional_notes changed → ALL agents (new context)
        - must_include_places changed → activity, transport, budget
    
    Note: assembler ALWAYS runs to ensure coherence
    """
    all_agents = ["flight", "hotel", "weather", "safety", "activity", "transport", "budget", "assembler"]
    run_agents = set()
    
    # Full re-plan if destination or additional notes changed
    if any(f in changed_fields for f in ["destination", "selected_cities", "additional_notes"]):
        return AgentSkipDecision(
            skip_agents=[],
            run_agents=all_agents,
            reason="Destination or special requests changed - full itinerary rebuild required"
        )
    
    # Budget or accommodation tier affects flights and hotels
    if any(f in changed_fields for f in ["total_budget", "budget_currency", "accommodation_tier"]):
        run_agents.update(["flight", "hotel", "budget"])
    
    # Number of travelers affects flights (seats) and hotels (rooms)
    if "number_of_travelers" in changed_fields:
        run_agents.update(["flight", "hotel", "budget"])
    
    # Travel dates affect flights, hotels, weather
    if any(f in changed_fields for f in ["start_date", "end_date", "month_of_travel", "trip_duration_days"]):
        run_agents.update(["flight", "hotel", "weather", "budget"])
    
    # Dietary preferences affect activities (restaurant recommendations)
    if "dietary_preferences" in changed_fields:
        run_agents.update(["activity", "budget"])
    
    # Travel styles affect hotels (category) and activities (activity types)
    if "travel_styles" in changed_fields:
        run_agents.update(["hotel", "activity", "budget"])
    
    # Bucket list changes affect activities and transport routing
    if "must_include_places" in changed_fields:
        run_agents.update(["activity", "transport", "budget"])
    
    # Traveling_with might affect activity types (family-friendly, romantic, etc.)
    if "traveling_with" in changed_fields:
        run_agents.update(["activity", "hotel", "budget"])
    
    # Home city/country affects flight routing and visa requirements
    if any(f in changed_fields for f in ["home_city", "home_country"]):
        run_agents.update(["flight", "safety", "budget"])
    
    # Budget always re-runs if anything financial changed
    if run_agents:
        run_agents.add("budget")
    
    # Assembler ALWAYS runs to merge outputs coherently
    run_agents.add("assembler")
    
    # Calculate skip list
    skip_agents = [agent for agent in all_agents if agent not in run_agents]
    
    # Generate reason summary
    changed_summary = ", ".join(changed_fields[:3])  # First 3 fields
    if len(changed_fields) > 3:
        changed_summary += f", and {len(changed_fields) - 3} more"
    
    reason = f"Changed: {changed_summary}. Re-running: {', '.join(sorted(run_agents))}."
    
    return AgentSkipDecision(
        skip_agents=skip_agents,
        run_agents=list(run_agents),
        reason=reason
    )


def calculate_minimum_viable_budget(
    destination_country: str,
    number_of_travelers: int,
    trip_duration_days: int,
    currency: str = "INR"
) -> float:
    """
    Calculate the minimum viable trip budget for warning purposes.
    
    This is a rough estimate based on:
    - Budget flight costs per traveler
    - Cheapest accommodation (hostel/budget hotel)
    - Basic food (3 meals/day at budget prices)
    - Minimal transport costs
    
    Args:
        destination_country: Country name (e.g., "UAE", "India", "USA")
        number_of_travelers: Number of people
        trip_duration_days: Trip length in days
        currency: Currency code (e.g., "INR", "USD")
    
    Returns:
        Minimum budget in specified currency
    """
    # Very rough estimates - you'd want to make this more sophisticated
    # with actual pricing data or API calls
    
    # Base costs per person per day (in USD for simplicity)
    base_costs_usd = {
        "India": {"flight": 100, "hotel": 20, "food": 15, "transport": 10},
        "UAE": {"flight": 200, "hotel": 50, "food": 30, "transport": 20},
        "Thailand": {"flight": 150, "hotel": 25, "food": 15, "transport": 10},
        "USA": {"flight": 400, "hotel": 80, "food": 40, "transport": 30},
        "Europe": {"flight": 350, "hotel": 60, "food": 35, "transport": 25},
        # Add more countries as needed
    }
    
    # Default to moderate costs if country not found
    costs = base_costs_usd.get(destination_country, {"flight": 250, "hotel": 50, "food": 25, "transport": 15})
    
    # Calculate minimum budget
    flight_cost = costs["flight"] * number_of_travelers * 2  # Round trip
    hotel_cost = costs["hotel"] * number_of_travelers * trip_duration_days
    food_cost = costs["food"] * number_of_travelers * trip_duration_days
    transport_cost = costs["transport"] * number_of_travelers * trip_duration_days
    
    total_usd = flight_cost + hotel_cost + food_cost + transport_cost
    
    # Convert to target currency (rough conversion rates)
    conversion_rates = {
        "INR": 83.0,
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "AED": 3.67,
    }
    
    rate = conversion_rates.get(currency, 1.0)
    total_local = total_usd * rate
    
    return round(total_local, 2)
