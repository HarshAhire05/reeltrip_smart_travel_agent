"""
Hotel Agent — finds accommodation using Google Places + Tavily for pricing.
Matches accommodation_tier and traveling_with preferences.
1 primary + 2 alternatives per city. Includes why_recommended + booking URL.
"""
import json
import logging
from urllib.parse import quote_plus

from services.openai_client import call_openai_json
from services.tavily_client import search_tavily
from services.google_places_client import nearby_search, get_photo_url, text_search

logger = logging.getLogger(__name__)

HOTEL_SYSTEM_PROMPT = """You are a hotel recommendation assistant.
Given Google Places hotel data and web search results about pricing,
recommend the best hotels matching the traveler's preferences.

For each hotel provide:
- Real hotel name from the Google Places data
- Estimated price per night based on search results
- A "why_recommended" explanation (1-2 sentences)
- Match to the traveler type

If price data is unavailable, estimate based on the hotel's rating and
the accommodation tier requested (budget/mid-range/luxury/ultra-luxury).

Respond in JSON format ONLY."""


def _build_booking_url(hotel_name: str, city: str) -> str:
    query = f"{hotel_name} {city}"
    return f"https://www.google.com/travel/hotels?q={quote_plus(query)}"


async def _search_hotels_for_city(
    city: str,
    country: str,
    lat: float | None,
    lng: float | None,
    prefs: dict,
) -> dict:
    """Search and score hotels for a single city."""
    month = prefs.get("month_of_travel", "")
    tier = prefs.get("accommodation_tier", "mid-range")
    traveling_with = prefs.get("traveling_with", "partner")
    budget_currency = prefs.get("budget_currency", "INR")
    duration = prefs.get("trip_duration_days", 3)

    # Step 1: Get real hotels from Google Places
    hotels_raw = []
    if lat and lng:
        hotels_raw = await nearby_search(lat, lng, "lodging", radius=15000, max_results=10)

    # Resolve photo URLs
    for h in hotels_raw:
        if h.get("photo_reference") and not h.get("photo_url"):
            h["photo_url"] = get_photo_url(h["photo_reference"])  # Not async

    # Step 2: Tavily for pricing
    price_query = f"best {tier} hotels {city} {month} 2026 price per night {budget_currency}"
    price_results = await search_tavily(price_query, max_results=3)

    if traveling_with in ("family", "friends"):
        family_query = f"{traveling_with}-friendly hotels {city} {month}"
        extra = await search_tavily(family_query, max_results=2)
        if extra and price_results:
            price_results.extend(extra)
        elif extra:
            price_results = extra

    if not hotels_raw and not price_results:
        logger.warning(f"Hotel agent: no data for {city}, returning empty")
        return {"recommended_hotels": [], "alternative_hotels": []}

    # Slim hotel data for prompt
    slim_hotels = []
    for h in hotels_raw[:10]:
        slim_hotels.append({
            "name": h.get("name", ""),
            "address": h.get("formatted_address", ""),
            "rating": h.get("rating"),
            "total_ratings": h.get("total_ratings"),
            "price_level": h.get("price_level"),
            "latitude": h.get("latitude", 0),
            "longitude": h.get("longitude", 0),
            "photo_url": h.get("photo_url", ""),
            "types": h.get("types", [])[:3],
        })

    user_prompt = f"""Recommend hotels for this trip:

Destination: {city}, {country}
Trip duration: {duration} nights
Accommodation tier: {tier}
Traveling with: {traveling_with}
Month: {month}
Currency: {budget_currency}

Google Places hotels found:
{json.dumps(slim_hotels, indent=1)}

Price research from web:
{json.dumps(price_results[:5], indent=1)[:3000] if price_results else "No pricing data found"}

Return JSON:
{{
    "recommended_hotels": [
        {{
            "name": "Hotel Name from Google Places",
            "city": "{city}",
            "address": "full address",
            "latitude": number,
            "longitude": number,
            "rating": number,
            "price_per_night_estimate": number_in_{budget_currency},
            "currency": "{budget_currency}",
            "photo_url": "url or empty string",
            "why_recommended": "1-2 sentences explaining why this hotel matches the traveler",
            "traveler_type_match": "{traveling_with}",
            "booking_search_url": "Google Hotels URL",
            "amenities": ["wifi", "pool", "spa"]
        }}
    ],
    "alternative_hotels": [
        ...2-3 more options with same structure...
    ]
}}

Pick 1 primary recommendation and 2-3 alternatives.
Primary should best match {tier} tier and {traveling_with} travel style."""

    result = await call_openai_json(
        task="fast",
        system_prompt=HOTEL_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=3072,
        temperature=0.3,
    )

    if result:
        # Ensure booking URLs exist
        for hotel_list in [result.get("recommended_hotels", []), result.get("alternative_hotels", [])]:
            for hotel in hotel_list:
                if not hotel.get("booking_search_url"):
                    hotel["booking_search_url"] = _build_booking_url(
                        hotel.get("name", "hotel"), city
                    )
        return result

    return {"recommended_hotels": [], "alternative_hotels": []}


async def run_hotel_agent(state: dict) -> dict:
    """Research hotel options for all cities in the trip."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[hotel] Processing cities: {selected_cities}, count: {len(selected_cities)}")

    primary_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    primary_lat = location.get("city_latitude")
    primary_lng = location.get("city_longitude")
    budget_currency = prefs.get("budget_currency", "INR")
    tier = prefs.get("accommodation_tier", "mid-range")

    if not primary_city and selected_cities:
        primary_city = selected_cities[0]

    cities_to_search = selected_cities if selected_cities else [primary_city]

    all_recommended = []
    all_alternatives = []

    for city in cities_to_search:
        # Get lat/lng: use primary coords if matching, otherwise geocode
        if city == primary_city and primary_lat and primary_lng:
            lat, lng = primary_lat, primary_lng
        else:
            logger.info(f"Hotel agent: geocoding {city} for hotel search")
            city_results = await text_search(f"{city}, {dest_country}", max_results=1)
            if city_results:
                lat = city_results[0].get("latitude")
                lng = city_results[0].get("longitude")
            else:
                lat, lng = None, None

        result = await _search_hotels_for_city(city, dest_country, lat, lng, prefs)
        all_recommended.extend(result.get("recommended_hotels", []))
        all_alternatives.extend(result.get("alternative_hotels", []))

    if not all_recommended:
        logger.warning("Hotel agent: no hotels found across all cities, returning fallback")
        return _fallback(cities_to_search[0] if cities_to_search else "Unknown", tier, budget_currency)

    return {
        "recommended_hotels": all_recommended,
        "alternative_hotels": all_alternatives,
    }


def _fallback(city: str, tier: str, currency: str) -> dict:
    """Return minimal hotel data when search fails."""
    return {
        "recommended_hotels": [
            {
                "name": f"Recommended {tier} hotel in {city}",
                "city": city,
                "address": "",
                "latitude": 0,
                "longitude": 0,
                "rating": 0,
                "price_per_night_estimate": 0,
                "currency": currency,
                "photo_url": "",
                "why_recommended": f"Search for {tier} hotels in {city} on Google Hotels for current availability.",
                "traveler_type_match": "",
                "booking_search_url": _build_booking_url("hotel", city),
                "amenities": [],
            }
        ],
        "alternative_hotels": [],
    }
