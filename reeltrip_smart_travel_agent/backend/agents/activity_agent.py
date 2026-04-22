"""
Activity Agent — the most complex agent.
Plans activities and restaurants for each day of the trip.

Uses: highlights data, must_include_places from preferences, Google Places
for restaurants, Tavily for prices/hours, and gpt-4o-mini for planning.
Groups by proximity, assigns day/time slots per weather/best-times.
Supports multi-city trips — searches restaurants per city.
"""
import json
import logging

from services.openai_client import call_openai_json
from services.tavily_client import search_tavily
from services.google_places_client import nearby_search, get_photo_url, text_search
from utils.geo import make_google_maps_url

logger = logging.getLogger(__name__)

ACTIVITY_SYSTEM_PROMPT = """You are an expert travel activity planner.
Given destination highlights, user preferences, weather data, and restaurant options,
plan a detailed activity schedule for each day of the trip.

RULES:
1. Must-include places from the user's bucket list take priority
2. Group nearby attractions together to minimize transit time
3. Assign outdoor activities to good weather times
4. Include 3 restaurant recommendations per day (breakfast, lunch, dinner)
5. All restaurants must match dietary preferences
6. No more than 4 major activities per day (excluding meals)
7. Estimate costs in the user's preferred currency
8. Include practical tips for each activity
9. Assign activities to specific days and time slots (morning/afternoon/evening)
10. For multi-city trips, assign activities and restaurants to the correct city for each day

Respond in JSON format ONLY."""


async def run_activity_agent(state: dict) -> dict:
    """Plan activities and dining for the trip."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    highlights = state.get("highlights", [])
    selected_cities = state.get("selected_cities", [])
    weather_data = state.get("weather_data")

    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    lat = location.get("city_latitude")
    lng = location.get("city_longitude")
    duration = prefs.get("trip_duration_days", 3)
    budget_currency = prefs.get("budget_currency", "INR")
    dietary = prefs.get("dietary_preferences", [])
    travel_styles = prefs.get("travel_styles", [])
    must_include = prefs.get("must_include_places", [])
    traveling_with = prefs.get("traveling_with", "partner")
    num_travelers = prefs.get("number_of_travelers", 2)

    if not dest_city and selected_cities:
        dest_city = selected_cities[0]

    cities_to_search = selected_cities if selected_cities else [dest_city]
    logger.info(f"[activity] Processing cities: {cities_to_search}, count: {len(cities_to_search)}")

    # Step 1: Gather activity data from highlights
    activities_from_highlights = []
    for h in highlights[:15]:
        activities_from_highlights.append({
            "name": h.get("place_name", ""),
            "description": h.get("description", ""),
            "vibe_tags": h.get("vibe_tags", []),
            "best_time": h.get("best_time_to_visit", ""),
            "duration": h.get("estimated_visit_duration", "1-2 hours"),
            "cost_usd": h.get("estimated_cost_usd", 0),
            "rating": h.get("rating"),
            "latitude": h.get("latitude", 0),
            "longitude": h.get("longitude", 0),
            "photo_url": h.get("photo_url", ""),
            "google_maps_url": h.get("google_maps_url", ""),
        })

    # Step 2: Tavily for prices/hours of top attractions
    price_data = []
    top_activities = (must_include + [a["name"] for a in activities_from_highlights[:5]])[:6]
    for activity_name in top_activities:
        if not activity_name:
            continue
        try:
            result = await search_tavily(
                f"{activity_name} {dest_city} ticket price hours 2026",
                max_results=2,
            )
            if result:
                price_data.append({
                    "activity": activity_name,
                    "results": [{"title": r.get("title", ""), "content": r.get("content", "")[:200]} for r in result[:2]],
                })
        except Exception as e:
            logger.warning(f"Activity agent: Tavily search failed for {activity_name}: {e}")

    # Step 3: Google Places for restaurants — search PER CITY
    restaurants_raw = []
    max_per_city = max(5, 15 // len(cities_to_search))

    for city in cities_to_search:
        try:
            # Get coordinates for this city
            if city == dest_city and lat and lng:
                city_lat, city_lng = lat, lng
            else:
                logger.info(f"Activity agent: geocoding {city} for restaurant search")
                geo_results = await text_search(f"{city}, {dest_country}", max_results=1)
                if geo_results:
                    city_lat = geo_results[0].get("latitude")
                    city_lng = geo_results[0].get("longitude")
                else:
                    logger.warning(f"Activity agent: could not geocode {city}, skipping restaurants")
                    continue

            city_restaurants = await nearby_search(city_lat, city_lng, "restaurant", radius=10000, max_results=max_per_city)

            # Tag each restaurant with its city and resolve photos
            for r in city_restaurants:
                r["city"] = city
                if r.get("photo_reference") and not r.get("photo_url"):
                    try:
                        r["photo_url"] = await get_photo_url(r["photo_reference"])
                    except Exception:
                        pass

            restaurants_raw.extend(city_restaurants)
            logger.info(f"Activity agent: found {len(city_restaurants)} restaurants in {city}")
        except Exception as e:
            logger.warning(f"Activity agent: restaurant search failed for {city}: {e}")

    slim_restaurants = []
    for r in restaurants_raw[:20]:
        slim_restaurants.append({
            "name": r.get("name", ""),
            "city": r.get("city", dest_city),
            "address": r.get("formatted_address", ""),
            "rating": r.get("rating"),
            "price_level": r.get("price_level"),
            "types": r.get("types", [])[:3],
            "latitude": r.get("latitude", 0),
            "longitude": r.get("longitude", 0),
            "photo_url": r.get("photo_url", ""),
        })

    # Step 4: Build the planning prompt
    weather_section = "No weather data available."
    if weather_data:
        weather_section = f"""Weather summary:
- Average high: {weather_data.get('avg_high_celsius', 'N/A')}°C
- Average low: {weather_data.get('avg_low_celsius', 'N/A')}°C
- Precipitation: {weather_data.get('precipitation_chance', 'unknown')}
- Best outdoor time: {weather_data.get('best_time_for_outdoor', 'morning and evening')}
- Warnings: {json.dumps(weather_data.get('warnings', []))}"""

    # Build multi-city instruction
    multi_city_instruction = ""
    if len(cities_to_search) > 1:
        days_per_city = max(1, duration // len(cities_to_search))
        city_day_map = []
        for i, city in enumerate(cities_to_search):
            start_day = i * days_per_city + 1
            end_day = min((i + 1) * days_per_city, duration) if i < len(cities_to_search) - 1 else duration
            city_day_map.append(f"  {city}: Days {start_day}-{end_day}")
        multi_city_instruction = f"""
MULTI-CITY TRIP — distribute activities across cities:
{chr(10).join(city_day_map)}
- Each city's days should have activities AND restaurants from THAT city only
- Assign the correct city to each activity and restaurant
- Travel days between cities may have fewer activities"""

    user_prompt = f"""Plan activities for a {duration}-day trip to {dest_country}.

CITIES: {json.dumps(cities_to_search)}
{multi_city_instruction}

TRAVELER PROFILE:
- Traveling with: {traveling_with}
- Number of travelers: {num_travelers}
- Travel styles: {json.dumps(travel_styles)}
- Dietary preferences: {json.dumps(dietary)}
- Must-include places: {json.dumps(must_include)}
- Currency: {budget_currency}

{weather_section}

DESTINATION HIGHLIGHTS (potential activities):
{json.dumps(activities_from_highlights, indent=1)[:4000]}

ACTIVITY PRICE RESEARCH:
{json.dumps(price_data, indent=1)[:2000]}

RESTAURANTS NEAR DESTINATIONS (tagged with city):
{json.dumps(slim_restaurants, indent=1)[:3000]}

Return JSON:
{{
    "planned_activities": [
        {{
            "name": "Activity Name",
            "type": "attraction|experience|show|tour",
            "city": "city name where this activity is",
            "address": "address if known",
            "latitude": number,
            "longitude": number,
            "photo_url": "url or empty",
            "rating": number or null,
            "suggested_day": day_number (1 to {duration}),
            "suggested_time_slot": "morning|afternoon|evening",
            "duration_minutes": number,
            "estimated_cost_per_person": number_in_{budget_currency},
            "currency": "{budget_currency}",
            "booking_url": "url or null",
            "description": "1-2 sentence description",
            "tip": "practical insider tip",
            "weather_dependent": true/false
        }}
    ],
    "restaurant_recommendations": [
        {{
            "name": "Restaurant Name",
            "cuisine": "cuisine type",
            "city": "city name where this restaurant is",
            "address": "address",
            "latitude": number,
            "longitude": number,
            "photo_url": "url or empty",
            "rating": number or null,
            "price_range": "$|$$|$$$|$$$$",
            "estimated_cost_per_person": number_in_{budget_currency},
            "currency": "{budget_currency}",
            "signature_dishes": ["dish1", "dish2"],
            "dietary_suitable": {json.dumps(dietary if dietary else ["no restrictions"])},
            "meal_type": "breakfast|lunch|dinner",
            "booking_url": null,
            "google_maps_url": "google maps url"
        }}
    ]
}}

IMPORTANT:
- Include {duration * 3} restaurant recommendations ({duration} days x 3 meals)
- All restaurants must serve food suitable for: {json.dumps(dietary if dietary else ['no restrictions'])}
- Must-include places MUST appear in planned_activities
- Group nearby activities on the same day
- Each activity and restaurant must have the correct "city" field"""

    result = await call_openai_json(
        task="fast",
        system_prompt=ACTIVITY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=6144,
        temperature=0.4,
    )

    if result:
        # Ensure google_maps_url for restaurants that have coordinates
        for r in result.get("restaurant_recommendations", []):
            if not r.get("google_maps_url") and r.get("latitude") and r.get("longitude"):
                r["google_maps_url"] = make_google_maps_url(
                    r["latitude"], r["longitude"], r.get("name", "")
                )
        return result

    return _fallback(highlights, cities_to_search, duration, budget_currency)


def _fallback(highlights: list, cities: list[str], duration: int, currency: str) -> dict:
    """Return highlights as basic activities when planning fails."""
    activities = []
    days_per_city = max(1, duration // len(cities)) if cities else duration

    for i, h in enumerate(highlights[:duration * 4]):
        day = (i // 4) + 1
        city_idx = min((day - 1) // days_per_city, len(cities) - 1) if cities else 0
        city = cities[city_idx] if cities else "Unknown"
        slots = ["morning", "afternoon", "afternoon", "evening"]
        activities.append({
            "name": h.get("place_name", f"Activity {i + 1}"),
            "type": "attraction",
            "city": city,
            "address": h.get("formatted_address", ""),
            "latitude": h.get("latitude", 0),
            "longitude": h.get("longitude", 0),
            "photo_url": h.get("photo_url", ""),
            "rating": h.get("rating"),
            "suggested_day": min(day, duration),
            "suggested_time_slot": slots[i % 4],
            "duration_minutes": 90,
            "estimated_cost_per_person": h.get("estimated_cost_usd", 0),
            "currency": "USD",
            "booking_url": None,
            "description": h.get("description", ""),
            "tip": None,
            "weather_dependent": False,
        })

    return {
        "planned_activities": activities,
        "restaurant_recommendations": [],
    }
