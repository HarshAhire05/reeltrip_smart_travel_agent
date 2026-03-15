"""
Safety Agent — researches travel advisories, safety tips, cultural etiquette.
Uses Tavily for web search + gpt-4o-mini for parsing.
"""
import json
import logging

from services.openai_client import call_openai_json
from services.tavily_client import search_tavily

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = """You are a travel safety research assistant.
Given web search results about a destination's safety, extract structured safety information.

Be factual and balanced — do not exaggerate dangers, but do not minimize real risks.
Include practical, actionable advice that travelers can use.

Respond in JSON format ONLY."""


async def run_safety_agent(state: dict) -> dict:
    """Research safety information for the destination."""
    location = state.get("location_result", {})
    prefs = state.get("user_preferences", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[safety] Processing cities: {selected_cities}")

    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    home_country = prefs.get("home_country", "India")

    if not dest_country:
        dest_country = dest_city

    # Search queries
    queries = [
        f"{dest_country} travel advisory 2026 safety",
        f"{dest_city} tourist safety tips scams to avoid",
        f"{dest_country} cultural etiquette tips for visitors from {home_country}",
    ]

    search_results = []
    for q in queries:
        result = await search_tavily(q, max_results=3)
        if result:
            search_results.append({"query": q, "results": result})

    if not search_results:
        logger.warning("Safety agent: no Tavily results, returning fallback")
        return _fallback(dest_city, dest_country)

    user_prompt = f"""Extract safety and travel advisory information for {dest_city}, {dest_country}
from these search results. The traveler is from {home_country}.

Search results:
{json.dumps(search_results, indent=1)[:5000]}

Return JSON:
{{
    "overall_safety_rating": "very safe|safe|moderate|use caution|avoid",
    "travel_advisory_summary": "2-3 sentence summary of current travel situation",
    "specific_warnings": ["specific safety concerns for tourists"],
    "health_advisories": ["vaccination needs, health risks, water safety"],
    "emergency_numbers": {{"police": "number", "ambulance": "number", "fire": "number", "tourist_helpline": "number"}},
    "cultural_etiquette": ["important cultural norms and customs to follow"],
    "scam_warnings": ["common tourist scams and how to avoid them"],
    "areas_to_avoid": ["neighborhoods or areas tourists should avoid, if any"]
}}"""

    result = await call_openai_json(
        task="fast",
        system_prompt=SAFETY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2,
    )

    if result:
        return result

    return _fallback(dest_city, dest_country)


def _fallback(city: str, country: str) -> dict:
    """Return generic safety info when search fails."""
    return {
        "overall_safety_rating": "safe",
        "travel_advisory_summary": f"Check your government's travel advisory for {country} before traveling.",
        "specific_warnings": ["Always be aware of your surroundings in tourist areas"],
        "health_advisories": ["Carry basic medications and check if any vaccinations are recommended"],
        "emergency_numbers": {"police": "check locally", "ambulance": "check locally"},
        "cultural_etiquette": [
            "Research local customs before your trip",
            "Dress appropriately when visiting religious sites",
        ],
        "scam_warnings": ["Be cautious of unsolicited offers from strangers in tourist areas"],
        "areas_to_avoid": [],
    }
