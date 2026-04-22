"""
Geographic utility functions.
"""
import math
from urllib.parse import quote


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lng1: Coordinates of point 1 (decimal degrees)
        lat2, lng2: Coordinates of point 2 (decimal degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def make_google_maps_url(latitude: float, longitude: float, label: str = "") -> str:
    """
    Generate a Google Maps URL for a location.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        label: Optional label for the marker

    Returns:
        Google Maps URL string
    """
    if label:
        return f"https://www.google.com/maps/search/?api=1&query={quote(label)}+{latitude},{longitude}"
    return f"https://www.google.com/maps?q={latitude},{longitude}"
