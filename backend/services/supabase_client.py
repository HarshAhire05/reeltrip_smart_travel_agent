"""
Thin wrapper around Supabase REST API. Every function is safe to call
even if Supabase is unreachable — returns None on failure.
NEVER let a cache failure crash the pipeline.
"""
from supabase import create_client, Client
from config import get_settings
import logging

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase() -> Client | None:
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.warning("Supabase not configured, caching disabled")
        return None
    try:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        return _client
    except Exception as e:
        logger.error(f"Supabase init failed: {e}")
        return None


# --- VIDEO INTELLIGENCE ---


async def get_cached_video(url: str) -> dict | None:
    """Return cached video intelligence or None."""
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("video_intelligence").select("*").eq("url", url).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Cache read error: {e}")
        return None


async def store_video(url: str, data: dict) -> bool:
    """Upsert video intelligence. Returns True on success."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("video_intelligence").upsert(
            {"url": url, **data}, on_conflict="url"
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Cache write error: {e}")
        return False


# --- LOCATION RESULTS ---


async def get_cached_location(url: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("location_results").select("*").eq("url", url).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Cache read error: {e}")
        return None


async def store_location(url: str, data: dict) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("location_results").upsert(
            {"url": url, **data}, on_conflict="url"
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Cache write error: {e}")
        return False


# --- ITINERARIES ---


async def store_itinerary(data: dict) -> str | None:
    """Store itinerary, return ID."""
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("itineraries").insert(data).execute()
        return result.data[0]["id"] if result and result.data else None
    except Exception as e:
        logger.error(f"Itinerary store error: {e}")
        return None


async def get_itinerary(itinerary_id: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("itineraries").select("*").eq("id", itinerary_id).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Itinerary read error: {e}")
        return None


async def update_itinerary(itinerary_id: str, updates: dict) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("itineraries").update(updates).eq("id", itinerary_id).execute()
        return True
    except Exception as e:
        logger.error(f"Itinerary update error: {e}")
        return False


# --- SESSIONS ---


async def create_session(session_id: str, url: str) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("sessions").upsert(
            {"id": session_id, "url": url, "stage": "processing"},
            on_conflict="id",
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Session create error: {e}")
        return False


async def get_session(session_id: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("sessions").select("*").eq("id", session_id).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        logger.error(f"Session read error: {e}")
        return None


async def update_session(session_id: str, updates: dict) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("sessions").update(updates).eq("id", session_id).execute()
        return True
    except Exception as e:
        logger.error(f"Session update error: {e}")
        return False


# --- PLACE CACHE ---


async def get_cached_place(place_id: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("place_cache").select("*").eq("place_id", place_id).execute()
        return result.data[0] if result and result.data else None
    except Exception as e:
        return None


async def store_place(data: dict) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("place_cache").upsert(data, on_conflict="place_id").execute()
        return True
    except Exception as e:
        return False
