"""
pipeline/vision_analyzer.py

GPT-4o vision analysis for location detection from video frames.
Uses the exact prompts from IMPLEMENTATION.md Section 7.
"""
from services.openai_client import call_openai_vision
import logging

logger = logging.getLogger(__name__)

VISION_SYSTEM_PROMPT = """You are a world-class travel location detection expert.
You have encyclopedic knowledge of landmarks, architecture styles, landscapes,
signage, and geographical indicators from every country on Earth.

Your job: analyze video frames from a travel video and detect EXACTLY which
location(s) they show. Be specific. If you can identify a specific landmark, name it.
If you can only determine a city or country, say that.

IMPORTANT: Only report what you actually SEE in the frames. Do not guess or add
places that are not visually evident. If a frame is unclear, say "unclear".

Respond in JSON format ONLY."""

VISION_USER_PROMPT = """Analyze these {frame_count} frames from a travel video.

For each frame, identify:
1. Recognizable landmarks, monuments, buildings, or famous locations
2. Any text visible on signs, boards, storefronts (include the language)
3. Architectural style (Islamic, European, Modern, Asian, Colonial, etc.)
4. Natural landscape features (beach, desert, mountain, jungle, urban, etc.)
5. Country-specific indicators (flags, license plates, road style, vegetation)
6. Any brand names or chains that indicate a specific region

Then provide your overall best guess for the location.

Respond as JSON:
{{
    "frame_observations": [
        {{
            "frame_index": 0,
            "landmarks": ["list of landmarks or empty"],
            "visible_text": ["any readable text"],
            "text_languages": ["English", "Arabic"],
            "architecture_style": "Modern Gulf",
            "landscape_type": "urban desert",
            "country_indicators": ["specific clues"],
            "location_guess": "Dubai, UAE",
            "confidence": "high"
        }}
    ],
    "overall_assessment": {{
        "country": "United Arab Emirates",
        "region": "Dubai",
        "city": "Dubai",
        "specific_places": ["Burj Khalifa", "Dubai Mall"],
        "confidence": "high",
        "reasoning": "Why you think this is the location"
    }}
}}"""


async def analyze_frames(frames_base64: list[str]) -> dict | None:
    """
    Send frames to GPT-4o vision for location detection.
    Returns the parsed JSON response or None on failure.
    """
    if not frames_base64:
        logger.warning("No frames to analyze")
        return None

    user_prompt = VISION_USER_PROMPT.format(frame_count=len(frames_base64))

    result = await call_openai_vision(
        system_prompt=VISION_SYSTEM_PROMPT,
        text_prompt=user_prompt,
        images_base64=frames_base64,
        max_tokens=2048,
        temperature=0.2,
    )

    return result
