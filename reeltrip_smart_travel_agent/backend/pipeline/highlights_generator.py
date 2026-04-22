"""
pipeline/highlights_generator.py

Batch highlight generation for all places in a single GPT-4o-mini call.
Uses exact prompts from IMPLEMENTATION.md Section 9.
"""
from services.openai_client import call_openai_json
import json

HIGHLIGHTS_SYSTEM_PROMPT = """You are an award-winning travel writer known for vivid,
engaging descriptions that make readers want to visit immediately.

Generate rich highlight data for each place provided. Your writing should feel like
a premium travel magazine — informative, inspiring, and practical.

RULES:
1. Each description should be 2-3 sentences, vivid and specific
2. Vibe tags must be exactly 3 single words
3. Signature experiences must be specific to THAT place (not generic)
4. Do NOT invent facts. If unsure about details, keep it general
5. Use the Google Places data provided (ratings, types) for accuracy
6. Estimate costs in USD

Respond in JSON format ONLY."""

HIGHLIGHTS_USER_PROMPT = """Generate magazine-quality highlights for these {count} places:

{places_json}

For each place, produce:
{{
    "place_id": "the place_id from input",
    "description": "2-3 vivid, engaging sentences",
    "vibe_tags": ["Word1", "Word2", "Word3"],
    "signature_experiences": ["Specific must-do 1", "Specific must-do 2"],
    "best_time_to_visit": "When to go for best experience",
    "know_more": "3-4 sentences of deeper context, history, insider tips",
    "estimated_visit_duration": "e.g., 2-3 hours",
    "estimated_cost_usd": 25.0
}}

Respond as: {{"highlights": [array of highlight objects]}}"""


async def generate_highlights(places: list[dict]) -> list[dict]:
    """
    Generate rich highlights for all places in one batch call.

    Args:
        places: List of place dicts from Google Places

    Returns:
        List of highlight dicts, or fallback highlights on failure
    """
    if not places:
        return []

    # Prepare slim place data to reduce token usage
    slim_places = []
    for p in places:
        slim_places.append({
            "place_id": p.get("place_id", ""),
            "name": p.get("name", "Unknown"),
            "address": p.get("formatted_address", ""),
            "types": p.get("types", [])[:3],
            "rating": p.get("rating"),
            "total_ratings": p.get("total_ratings"),
            "price_level": p.get("price_level"),
        })

    user_prompt = HIGHLIGHTS_USER_PROMPT.format(
        count=len(slim_places),
        places_json=json.dumps(slim_places, indent=1),
    )

    result = await call_openai_json(
        task="fast",
        system_prompt=HIGHLIGHTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=4096,
        temperature=0.6,
    )

    if result and "highlights" in result:
        return result["highlights"]

    # Fallback: generate basic highlights without AI
    return [_fallback_highlight(p) for p in places]


def _fallback_highlight(place: dict) -> dict:
    """Fallback highlight using only Google Places data."""
    place_type = (place.get("types", ["place"])[0] or "place").replace("_", " ")
    return {
        "place_id": place.get("place_id", ""),
        "description": f"A popular {place_type} in the area. Rated {place.get('rating', 'N/A')} by visitors.",
        "vibe_tags": ["Popular", "Recommended", place_type.title()],
        "signature_experiences": ["Visit and explore"],
        "best_time_to_visit": "Check local timings",
        "know_more": "Visit the official website for more details about this location.",
        "estimated_visit_duration": "1-2 hours",
        "estimated_cost_usd": 0.0,
    }
