"""
pipeline/orchestrator.py

Master pipeline that chains Stages 1-4 together.
Async generator yielding SSE-compatible progress events.
Checks cache at every stage, cleans up all temp files, never crashes.
"""
import uuid
import asyncio
import json
import os
import logging
from typing import AsyncGenerator

from services.supabase_client import (
    get_cached_video, store_video,
    get_cached_location, store_location,
    create_session,
)
from pipeline.video_extractor import extract_video_metadata
from pipeline.audio_processor import extract_and_transcribe
from pipeline.frame_extractor import extract_frames
from pipeline.vision_analyzer import analyze_frames
from pipeline.content_fuser import fuse_content
from pipeline.location_validator import validate_and_enrich_locations
from pipeline.highlights_generator import generate_highlights
from services.google_places_client import get_photo_url
from utils.url_validator import validate_url
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_pipeline(url: str) -> AsyncGenerator[dict, None]:
    """
    Run the full video processing pipeline (Stages 1-4).
    Yields progress events as dicts: {"event": "event_name", "data": {...}}

    Never raises — yields error events instead.
    """
    video_file_path = None

    try:
        # --- VALIDATE URL ---
        is_valid, platform = validate_url(url)
        if not is_valid:
            yield {"event": "error", "data": {"message": "Invalid URL. Please paste an Instagram Reel, YouTube Short, or TikTok URL."}}
            return

        # --- CREATE SESSION ---
        session_id = str(uuid.uuid4())
        await create_session(session_id, url)
        yield {"event": "session", "data": {"session_id": session_id}}

        # =============================================
        # STAGE 1: VIDEO EXTRACTION
        # =============================================
        yield {"event": "progress", "data": {"stage": "extracting", "percent": 5, "message": "Extracting video data..."}}

        # Check cache first
        cached_video = await get_cached_video(url) if settings.ENABLE_CACHE else None

        if cached_video and cached_video.get("content_analysis"):
            # Full cache hit — skip stages 1 and 2
            logger.info(f"Cache HIT for video: {url}")
            yield {"event": "progress", "data": {"stage": "extracting", "percent": 15, "message": "Loaded from cache"}}
            yield {"event": "metadata", "data": {
                "title": cached_video.get("title", ""),
                "thumbnail_url": cached_video.get("thumbnail_url", ""),
                "platform": cached_video.get("platform", ""),
                "duration": cached_video.get("duration_seconds", 0),
            }}

            content_analysis = cached_video["content_analysis"]
            if isinstance(content_analysis, str):
                content_analysis = json.loads(content_analysis)

            yield {"event": "progress", "data": {"stage": "analyzing", "percent": 40, "message": "Loaded from cache"}}
            yield {"event": "analysis", "data": content_analysis}

        else:
            # Cache miss — full extraction
            logger.info(f"Cache MISS for video: {url}")
            metadata = await extract_video_metadata(url, platform)

            if not metadata:
                yield {"event": "error", "data": {"message": "Could not extract video data. The video may be private or unavailable."}}
                return

            video_file_path = metadata.pop("video_file_path", None)

            yield {"event": "progress", "data": {"stage": "extracting", "percent": 15, "message": "Video data extracted"}}
            yield {"event": "metadata", "data": {
                "title": metadata.get("title", ""),
                "thumbnail_url": metadata.get("thumbnail_url", ""),
                "platform": platform,
                "duration": metadata.get("duration_seconds", 0),
            }}

            # =============================================
            # STAGE 2: CONTENT ANALYSIS
            # =============================================
            yield {"event": "progress", "data": {"stage": "analyzing", "percent": 20, "message": "Analyzing video content..."}}

            # Run audio and frame extraction in parallel
            transcript_result = {"text": "", "language": "", "has_speech": False}
            frames_base64 = []

            if video_file_path and os.path.exists(video_file_path):
                transcript_task = extract_and_transcribe(video_file_path)
                frames_task = extract_frames(video_file_path, metadata.get("duration_seconds", 30))

                transcript_result, frames_base64 = await asyncio.gather(
                    transcript_task, frames_task
                )

            yield {"event": "progress", "data": {"stage": "analyzing", "percent": 30, "message": "Analyzing visual content..."}}

            # Vision analysis
            vision_result = None
            if frames_base64 and settings.ENABLE_VISION:
                vision_result = await analyze_frames(frames_base64)

            yield {"event": "progress", "data": {"stage": "analyzing", "percent": 38, "message": "Fusing content signals..."}}

            # Content fusion
            content_analysis = await fuse_content(
                title=metadata.get("title", ""),
                description=metadata.get("description", ""),
                hashtags=metadata.get("hashtags", []),
                platform=platform,
                transcript=transcript_result.get("text", ""),
                has_speech=transcript_result.get("has_speech", False),
                vision_result=vision_result,
            )

            if not content_analysis:
                yield {"event": "error", "data": {"message": "Could not analyze video content. Please try a different video."}}
                return

            yield {"event": "progress", "data": {"stage": "analyzing", "percent": 42, "message": "Content analyzed"}}
            yield {"event": "analysis", "data": content_analysis}

            # Cache stages 1-2
            if settings.ENABLE_CACHE:
                await store_video(url, {
                    **metadata,
                    "transcript": transcript_result.get("text", ""),
                    "transcript_language": transcript_result.get("language", ""),
                    "has_speech": transcript_result.get("has_speech", False),
                    "content_analysis": json.dumps(content_analysis),
                })

            # Clean up video file
            if video_file_path and os.path.exists(video_file_path):
                os.remove(video_file_path)
                video_file_path = None

        # =============================================
        # STAGE 3: LOCATION VALIDATION
        # =============================================

        # Check location cache
        cached_loc = await get_cached_location(url) if settings.ENABLE_CACHE else None

        if cached_loc and cached_loc.get("highlights"):
            logger.info(f"Cache HIT for locations: {url}")
            yield {"event": "progress", "data": {"stage": "locating", "percent": 75, "message": "Loaded from cache"}}
            yield {"event": "progress", "data": {"stage": "highlights", "percent": 90, "message": "Loaded from cache"}}

            highlights = cached_loc.get("highlights", [])
            if isinstance(highlights, str):
                highlights = json.loads(highlights)

            location_result = cached_loc

        else:
            logger.info(f"Cache MISS for locations: {url}")
            yield {"event": "progress", "data": {"stage": "locating", "percent": 48, "message": "Detecting locations..."}}

            # Validate and enrich locations with Google Places
            location_result = await validate_and_enrich_locations(content_analysis)

            if not location_result:
                yield {"event": "error", "data": {"message": "Could not identify valid locations from this video."}}
                return

            yield {"event": "progress", "data": {"stage": "locating", "percent": 68, "message": "Locations validated"}}

            # =============================================
            # STAGE 4: HIGHLIGHTS
            # =============================================
            yield {"event": "progress", "data": {"stage": "highlights", "percent": 72, "message": "Generating highlights..."}}

            # Collect all places for highlight generation
            all_places = []
            all_places.extend(location_result.get("validated_places", []))
            all_places.extend(location_result.get("nearby_attractions", []))
            all_places.extend(location_result.get("nearby_restaurants", [])[:5])

            # Resolve photo URLs for any remaining places
            for place in all_places:
                if place.get("photo_reference") and not place.get("photo_url"):
                    place["photo_url"] = get_photo_url(place["photo_reference"])

            highlights = await generate_highlights(all_places)

            # Merge photo URLs into highlights
            place_photo_map = {
                p.get("place_id"): p.get("photo_url")
                for p in all_places
                if p.get("photo_url")
            }
            for h in highlights:
                if not h.get("photo_url"):
                    h["photo_url"] = place_photo_map.get(h.get("place_id"), "")

            location_result["highlights"] = highlights

            yield {"event": "progress", "data": {"stage": "highlights", "percent": 88, "message": "Highlights ready"}}

            # Cache stages 3-4
            if settings.ENABLE_CACHE:
                await store_location(url, location_result)

        # =============================================
        # DELIVER RESULTS
        # =============================================
        yield {"event": "highlights", "data": {
            "highlights": location_result.get("highlights", []),
            "primary_city": location_result.get("primary_city", ""),
            "primary_country": location_result.get("primary_country", ""),
            "city_latitude": location_result.get("city_latitude"),
            "city_longitude": location_result.get("city_longitude"),
        }}

        yield {"event": "complete", "data": {
            "session_id": session_id,
            "destination": f"{location_result.get('primary_city', '')}, {location_result.get('primary_country', '')}",
        }}

    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        yield {"event": "error", "data": {"message": f"An unexpected error occurred: {str(e)}"}}

    finally:
        # Clean up any remaining temp files
        if video_file_path and os.path.exists(video_file_path):
            try:
                os.remove(video_file_path)
            except Exception:
                pass
