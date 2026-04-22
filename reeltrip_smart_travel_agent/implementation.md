# ReelTrip — Implementation Planning Guide for Claude Code

**Purpose:** This document is a companion to the "ReelTrip Master Documentation." That document describes WHAT to build. This document describes HOW to build it, in what order, and provides critical code snippets, patterns, gotchas, and suggestions for every part of the system.

**Audience:** You are Claude Code (Opus 4.6). You are about to engineer the entire ReelTrip system. Read both documents fully before writing any code. This planning guide gives you the exact implementation sequence, key code patterns, and decision points.

**Critical Rule:** Where I say "I suggest you use this logic" — it is a tested recommendation. If you find something genuinely better during implementation, use that instead. But do not change things just for style preference. Change only when you have a concrete technical reason.

---

## TABLE OF CONTENTS

1. [Implementation Order (Build Sequence)](#1-implementation-order)
2. [Project Bootstrap & Scaffolding](#2-project-bootstrap--scaffolding)
3. [Environment & Configuration Setup](#3-environment--configuration-setup)
4. [Supabase Database Setup](#4-supabase-database-setup)
5. [OpenAI Client Wrapper (Model Router)](#5-openai-client-wrapper)
6. [Pipeline Stage 1: Video Extraction — Key Code](#6-pipeline-stage-1-video-extraction)
7. [Pipeline Stage 2: Content Analysis — Key Code](#7-pipeline-stage-2-content-analysis)
8. [Pipeline Stage 3: Location Validation — Key Code](#8-pipeline-stage-3-location-validation)
9. [Pipeline Stage 4: Highlights Generation — Key Code](#9-pipeline-stage-4-highlights-generation)
10. [Pipeline Orchestrator (Stages 1-4 Combined)](#10-pipeline-orchestrator)
11. [SSE Streaming Pattern](#11-sse-streaming-pattern)
12. [Session Management](#12-session-management)
13. [Preference Collection API](#13-preference-collection-api)
14. [Multi-Agent System: LangGraph Setup](#14-multi-agent-system-langgraph)
15. [Agent Implementation Patterns](#15-agent-implementation-patterns)
16. [Flight Agent — Detailed Implementation](#16-flight-agent)
17. [Hotel Agent — Detailed Implementation](#17-hotel-agent)
18. [Weather Agent — Detailed Implementation](#18-weather-agent)
19. [Safety Agent — Detailed Implementation](#19-safety-agent)
20. [Activity Agent — Detailed Implementation](#20-activity-agent)
21. [Transport Agent — Detailed Implementation](#21-transport-agent)
22. [Budget Agent — Detailed Implementation](#22-budget-agent)
23. [Itinerary Assembler — The Big Prompt](#23-itinerary-assembler)
24. [Itinerary Customization Logic](#24-itinerary-customization)
25. [Frontend: Next.js Project Setup](#25-frontend-nextjs-setup)
26. [Frontend: Landing Page](#26-frontend-landing-page)
27. [Frontend: Processing & Progress Screen](#27-frontend-processing-screen)
28. [Frontend: Highlights Display](#28-frontend-highlights)
29. [Frontend: Preference Form](#29-frontend-preference-form)
30. [Frontend: City Selector](#30-frontend-city-selector)
31. [Frontend: Itinerary View](#31-frontend-itinerary-view)
32. [Frontend: Customization Chat](#32-frontend-customization-chat)
33. [Critical Gotchas & Common Mistakes](#33-critical-gotchas)
34. [Testing Plan](#34-testing-plan)
35. [Deployment Checklist](#35-deployment-checklist)

---

## 1. Implementation Order

**BUILD IN THIS EXACT ORDER. Do not skip ahead.**

```
Phase 1: Foundation (Do this first, everything depends on it)
  1.1  Project scaffolding (backend + frontend directories)
  1.2  Environment config (config.py with all env vars)
  1.3  Supabase tables (run SQL schema)
  1.4  OpenAI client wrapper with model routing
  1.5  Supabase client wrapper (CRUD helpers)
  1.6  Pydantic models (ALL schemas defined upfront)

Phase 2: Video Pipeline (Stages 1-4)
  2.1  URL validator
  2.2  Video extractor (yt-dlp wrapper)
  2.3  Audio processor (ffmpeg + Whisper)
  2.4  Frame extractor (ffmpeg)
  2.5  Vision analyzer (GPT-4o)
  2.6  Content fuser (GPT-4o-mini)
  2.7  Location detector + ranker (GPT-4o-mini)
  2.8  Google Places client (geocode, details, nearby, photos)
  2.9  Location validator (Google Places integration)
  2.10 Highlights generator (GPT-4o-mini)
  2.11 Pipeline orchestrator (chains stages 1-4)
  2.12 SSE streaming endpoint for /api/v1/process

Phase 3: Frontend — First Screens
  3.1  Next.js project scaffold with Tailwind + shadcn
  3.2  Landing page with URL input
  3.3  Processing screen with progress tracker
  3.4  Location display card
  3.5  Highlights bottom sheet with cards
  3.6  SSE client hook for streaming

Phase 4: Itinerary Planning System
  4.1  Preference collection API + form
  4.2  City selector component + API
  4.3  Tavily client wrapper
  4.4  Weather client wrapper  
  4.5  Exchange rate client wrapper
  4.6  Flight agent
  4.7  Hotel agent
  4.8  Weather agent
  4.9  Safety agent
  4.10 Activity agent
  4.11 Transport agent
  4.12 Budget agent
  4.13 LangGraph orchestrator (wires all agents)
  4.14 Itinerary assembler (GPT-4o)
  4.15 SSE streaming endpoint for /api/v1/itinerary/preferences

Phase 5: Frontend — Itinerary Screens
  5.1  Itinerary page with tab navigation
  5.2  Reservations tab (flights + hotels)
  5.3  Day timeline components
  5.4  Budget breakdown component
  5.5  Miscellaneous tab
  5.6  Customization chat interface
  5.7  Customization API endpoint

Phase 6: Polish
  6.1  Caching (check cache before processing)
  6.2  Error handling + fallbacks on every stage
  6.3  Loading skeletons on all frontend components
  6.4  Mobile responsive testing
  6.5  End-to-end test with a real YouTube Short URL
```

---

## 2. Project Bootstrap & Scaffolding

### Backend

```bash
mkdir -p reeltrip/backend/{pipeline,agents,services,models,utils,database}
mkdir -p reeltrip/frontend
cd reeltrip/backend
touch __init__.py main.py config.py dependencies.py
touch pipeline/__init__.py pipeline/orchestrator.py pipeline/video_extractor.py
touch pipeline/audio_processor.py pipeline/frame_extractor.py pipeline/vision_analyzer.py
touch pipeline/content_fuser.py pipeline/location_detector.py pipeline/location_validator.py
touch pipeline/highlights_generator.py
touch agents/__init__.py agents/orchestrator.py agents/state.py
touch agents/flight_agent.py agents/hotel_agent.py agents/weather_agent.py
touch agents/safety_agent.py agents/activity_agent.py agents/transport_agent.py
touch agents/budget_agent.py agents/itinerary_assembler.py
touch services/__init__.py services/openai_client.py services/google_places_client.py
touch services/tavily_client.py services/weather_client.py services/exchange_rate_client.py
touch services/supabase_client.py
touch models/__init__.py models/video.py models/location.py models/preferences.py
touch models/agents.py models/itinerary.py models/api.py
touch utils/__init__.py utils/url_validator.py utils/currency.py utils/geo.py utils/prompts.py
touch database/schema.sql
```

### requirements.txt

I suggest you use these exact versions. If something newer is clearly better, feel free to upgrade, but test it:

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
python-dotenv==1.0.1
openai==1.50.0
yt-dlp==2024.12.23
langgraph==0.2.0
langchain-openai==0.2.0
langchain-core==0.3.0
tavily-python==0.5.0
httpx==0.27.0
supabase==2.9.0
python-multipart==0.0.9
aiofiles==24.1.0
Pillow==10.4.0
```

**Important:** yt-dlp updates frequently. Pin it, but if Instagram extraction breaks, try upgrading yt-dlp first.

**Important:** For `langgraph`, the API has evolved. The pattern I show below works with `langgraph>=0.2.0`. If you use a different version, check the LangGraph docs for the correct `StateGraph` API.

---

## 3. Environment & Configuration Setup

### config.py — I suggest this pattern:

```python
"""
Central configuration. Every service reads from here.
Never import os.environ directly in service files.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Required
    OPENAI_API_KEY: str
    GOOGLE_PLACES_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    
    # Recommended (with defaults so app runs without them, but degraded)
    TAVILY_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    EXCHANGERATE_API_KEY: str = ""
    
    # Optional
    INSTAGRAM_COOKIES_PATH: str = ""
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_HOME_CITY: str = "Mumbai"
    MAX_FRAME_COUNT: int = 5
    
    # Model configuration — CRITICAL for cost control
    VISION_MODEL: str = "gpt-4o"
    REASONING_MODEL: str = "gpt-4o"
    FAST_MODEL: str = "gpt-4o-mini"
    WHISPER_MODEL: str = "whisper-1"
    
    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Feature flags — useful for development/testing
    ENABLE_CACHE: bool = True
    ENABLE_VISION: bool = True          # Set False to skip vision (saves money during dev)
    ENABLE_TAVILY: bool = True          # Set False to skip web search
    ENABLE_WEATHER: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Why this pattern?**
- `lru_cache` means Settings is loaded once and reused everywhere
- Feature flags let you disable expensive APIs during development
- Default values mean the app starts even with minimal config
- `pydantic_settings` validates types automatically

**Install:** `pip install pydantic-settings`

---

## 4. Supabase Database Setup

### Run this SQL in the Supabase SQL Editor:

```sql
-- ============================================================
-- ReelTrip Database Schema
-- Run this ONCE in the Supabase SQL Editor (Dashboard → SQL)
-- ============================================================

-- Table 1: Video intelligence cache (Stages 1-2)
CREATE TABLE IF NOT EXISTS video_intelligence (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL DEFAULT 'unknown',
    title TEXT,
    description TEXT,
    caption_text TEXT,
    hashtags JSONB DEFAULT '[]'::jsonb,
    uploader TEXT,
    duration_seconds INTEGER,
    view_count BIGINT,
    thumbnail_url TEXT,
    transcript TEXT,
    transcript_language TEXT,
    has_speech BOOLEAN DEFAULT false,
    content_analysis JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_vi_url ON video_intelligence(url);

-- Table 2: Location results cache (Stages 3-4)
CREATE TABLE IF NOT EXISTS location_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    primary_country TEXT NOT NULL DEFAULT '',
    primary_region TEXT DEFAULT '',
    primary_city TEXT NOT NULL DEFAULT '',
    city_latitude DOUBLE PRECISION,
    city_longitude DOUBLE PRECISION,
    validated_places JSONB DEFAULT '[]'::jsonb,
    nearby_attractions JSONB DEFAULT '[]'::jsonb,
    nearby_restaurants JSONB DEFAULT '[]'::jsonb,
    nearby_hotels JSONB DEFAULT '[]'::jsonb,
    highlights JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lr_url ON location_results(url);

-- Table 3: Generated itineraries
CREATE TABLE IF NOT EXISTS itineraries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL,
    session_id TEXT NOT NULL,
    user_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected_cities JSONB DEFAULT '[]'::jsonb,
    itinerary JSONB NOT NULL DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_it_url ON itineraries(url);
CREATE INDEX IF NOT EXISTS idx_it_session ON itineraries(session_id);

-- Table 4: Session state
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    url TEXT,
    stage TEXT NOT NULL DEFAULT 'processing',
    preferences JSONB,
    selected_cities JSONB DEFAULT '[]'::jsonb,
    chat_history JSONB DEFAULT '[]'::jsonb,
    itinerary_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table 5: Google Places cache (reduces API costs)
CREATE TABLE IF NOT EXISTS place_cache (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    formatted_address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    rating DOUBLE PRECISION,
    total_ratings INTEGER,
    price_level INTEGER,
    types JSONB DEFAULT '[]'::jsonb,
    photo_url TEXT,
    website TEXT,
    opening_hours JSONB,
    cached_at TIMESTAMPTZ DEFAULT now()
);
```

### Supabase Client Helper — I suggest this pattern:

```python
"""
services/supabase_client.py

Thin wrapper around Supabase REST API. Every function is safe to call
even if Supabase is unreachable — returns None on failure.
This is important: NEVER let a cache failure crash the pipeline.
"""
from supabase import create_client, Client
from config import get_settings
import json
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
        result = sb.table("video_intelligence").select("*").eq("url", url).maybe_single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Cache read error: {e}")
        return None

async def store_video(url: str, data: dict) -> bool:
    """Upsert video intelligence. Returns True on success."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("video_intelligence").upsert({
            "url": url,
            **data
        }, on_conflict="url").execute()
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
        result = sb.table("location_results").select("*").eq("url", url).maybe_single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Cache read error: {e}")
        return None

async def store_location(url: str, data: dict) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("location_results").upsert({
            "url": url,
            **data
        }, on_conflict="url").execute()
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
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        logger.error(f"Itinerary store error: {e}")
        return None

async def get_itinerary(itinerary_id: str) -> dict | None:
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table("itineraries").select("*").eq("id", itinerary_id).maybe_single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Itinerary read error: {e}")
        return None

# --- SESSIONS ---

async def create_session(session_id: str, url: str) -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("sessions").upsert({
            "id": session_id,
            "url": url,
            "stage": "processing"
        }, on_conflict="id").execute()
        return True
    except Exception as e:
        logger.error(f"Session create error: {e}")
        return False

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
        result = sb.table("place_cache").select("*").eq("place_id", place_id).maybe_single().execute()
        return result.data if result.data else None
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
```

**Why this pattern?**
- Every function has try/except and returns None on failure
- No function ever raises an exception that could crash the pipeline
- Global client singleton avoids reconnecting on every call
- `upsert` with `on_conflict` is idempotent — safe to call multiple times

---

## 5. OpenAI Client Wrapper

This is THE most important utility in the project. Every AI call goes through this wrapper. It handles model routing, retries, and structured output.

### I suggest this pattern:

```python
"""
services/openai_client.py

Central OpenAI API wrapper. ALL AI calls go through here.
Handles model routing, structured JSON output, retries, and error handling.
"""
from openai import OpenAI, AsyncOpenAI
from config import get_settings
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()

# Use async client for non-blocking calls in FastAPI
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ---- MODEL ROUTER ----
# This is the cost control center. Change models here, not in individual services.

def get_model(task: str) -> str:
    """
    Route tasks to the cheapest sufficient model.
    
    RULES:
    - "vision" → gpt-4o (only model with vision)
    - "reasoning" → gpt-4o (complex multi-constraint tasks)
    - "fast" → gpt-4o-mini (simple text tasks, classification, extraction)
    """
    model_map = {
        "vision": settings.VISION_MODEL,       # gpt-4o
        "reasoning": settings.REASONING_MODEL,  # gpt-4o  
        "fast": settings.FAST_MODEL,            # gpt-4o-mini
    }
    return model_map.get(task, settings.FAST_MODEL)


async def call_openai_json(
    task: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retries: int = 2
) -> dict | None:
    """
    Call OpenAI with JSON response format.
    
    Args:
        task: "vision" | "reasoning" | "fast" — determines which model to use
        system_prompt: System message
        user_prompt: User message (text only, no images)
        max_tokens: Max response tokens
        temperature: 0.0-1.0 (lower = more deterministic)
        retries: Number of retries on failure
    
    Returns:
        Parsed JSON dict, or None on failure
    """
    model = get_model(task)
    
    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error (attempt {attempt+1}): {e}")
            logger.error(f"Raw response: {content[:500]}")
            if attempt < retries:
                await asyncio.sleep(1)
                continue
            return None
            
        except Exception as e:
            logger.error(f"OpenAI call failed (attempt {attempt+1}): {e}")
            if attempt < retries:
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(wait)
                continue
            return None


async def call_openai_vision(
    system_prompt: str,
    text_prompt: str,
    images_base64: list[str],
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retries: int = 1  # Vision calls are expensive, fewer retries
) -> dict | None:
    """
    Call OpenAI with images (vision). Always uses gpt-4o.
    
    Args:
        system_prompt: System message
        text_prompt: Text part of user message
        images_base64: List of base64-encoded images
        max_tokens: Max response tokens
        temperature: Creativity level
        retries: Retry count (keep low — vision is expensive)
    
    Returns:
        Parsed JSON dict, or None on failure
    """
    model = get_model("vision")
    
    # Build content array with text + images
    content = [{"type": "text", "text": text_prompt}]
    for img_b64 in images_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}",
                "detail": "low"  # "low" is cheaper. Use "high" only if detection is poor.
                # NOTE: "low" costs 85 tokens per image. "high" costs up to 1105 tokens.
                # I suggest starting with "low" and upgrading to "high" only if location
                # detection accuracy is insufficient. This saves ~90% on vision costs.
            }
        })
    
    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            raw = response.choices[0].message.content
            return json.loads(raw)
            
        except Exception as e:
            logger.error(f"Vision call failed (attempt {attempt+1}): {e}")
            if attempt < retries:
                await asyncio.sleep(2)
                continue
            return None


async def call_openai_text(
    task: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str | None:
    """
    Call OpenAI for free-form text response (not JSON).
    Used for itinerary customization chat and similar conversational tasks.
    """
    model = get_model(task)
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI text call failed: {e}")
        return None


async def transcribe_audio(audio_file_path: str) -> dict | None:
    """
    Transcribe audio using Whisper.
    Returns {"text": "...", "language": "en"} or None on failure.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL,
                file=audio_file,
                response_format="verbose_json"
            )
        return {
            "text": response.text,
            "language": response.language if hasattr(response, 'language') else "unknown"
        }
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None
```

**CRITICAL NOTES:**

1. The `detail: "low"` on vision images is a MASSIVE cost saver. Each "low" image is 85 tokens (~$0.0004). Each "high" image can be 1105+ tokens (~$0.005). For 5 frames, that is $0.002 vs $0.025. Start with "low". If location detection accuracy is poor for certain videos, you can switch to "auto" or "high" per-image.

2. `response_format={"type": "json_object"}` forces the model to return valid JSON. This prevents parsing errors. However, the system prompt MUST contain the word "JSON" somewhere for this to work with OpenAI.

3. The retry logic with exponential backoff handles rate limits gracefully.

---

## 6. Pipeline Stage 1: Video Extraction

### URL Validator

```python
"""
utils/url_validator.py
"""
import re

PLATFORM_PATTERNS = {
    "instagram": [
        r"https?://(?:www\.)?instagram\.com/reel/[\w-]+",
        r"https?://(?:www\.)?instagram\.com/p/[\w-]+",
    ],
    "youtube": [
        r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"https?://youtu\.be/[\w-]+",
    ],
    "tiktok": [
        r"https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+",
        r"https?://vm\.tiktok\.com/[\w]+",
    ],
}

def validate_url(url: str) -> tuple[bool, str]:
    """
    Returns (is_valid, platform_name).
    If invalid, platform_name will be "unknown".
    """
    url = url.strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url):
                return True, platform
    return False, "unknown"
```

### Video Extractor — Key Logic

```python
"""
pipeline/video_extractor.py

I suggest using yt-dlp as a Python library, not CLI.
It gives you more control and better error messages.
"""
import yt_dlp
import tempfile
import os
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def extract_video_metadata(url: str, platform: str) -> dict | None:
    """
    Extract metadata + download video for audio/frame processing.
    
    Returns dict with metadata fields, or None on failure.
    Also saves the video to a temp file and returns the path.
    """
    
    # yt-dlp options
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        # Download the video to a temp file (needed for audio + frames)
        "outtmpl": os.path.join(tempfile.gettempdir(), "reeltrip_%(id)s.%(ext)s"),
        "format": "best[height<=720]",  # 720p max — saves bandwidth & processing
        # IMPORTANT: For Instagram, cookies may be needed
    }
    
    # Add cookies for Instagram if configured
    if platform == "instagram" and settings.INSTAGRAM_COOKIES_PATH:
        if os.path.exists(settings.INSTAGRAM_COOKIES_PATH):
            ydl_opts["cookiefile"] = settings.INSTAGRAM_COOKIES_PATH
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                logger.error(f"yt-dlp returned no info for {url}")
                return None
            
            # Build the expected file path
            video_path = ydl.prepare_filename(info)
            if not os.path.exists(video_path):
                # Try common extensions
                for ext in ["mp4", "webm", "mkv"]:
                    alt = video_path.rsplit(".", 1)[0] + f".{ext}"
                    if os.path.exists(alt):
                        video_path = alt
                        break
            
            return {
                "title": info.get("title", ""),
                "description": info.get("description", ""),
                "caption_text": info.get("description", ""),  # Instagram puts caption in description
                "hashtags": _extract_hashtags(info),
                "uploader": info.get("uploader", info.get("channel", "")),
                "duration_seconds": info.get("duration", 0),
                "view_count": info.get("view_count"),
                "thumbnail_url": info.get("thumbnail", ""),
                "platform": platform,
                "video_file_path": video_path,  # Temp file path for audio/frame extraction
            }
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp download error: {e}")
        return None
    except Exception as e:
        logger.error(f"Video extraction error: {e}")
        return None


def _extract_hashtags(info: dict) -> list[str]:
    """Extract hashtags from all available fields."""
    hashtags = set()
    
    # Direct hashtags field (YouTube)
    if info.get("tags"):
        for tag in info["tags"]:
            hashtags.add(tag.lower().strip())
    
    # Parse from description (Instagram, TikTok)
    desc = info.get("description", "")
    import re
    found = re.findall(r"#(\w+)", desc)
    for h in found:
        hashtags.add(h.lower())
    
    return list(hashtags)[:20]  # Cap at 20 hashtags
```

### Audio Extraction & Transcription

```python
"""
pipeline/audio_processor.py

I suggest extracting audio with ffmpeg subprocess (faster and more reliable
than Python audio libraries). If you find a cleaner approach with pydub or
similar, that works too, but ffmpeg subprocess is battle-tested.
"""
import subprocess
import tempfile
import os
import logging
from services.openai_client import transcribe_audio

logger = logging.getLogger(__name__)

async def extract_and_transcribe(video_path: str) -> dict:
    """
    Extract audio from video, transcribe with Whisper.
    
    Returns:
        {"text": "transcript...", "language": "en", "has_speech": True}
        OR
        {"text": "", "language": "", "has_speech": False}
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return {"text": "", "language": "", "has_speech": False}
    
    # Step 1: Extract audio to WAV (Whisper works best with WAV)
    audio_path = tempfile.mktemp(suffix=".wav")
    
    try:
        # Extract audio, convert to 16kHz mono WAV
        # -vn = no video, -acodec pcm_s16le = standard WAV, -ar 16000 = 16kHz, -ac 1 = mono
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y",  # Overwrite output
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"ffmpeg audio extraction failed: {result.stderr.decode()[:200]}")
            return {"text": "", "language": "", "has_speech": False}
        
        # Check if audio file is too small (likely no audio track)
        if os.path.getsize(audio_path) < 1024:  # Less than 1KB
            logger.info("Audio file too small, likely no audio track")
            return {"text": "", "language": "", "has_speech": False}
        
        # Step 2: Transcribe with Whisper
        result = await transcribe_audio(audio_path)
        
        if not result or not result.get("text", "").strip():
            return {"text": "", "language": "", "has_speech": False}
        
        # Step 3: Detect if it's actual speech or just music
        transcript_text = result["text"].strip()
        word_count = len(transcript_text.split())
        
        # Heuristic: if fewer than 5 words, likely not meaningful speech
        # Also check for common music transcription artifacts
        has_speech = word_count >= 5
        
        return {
            "text": transcript_text if has_speech else "",
            "language": result.get("language", ""),
            "has_speech": has_speech
        }
    
    finally:
        # ALWAYS clean up temp audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
```

### Frame Extraction

```python
"""
pipeline/frame_extractor.py

I suggest extracting frames with ffmpeg -vf fps=... filter.
This gives evenly-spaced frames without needing to calculate frame numbers.
If you find a better approach (e.g., selecting visually distinct frames
using image hashing), that's even better, but this works reliably.
"""
import subprocess
import tempfile
import base64
import os
import glob
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def extract_frames(video_path: str, duration_seconds: int) -> list[str]:
    """
    Extract key frames from video as base64-encoded JPEGs.
    
    Strategy: Extract MAX_FRAME_COUNT frames evenly distributed across the video.
    Resize to 768px width to reduce vision API token cost.
    
    Returns: List of base64 strings (no data URI prefix)
    """
    if not os.path.exists(video_path):
        return []
    
    max_frames = settings.MAX_FRAME_COUNT  # Default: 5
    
    # Calculate fps filter value
    # For a 30s video with 5 frames: fps=5/30 = 0.167 = ~1 frame every 6 seconds
    if duration_seconds and duration_seconds > 0:
        fps_value = max_frames / duration_seconds
    else:
        fps_value = 0.2  # Fallback: 1 frame every 5 seconds
    
    # Create temp directory for frames
    frame_dir = tempfile.mkdtemp(prefix="reeltrip_frames_")
    
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps={fps_value},scale=768:-1",  # Resize width to 768px
            "-frames:v", str(max_frames),
            "-q:v", "3",  # JPEG quality (2=best, 31=worst, 3 is good balance)
            "-y",
            os.path.join(frame_dir, "frame_%03d.jpg")
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"Frame extraction failed: {result.stderr.decode()[:200]}")
            return []
        
        # Read frames as base64
        frames_b64 = []
        frame_files = sorted(glob.glob(os.path.join(frame_dir, "frame_*.jpg")))
        
        for fpath in frame_files[:max_frames]:
            with open(fpath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                frames_b64.append(b64)
        
        logger.info(f"Extracted {len(frames_b64)} frames")
        return frames_b64
    
    finally:
        # Clean up frame directory
        import shutil
        shutil.rmtree(frame_dir, ignore_errors=True)
```

---

## 7. Pipeline Stage 2: Content Analysis

### Vision Analyzer — The Prompt Matters Most

```python
"""
pipeline/vision_analyzer.py

The vision prompt is critical. A bad prompt here means wrong location detection
for the entire rest of the pipeline. I suggest this exact prompt — it has been
designed to extract maximum location signals. If you find it misses things for
certain video types, add to it, but don't remove the existing instructions.
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
        temperature=0.2  # Low temperature for factual detection
    )
    
    return result
```

### Content Fuser — Merging All Signals

```python
"""
pipeline/content_fuser.py

This merges transcript + vision + metadata into one unified analysis.
Uses gpt-4o-mini because it's a text-only merge task — no reasoning needed.
"""
from services.openai_client import call_openai_json
import json

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
    vision_result: dict | None
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
        vision_analysis=json.dumps(vision_result, indent=2) if vision_result else "(Vision analysis unavailable)"
    )
    
    result = await call_openai_json(
        task="fast",  # gpt-4o-mini — text-only merge
        system_prompt=FUSION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2
    )
    
    return result
```

---

## 8. Pipeline Stage 3: Location Validation

### Google Places Client — Critical Implementation

```python
"""
services/google_places_client.py

I suggest using the Google Places API (New) via httpx, not the old googlemaps 
Python library. The new API is cleaner, cheaper, and supports field masks 
(which reduce cost per call). If you prefer the googlemaps library, it works 
too, but make sure to use field masks.

KEY COST NOTE: Google Places charges per field requested. Always use field masks
to only request what you need. A Place Details call with all fields costs ~$0.017.
With only basic fields, it costs ~$0.003. This adds up fast.
"""
import httpx
import logging
from config import get_settings
from services.supabase_client import get_cached_place, store_place

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = "https://places.googleapis.com/v1"

# Field masks — only request what we need
BASIC_FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types,places.photos,places.priceLevel,places.websiteUri"
NEARBY_FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types,places.photos,places.priceLevel"


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
                    "X-Goog-FieldMask": BASIC_FIELDS
                },
                json={
                    "textQuery": query,
                    "maxResultCount": max_results,
                    "languageCode": "en"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Places text search failed: {response.status_code} {response.text[:200]}")
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
    max_results: int = 10
) -> list[dict]:
    """
    Search for places near a location.
    
    place_type: "tourist_attraction" | "restaurant" | "lodging"
    """
    # Map our types to Google's includedTypes
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
                    "X-Goog-FieldMask": NEARBY_FIELDS
                },
                json={
                    "includedTypes": included_types,
                    "maxResultCount": min(max_results, 20),
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": latitude, "longitude": longitude},
                            "radius": float(radius)
                        }
                    },
                    "rankPreference": "POPULARITY"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Nearby search failed: {response.status_code}")
                return []
            
            data = response.json()
            return [_parse_place(p) for p in data.get("places", [])]
            
        except Exception as e:
            logger.error(f"Nearby search error: {e}")
            return []


async def get_photo_url(photo_name: str, max_width: int = 800) -> str | None:
    """
    Get a photo URL from a Google Places photo reference.
    
    The photo_name comes from the place data: places.photos[0].name
    Format: "places/{place_id}/photos/{photo_reference}"
    
    IMPORTANT: Google Places photos API returns the image directly,
    not a URL. To get a URL that works in <img> tags, we need to 
    construct the URL with our API key as a parameter.
    """
    if not photo_name:
        return None
    
    # The new Places API photo endpoint
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {
        "maxWidthPx": max_width,
        "key": settings.GOOGLE_PLACES_API_KEY
    }
    
    # This URL can be used directly in <img> tags (it redirects to the image)
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
```

**IMPORTANT NOTE on Google Places API versions:**
The code above uses the **Google Places API (New)** — the latest version. If you run into issues, check Google's docs. The old API uses different endpoints (`https://maps.googleapis.com/maps/api/place/...`). If you prefer the old API, that's fine — just be aware the new one has better pricing with field masks. It's up to you which to use.

---

## 9. Pipeline Stage 4: Highlights Generation

```python
"""
pipeline/highlights_generator.py

I suggest generating ALL highlights in a single API call (batch).
This is much cheaper than one call per place.

For 15 places, 1 batch call costs ~$0.0005.
15 individual calls would cost ~$0.0075. That's 15x more expensive.
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
        places: List of place dicts from Google Places (each has name, types, rating, etc.)
    
    Returns:
        List of highlight dicts, or fallback highlights on failure
    """
    if not places:
        return []
    
    # Prepare slim place data for the prompt (reduce token usage)
    slim_places = []
    for p in places:
        slim_places.append({
            "place_id": p.get("place_id", ""),
            "name": p.get("name", "Unknown"),
            "address": p.get("formatted_address", ""),
            "types": p.get("types", [])[:3],  # Only first 3 types
            "rating": p.get("rating"),
            "total_ratings": p.get("total_ratings"),
            "price_level": p.get("price_level"),
        })
    
    user_prompt = HIGHLIGHTS_USER_PROMPT.format(
        count=len(slim_places),
        places_json=json.dumps(slim_places, indent=1)
    )
    
    result = await call_openai_json(
        task="fast",  # gpt-4o-mini
        system_prompt=HIGHLIGHTS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=4096,
        temperature=0.6  # Slightly creative for engaging writing
    )
    
    if result and "highlights" in result:
        return result["highlights"]
    
    # FALLBACK: Generate basic highlights without AI
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
        "estimated_cost_usd": 0.0
    }
```

---

## 10. Pipeline Orchestrator

This is the master function that chains Stages 1-4 together and handles caching:

```python
"""
pipeline/orchestrator.py

This is the main pipeline. It chains all stages together.
Each stage checks cache first, only processes if cache misses.

I suggest implementing this as an async generator that yields progress events.
This naturally feeds into the SSE endpoint.
"""
import uuid
import logging
from typing import AsyncGenerator
from services.supabase_client import (
    get_cached_video, store_video,
    get_cached_location, store_location,
    create_session
)
from pipeline.video_extractor import extract_video_metadata
from pipeline.audio_processor import extract_and_transcribe
from pipeline.frame_extractor import extract_frames
from pipeline.vision_analyzer import analyze_frames
from pipeline.content_fuser import fuse_content
from pipeline.location_detector import detect_locations
from pipeline.location_validator import validate_and_enrich_locations
from pipeline.highlights_generator import generate_highlights
from services.google_places_client import get_photo_url
from utils.url_validator import validate_url
from config import get_settings
import json
import os

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_pipeline(url: str) -> AsyncGenerator[dict, None]:
    """
    Run the full video processing pipeline (Stages 1-4).
    Yields progress events as dicts that can be serialized to SSE.
    
    Each yielded dict has format:
        {"event": "event_name", "data": {...}}
    """
    
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
        
        video_metadata = cached_video
        video_file_path = None  # No video file needed from cache
        
    else:
        # Cache miss — full extraction
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
        
        # 2a: Audio transcription (parallel with frame extraction)
        transcript_result = {"text": "", "language": "", "has_speech": False}
        frames_base64 = []
        
        if video_file_path and os.path.exists(video_file_path):
            # Run audio and frame extraction in parallel
            import asyncio
            transcript_task = extract_and_transcribe(video_file_path)
            frames_task = extract_frames(video_file_path, metadata.get("duration_seconds", 30))
            
            transcript_result, frames_base64 = await asyncio.gather(
                transcript_task, frames_task
            )
        
        yield {"event": "progress", "data": {"stage": "analyzing", "percent": 30, "message": "Analyzing visual content..."}}
        
        # 2b: Vision analysis
        vision_result = None
        if frames_base64 and settings.ENABLE_VISION:
            vision_result = await analyze_frames(frames_base64)
        
        yield {"event": "progress", "data": {"stage": "analyzing", "percent": 38, "message": "Fusing content signals..."}}
        
        # 2c: Content fusion
        content_analysis = await fuse_content(
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            hashtags=metadata.get("hashtags", []),
            platform=platform,
            transcript=transcript_result.get("text", ""),
            has_speech=transcript_result.get("has_speech", False),
            vision_result=vision_result
        )
        
        if not content_analysis:
            yield {"event": "error", "data": {"message": "Could not analyze video content. Please try a different video."}}
            return
        
        yield {"event": "progress", "data": {"stage": "analyzing", "percent": 42, "message": "Content analyzed"}}
        yield {"event": "analysis", "data": content_analysis}
        
        # Cache stages 1-2
        await store_video(url, {
            **metadata,
            "transcript": transcript_result.get("text", ""),
            "transcript_language": transcript_result.get("language", ""),
            "has_speech": transcript_result.get("has_speech", False),
            "content_analysis": json.dumps(content_analysis),
        })
        
        video_metadata = metadata
        
        # Clean up video file
        if video_file_path and os.path.exists(video_file_path):
            os.remove(video_file_path)
    
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
        yield {"event": "progress", "data": {"stage": "locating", "percent": 48, "message": "Detecting locations..."}}
        
        # 3a: Validate and enrich locations with Google Places
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
        # Optionally include some restaurants too
        all_places.extend(location_result.get("nearby_restaurants", [])[:5])
        
        # Resolve photo URLs
        for place in all_places:
            if place.get("photo_reference") and not place.get("photo_url"):
                place["photo_url"] = await get_photo_url(place["photo_reference"])
        
        highlights = await generate_highlights(all_places)
        
        # Merge photo URLs into highlights
        place_photo_map = {p.get("place_id"): p.get("photo_url") for p in all_places if p.get("photo_url")}
        for h in highlights:
            if not h.get("photo_url"):
                h["photo_url"] = place_photo_map.get(h.get("place_id"), "")
        
        location_result["highlights"] = highlights
        
        yield {"event": "progress", "data": {"stage": "highlights", "percent": 88, "message": "Highlights ready"}}
        
        # Cache stages 3-4
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
```

---

## 11. SSE Streaming Pattern

### The FastAPI SSE Endpoint

```python
"""
This is the main endpoint that the frontend calls.
I suggest using this exact pattern for SSE with POST requests.

GOTCHA: Standard EventSource only supports GET. For POST, we use
fetch() with ReadableStream on the frontend side.
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="ReelTrip API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/process")
async def process_video(request: Request):
    body = await request.json()
    url = body.get("url", "").strip()
    
    if not url:
        return {"error": "URL is required"}
    
    async def event_stream():
        try:
            async for event in run_pipeline(url):
                event_name = event.get("event", "message")
                event_data = json.dumps(event.get("data", {}))
                yield f"event: {event_name}\ndata: {event_data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### Frontend SSE Consumer (React)

```typescript
/**
 * lib/sse.ts
 * 
 * I suggest this pattern for consuming SSE from a POST endpoint.
 * Standard EventSource does NOT support POST, so we use fetch + ReadableStream.
 * If you find a library like 'eventsource-parser' cleaner, use that instead,
 * but this vanilla approach has zero dependencies.
 */

export interface SSEEvent {
  event: string;
  data: any;
}

export async function streamPost(
  url: string,
  body: object,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): Promise<void> {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      let currentEvent = "message";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentData) {
          // Empty line = end of event
          try {
            const parsed = JSON.parse(currentData);
            onEvent({ event: currentEvent, data: parsed });
          } catch (e) {
            console.warn("Failed to parse SSE data:", currentData);
          }
          currentEvent = "message";
          currentData = "";
        }
      }
    }

    onComplete?.();
  } catch (error) {
    onError?.(error as Error);
  }
}
```

Usage in a React component:

```typescript
// In your processing page component:
import { streamPost } from "@/lib/sse";

const processVideo = async (url: string) => {
  setIsProcessing(true);
  
  await streamPost(
    "/api/v1/process",
    { url },
    (event) => {
      switch (event.event) {
        case "progress":
          setProgress(event.data.percent);
          setStageMessage(event.data.message);
          break;
        case "metadata":
          setVideoTitle(event.data.title);
          setThumbnail(event.data.thumbnail_url);
          break;
        case "analysis":
          setDestination(event.data.destination_city + ", " + event.data.destination_country);
          setVibe(event.data.dominant_vibe);
          break;
        case "highlights":
          setHighlights(event.data.highlights);
          setShowHighlights(true);
          break;
        case "complete":
          setSessionId(event.data.session_id);
          setIsProcessing(false);
          break;
        case "error":
          setError(event.data.message);
          setIsProcessing(false);
          break;
      }
    },
    (error) => {
      setError(error.message);
      setIsProcessing(false);
    }
  );
};
```

---

## 14. Multi-Agent System: LangGraph Setup

### I suggest this LangGraph pattern:

```python
"""
agents/orchestrator.py

LangGraph orchestrator for the multi-agent travel planner.

CRITICAL NOTE: LangGraph's API changes between versions. The pattern below 
works with langgraph >= 0.2.0. If you use a different version, check their 
docs. The core concept (StateGraph with nodes and edges) stays the same.

I suggest running agents in two batches:
  Batch 1 (parallel): flight, hotel, weather, safety  
  Batch 2 (after batch 1): activity, transport
  Then: budget → assembler

If LangGraph's parallel execution is tricky to set up, you can simplify 
by running them sequentially. It's slower but simpler. Up to you.
Parallel saves ~10-15 seconds of total time.
"""
from langgraph.graph import StateGraph, END
from agents.state import TravelPlannerState
from agents.flight_agent import run_flight_agent
from agents.hotel_agent import run_hotel_agent
from agents.weather_agent import run_weather_agent
from agents.safety_agent import run_safety_agent
from agents.activity_agent import run_activity_agent
from agents.transport_agent import run_transport_agent
from agents.budget_agent import run_budget_agent
from agents.itinerary_assembler import run_assembler
import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_travel_planner(state: TravelPlannerState) -> TravelPlannerState:
    """
    Run all agents and assemble the itinerary.
    
    SIMPLER ALTERNATIVE to full LangGraph if you find the graph setup complex:
    Just run agents in sequence/parallel using asyncio directly.
    
    I suggest trying the simple asyncio approach first. If you want the 
    LangGraph graph for better error handling and retries, refactor later.
    """
    
    # --- BATCH 1: Research (parallel) ---
    logger.info("Starting Batch 1: Research agents...")
    
    flight_task = run_flight_agent(state)
    hotel_task = run_hotel_agent(state)
    weather_task = run_weather_agent(state)
    safety_task = run_safety_agent(state)
    
    results = await asyncio.gather(
        flight_task, hotel_task, weather_task, safety_task,
        return_exceptions=True  # Don't crash if one agent fails
    )
    
    # Assign results (handle exceptions gracefully)
    state["flight_data"] = results[0] if not isinstance(results[0], Exception) else None
    state["hotel_data"] = results[1] if not isinstance(results[1], Exception) else None
    state["weather_data"] = results[2] if not isinstance(results[2], Exception) else None
    state["safety_data"] = results[3] if not isinstance(results[3], Exception) else None
    
    # Log any failures
    for i, name in enumerate(["flight", "hotel", "weather", "safety"]):
        if isinstance(results[i], Exception):
            logger.error(f"{name} agent failed: {results[i]}")
            state["agent_errors"].append(f"{name}: {str(results[i])}")
    
    # --- BATCH 2: Planning (needs batch 1 results) ---
    logger.info("Starting Batch 2: Planning agents...")
    
    activity_task = run_activity_agent(state)
    transport_task = run_transport_agent(state)
    
    results2 = await asyncio.gather(
        activity_task, transport_task,
        return_exceptions=True
    )
    
    state["activity_data"] = results2[0] if not isinstance(results2[0], Exception) else None
    state["transport_data"] = results2[1] if not isinstance(results2[1], Exception) else None
    
    for i, name in enumerate(["activity", "transport"]):
        if isinstance(results2[i], Exception):
            logger.error(f"{name} agent failed: {results2[i]}")
            state["agent_errors"].append(f"{name}: {str(results2[i])}")
    
    # --- BUDGET OPTIMIZATION ---
    logger.info("Running budget agent...")
    try:
        state["budget_analysis"] = await run_budget_agent(state)
    except Exception as e:
        logger.error(f"Budget agent failed: {e}")
        state["budget_analysis"] = None
    
    # --- FINAL ASSEMBLY ---
    logger.info("Assembling itinerary...")
    try:
        state["itinerary"] = await run_assembler(state)
    except Exception as e:
        logger.error(f"Itinerary assembly failed: {e}")
        state["itinerary"] = None
    
    return state
```

### Agent State Definition

```python
"""
agents/state.py
"""
from typing import TypedDict

class TravelPlannerState(TypedDict):
    # Input (set before running planner)
    location_result: dict           # From pipeline stage 3
    user_preferences: dict          # From preference form
    highlights: list[dict]          # From pipeline stage 4
    selected_cities: list[str]      # Cities user selected
    
    # Agent outputs (populated during planning)
    flight_data: dict | None
    hotel_data: dict | None
    weather_data: dict | None
    safety_data: dict | None
    activity_data: dict | None
    transport_data: dict | None
    budget_analysis: dict | None
    
    # Final output
    itinerary: dict | None
    
    # Monitoring
    agent_errors: list[str]
    progress_updates: list[dict]
```

---

## 15-22. Agent Implementation Pattern

Every agent follows the same pattern. I'll show the Flight Agent in full detail, then summarize the pattern for others.

### Universal Agent Pattern

```python
"""
PATTERN: Every agent has the same structure:

1. Read what it needs from state
2. Build search queries (for Tavily) or API calls (for Google Places, Weather, etc.)
3. Call the external service
4. Parse the results into structured data using gpt-4o-mini
5. Return the structured output

If the external service fails, return a degraded but usable fallback.
NEVER return None without trying the fallback first.
"""
```

### Flight Agent — Full Implementation

```python
"""
agents/flight_agent.py

I suggest using Tavily search to find flight information rather than trying
to scrape airline websites. Tavily returns structured snippets that gpt-4o-mini
can parse into flight data. If you find a better flight data source (like an
actual flight API), use that instead — it would be more reliable.
"""
from services.openai_client import call_openai_json
from services.tavily_client import search_tavily  # You'll need to implement this
import json
import logging

logger = logging.getLogger(__name__)

FLIGHT_EXTRACTION_PROMPT = """You are a flight data extraction assistant.
Given search results about flights between two cities, extract structured flight information.

If the search results contain actual flight data (prices, airlines, durations), extract it.
If the search results are vague, provide reasonable estimates based on the route.

ALWAYS provide at least one flight option. If you truly cannot find any data, estimate based
on the distance between cities and typical airline pricing.

Respond in JSON format ONLY."""

async def run_flight_agent(state: dict) -> dict:
    """
    Research flight options for the trip.
    """
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    
    home_city = prefs.get("home_city", "Mumbai")
    home_country = prefs.get("home_country", "India")
    dest_city = location.get("primary_city", "")
    dest_country = location.get("primary_country", "")
    month = prefs.get("month_of_travel", "")
    budget_currency = prefs.get("budget_currency", "USD")
    
    # Determine if flights are needed
    if home_country.lower() == dest_country.lower():
        route_type = "domestic"
    else:
        route_type = "international"
    
    # Build search queries
    queries = [
        f"cheapest flights from {home_city} to {dest_city} {month} 2026",
        f"{home_city} to {dest_city} flight duration airlines",
    ]
    
    # For multi-city trips, add inter-city flights/transport
    selected_cities = state.get("selected_cities", [])
    if len(selected_cities) > 1:
        queries.append(f"travel from {selected_cities[0]} to {selected_cities[1]} options")
    
    # Return flight query
    queries.append(f"cheapest flights from {dest_city} to {home_city} {month} 2026")
    
    # Search with Tavily
    search_results = []
    for q in queries:
        result = await search_tavily(q)
        if result:
            search_results.append({"query": q, "results": result})
    
    # Parse with LLM
    user_prompt = f"""Extract flight information from these search results:

Route: {home_city} → {dest_city} (and return)
Month: {month}
Route type: {route_type}
Selected cities: {json.dumps(selected_cities)}
Currency preference: {budget_currency}

Search results:
{json.dumps(search_results, indent=1)[:4000]}

Return JSON:
{{
    "flights_needed": true,
    "route_type": "{route_type}",
    "outbound": {{
        "from_city": "{home_city}",
        "from_airport_code": "airport IATA code",
        "to_city": "{dest_city}",
        "to_airport_code": "airport IATA code",
        "airlines": ["airline names found"],
        "estimated_duration": "Xh Ym",
        "estimated_price": number in {budget_currency},
        "price_currency": "{budget_currency}",
        "departure_time_suggestion": "morning/evening",
        "source": "where this price came from"
    }},
    "return": {{
        ...same structure...
    }},
    "inter_city_flights": [
        ...if multi-city, flights between cities...
    ],
    "booking_url": "https://www.google.com/travel/flights?q=from+{home_city}+to+{dest_city}"
}}"""

    result = await call_openai_json(
        task="fast",
        system_prompt=FLIGHT_EXTRACTION_PROMPT,
        user_prompt=user_prompt,
        max_tokens=2048,
        temperature=0.2
    )
    
    if result:
        return result
    
    # Fallback: return a skeleton with just the route info
    return {
        "flights_needed": True,
        "route_type": route_type,
        "outbound": {
            "from_city": home_city,
            "to_city": dest_city,
            "estimated_price": 0,
            "price_currency": budget_currency,
            "source": "Unable to find pricing data"
        },
        "return": {
            "from_city": dest_city,
            "to_city": home_city,
            "estimated_price": 0,
            "price_currency": budget_currency,
            "source": "Unable to find pricing data"
        },
        "booking_url": f"https://www.google.com/travel/flights"
    }
```

### Tavily Client

```python
"""
services/tavily_client.py

I suggest keeping Tavily queries short and specific (3-8 words work best).
Use search_depth="basic" for most queries (cheaper).
Use "advanced" only for complex queries where basic misses results.
"""
from tavily import TavilyClient, AsyncTavilyClient
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

_client = None

def _get_client():
    global _client
    if _client is None and settings.TAVILY_API_KEY:
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client

async def search_tavily(query: str, max_results: int = 5, depth: str = "basic") -> list[dict] | None:
    """
    Search the web using Tavily.
    Returns list of result dicts with 'title', 'content', 'url' keys.
    Returns None on failure (never crashes).
    """
    client = _get_client()
    if not client:
        logger.warning("Tavily not configured, skipping web search")
        return None
    
    try:
        # NOTE: Tavily's Python client is synchronous by default.
        # If this blocks the event loop, wrap in asyncio.to_thread().
        import asyncio
        result = await asyncio.to_thread(
            client.search,
            query=query,
            search_depth=depth,
            max_results=max_results,
            include_answer=True
        )
        
        return result.get("results", [])
    
    except Exception as e:
        logger.error(f"Tavily search failed for '{query}': {e}")
        return None
```

### Hotel, Weather, Safety, Activity, Transport, Budget Agents

Each follows the same pattern as Flight Agent. Here are the KEY DIFFERENCES for each:

**Hotel Agent:**
- Uses BOTH Google Places nearby_search (for hotel names, ratings) AND Tavily (for prices)
- Google Places gives you real hotel names + photos; Tavily gives approximate prices
- I suggest searching Google Places first, then Tavily for prices of the top 5 results

**Weather Agent:**
- Uses OpenWeatherMap API directly (not Tavily)
- For trips within 5 days: use forecast endpoint
- For trips further out: use Tavily to search "average weather {city} {month}"
- Very simple agent — minimal LLM usage, mostly API data parsing

**Safety Agent:**
- Primarily uses Tavily to search travel advisories
- Queries: "{country} travel advisory 2026", "{city} tourist safety tips"
- gpt-4o-mini summarizes the search results
- Also include cultural etiquette tips

**Activity Agent:**
- Uses highlights data (already generated), Google Places, and Tavily
- Groups activities by day based on geographic proximity
- Accounts for weather (outdoor vs indoor) and user preferences
- This is the MOST complex agent after the assembler

**Transport Agent:**
- Uses Tavily for inter-city transport options
- Uses Google Places knowledge for intra-city transport (metro, taxi)
- Simple queries like "best way to travel from Dubai to Abu Dhabi"

**Budget Agent:**
- Does NOT call external APIs
- Receives all other agent outputs and sums up costs
- Compares to user's stated budget
- If over budget, suggests specific cuts
- Uses gpt-4o-mini for the optimization suggestions

---

## 23. Itinerary Assembler — The Big Prompt

```python
"""
agents/itinerary_assembler.py

This is the MOST IMPORTANT prompt in the entire system.
It takes ALL agent outputs and creates the final itinerary.
Uses gpt-4o because it needs complex multi-constraint reasoning.

I suggest keeping this prompt VERY structured with clear sections.
The more structured the input, the better the output.
"""
from services.openai_client import call_openai_json
import json

ASSEMBLER_SYSTEM_PROMPT = """You are the world's best travel itinerary planner. 
You have been given research data from specialized travel agents. Your job is to 
assemble this data into a perfect day-by-day itinerary.

CRITICAL RULES:
1. The itinerary must be PHYSICALLY POSSIBLE — check travel times
2. First day starts AFTER flight arrival time
3. Last day ends BEFORE flight departure time  
4. Meals: breakfast 7:30-9:00, lunch 12:00-14:00, dinner 19:00-21:00
5. No more than 4 major activities per day
6. Group nearby places together to minimize transit
7. Respect dietary preferences for ALL food recommendations
8. Include must-have items from the user's bucket list
9. Account for weather — no outdoor activities during bad weather times
10. Budget must not exceed the stated budget
11. Include realistic travel times between every activity
12. Every restaurant must match dietary preferences
13. Every cost must be in the user's preferred currency

Respond in JSON format ONLY.
Output must follow the EXACT schema provided."""

async def run_assembler(state: dict) -> dict | None:
    """
    Assemble the final itinerary from all agent outputs.
    """
    prefs = state.get("user_preferences", {})
    location = state.get("location_result", {})
    
    # Build the mega-prompt with all agent data
    user_prompt = f"""
DESTINATION: {location.get('primary_city', '')}, {location.get('primary_country', '')}
SELECTED CITIES: {json.dumps(state.get('selected_cities', []))}

USER PREFERENCES:
{json.dumps(prefs, indent=2)}

FLIGHT DATA:
{json.dumps(state.get('flight_data'), indent=2) if state.get('flight_data') else 'No flight data available'}

HOTEL DATA:
{json.dumps(state.get('hotel_data'), indent=2) if state.get('hotel_data') else 'No hotel data available'}

WEATHER DATA:
{json.dumps(state.get('weather_data'), indent=2) if state.get('weather_data') else 'No weather data available'}

SAFETY DATA:
{json.dumps(state.get('safety_data'), indent=2) if state.get('safety_data') else 'No safety data available'}

ACTIVITY DATA:
{json.dumps(state.get('activity_data'), indent=2)[:6000] if state.get('activity_data') else 'No activity data available'}

TRANSPORT DATA:
{json.dumps(state.get('transport_data'), indent=2) if state.get('transport_data') else 'No transport data available'}

BUDGET ANALYSIS:
{json.dumps(state.get('budget_analysis'), indent=2) if state.get('budget_analysis') else 'No budget analysis available'}

---

Generate a complete itinerary as JSON with this EXACT structure:
{{
    "trip_title": "Creative trip title",
    "destination_country": "string",
    "destination_cities": ["city1", "city2"],
    "start_date": "estimated date based on month",
    "end_date": "estimated end date",
    "total_days": {prefs.get('trip_duration_days', 3)},
    "total_travelers": {prefs.get('number_of_travelers', 2)},
    "flights": [
        {{
            "type": "international or domestic",
            "from_city": "string",
            "from_airport_code": "IATA",
            "to_city": "string", 
            "to_airport_code": "IATA",
            "departure_time": "HH:MM",
            "arrival_time": "HH:MM",
            "duration": "Xh Ym",
            "estimated_price": number,
            "price_currency": "INR",
            "booking_url": "https://google.com/travel/flights?...",
            "day_number": 1
        }}
    ],
    "hotels": [
        {{
            "name": "Hotel Name",
            "city": "City",
            "address": "Address",
            "check_in_date": "date",
            "check_out_date": "date",
            "nights": number,
            "price_per_night": number,
            "total_price": number,
            "price_currency": "INR",
            "rating": 4.5,
            "photo_url": "url or empty",
            "why_recommended": "1-2 sentences",
            "booking_url": "url",
            "latitude": number,
            "longitude": number
        }}
    ],
    "days": [
        {{
            "day_number": 1,
            "date": "March 7, 2026",
            "city": "Dubai",
            "theme": "Arrival & First Impressions",
            "activities": [
                {{
                    "time": "14:00",
                    "title": "Check-in at Hotel",
                    "type": "checkin",
                    "venue_name": "Hotel Name",
                    "description": "Brief description",
                    "duration_minutes": 30,
                    "estimated_cost": 0,
                    "cost_currency": "INR",
                    "latitude": number,
                    "longitude": number,
                    "google_maps_url": "https://maps.google.com/?q=lat,lng",
                    "photo_url": "",
                    "practical_tip": "Insider tip",
                    "booking_url": ""
                }}
            ]
        }}
    ],
    "budget_breakdown": {{
        "flights_total": number,
        "accommodation_total": number,
        "food_total": number,
        "activities_total": number,
        "transportation_total": number,
        "miscellaneous_buffer": number,
        "grand_total": number,
        "currency": "INR"
    }},
    "weather_summary": "Brief weather description for the period",
    "packing_suggestions": ["item1", "item2"],
    "cultural_tips": ["tip1", "tip2"],
    "visa_info": "Visa requirements or null",
    "emergency_numbers": {{"police": "number", "ambulance": "number"}}
}}"""

    result = await call_openai_json(
        task="reasoning",  # gpt-4o — this is complex multi-constraint reasoning
        system_prompt=ASSEMBLER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=8192,  # Itineraries are large
        temperature=0.3
    )
    
    return result
```

---

## 33. Critical Gotchas & Common Mistakes

### MUST READ BEFORE CODING:

1. **yt-dlp needs ffmpeg installed.** Without ffmpeg on the system, audio extraction and frame extraction will fail silently. Make sure your Dockerfile or system has `ffmpeg` installed.

2. **Google Places API (New) vs (Old).** The new API uses `places.googleapis.com`. The old uses `maps.googleapis.com/maps/api/place`. The new one is better but has different request formats. Don't mix them. Pick one.

3. **OpenAI `response_format: json_object` requires "JSON" in the prompt.** If your system prompt doesn't contain the word "JSON" somewhere, the API will reject the request. Always include "Respond in JSON format" in your system prompt.

4. **SSE with POST requests.** The browser's native `EventSource` API only supports GET. For POST, you must use `fetch()` with `response.body.getReader()`. This is shown in the SSE section above. Don't try to use EventSource for POST — it won't work.

5. **Supabase `maybe_single()` vs `single()`.** Use `maybe_single()` for cache lookups. `single()` throws an error if no row is found. `maybe_single()` returns None.

6. **Google Places photo URLs.** The new Places API returns a `photo.name` like `places/ABC/photos/XYZ`. To get a displayable URL, you construct: `https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=800&key=YOUR_KEY`. This URL can be used directly in `<img>` tags.

7. **Tavily Python client is synchronous.** In an async FastAPI app, wrap Tavily calls in `asyncio.to_thread()` to avoid blocking the event loop.

8. **gpt-4o vision `detail` parameter.** `"low"` = 85 tokens per image. `"high"` = up to 1105 tokens. `"auto"` = model decides. Start with `"low"` to save money. Most travel videos have clear, recognizable landmarks that `"low"` handles fine.

9. **Next.js API proxy.** If your frontend (Vercel) and backend (Railway/Render) are on different domains, you'll need either CORS configuration or a Next.js API route proxy. I suggest the API route proxy in `app/api/[...proxy]/route.ts` — it's cleaner and avoids CORS issues entirely.

10. **JSON inside JSONB.** When storing JSON in Supabase JSONB columns, use `json.dumps()` before inserting and `json.loads()` after reading. Supabase's Python client sometimes returns JSONB as strings, sometimes as dicts. Always handle both cases.

11. **Temp file cleanup.** The video pipeline creates temp files (video, audio, frames). ALWAYS clean them up in a `finally` block. Leaked temp files will fill disk space.

12. **Rate limits.** OpenAI has rate limits per minute. If you're processing multiple videos simultaneously, you'll hit them. I suggest processing one video at a time per user and queuing additional requests.

13. **Currency in itinerary.** The user specifies a budget currency (e.g., INR). ALL costs in the itinerary must be in that currency. Use ExchangeRate API to convert USD prices (from Tavily search results) to the user's currency.

14. **Instagram cookies expire.** If Instagram extraction stops working, the cookies file is likely expired. Users need to re-export cookies from their browser.

15. **The `location_validator.py` file I mentioned in the project structure** — this is the function that chains location_detector output → Google Places text_search → nearby_search. It's a glue function, not an LLM call. I suggest implementing it as a simple async function that calls google_places_client methods.

---

## 34. Testing Plan

### Test with these REAL URLs:

```
# YouTube Shorts (stable, public, no auth needed)
https://youtube.com/shorts/dQw4w9WgXcQ   # Well-known video
https://www.youtube.com/shorts/{any_travel_short}

# To find travel shorts, search YouTube for "travel shorts"
# Pick 3-4 from different destinations (beach, city, mountain, etc.)
```

### Quick Smoke Test Script:

```python
"""
tests/smoke_test.py

Run this after implementing stages 1-4 to verify the pipeline works.
"""
import asyncio
from pipeline.orchestrator import run_pipeline

async def main():
    url = "https://www.youtube.com/shorts/YOUR_TEST_SHORT_ID"
    
    async for event in run_pipeline(url):
        print(f"[{event['event']}] {event.get('data', {}).get('message', event.get('data', ''))}")
    
    print("\n✅ Pipeline completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 35. Deployment Checklist

Before deploying, verify:

```
[ ] All environment variables are set in the deployment platform
[ ] ffmpeg is available in the deployment environment
[ ] yt-dlp is installed and up-to-date
[ ] Supabase tables are created (run schema.sql)
[ ] Google Places API key has Places API (New) enabled
[ ] OpenAI API key has sufficient credits
[ ] CORS is configured correctly for the frontend domain
[ ] Rate limiting is implemented on /api/v1/process
[ ] Temp file cleanup works (no disk space leaks)
[ ] SSE streaming works through any reverse proxy (check X-Accel-Buffering)
[ ] Frontend builds successfully with `npm run build`
[ ] All booking URLs point to real booking sites (Google Flights, Google Hotels)
[ ] All map links generate correct Google Maps URLs
[ ] Error states show user-friendly messages
[ ] Mobile layout is tested on a real phone
```

---

## Summary: Files to Create (in order)

```
BACKEND:
1.  config.py                        → Section 3
2.  services/supabase_client.py      → Section 4
3.  services/openai_client.py        → Section 5
4.  models/*.py                      → Define all Pydantic models from master doc
5.  utils/url_validator.py           → Section 6
6.  pipeline/video_extractor.py      → Section 6
7.  pipeline/audio_processor.py      → Section 6
8.  pipeline/frame_extractor.py      → Section 6
9.  pipeline/vision_analyzer.py      → Section 7
10. pipeline/content_fuser.py        → Section 7
11. pipeline/location_detector.py    → Small gpt-4o-mini call for ranking
12. services/google_places_client.py → Section 8
13. pipeline/location_validator.py   → Chains detector + Google Places
14. pipeline/highlights_generator.py → Section 9
15. pipeline/orchestrator.py         → Section 10
16. main.py                          → Section 11 (SSE endpoint)
17. services/tavily_client.py        → Section 15
18. services/weather_client.py       → OpenWeatherMap wrapper
19. services/exchange_rate_client.py → ExchangeRate API wrapper
20. agents/state.py                  → Section 14
21. agents/flight_agent.py           → Section 16
22. agents/hotel_agent.py            → Same pattern as flight
23. agents/weather_agent.py          → Uses weather_client
24. agents/safety_agent.py           → Uses Tavily
25. agents/activity_agent.py         → Most complex agent
26. agents/transport_agent.py        → Uses Tavily
27. agents/budget_agent.py           → Pure calculation
28. agents/itinerary_assembler.py    → Section 23
29. agents/orchestrator.py           → Section 14

FRONTEND:
30. Next.js project scaffold         → Section 25
31. lib/sse.ts                       → Section 11
32. Landing page                     → URL input
33. Processing page                  → Progress tracker + highlights
34. Itinerary page                   → Tabs + timeline + budget
35. All components from master doc Section 20

DATABASE:
36. Run schema.sql in Supabase       → Section 4
```

---

**FINAL NOTE TO CLAUDE CODE:**

You have two documents:
1. **Master Documentation** — WHAT to build (architecture, schemas, user flow)
2. **This Planning Guide** — HOW to build it (code snippets, order, gotchas)

Build the backend first (Phases 1-2). Test with a real YouTube Short URL using the smoke test. Then build the frontend (Phase 3). Then build the agent system (Phase 4-5). Then polish (Phase 6).

Do not try to build everything at once. Follow the implementation order. Each phase builds on the previous one.

The code snippets in this document are SUGGESTIONS — they show the correct pattern and approach. Adapt them as needed. If you find a better way to do something, do it. But if the snippet works as-is, use it as-is. Don't rewrite working code for style.

The goal: a system where a real user pastes a travel reel URL and gets a trip plan they would actually follow. Everything else is secondary.

---

*End of ReelTrip Implementation Planning Guide*
