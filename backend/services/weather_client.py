"""
Weather data client using Open-Meteo API.
Completely free, no API key required, no signup needed.
Endpoint: https://api.open-meteo.com/v1/forecast
"""
import httpx
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def get_forecast(latitude: float, longitude: float, forecast_days: int = 16) -> dict | None:
    """
    Get weather forecast for a location.
    Works for trips within 16 days from today.

    Returns dict with daily forecast data:
    {
        "dates": ["2026-03-15", ...],
        "temperature_max": [32.5, ...],
        "temperature_min": [22.1, ...],
        "precipitation_probability_max": [10, ...],
        "weather_code": [0, ...]
    }
    or None on failure.

    Weather codes: https://open-meteo.com/en/docs
    0 = Clear, 1-3 = Partly cloudy, 45-48 = Fog,
    51-55 = Drizzle, 61-65 = Rain, 71-77 = Snow,
    80-82 = Rain showers, 95-99 = Thunderstorm
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "timezone": "auto",
        "forecast_days": min(forecast_days, 16),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"Open-Meteo request failed: {response.status_code} {response.text[:200]}")
                return None

            data = response.json()
            daily = data.get("daily", {})

            return {
                "dates": daily.get("time", []),
                "temperature_max": daily.get("temperature_2m_max", []),
                "temperature_min": daily.get("temperature_2m_min", []),
                "precipitation_probability_max": daily.get("precipitation_probability_max", []),
                "weather_code": daily.get("weather_code", []),
            }

        except Exception as e:
            logger.error(f"Open-Meteo forecast error: {e}")
            return None


async def get_monthly_averages(city: str, month: str) -> dict | None:
    """
    Get average weather for a city in a specific month.
    Uses Tavily web search as fallback for trips beyond 16 days.

    Returns dict with average data or None on failure.
    """
    # Import here to avoid circular dependency
    from services.tavily_client import search_tavily

    query = f"average weather {city} {month} temperature rainfall"
    results = await search_tavily(query, max_results=3)

    if not results:
        return None

    # Import here to avoid circular dependency
    from services.openai_client import call_openai_json

    search_text = "\n".join(
        [f"- {r.get('title', '')}: {r.get('content', '')[:300]}" for r in results[:3]]
    )

    result = await call_openai_json(
        task="fast",
        system_prompt=(
            "You are a weather data extraction assistant. "
            "Extract average weather information from search results. "
            "Respond in JSON format ONLY."
        ),
        user_prompt=f"""Extract average weather for {city} in {month} from these search results:

{search_text}

Return JSON:
{{
    "avg_high_celsius": number,
    "avg_low_celsius": number,
    "precipitation_chance": "low|moderate|high",
    "weather_description": "brief description",
    "data_source": "web_search_estimate"
}}""",
        max_tokens=512,
        temperature=0.2,
    )

    return result


def decode_weather_code(code: int) -> str:
    """Convert WMO weather code to human-readable description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return weather_codes.get(code, f"Unknown (code {code})")
