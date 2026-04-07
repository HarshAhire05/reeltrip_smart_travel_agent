"""
Google Places API (New) wrapper using httpx async.
Uses field masks to minimize cost per call.
"""
import httpx
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = "https://places.googleapis.com/v1"

# Field masks — only request what we need
BASIC_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.userRatingCount,places.types,places.photos,"
    "places.priceLevel,places.websiteUri"
)
NEARBY_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.userRatingCount,places.types,places.photos,"
    "places.priceLevel"
)


async def text_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for places by text query.
    Example: text_search("Burj Khalifa, Dubai")
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
                    "X-Goog-FieldMask": BASIC_FIELDS,
                },
                json={
                    "textQuery": query,
                    "maxResultCount": max_results,
                    "languageCode": "en",
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                logger.error(
                    f"Places text search failed: {response.status_code} {response.text[:200]}"
                )
                return []

            data = response.json()
            return [_parse_place(p) for p in data.get("places", [])]

        except Exception as e:
            logger.error(f"Places text search error: {e}")
            return []


async def nearby_search(
    latitude: float,
    longitude: float,
    place_type: str,
    radius: int = 15000,
    max_results: int = 10,
) -> list[dict]:
    """
    Search for places near a location.
    place_type: "tourist_attraction" | "restaurant" | "lodging"
    """
    type_map = {
        "tourist_attraction": ["tourist_attraction", "museum", "amusement_park", "zoo", "aquarium"],
        "restaurant": ["restaurant", "cafe"],
        "lodging": ["lodging", "hotel"],
    }

    included_types = type_map.get(place_type, [place_type])

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/places:searchNearby",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
                    "X-Goog-FieldMask": NEARBY_FIELDS,
                },
                json={
                    "includedTypes": included_types,
                    "maxResultCount": min(max_results, 20),
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": latitude, "longitude": longitude},
                            "radius": float(radius),
                        }
                    },
                    "rankPreference": "POPULARITY",
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                logger.error(f"Nearby search failed: {response.status_code}")
                return []

            data = response.json()
            return [_parse_place(p) for p in data.get("places", [])]

        except Exception as e:
            logger.error(f"Nearby search error: {e}")
            return []


def get_photo_url(photo_name: str, max_width: int = 800) -> str | None:
    """
    Get a displayable photo URL from a Google Places photo reference.

    The photo_name comes from place data: places.photos[0].name
    Format: "places/{place_id}/photos/{photo_reference}"

    Returns a URL that can be used directly in <img> tags.
    """
    if not photo_name:
        return None

    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    return f"{url}?maxWidthPx={max_width}&key={settings.GOOGLE_PLACES_API_KEY}"


def _parse_place(raw: dict) -> dict:
    """Parse a raw Google Places API response into our format."""
    location = raw.get("location", {})
    display_name = raw.get("displayName", {})
    photos = raw.get("photos", [])

    return {
        "place_id": raw.get("id", ""),
        "name": display_name.get("text", "Unknown"),
        "formatted_address": raw.get("formattedAddress", ""),
        "latitude": location.get("latitude", 0.0),
        "longitude": location.get("longitude", 0.0),
        "rating": raw.get("rating"),
        "total_ratings": raw.get("userRatingCount"),
        "price_level": raw.get("priceLevel"),
        "types": raw.get("types", []),
        "photo_reference": photos[0].get("name") if photos else None,
        "website": raw.get("websiteUri"),
    }
