"""
pipeline/location_validator.py

Google Places integration — API orchestration, NOT an LLM call.
Takes location_detector output, validates via Google Places, enriches with
nearby attractions/restaurants/hotels, resolves photo URLs.
"""
import asyncio
import logging
from pipeline.location_detector import detect_locations
from services.google_places_client import text_search, nearby_search, get_photo_url
from services.supabase_client import get_cached_place, store_place
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def validate_and_enrich_locations(content_analysis: dict) -> dict | None:
    """
    Full location validation and enrichment pipeline.

    Steps:
        1. detect_locations() -> primary destination + ranked places
        2. text_search() for primary city -> coordinates
        3. text_search() for each specific place -> validated_places
        4. nearby_search() for attractions, restaurants, hotels (parallel)
        5. Resolve photo URLs

    Returns LocationResult-compatible dict or None on failure.
    """
    # Step 1: Detect and rank locations
    detection = await detect_locations(content_analysis)
    if not detection:
        logger.error("Location detection returned None")
        return None

    primary_country = detection.get("primary_country", "")
    primary_region = detection.get("primary_region", "")
    primary_city = detection.get("primary_city", "")
    ranked_locations = detection.get("ranked_locations", [])

    if not primary_city:
        logger.error("No primary city detected")
        return None

    # Step 2: Search for primary city to get coordinates
    city_results = await text_search(f"{primary_city}, {primary_country}", max_results=1)
    if not city_results:
        logger.warning(f"Could not find city coordinates for {primary_city}")
        # Try without country
        city_results = await text_search(primary_city, max_results=1)

    city_lat = None
    city_lng = None
    if city_results:
        city_lat = city_results[0].get("latitude", 0.0)
        city_lng = city_results[0].get("longitude", 0.0)

    # Step 3: Validate each specific place via text_search
    validated_places = []
    for loc in ranked_locations[:10]:  # Cap at 10 to limit API calls
        place_name = loc.get("name", "")
        if not place_name:
            continue

        # Check place cache first
        cached = None
        if settings.ENABLE_CACHE:
            # Use a composite key for cache lookup
            cached = await _search_place_cache(place_name, primary_city)

        if cached:
            validated_places.append(cached)
            continue

        try:
            results = await text_search(f"{place_name}, {primary_city}", max_results=1)
            if results:
                place = results[0]
                place["source"] = "video_detected"
                validated_places.append(place)

                # Cache the place
                if settings.ENABLE_CACHE and place.get("place_id"):
                    await store_place(place)
        except Exception as e:
            logger.warning(f"Failed to validate place '{place_name}': {e}")
            continue

    # Step 4: Nearby searches (parallel) — only if we have coordinates
    nearby_attractions = []
    nearby_restaurants = []
    nearby_hotels = []

    if city_lat and city_lng:
        try:
            attractions_task = nearby_search(city_lat, city_lng, "tourist_attraction", radius=15000, max_results=10)
            restaurants_task = nearby_search(city_lat, city_lng, "restaurant", radius=10000, max_results=8)
            hotels_task = nearby_search(city_lat, city_lng, "lodging", radius=15000, max_results=8)

            results = await asyncio.gather(
                attractions_task, restaurants_task, hotels_task,
                return_exceptions=True,
            )

            if not isinstance(results[0], Exception):
                nearby_attractions = results[0]
            else:
                logger.warning(f"Nearby attractions search failed: {results[0]}")

            if not isinstance(results[1], Exception):
                nearby_restaurants = results[1]
            else:
                logger.warning(f"Nearby restaurants search failed: {results[1]}")

            if not isinstance(results[2], Exception):
                nearby_hotels = results[2]
            else:
                logger.warning(f"Nearby hotels search failed: {results[2]}")

        except Exception as e:
            logger.error(f"Nearby search failed: {e}")

    # Step 5: Resolve photo URLs for all places
    all_places = validated_places + nearby_attractions + nearby_restaurants + nearby_hotels
    for place in all_places:
        if place.get("photo_reference") and not place.get("photo_url"):
            place["photo_url"] = get_photo_url(place["photo_reference"])

    return {
        "primary_country": primary_country,
        "primary_region": primary_region,
        "primary_city": primary_city,
        "city_latitude": city_lat,
        "city_longitude": city_lng,
        "validated_places": validated_places,
        "nearby_attractions": nearby_attractions,
        "nearby_restaurants": nearby_restaurants,
        "nearby_hotels": nearby_hotels,
    }


async def _search_place_cache(place_name: str, city: str) -> dict | None:
    """Try to find a cached place by searching for a matching place_id."""
    # Place cache is keyed by place_id, not by name.
    # We can't efficiently look up by name, so skip cache for text_search lookups.
    # The cache is more useful for individual place_id lookups in later stages.
    return None
