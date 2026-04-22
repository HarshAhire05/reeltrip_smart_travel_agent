"""
Transport Agent — researches inter-city transport, local transport, and airport transfers.
Uses Tavily for web search + gpt-4o-mini for parsing.
"""
import json
import logging

from services.openai_client import call_openai_json
from services.tavily_client import search_tavily

logger = logging.getLogger(__name__)

TRANSPORT_SYSTEM_PROMPT = """You are a transportation research assistant for travel planning.
Given search results about transportation options at a destination, extract structured data.

Include practical information travelers actually need:
- How to get from the airport to the city/hotel
- Best way to travel between cities (if multi-city trip)
- Local transport options (metro, taxi, ride-hailing apps)
- Estimated costs for each option

Respond in JSON format ONLY."""


async def run_transport_agent(state: dict) -> dict:
    """Research transportation options for the trip."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[transport] Processing cities: {selected_cities}, count: {len(selected_cities)}")
    flight_data = state.get("flight_data")

    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    budget_currency = prefs.get("budget_currency", "INR")

    if not dest_city and selected_cities:
        dest_city = selected_cities[0]

    # Build search queries
    queries = [
        f"{dest_city} airport to city center transport options taxi metro cost",
        f"{dest_city} public transport guide tourists metro bus ride-hailing apps",
    ]

    # Inter-city transport queries
    if len(selected_cities) > 1:
        for i in range(len(selected_cities) - 1):
            queries.append(
                f"best way to travel from {selected_cities[i]} to {selected_cities[i + 1]} cost duration"
            )

    # Search with Tavily
    search_results = []
    for q in queries:
        try:
            result = await search_tavily(q, max_results=3)
            if result:
                search_results.append({"query": q, "results": result})
        except Exception as e:
            logger.warning(f"Transport agent: Tavily search failed for query '{q}': {e}")

    if not search_results:
        logger.warning("Transport agent: no Tavily results, returning fallback")
        return _fallback(dest_city, dest_country, budget_currency, selected_cities)

    # Detect airport from flight data
    airport_info = ""
    if flight_data and flight_data.get("outbound_options"):
        outbound = flight_data["outbound_options"][0] if flight_data["outbound_options"] else {}
        airport_code = outbound.get("to_airport", "")
        if airport_code:
            airport_info = f"Arriving at airport: {airport_code}"

    inter_city_section = ""
    if len(selected_cities) > 1:
        inter_city_section = f"""
Inter-city travel needed between: {' -> '.join(selected_cities)}
Include options for each leg (driving, bus, train, internal flights)."""

    user_prompt = f"""Extract transportation information for {dest_city}, {dest_country}:

{airport_info}
Currency: {budget_currency}
{inter_city_section}

Search results:
{json.dumps(search_results, indent=1)[:5000]}

Return JSON:
{{
    "inter_city_options": [
        {{
            "from_city": "City A",
            "to_city": "City B",
            "mode": "car|bus|train|flight",
            "duration": "Xh Ym",
            "estimated_cost": number_in_{budget_currency},
            "currency": "{budget_currency}",
            "recommended": true/false,
            "notes": "practical notes"
        }}
    ],
    "airport_transfers": [
        {{
            "airport": "airport name or code",
            "hotel": "city center or hotel area",
            "recommended_mode": "taxi|metro|shuttle|bus",
            "estimated_cost": number_in_{budget_currency},
            "estimated_duration": "XX minutes"
        }}
    ],
    "local_transport_summary": [
        {{
            "city": "{dest_city}",
            "best_option": "metro|taxi|ride_hailing|walking",
            "metro_available": true/false,
            "ride_hailing_apps": ["app names available"],
            "avg_taxi_cost_per_km": number_in_{budget_currency},
            "daily_transport_budget": number_in_{budget_currency},
            "tips": ["practical transport tips for tourists"]
        }}
    ]
}}"""

    result = await call_openai_json(
        task="fast",
        system_prompt=TRANSPORT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2,
    )

    if result:
        return result

    return _fallback(dest_city, dest_country, budget_currency, selected_cities)


def _fallback(city: str, country: str, currency: str, selected_cities: list[str]) -> dict:
    """Return basic transport info when search fails."""
    inter_city = []
    if len(selected_cities) > 1:
        for i in range(len(selected_cities) - 1):
            inter_city.append({
                "from_city": selected_cities[i],
                "to_city": selected_cities[i + 1],
                "mode": "car",
                "duration": "check locally",
                "estimated_cost": 0,
                "currency": currency,
                "recommended": True,
                "notes": "Check local transport options for this route",
            })

    return {
        "inter_city_options": inter_city,
        "airport_transfers": [
            {
                "airport": f"{city} airport",
                "hotel": "city center",
                "recommended_mode": "taxi",
                "estimated_cost": 0,
                "estimated_duration": "30-60 minutes",
            }
        ],
        "local_transport_summary": [
            {
                "city": city,
                "best_option": "taxi",
                "metro_available": False,
                "ride_hailing_apps": ["Uber"],
                "avg_taxi_cost_per_km": 0,
                "daily_transport_budget": 0,
                "tips": [
                    "Use official taxis or ride-hailing apps for safety",
                    "Agree on the fare before getting in unmarked taxis",
                ],
            }
        ],
    }
