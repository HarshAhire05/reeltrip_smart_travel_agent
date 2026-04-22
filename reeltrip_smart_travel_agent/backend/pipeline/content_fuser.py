"""
pipeline/content_fuser.py

Merge transcript + vision + metadata into unified content analysis.
Uses GPT-4o-mini (text-only merge task). Exact prompts from IMPLEMENTATION.md Section 7.
"""
import json
import logging

from services.openai_client import call_openai_json

logger = logging.getLogger(__name__)

FUSION_SYSTEM_PROMPT = """You are a travel content analyst. You will receive multiple
signals extracted from a travel video. Your job is to merge them into one unified
analysis of the travel destination.

CRITICAL RULES:
1. Only include locations that appear in AT LEAST ONE signal source
2. Do NOT add locations that were not mentioned or shown
3. If signals conflict, trust VISION analysis over metadata (what you see > what's written)
4. If vision is unavailable, rely on transcript + hashtags
5. Be conservative — if unsure about a location, mark confidence as "low"

Respond in JSON format ONLY."""

FUSION_USER_PROMPT = """Merge these signals from a travel video:

VIDEO METADATA:
- Title: {title}
- Description: {description}
- Hashtags: {hashtags}
- Platform: {platform}

AUDIO TRANSCRIPT:
{transcript}
(Speech detected: {has_speech})

VISION ANALYSIS:
{vision_analysis}

Produce a unified JSON:
{{
    "destination_country": "string",
    "destination_region": "string (state/province/emirate)",
    "destination_city": "string",
    "location_confidence": "high|medium|low",
    "candidate_locations": [
        {{
            "name": "Place Name",
            "type": "city|landmark|area|beach|restaurant|hotel|market",
            "mentioned_in": ["vision", "hashtags", "transcript", "title", "description"],
            "confidence": "high|medium|low"
        }}
    ],
    "dominant_vibe": "one phrase like 'luxury urban experience' or 'tropical beach getaway'",
    "content_summary": "2-3 sentences summarizing what the video shows",
    "detected_activities": ["activity1", "activity2"],
    "target_audience": "couples|families|solo|friends|luxury|backpackers"
}}"""


async def fuse_content(
    title: str,
    description: str,
    hashtags: list[str],
    platform: str,
    transcript: str,
    has_speech: bool,
    vision_result: dict | None,
) -> dict | None:
    """
    Merge all signals into unified content analysis.
    """
    user_prompt = FUSION_USER_PROMPT.format(
        title=title,
        description=description,
        hashtags=json.dumps(hashtags),
        platform=platform,
        transcript=transcript if transcript else "(No speech detected in video)",
        has_speech=has_speech,
        vision_analysis=json.dumps(vision_result, indent=2) if vision_result else "(Vision analysis unavailable)",
    )

    try:
        result = await call_openai_json(
            task="fast",
            system_prompt=FUSION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2048,
            temperature=0.2,
        )
        if result:
            return result
    except Exception as e:
        logger.error(f"Content fusion LLM call failed: {e}")

    # Fallback: build minimal content analysis from raw inputs
    logger.warning("Using fallback content fusion from raw metadata")
    return _fallback_fusion(title, description, hashtags, platform)


def _fallback_fusion(
    title: str, description: str, hashtags: list[str], platform: str
) -> dict:
    """Build a minimal content analysis from raw metadata when LLM fails."""
    # Extract candidate locations from hashtags and title
    candidates = []
    for tag in hashtags:
        cleaned = tag.strip("#").replace("_", " ")
        if len(cleaned) > 2 and not cleaned.lower() in ("travel", "reels", "fyp", "viral", "explore"):
            candidates.append({
                "name": cleaned.title(),
                "type": "city",
                "mentioned_in": ["hashtags"],
                "confidence": "low",
            })

    return {
        "destination_country": "",
        "destination_region": "",
        "destination_city": "",
        "location_confidence": "low",
        "candidate_locations": candidates[:10],
        "dominant_vibe": "travel experience",
        "content_summary": f"Travel video from {platform}: {title[:100]}",
        "detected_activities": [],
        "target_audience": "solo",
    }
