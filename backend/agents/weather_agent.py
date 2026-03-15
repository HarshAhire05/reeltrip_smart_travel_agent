"""
Weather Agent — uses Open-Meteo (NOT OpenWeatherMap) for weather data.
For trips within 16 days: Open-Meteo daily forecast.
For trips further out: Tavily fallback for monthly averages.
Minimal LLM usage — mostly direct data parsing.
"""
import logging
from datetime import datetime, timedelta

from services.weather_client import get_forecast, get_monthly_averages, decode_weather_code
from services.openai_client import call_openai_json

logger = logging.getLogger(__name__)


async def run_weather_agent(state: dict) -> dict:
    """Analyze weather conditions for the trip destination."""
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[weather] Processing cities: {selected_cities}")

    dest_city = location.get("primary_city", "")
    lat = location.get("city_latitude")
    lng = location.get("city_longitude")
    month = prefs.get("month_of_travel", "")
    duration = prefs.get("trip_duration_days", 3)

    # Determine if we can use the forecast API (within 16 days)
    use_forecast = False
    if lat and lng:
        try:
            # Estimate trip start: if month matches current/next month, use forecast
            now = datetime.now()
            month_names = [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
            ]
            if month.lower() in month_names:
                month_idx = month_names.index(month.lower()) + 1
                # Check if trip is within 16 days from now
                if month_idx == now.month:
                    use_forecast = True
                elif month_idx == now.month + 1 and now.day > 15:
                    use_forecast = True
        except Exception:
            pass

    weather_data = None

    if use_forecast and lat and lng:
        # Use Open-Meteo daily forecast
        forecast = await get_forecast(lat, lng, forecast_days=min(duration + 2, 16))
        if forecast and forecast.get("dates"):
            weather_data = _parse_forecast(forecast, dest_city, month)

    if not weather_data:
        # Fallback: monthly averages via Tavily
        averages = await get_monthly_averages(dest_city, month)
        if averages:
            weather_data = {
                "destination_city": dest_city,
                "travel_month": month,
                "avg_high_celsius": averages.get("avg_high_celsius", 0),
                "avg_low_celsius": averages.get("avg_low_celsius", 0),
                "precipitation_chance": averages.get("precipitation_chance", "low"),
                "weather_description": averages.get("weather_description", ""),
                "data_source": "monthly_averages",
            }

    if not weather_data:
        logger.warning("Weather agent: no data available, returning fallback")
        return _fallback(dest_city, month)

    # Use LLM only for generating warnings and packing suggestions from raw data
    result = await _enrich_with_suggestions(weather_data)
    return result


def _parse_forecast(forecast: dict, city: str, month: str) -> dict:
    """Parse Open-Meteo forecast arrays into summary."""
    temps_max = forecast.get("temperature_max", [])
    temps_min = forecast.get("temperature_min", [])
    precip = forecast.get("precipitation_probability_max", [])
    codes = forecast.get("weather_code", [])

    avg_high = sum(temps_max) / len(temps_max) if temps_max else 0
    avg_low = sum(temps_min) / len(temps_min) if temps_min else 0
    avg_precip = sum(precip) / len(precip) if precip else 0

    # Determine precipitation level
    if avg_precip > 60:
        precip_level = "high"
    elif avg_precip > 30:
        precip_level = "moderate"
    else:
        precip_level = "low"

    # Decode most common weather codes
    weather_descriptions = [decode_weather_code(c) for c in codes if c is not None]
    most_common = max(set(weather_descriptions), key=weather_descriptions.count) if weather_descriptions else "Unknown"

    return {
        "destination_city": city,
        "travel_month": month,
        "avg_high_celsius": round(avg_high, 1),
        "avg_low_celsius": round(avg_low, 1),
        "precipitation_chance": precip_level,
        "weather_description": f"Mostly {most_common.lower()}. Highs around {round(avg_high)}°C, lows around {round(avg_low)}°C.",
        "daily_forecast": [
            {
                "date": forecast["dates"][i] if i < len(forecast.get("dates", [])) else "",
                "high": temps_max[i] if i < len(temps_max) else 0,
                "low": temps_min[i] if i < len(temps_min) else 0,
                "precip_chance": precip[i] if i < len(precip) else 0,
                "condition": decode_weather_code(codes[i]) if i < len(codes) else "",
            }
            for i in range(len(forecast.get("dates", [])))
        ],
        "data_source": "open_meteo_forecast",
    }


async def _enrich_with_suggestions(weather_data: dict) -> dict:
    """Use gpt-4o-mini to generate human-readable warnings and packing suggestions."""
    avg_high = weather_data.get("avg_high_celsius", 0)
    avg_low = weather_data.get("avg_low_celsius", 0)
    precip = weather_data.get("precipitation_chance", "low")
    description = weather_data.get("weather_description", "")
    city = weather_data.get("destination_city", "")
    month = weather_data.get("travel_month", "")

    result = await call_openai_json(
        task="fast",
        system_prompt="You are a travel weather advisor. Generate practical weather advice for travelers. Respond in JSON format ONLY.",
        user_prompt=f"""Weather data for {city} in {month}:
- Average high: {avg_high}°C
- Average low: {avg_low}°C
- Precipitation chance: {precip}
- Conditions: {description}

Return JSON:
{{
    "warnings": ["list of weather warnings if any, e.g. extreme heat, monsoon season"],
    "recommendations": ["practical advice like schedule outdoor activities for morning"],
    "best_time_for_outdoor": "when outdoor activities are best",
    "pack_suggestions": ["specific items to pack based on this weather"]
}}""",
        max_tokens=512,
        temperature=0.3,
    )

    # Merge LLM suggestions into weather data
    if result:
        weather_data["warnings"] = result.get("warnings", [])
        weather_data["recommendations"] = result.get("recommendations", [])
        weather_data["best_time_for_outdoor"] = result.get("best_time_for_outdoor", "")
        weather_data["pack_suggestions"] = result.get("pack_suggestions", [])
    else:
        # Basic fallback suggestions
        weather_data["warnings"] = []
        weather_data["recommendations"] = ["Check local weather before outdoor activities"]
        weather_data["best_time_for_outdoor"] = "morning and evening"
        weather_data["pack_suggestions"] = _basic_packing(avg_high, avg_low, precip)

    return weather_data


def _basic_packing(high: float, low: float, precip: str) -> list[str]:
    """Generate basic packing suggestions without LLM."""
    items = []
    if high > 30:
        items.extend(["sunscreen SPF 50+", "sunglasses", "hat", "light breathable clothing"])
    elif high > 20:
        items.extend(["light layers", "sunscreen", "sunglasses"])
    else:
        items.extend(["warm jacket", "layers", "scarf"])

    if low < 10:
        items.append("warm coat for evenings")

    if precip in ("moderate", "high"):
        items.extend(["umbrella", "waterproof jacket"])

    items.append("comfortable walking shoes")
    return items


def _fallback(city: str, month: str) -> dict:
    """Return minimal weather data when all sources fail."""
    return {
        "destination_city": city,
        "travel_month": month,
        "avg_high_celsius": 0,
        "avg_low_celsius": 0,
        "precipitation_chance": "unknown",
        "weather_description": f"Weather data unavailable for {city} in {month}. Check local forecasts before traveling.",
        "warnings": [],
        "recommendations": ["Check local weather forecast before your trip"],
        "best_time_for_outdoor": "morning and evening",
        "pack_suggestions": ["layers for varying conditions", "comfortable walking shoes", "sunscreen"],
    }
