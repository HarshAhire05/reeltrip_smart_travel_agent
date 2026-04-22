"""
Flight Agent — researches flight options using Tavily + gpt-4o-mini.
Determines domestic vs international, finds outbound + return + inter-city flights.
Supports open-jaw routing for multi-city trips (arrive city 1, depart city N).
Generates Google Flights booking URL. Fallback: route skeleton without prices.
"""
import json
import logging
from urllib.parse import quote_plus

from services.openai_client import call_openai_json
from services.tavily_client import search_tavily

logger = logging.getLogger(__name__)

FLIGHT_SYSTEM_PROMPT = """You are a flight data extraction assistant.
Given search results about flights between cities, extract structured flight information.

If the search results contain actual flight data (prices, airlines, durations), extract it.
If the search results are vague, provide reasonable estimates based on the route.

ALWAYS provide at least one flight option. If you truly cannot find any data, estimate based
on the distance between cities and typical airline pricing for the region.

Respond in JSON format ONLY."""


def _build_google_flights_url(from_city: str, to_city: str, month: str = "") -> str:
    query = f"flights from {from_city} to {to_city}"
    if month:
        query += f" {month}"
    return f"https://www.google.com/travel/flights?q={quote_plus(query)}"


async def run_flight_agent(state: dict) -> dict:
    """Research flight options for the trip."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])

    home_city = prefs.get("home_city", "Mumbai")
    home_country = prefs.get("home_country", "India")
    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    month = prefs.get("month_of_travel", "")
    budget_currency = prefs.get("budget_currency", "INR")
    num_travelers = prefs.get("number_of_travelers", 2)

    if not dest_city and selected_cities:
        dest_city = selected_cities[0]

    # Determine arrival and departure cities for multi-city trips
    arrival_city = selected_cities[0] if selected_cities else dest_city
    departure_city = selected_cities[-1] if len(selected_cities) > 1 else arrival_city
    is_open_jaw = arrival_city != departure_city

    logger.info(f"[flight] Processing cities: {selected_cities}, arrival: {arrival_city}, departure: {departure_city}, open_jaw: {is_open_jaw}")

    route_type = "domestic" if home_country.lower() == dest_country.lower() else "international"

    # Build search queries — outbound to first city, return from LAST city
    queries = [
        f"cheapest flights from {home_city} to {arrival_city} {month} 2026",
        f"{home_city} to {arrival_city} flight duration airlines",
        f"cheapest flights from {departure_city} to {home_city} {month} 2026",
    ]

    # If open-jaw, also search return from arrival city so LLM can compare
    if is_open_jaw:
        queries.append(f"cheapest flights from {arrival_city} to {home_city} {month} 2026")

    # Inter-city flight/transport queries
    if len(selected_cities) > 1:
        for i in range(len(selected_cities) - 1):
            queries.append(
                f"travel from {selected_cities[i]} to {selected_cities[i + 1]} flights or transport"
            )

    # Search with Tavily
    search_results = []
    for q in queries:
        try:
            result = await search_tavily(q, max_results=3)
            if result:
                search_results.append({"query": q, "results": result})
        except Exception as e:
            logger.warning(f"Flight agent: Tavily search failed for query '{q}': {e}")

    if not search_results:
        logger.warning("Flight agent: no Tavily results, returning fallback")
        return _fallback(home_city, arrival_city, departure_city, route_type, budget_currency, selected_cities)

    inter_city_section = ""
    if len(selected_cities) > 1:
        inter_city_section = f"""
MULTI-CITY ROUTING:
Cities in order: {' -> '.join(selected_cities)}
- Outbound flight: {home_city} -> {arrival_city} (first city)
- Return flight: {departure_city} -> {home_city} (last city)
{"- This is an OPEN-JAW route: arrival and departure are from DIFFERENT cities." if is_open_jaw else ""}
- Also include inter-city flights/transport between consecutive cities as "inter_city_flights" entries.
- The return flight MUST depart from {departure_city}, NOT from {arrival_city}."""

    user_prompt = f"""Extract flight information from these search results:

Outbound: {home_city} -> {arrival_city}
Return: {departure_city} -> {home_city}
{"(Open-jaw route — arriving and departing from different cities)" if is_open_jaw else ""}
Month: {month}
Route type: {route_type}
Number of travelers: {num_travelers}
Currency preference: {budget_currency}
Selected cities: {json.dumps(selected_cities)}
{inter_city_section}

Search results:
{json.dumps(search_results, indent=1)[:6000]}

Return JSON:
{{
    "flights_needed": true,
    "route_type": "{route_type}",
    "is_open_jaw": {str(is_open_jaw).lower()},
    "outbound_options": [
        {{
            "airline": "airline name",
            "from_city": "{home_city}",
            "from_airport": "IATA code",
            "to_city": "{arrival_city}",
            "to_airport": "IATA code",
            "departure_time": "approximate HH:MM",
            "arrival_time": "approximate HH:MM",
            "duration": "Xh Ym",
            "stops": 0,
            "estimated_price": number_per_person_in_{budget_currency},
            "price_currency": "{budget_currency}",
            "source": "where this data came from"
        }}
    ],
    "return_options": [
        {{
            "airline": "airline name",
            "from_city": "{departure_city}",
            "from_airport": "IATA code",
            "to_city": "{home_city}",
            "to_airport": "IATA code",
            "departure_time": "approximate HH:MM",
            "arrival_time": "approximate HH:MM",
            "duration": "Xh Ym",
            "stops": 0,
            "estimated_price": number_per_person_in_{budget_currency},
            "price_currency": "{budget_currency}",
            "source": "where this data came from"
        }}
    ],
    "recommended_outbound": {{...best option from outbound_options...}},
    "recommended_return": {{...best option from return_options...}},
    "inter_city_flights": [],
    "booking_search_url": "Google Flights URL for outbound",
    "return_booking_url": "Google Flights URL for return"
}}"""

    result = await call_openai_json(
        task="fast",
        system_prompt=FLIGHT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=3072,
        temperature=0.2,
    )

    if result:
        if not result.get("booking_search_url"):
            result["booking_search_url"] = _build_google_flights_url(home_city, arrival_city, month)
        if not result.get("return_booking_url"):
            result["return_booking_url"] = _build_google_flights_url(departure_city, home_city, month)
        return result

    return _fallback(home_city, arrival_city, departure_city, route_type, budget_currency, selected_cities)


def _fallback(
    home_city: str,
    arrival_city: str,
    departure_city: str,
    route_type: str,
    currency: str,
    selected_cities: list[str] | None = None,
) -> dict:
    """Return a skeleton with just route info when search/LLM fails."""
    inter_city = []
    if selected_cities and len(selected_cities) > 1:
        for i in range(len(selected_cities) - 1):
            inter_city.append({
                "from_city": selected_cities[i],
                "to_city": selected_cities[i + 1],
                "mode": "train or flight",
                "estimated_price": 0,
                "price_currency": currency,
                "duration": "check locally",
                "source": "Unable to find pricing data",
            })

    return {
        "flights_needed": True,
        "route_type": route_type,
        "is_open_jaw": arrival_city != departure_city,
        "outbound_options": [
            {
                "airline": "Various airlines",
                "from_city": home_city,
                "from_airport": "",
                "to_city": arrival_city,
                "to_airport": "",
                "departure_time": "morning",
                "arrival_time": "",
                "duration": "",
                "stops": 0,
                "estimated_price": 0,
                "price_currency": currency,
                "source": "Unable to find pricing data",
            }
        ],
        "return_options": [
            {
                "airline": "Various airlines",
                "from_city": departure_city,
                "from_airport": "",
                "to_city": home_city,
                "to_airport": "",
                "departure_time": "evening",
                "arrival_time": "",
                "duration": "",
                "stops": 0,
                "estimated_price": 0,
                "price_currency": currency,
                "source": "Unable to find pricing data",
            }
        ],
        "recommended_outbound": None,
        "recommended_return": None,
        "inter_city_flights": inter_city,
        "booking_search_url": _build_google_flights_url(home_city, arrival_city),
        "return_booking_url": _build_google_flights_url(departure_city, home_city),
    }
