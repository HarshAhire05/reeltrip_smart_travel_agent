"""
pipeline/location_detector.py

GPT-4o-mini location ranking and deduplication.
Takes candidate_locations from content fusion, deduplicates, ranks by confidence,
and extracts the primary destination.
"""
from services.openai_client import call_openai_json
import json
import logging

logger = logging.getLogger(__name__)

# Generic terms that are not actual places
NON_PLACE_WORDS = {
    "travel", "adventure", "vlog", "explore", "wanderlust", "trip",
    "vacation", "holiday", "tourism", "tourist", "journey", "destination",
    "backpacking", "roadtrip", "weekend", "getaway", "staycation",
    "foodie", "luxury", "budget", "solo", "couple", "family",
    "reels", "shorts", "tiktok", "viral", "trending", "fyp",
}

DETECTOR_SYSTEM_PROMPT = """You are a geographic location specialist. You will receive
candidate locations detected from a travel video along with destination information.

Your job:
1. Deduplicate locations (merge "Burj Khalifa" and "Burj Khalifa, Dubai" into one)
2. Standardize names (use the most common/recognizable form)
3. Remove non-place entries (generic terms, hashtags, activities)
4. Rank by confidence (how certain we are this place appears in the video)
5. Identify the PRIMARY destination (the main city/country the video is about)

Respond in JSON format ONLY."""

DETECTOR_USER_PROMPT = """Analyze these detected locations from a travel video:

Destination info from content analysis:
- Country: {country}
- Region: {region}
- City: {city}
- Confidence: {confidence}

Candidate locations:
{candidates_json}

Return JSON:
{{
    "primary_country": "string",
    "primary_region": "string",
    "primary_city": "string",
    "ranked_locations": [
        {{
            "name": "Place Name (standardized)",
            "type": "city|landmark|area|beach|restaurant|hotel|market|attraction",
            "confidence": "high|medium|low"
        }}
    ]
}}

Rules:
- Remove duplicates (keep the most specific version)
- Remove generic/non-place entries
- Rank from highest to lowest confidence
- Limit to top 10 most relevant places
- The primary city should be the main city featured in the video"""


def _prefilter_candidates(candidates: list[dict]) -> list[dict]:
    """Remove obviously non-place candidates before sending to LLM."""
    filtered = []
    for c in candidates:
        name = c.get("name", "").strip().lower()
        # Skip empty names, single characters, or known non-place words
        if not name or len(name) < 2:
            continue
        if name in NON_PLACE_WORDS:
            continue
        filtered.append(c)
    return filtered


async def detect_locations(content_analysis: dict) -> dict | None:
    """
    Deduplicate, rank, and extract primary destination from content analysis.

    Args:
        content_analysis: Dict from content_fuser with candidate_locations, etc.

    Returns:
        Dict with primary_country, primary_region, primary_city, ranked_locations
    """
    candidates = content_analysis.get("candidate_locations", [])

    # Pre-filter obvious non-places
    candidates = _prefilter_candidates(candidates)

    if not candidates and not content_analysis.get("destination_city"):
        logger.warning("No candidate locations to detect")
        return None

    user_prompt = DETECTOR_USER_PROMPT.format(
        country=content_analysis.get("destination_country", ""),
        region=content_analysis.get("destination_region", ""),
        city=content_analysis.get("destination_city", ""),
        confidence=content_analysis.get("location_confidence", "low"),
        candidates_json=json.dumps(candidates, indent=1),
    )

    result = await call_openai_json(
        task="fast",
        system_prompt=DETECTOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.2,
    )

    if not result:
        # Fallback: use content analysis directly
        return {
            "primary_country": content_analysis.get("destination_country", ""),
            "primary_region": content_analysis.get("destination_region", ""),
            "primary_city": content_analysis.get("destination_city", ""),
            "ranked_locations": candidates[:10],
        }

    return result
