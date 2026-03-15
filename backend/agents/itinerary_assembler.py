"""
Itinerary Assembler — the most important prompt in the system.
Takes ALL agent outputs and creates the final day-by-day TripItinerary.
Uses gpt-4o (reasoning model) for complex multi-constraint reasoning.
"""
import json
import logging
from datetime import datetime, timedelta

from services.openai_client import call_openai_json

logger = logging.getLogger(__name__)

ASSEMBLER_SYSTEM_PROMPT = """You are the world's best travel itinerary planner.
You have been given research data from specialized travel agents. Your job is to
assemble this data into a perfect day-by-day itinerary.

CRITICAL RULES:
1. The itinerary must be PHYSICALLY POSSIBLE — check travel times between locations
2. First day starts AFTER flight arrival time
3. Last day ends BEFORE flight departure time
4. Meals: breakfast 7:30-9:00, lunch 12:00-14:00, dinner 19:00-21:00
5. No more than 4 major activities per day (excluding meals and transport)
6. Group nearby places together to minimize transit time
7. Respect dietary preferences for ALL food recommendations
8. Include must-have items from the user's bucket list
9. Account for weather — avoid outdoor activities during bad weather times
10. Budget must not exceed the stated budget if possible
11. Include realistic travel times between every activity
12. Every restaurant must match dietary preferences
13. Every cost must be in the user's preferred currency
14. MULTI-CITY RULES (when multiple cities are selected):
    a. Allocate days across cities proportionally: for N cities over D days, roughly D/N days per city
    b. Travel days between cities: include inter-city transport as first activity after hotel checkout.
       Account for travel time — a 4-hour train means fewer activities that day
    c. Hotel check-out in departing city happens in the morning; check-in in arriving city after arrival
    d. The international departure flight should leave from the LAST city (open-jaw routing).
       Do NOT backtrack to the first city unless no international airport exists in the last city
    e. In Europe: prefer trains (Deutsche Bahn, TGV, Eurostar). In large countries (USA, India): use domestic flights.
       In small areas (UAE, Singapore): use taxi/bus
    f. Each city must have its own hotel, own restaurant recommendations, and own activities
    g. Assign each day's activities and restaurants only from the city the traveler is in that day
15. Include check-in on arrival day and check-out on departure day
16. Each activity needs time, title, type, description, and practical_tip

Respond in JSON format ONLY.
Output must follow the EXACT schema provided."""


async def run_assembler(state: dict) -> dict | None:
    """Assemble the final itinerary from all agent outputs."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[assembler] Processing cities: {selected_cities}, duration: {prefs.get('trip_duration_days', 3)} days")

    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    duration = prefs.get("trip_duration_days", 3)
    num_travelers = prefs.get("number_of_travelers", 2)
    month = prefs.get("month_of_travel", "")
    budget_currency = prefs.get("budget_currency", "INR")

    # Build the mega-prompt with all agent data
    user_prompt = f"""
DESTINATION: {dest_city}, {dest_country}
SELECTED CITIES: {json.dumps(selected_cities)}

USER PREFERENCES:
{json.dumps(prefs, indent=2)}

FLIGHT DATA:
{_safe_json(state.get('flight_data'), 'No flight data available')}

HOTEL DATA:
{_safe_json(state.get('hotel_data'), 'No hotel data available')}

WEATHER DATA:
{_safe_json(state.get('weather_data'), 'No weather data available')}

SAFETY DATA:
{_safe_json(state.get('safety_data'), 'No safety data available')}

ACTIVITY DATA:
{_safe_json(state.get('activity_data'), 'No activity data available', max_len=6000)}

TRANSPORT DATA:
{_safe_json(state.get('transport_data'), 'No transport data available')}

BUDGET ANALYSIS:
{_safe_json(state.get('budget_analysis'), 'No budget analysis available')}

---

Generate a complete itinerary as JSON with this EXACT structure:
{{
    "trip_title": "Creative, inspiring trip title",
    "destination_country": "{dest_country}",
    "destination_cities": {json.dumps(selected_cities if selected_cities else [dest_city])},
    "start_date": "estimated date based on {month} (e.g., {month} 1, 2026)",
    "end_date": "start_date + {duration - 1} days",
    "total_days": {duration},
    "total_travelers": {num_travelers},
    "flights": [
        {{
            "type": "international or domestic",
            "from_city": "string",
            "from_airport_code": "IATA",
            "to_city": "string",
            "to_airport_code": "IATA",
            "departure_datetime": "YYYY-MM-DD HH:MM",
            "arrival_datetime": "YYYY-MM-DD HH:MM",
            "duration": "Xh Ym",
            "estimated_price": number_per_person,
            "price_currency": "{budget_currency}",
            "booking_url": "Google Flights URL",
            "notes": "any notes",
            "day_number": 1
        }}
    ],
    "hotels": [
        {{
            "hotel_name": "Real Hotel Name",
            "city": "City",
            "address": "Full address",
            "check_in_date": "YYYY-MM-DD",
            "check_out_date": "YYYY-MM-DD",
            "nights": {duration - 1},
            "price_per_night": number,
            "total_price": number,
            "price_currency": "{budget_currency}",
            "rating": 4.5,
            "photo_url": null,
            "why_recommended": "1-2 sentences",
            "booking_url": "Google Hotels URL",
            "latitude": number,
            "longitude": number
        }}
    ],
    "days": [
        {{
            "day_number": 1,
            "date": "{month} 1, 2026",
            "city": "{dest_city}",
            "theme": "Arrival & First Impressions",
            "activities": [
                {{
                    "time": "HH:MM",
                    "title": "Activity Title",
                    "type": "flight|checkin|checkout|meal|attraction|activity|transport|free_time",
                    "venue_name": "Venue Name or null",
                    "venue_address": "address or null",
                    "latitude": null,
                    "longitude": null,
                    "photo_url": null,
                    "rating": null,
                    "duration_minutes": number,
                    "estimated_cost": number (total for all travelers),
                    "cost_currency": "{budget_currency}",
                    "description": "1 concise sentence",
                    "practical_tip": "1 short sentence or null",
                    "booking_url": null,
                    "google_maps_url": null
                }}
            ]
        }}
    ],
    "budget_breakdown": {{
        "flights_total": number,
        "accommodation_total": number,
        "food_total": number,
        "activities_total": number,
        "transportation_total": number,
        "miscellaneous_buffer": number,
        "grand_total": number,
        "currency": "{budget_currency}",
        "budget_status": "within_budget|over_budget|under_budget",
        "savings_tips": ["tip1", "tip2"] or null
    }},
    "visa_requirements": {{
        "required": true/false,
        "visa_type": "type or empty",
        "processing_time": "time or empty",
        "estimated_cost": "cost or empty",
        "documents_needed": ["list"],
        "notes": "additional notes"
    }} or null,
    "weather_summary": {{
        "overview": "brief weather description for the travel period",
        "avg_high_celsius": number,
        "avg_low_celsius": number,
        "precipitation_chance": "low|moderate|high",
        "pack_suggestions": ["item1", "item2"]
    }},
    "packing_suggestions": ["item1", "item2", "item3"],
    "cultural_tips": ["tip1", "tip2"],
    "emergency_info": {{
        "police": "number",
        "ambulance": "number",
        "fire": "number",
        "tourist_police": "number or empty",
        "embassy_phone": "number or empty",
        "emergency_notes": ["useful notes"]
    }},
    "currency_info": {{
        "local_currency": "currency code",
        "local_currency_name": "full name",
        "exchange_rate": "1 {budget_currency} = X local currency",
        "tips": ["currency tips"]
    }}
}}

IMPORTANT:
- Generate exactly {duration} days in the "days" array
- Each day must have a full schedule from morning to evening
- Include 3 meals per day (breakfast, lunch, dinner)
- First activity of Day 1 should be flight arrival (if applicable)
- Last activity of Day {duration} should be flight departure (if applicable)
- All costs in {budget_currency}
- Keep descriptions to 1 sentence max per activity
- Include photo_url from activity data when available, otherwise set to null
- Keep practical_tip to 1 short sentence or null
- Include booking_url and google_maps_url from activity data when available
- For venues with latitude/longitude, generate google_maps_url as: https://www.google.com/maps/search/?api=1&query=LAT,LNG
- Keep descriptions concise to stay within token limits"""

    result = await call_openai_json(
        task="reasoning",  # gpt-4o — complex multi-constraint reasoning
        system_prompt=ASSEMBLER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=16384,
        temperature=0.3,
        retries=3,
    )

    if result:
        return result

    # Fallback: build a basic itinerary from raw agent data
    logger.warning("Itinerary assembly failed — using fallback builder")
    return _build_fallback_itinerary(state)


def _safe_json(data: dict | None, fallback_msg: str, max_len: int = 3000) -> str:
    """Safely serialize data to JSON string with length limit."""
    if not data:
        return fallback_msg
    text = json.dumps(data, indent=2)
    if len(text) > max_len:
        return text[:max_len] + "\n... (truncated)"
    return text


def _build_fallback_itinerary(state: dict) -> dict:
    """
    Build a basic but valid itinerary from raw agent data when LLM assembly fails.
    This is a degraded fallback — better than showing nothing.
    """
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])
    flight_data = state.get("flight_data") or {}
    hotel_data = state.get("hotel_data") or {}
    weather_data = state.get("weather_data") or {}
    safety_data = state.get("safety_data") or {}
    activity_data = state.get("activity_data") or {}
    budget_data = state.get("budget_analysis") or {}

    dest_city = location.get("primary_city", "Unknown")
    dest_country = location.get("primary_country", "Unknown")
    duration = prefs.get("trip_duration_days", 3)
    num_travelers = prefs.get("number_of_travelers", 2)
    month = prefs.get("month_of_travel", "January")
    currency = prefs.get("budget_currency", "INR")

    cities = selected_cities if selected_cities else [dest_city]

    # Build start date
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    month_num = month_map.get(month, 1)
    start = datetime(2026, month_num, 7)

    # Extract flights
    flights = []
    outbound = flight_data.get("recommended_outbound") or (
        flight_data.get("outbound_options", [{}])[0] if flight_data.get("outbound_options") else {}
    )
    ret = flight_data.get("recommended_return") or (
        flight_data.get("return_options", [{}])[0] if flight_data.get("return_options") else {}
    )
    if outbound and outbound.get("from_city"):
        flights.append({
            "type": flight_data.get("route_type", "international"),
            "from_city": outbound.get("from_city", ""),
            "from_airport_code": outbound.get("from_airport_code", "???"),
            "to_city": outbound.get("to_city", dest_city),
            "to_airport_code": outbound.get("to_airport_code", "???"),
            "departure_datetime": outbound.get("departure_datetime", f"{start.strftime('%Y-%m-%d')} 06:00"),
            "arrival_datetime": outbound.get("arrival_datetime", f"{start.strftime('%Y-%m-%d')} 12:00"),
            "duration": outbound.get("duration", "6h 0m"),
            "estimated_price": outbound.get("estimated_price", 0),
            "price_currency": currency,
            "booking_url": flight_data.get("booking_search_url", ""),
            "notes": None,
            "day_number": 1,
        })
    if ret and ret.get("from_city"):
        end_date = start + timedelta(days=duration - 1)
        flights.append({
            "type": flight_data.get("route_type", "international"),
            "from_city": ret.get("from_city", dest_city),
            "from_airport_code": ret.get("from_airport_code", "???"),
            "to_city": ret.get("to_city", ""),
            "to_airport_code": ret.get("to_airport_code", "???"),
            "departure_datetime": ret.get("departure_datetime", f"{end_date.strftime('%Y-%m-%d')} 20:00"),
            "arrival_datetime": ret.get("arrival_datetime", f"{end_date.strftime('%Y-%m-%d')} 23:59"),
            "duration": ret.get("duration", "6h 0m"),
            "estimated_price": ret.get("estimated_price", 0),
            "price_currency": currency,
            "booking_url": flight_data.get("booking_search_url", ""),
            "notes": None,
            "day_number": duration,
        })

    # Extract hotels — distribute across cities with proper check-in/check-out dates
    hotels = []
    # Calculate days per city for multi-city distribution
    days_per_city: dict[str, tuple[int, int]] = {}  # city -> (start_day, end_day)
    if cities:
        days_each = max(1, duration // len(cities))
        remainder = duration - days_each * len(cities)
        day_cursor = 0
        for i, c in enumerate(cities):
            extra = 1 if i < remainder else 0
            city_days = days_each + extra
            days_per_city[c] = (day_cursor, day_cursor + city_days)
            day_cursor += city_days

    for h in hotel_data.get("recommended_hotels", []):
        hotel_city = h.get("city", dest_city)
        # Find this hotel's city check-in/check-out dates
        if hotel_city in days_per_city:
            city_start_day, city_end_day = days_per_city[hotel_city]
        else:
            city_start_day, city_end_day = 0, duration
        checkin = start + timedelta(days=city_start_day)
        checkout = start + timedelta(days=city_end_day - 1) if city_end_day > city_start_day else checkin + timedelta(days=1)
        nights = max(1, (checkout - checkin).days)

        hotels.append({
            "hotel_name": h.get("name", "Hotel"),
            "city": hotel_city,
            "address": h.get("address", ""),
            "check_in_date": checkin.strftime("%Y-%m-%d"),
            "check_out_date": checkout.strftime("%Y-%m-%d"),
            "nights": nights,
            "price_per_night": h.get("price_per_night_estimate", 0),
            "total_price": h.get("price_per_night_estimate", 0) * nights,
            "price_currency": currency,
            "rating": h.get("rating", 4.0),
            "photo_url": h.get("photo_url"),
            "why_recommended": h.get("why_recommended", "Recommended by our hotel agent."),
            "booking_url": h.get("booking_search_url", ""),
            "latitude": h.get("latitude", 0),
            "longitude": h.get("longitude", 0),
        })

    # Build days with basic activities
    planned = activity_data.get("planned_activities", [])
    restaurants = activity_data.get("restaurant_recommendations", [])
    days = []

    for d in range(1, duration + 1):
        date = start + timedelta(days=d - 1)
        city = cities[min(d - 1, len(cities) - 1)] if cities else dest_city
        activities = []

        # Day 1: arrival
        if d == 1 and flights:
            activities.append(_make_activity("12:00", "Arrive & Check In", "checkin", currency, 0))

        # Breakfast
        breakfast_rest = next((r for r in restaurants if r.get("meal_type") == "breakfast" and r.get("city", dest_city) == city), None)
        activities.append(_make_activity(
            "08:00", breakfast_rest.get("name", "Breakfast") if breakfast_rest else "Breakfast",
            "meal", currency, breakfast_rest.get("estimated_cost_per_person", 0) * num_travelers if breakfast_rest else 0
        ))

        # Morning + afternoon activities for this day
        day_activities = [a for a in planned if a.get("suggested_day") == d]
        if not day_activities:
            # Distribute evenly if no day assignment
            per_day = max(1, len(planned) // duration)
            start_idx = (d - 1) * per_day
            day_activities = planned[start_idx:start_idx + per_day]

        times = ["09:30", "11:00", "14:30", "16:00"]
        for idx, act in enumerate(day_activities[:4]):
            t = times[idx] if idx < len(times) else f"{14 + idx}:00"
            activities.append(_make_activity(
                t,
                act.get("name", "Activity"),
                "attraction",
                currency,
                act.get("estimated_cost_per_person", 0) * num_travelers,
                venue=act.get("name"),
                address=act.get("address"),
                description=act.get("description", ""),
                tip=act.get("tip"),
                photo_url=act.get("photo_url"),
                latitude=act.get("latitude"),
                longitude=act.get("longitude"),
                booking_url=act.get("booking_url"),
                google_maps_url=act.get("google_maps_url"),
            ))

        # Lunch
        lunch_rest = next((r for r in restaurants if r.get("meal_type") == "lunch" and r.get("city", dest_city) == city), None)
        activities.append(_make_activity(
            "12:30", lunch_rest.get("name", "Lunch") if lunch_rest else "Lunch",
            "meal", currency, lunch_rest.get("estimated_cost_per_person", 0) * num_travelers if lunch_rest else 0
        ))

        # Dinner
        dinner_rest = next((r for r in restaurants if r.get("meal_type") == "dinner" and r.get("city", dest_city) == city), None)
        activities.append(_make_activity(
            "19:30", dinner_rest.get("name", "Dinner") if dinner_rest else "Dinner",
            "meal", currency, dinner_rest.get("estimated_cost_per_person", 0) * num_travelers if dinner_rest else 0
        ))

        # Last day: departure
        if d == duration and flights:
            activities.append(_make_activity("21:00", "Depart", "flight", currency, 0))

        # Sort by time
        activities.sort(key=lambda a: a["time"])

        days.append({
            "day_number": d,
            "date": date.strftime("%B %d, %Y"),
            "city": city,
            "theme": f"Day {d} in {city}",
            "activities": activities,
        })

    # Budget breakdown
    breakdown = {
        "flights_total": budget_data.get("breakdown", {}).get("flights", 0),
        "accommodation_total": budget_data.get("breakdown", {}).get("accommodation", 0),
        "food_total": budget_data.get("breakdown", {}).get("food", 0),
        "activities_total": budget_data.get("breakdown", {}).get("activities", 0),
        "transportation_total": budget_data.get("breakdown", {}).get("transportation", 0),
        "miscellaneous_buffer": budget_data.get("breakdown", {}).get("misc_buffer", 0),
        "grand_total": budget_data.get("total_estimated_cost", 0),
        "currency": currency,
        "budget_status": budget_data.get("budget_status", "within_budget"),
        "savings_tips": budget_data.get("optimization_suggestions"),
    }

    # Weather
    weather = {
        "overview": weather_data.get("weather_description", f"Typical {month} weather."),
        "avg_high_celsius": weather_data.get("avg_high_celsius", 30),
        "avg_low_celsius": weather_data.get("avg_low_celsius", 20),
        "precipitation_chance": weather_data.get("precipitation_chance", "low"),
        "pack_suggestions": weather_data.get("pack_suggestions", []),
    }

    # Emergency
    emergency = safety_data.get("emergency_numbers", {})
    emergency_info = {
        "police": emergency.get("police", "911"),
        "ambulance": emergency.get("ambulance", "911"),
        "fire": emergency.get("fire", "911"),
        "tourist_police": emergency.get("tourist_police", ""),
        "embassy_phone": "",
        "emergency_notes": safety_data.get("scam_warnings", []),
    }

    return {
        "trip_title": f"{duration}-Day {dest_city} Adventure",
        "destination_country": dest_country,
        "destination_cities": cities,
        "start_date": start.strftime("%B %d, %Y"),
        "end_date": (start + timedelta(days=duration - 1)).strftime("%B %d, %Y"),
        "total_days": duration,
        "total_travelers": num_travelers,
        "flights": flights,
        "hotels": hotels,
        "days": days,
        "budget_breakdown": breakdown,
        "visa_requirements": None,
        "weather_summary": weather,
        "packing_suggestions": weather_data.get("pack_suggestions", ["Comfortable shoes", "Sunscreen", "Light layers"]),
        "cultural_tips": safety_data.get("cultural_etiquette", ["Respect local customs."]),
        "emergency_info": emergency_info,
        "currency_info": {
            "local_currency": currency,
            "local_currency_name": currency,
            "exchange_rate": "",
            "tips": [],
        },
    }


def _make_activity(
    time: str,
    title: str,
    activity_type: str,
    currency: str,
    cost: float,
    venue: str | None = None,
    address: str | None = None,
    description: str = "",
    tip: str | None = None,
    photo_url: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    booking_url: str | None = None,
    google_maps_url: str | None = None,
) -> dict:
    """Create a single activity dict with safe defaults."""
    # Generate google_maps_url from coordinates if not provided
    if not google_maps_url and latitude and longitude:
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

    return {
        "time": time,
        "title": title,
        "type": activity_type,
        "venue_name": venue,
        "venue_address": address,
        "latitude": latitude,
        "longitude": longitude,
        "photo_url": photo_url,
        "rating": None,
        "duration_minutes": 60,
        "estimated_cost": cost,
        "cost_currency": currency,
        "description": description or title,
        "practical_tip": tip,
        "booking_url": booking_url,
        "google_maps_url": google_maps_url,
    }
