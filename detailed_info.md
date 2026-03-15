# ReelTrip - Complete Project Documentation

> **AI-Powered Travel Planning from Short-Form Videos**
> Transform Instagram Reels, YouTube Shorts, and TikTok videos into complete, personalized trip itineraries with real flights, hotels, activities, budgets, and booking links.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Directory Structure](#3-directory-structure)
4. [Prerequisites & Quick Start](#4-prerequisites--quick-start)
5. [Environment Variables](#5-environment-variables)
6. [API Keys Reference](#6-api-keys-reference)
7. [Database Schema](#7-database-schema)
8. [API Endpoints](#8-api-endpoints)
9. [7-Stage Pipeline](#9-7-stage-pipeline)
10. [Multi-Agent System](#10-multi-agent-system)
11. [Backend Architecture](#11-backend-architecture)
12. [Frontend Architecture](#12-frontend-architecture)
13. [State Management (Zustand)](#13-state-management-zustand)
14. [Type System (TypeScript)](#14-type-system-typescript)
15. [SSE Streaming](#15-sse-streaming)
16. [User Flow](#16-user-flow)
17. [Styling & Design System](#17-styling--design-system)
18. [Component Hierarchy](#18-component-hierarchy)
19. [External Service Integrations](#19-external-service-integrations)
20. [Cost Optimization](#20-cost-optimization)
21. [Error Handling](#21-error-handling)
22. [Deployment](#22-deployment)
23. [Known Limitations & Future Roadmap](#23-known-limitations--future-roadmap)

---

## 1. Project Overview

### What is ReelTrip?

ReelTrip is an end-to-end AI-powered travel planning system. A user pastes a short-form travel video URL, and the system:

1. **Extracts** video metadata, audio transcript, and visual frames
2. **Analyzes** content using GPT-4o vision and text models
3. **Identifies** real-world locations and validates them via Google Places API
4. **Generates** rich, magazine-quality destination highlights with photos
5. **Collects** user preferences (budget, style, duration, dietary needs)
6. **Plans** a complete itinerary using 8 specialized AI agents running in parallel
7. **Delivers** a day-by-day plan with flights, hotels, activities, budget breakdown, visa info, weather, and booking links

### The Problem It Solves

People discover dream destinations on social media but have no easy way to turn "I want to go there" into a real, actionable trip plan. ReelTrip bridges that gap -- from inspiration (a 30-second Reel) to execution (a fully planned itinerary).

### Core Design Principles

- **Zero Hallucination Policy**: All facts grounded in real API data (Google Places, Tavily web search, Open-Meteo weather)
- **Progressive Disclosure**: Information revealed step-by-step, never overwhelming the user
- **Cost-Conscious AI**: Use the cheapest model that can handle each task (gpt-4o-mini for simple tasks, gpt-4o only for vision/complex reasoning)
- **Real Data, Not Templates**: Actual API integrations for flights, hotels, weather, currency
- **Every Button Works**: No placeholder UI -- all interactive elements are functional

---

## 2. Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Core runtime |
| FastAPI | 0.115.0 | Async web framework |
| Uvicorn | 0.30.0 | ASGI server |
| Pydantic | 2.9.0 | Data validation & serialization |
| pydantic-settings | 2.5.0 | Environment configuration |
| OpenAI SDK | 1.50.0 | GPT-4o, GPT-4o-mini, Whisper API |
| yt-dlp | 2024.12.23 | Video extraction from social platforms |
| LangGraph | >=0.2.0 | Multi-agent orchestration |
| LangChain OpenAI | >=0.1.0 | LangChain-OpenAI integration |
| LangChain Core | >=0.2.27 | LangChain base abstractions |
| Tavily Python | 0.5.0 | Web search API |
| httpx | 0.27.0 | Async HTTP client |
| Supabase | 2.9.0 | Database client |
| Pillow | 10.4.0 | Image processing |
| aiofiles | 24.1.0 | Async file operations |
| python-multipart | 0.0.9 | Multipart form handling |
| python-dotenv | 1.0.1 | .env file loading |

**System dependency**: `ffmpeg` must be installed on PATH (audio extraction + frame extraction)

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.1.6 | React meta-framework (App Router) |
| React | 19.2.3 | UI library |
| TypeScript | ^5 | Type safety |
| Tailwind CSS | ^4 | Utility-first CSS |
| Zustand | 5.0.11 | Lightweight state management |
| Framer Motion | 12.36.0 | Animations & transitions |
| shadcn/ui | 4.0.6 | Component library |
| Lucide React | 0.577.0 | Icon library |
| clsx | 2.1.1 | Class name concatenation |
| tailwind-merge | 3.5.0 | Tailwind class merging |
| tw-animate-css | 1.4.0 | CSS animations |
| @base-ui/react | ^1.3.0 | Base UI primitives |
| class-variance-authority | 0.7.1 | Component variant management |

### Infrastructure

| Service | Purpose |
|---------|---------|
| Supabase | PostgreSQL database, REST API |
| Vercel | Frontend deployment |
| Railway / Render | Backend deployment |

---

## 3. Directory Structure

```
reeltrip-travel/
|
|-- architechture.md                  # Master system architecture doc (95KB)
|-- implementation.md                 # Implementation guide for Claude Code (95KB)
|-- README.md                         # Quick start guide
|-- api_keys_which_you_will_require.txt  # API key reference
|-- detailed_info.md                  # THIS FILE
|
|-- backend/
|   |-- main.py                       # FastAPI app entry point, all API endpoints
|   |-- config.py                     # Centralized Settings class (Pydantic BaseSettings)
|   |-- dependencies.py               # FastAPI injectable dependencies
|   |-- requirements.txt              # Python dependencies
|   |-- .env                          # Environment variables (actual keys)
|   |-- .env.example                  # Environment template
|   |
|   |-- pipeline/                     # Video Processing Pipeline (Stages 1-4)
|   |   |-- orchestrator.py           # Master pipeline coordinator, chains all stages
|   |   |-- video_extractor.py        # yt-dlp video metadata extraction
|   |   |-- audio_processor.py        # ffmpeg audio extraction + Whisper transcription
|   |   |-- frame_extractor.py        # ffmpeg keyframe extraction (base64)
|   |   |-- vision_analyzer.py        # GPT-4o multi-frame vision analysis
|   |   |-- content_fuser.py          # GPT-4o-mini signal fusion (text+audio+vision)
|   |   |-- location_detector.py      # GPT-4o-mini location ranking & deduplication
|   |   |-- location_validator.py     # Google Places geocoding & enrichment
|   |   |-- highlights_generator.py   # GPT-4o-mini rich highlight generation
|   |
|   |-- agents/                       # Multi-Agent Travel Planner (Stages 5-7)
|   |   |-- orchestrator.py           # Agent coordinator (batch execution)
|   |   |-- state.py                  # TravelPlannerState TypedDict
|   |   |-- flight_agent.py           # Flight research via Tavily search
|   |   |-- hotel_agent.py            # Hotel search via Tavily search
|   |   |-- activity_agent.py         # Activity planning using highlights data
|   |   |-- weather_agent.py          # Weather forecasting via Open-Meteo
|   |   |-- safety_agent.py           # Safety & visa assessment via Tavily
|   |   |-- transport_agent.py        # Inter-city transport planning
|   |   |-- budget_agent.py           # Budget analysis & optimization
|   |   |-- itinerary_assembler.py    # Final GPT-4o itinerary assembly
|   |
|   |-- services/                     # External API Clients
|   |   |-- openai_client.py          # OpenAI wrapper (model routing, JSON repair, retries)
|   |   |-- google_places_client.py   # Google Places API (search, details, nearby, photos)
|   |   |-- tavily_client.py          # Tavily web search wrapper
|   |   |-- weather_client.py         # Open-Meteo weather API client
|   |   |-- exchange_rate_client.py   # ExchangeRate-API currency conversion
|   |   |-- supabase_client.py        # Supabase CRUD operations for all tables
|   |
|   |-- models/                       # Pydantic Data Schemas
|   |   |-- video.py                  # VideoMetadata, TranscriptResult models
|   |   |-- location.py              # CandidateLocation, ValidatedPlace models
|   |   |-- preferences.py            # UserPreferences model
|   |   |-- agents.py                 # Agent output models (FlightData, HotelData, etc.)
|   |   |-- itinerary.py              # TripItinerary and all sub-models
|   |   |-- api.py                    # API request/response models (HealthResponse, etc.)
|   |
|   |-- utils/                        # Utility Functions
|   |   |-- url_validator.py          # URL validation regex (Instagram, YouTube, TikTok)
|   |   |-- currency.py               # Currency conversion logic
|   |   |-- geo.py                    # Geolocation distance calculations
|   |
|   |-- database/
|       |-- schema.sql                # PostgreSQL schema (run in Supabase SQL Editor)
|
|-- frontend/
    |-- package.json                  # Node.js dependencies & scripts
    |-- package-lock.json             # Dependency lock file
    |-- tsconfig.json                 # TypeScript configuration
    |-- next.config.ts                # Next.js configuration
    |-- postcss.config.mjs            # PostCSS + Tailwind CSS 4 config
    |-- components.json               # shadcn/ui configuration
    |-- .env.local                    # Frontend environment variables
    |-- .gitignore                    # Git ignore rules
    |-- next-env.d.ts                 # Next.js type declarations
    |-- README.md                     # Frontend readme
    |
    |-- app/                          # Next.js App Router
    |   |-- layout.tsx                # Root layout (html, body, Inter font, metadata)
    |   |-- page.tsx                  # Landing page (URL input)
    |   |-- globals.css               # Global styles, CSS variables, custom utilities
    |   |-- favicon.ico               # App icon
    |   |-- trip/
    |       |-- [sessionId]/
    |           |-- page.tsx          # Trip processing & preferences page
    |           |-- itinerary/
    |               |-- page.tsx      # Final itinerary display page
    |
    |-- lib/                          # Core Libraries
    |   |-- types.ts                  # ALL TypeScript interfaces (20+ interfaces)
    |   |-- store.ts                  # Zustand state store (50+ state fields & actions)
    |   |-- sse.ts                    # Server-Sent Events streaming client
    |   |-- api.ts                    # API base URL configuration
    |   |-- utils.ts                  # cn() helper (clsx + tailwind-merge)
    |
    |-- components/
    |   |-- processing/               # Video Processing UI
    |   |   |-- ProgressTracker.tsx    # 4-stage progress indicator with bar
    |   |   |-- VideoPreview.tsx       # Video metadata card (thumbnail, title, platform)
    |   |   |-- LocationCard.tsx       # Detected destination with confidence badge
    |   |
    |   |-- highlights/               # Place Discovery UI
    |   |   |-- HighlightsSheet.tsx    # Right-sliding sheet with place cards
    |   |   |-- HighlightCard.tsx      # Expandable place detail card with carousel
    |   |   |-- BucketListSelector.tsx # Multi-select checklist for places
    |   |
    |   |-- preferences/              # User Configuration UI
    |   |   |-- PreferenceForm.tsx     # 12+ field preference form with validation
    |   |   |-- CitySelector.tsx       # Modal for multi-city selection + suggestions
    |   |   |-- GenerationProgress.tsx # Real-time 8-agent progress display
    |   |
    |   |-- itinerary/                # Itinerary Display UI
    |   |   |-- ItineraryHeader.tsx    # Trip title, dates, share button
    |   |   |-- TabNavigation.tsx      # Sticky tab bar (Reservations, Days, Misc)
    |   |   |-- ReservationsTab.tsx    # Flights + Hotels container
    |   |   |-- FlightCard.tsx         # Flight route display with booking
    |   |   |-- HotelCard.tsx          # Hotel card with photos and pricing
    |   |   |-- DayTimeline.tsx        # Day header + vertical activity timeline
    |   |   |-- ActivityCard.tsx       # Type-coded activity with expandable details
    |   |   |-- BudgetBreakdown.tsx    # 6-category budget summary
    |   |   |-- MiscellaneousTab.tsx   # Visa, weather, packing, cultural, emergency
    |   |   |-- CustomizeChat.tsx      # Floating chat for natural language modifications
    |   |
    |   |-- shared/                   # Reusable Components
    |   |   |-- PhotoCarousel.tsx      # Image carousel with crossfade transitions
    |   |   |-- RatingBadge.tsx        # Star rating pill component
    |   |   |-- BookButton.tsx         # External link button
    |   |
    |   |-- ui/                       # shadcn/ui Base Components
    |       |-- badge.tsx
    |       |-- button.tsx
    |       |-- card.tsx
    |       |-- checkbox.tsx
    |       |-- dialog.tsx
    |       |-- input.tsx
    |       |-- label.tsx
    |       |-- scroll-area.tsx
    |       |-- select.tsx
    |       |-- separator.tsx
    |       |-- sheet.tsx
    |       |-- skeleton.tsx
    |       |-- slider.tsx
    |       |-- tabs.tsx
    |       |-- textarea.tsx
    |
    |-- public/                       # Static Assets
        |-- file.svg
        |-- globe.svg
        |-- next.svg
        |-- vercel.svg
        |-- window.svg
```

---

## 4. Prerequisites & Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **ffmpeg** installed and available on PATH
- **Supabase** account (free tier works)
- **API Keys**: OpenAI (required), Google Places (required), Tavily (recommended), ExchangeRate-API (optional)

### Setup

#### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Frontend

```bash
cd frontend
npm install
```

#### 3. Database

1. Create a Supabase project at supabase.com
2. Go to SQL Editor in Supabase Dashboard
3. Copy and execute the contents of `backend/database/schema.sql`

#### 4. Environment Variables

Create `backend/.env`:
```env
OPENAI_API_KEY=sk-...
GOOGLE_PLACES_API_KEY=AIza...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
TAVILY_API_KEY=tvly-...          # Recommended
EXCHANGERATE_API_KEY=...         # Optional
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running

**Backend** (terminal 1):
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 5. Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Type | Default | Description |
|----------|----------|------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | string | -- | OpenAI API key for GPT-4o, GPT-4o-mini, Whisper |
| `GOOGLE_PLACES_API_KEY` | **Yes** | string | -- | Google Places API (New) key |
| `SUPABASE_URL` | **Yes** | string | -- | Supabase project URL |
| `SUPABASE_ANON_KEY` | **Yes** | string | -- | Supabase anonymous/public key |
| `TAVILY_API_KEY` | No | string | `""` | Tavily web search for real-time flight/hotel pricing |
| `EXCHANGERATE_API_KEY` | No | string | `""` | ExchangeRate-API for currency conversion |
| `INSTAGRAM_COOKIES_PATH` | No | string | `""` | Path to Instagram cookies file for private videos |
| `DEFAULT_CURRENCY` | No | string | `INR` | Default currency for budget calculations |
| `DEFAULT_HOME_CITY` | No | string | `Mumbai` | Default departure city |
| `MAX_FRAME_COUNT` | No | int | `5` | Max video frames to extract for vision analysis |
| `VISION_MODEL` | No | string | `gpt-4o` | OpenAI model for vision tasks |
| `REASONING_MODEL` | No | string | `gpt-4o` | OpenAI model for complex reasoning |
| `FAST_MODEL` | No | string | `gpt-4o-mini` | OpenAI model for fast/cheap text tasks |
| `WHISPER_MODEL` | No | string | `whisper-1` | OpenAI model for audio transcription |
| `BACKEND_HOST` | No | string | `0.0.0.0` | Server bind host |
| `BACKEND_PORT` | No | int | `8000` | Server bind port |
| `FRONTEND_URL` | No | string | `http://localhost:3000` | Frontend URL for CORS |
| `ENABLE_CACHE` | No | bool | `true` | Enable Supabase caching of pipeline results |
| `ENABLE_VISION` | No | bool | `true` | Enable GPT-4o vision frame analysis |
| `ENABLE_TAVILY` | No | bool | `true` | Enable Tavily web search |
| `ENABLE_WEATHER` | No | bool | `true` | Enable weather API integration |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API base URL |

### Configuration Loading

Backend config is managed by `backend/config.py`:

```python
class Settings(BaseSettings):
    # All env vars defined with type hints and defaults
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()  # Singleton, loaded once
```

**Rule**: Never import `os.environ` directly. Always use `get_settings()`.

---

## 6. API Keys Reference

| Service | Key Variable | Where to Get | Free Tier |
|---------|-------------|-------------|-----------|
| OpenAI | `OPENAI_API_KEY` | platform.openai.com | Pay-as-you-go |
| Google Places | `GOOGLE_PLACES_API_KEY` | console.cloud.google.com | $200/month credit |
| Supabase | `SUPABASE_URL` + `SUPABASE_ANON_KEY` | supabase.com | 500MB DB free |
| Tavily | `TAVILY_API_KEY` | tavily.com | 1000 searches/month free |
| ExchangeRate-API | `EXCHANGERATE_API_KEY` | exchangerate-api.com | 1500 requests/month free |
| Open-Meteo | None required | open-meteo.com | Completely free, no key |

---

## 7. Database Schema

**Platform**: Supabase (PostgreSQL)
**Schema file**: `backend/database/schema.sql`

### Table 1: `video_intelligence` (Stages 1-2 Cache)

Caches video metadata, transcripts, and content analysis results so the same URL is never processed twice.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | No | `gen_random_uuid()` | Primary key |
| `url` | TEXT | No | -- | Video URL (UNIQUE) |
| `platform` | TEXT | No | `'unknown'` | `instagram` / `youtube` / `tiktok` |
| `title` | TEXT | Yes | -- | Video title |
| `description` | TEXT | Yes | -- | Video description/caption |
| `caption_text` | TEXT | Yes | -- | Extracted caption |
| `hashtags` | JSONB | Yes | `'[]'` | Array of hashtags |
| `uploader` | TEXT | Yes | -- | Creator username |
| `duration_seconds` | INTEGER | Yes | -- | Video length |
| `view_count` | BIGINT | Yes | -- | View count |
| `thumbnail_url` | TEXT | Yes | -- | Thumbnail image URL |
| `transcript` | TEXT | Yes | -- | Whisper transcription text |
| `transcript_language` | TEXT | Yes | -- | Detected language code |
| `has_speech` | BOOLEAN | Yes | `false` | Whether audio contains speech |
| `content_analysis` | JSONB | Yes | -- | Fused analysis result (destination, vibe, etc.) |
| `created_at` | TIMESTAMPTZ | Yes | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Yes | `now()` | Last update timestamp |

**Index**: `idx_vi_url` on `url`

### Table 2: `location_results` (Stages 3-4 Cache)

Caches validated locations, nearby places, and generated highlights.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | No | `gen_random_uuid()` | Primary key |
| `url` | TEXT | No | -- | Video URL (UNIQUE) |
| `primary_country` | TEXT | No | `''` | Detected country |
| `primary_region` | TEXT | Yes | `''` | Detected region/state |
| `primary_city` | TEXT | No | `''` | Detected city |
| `city_latitude` | DOUBLE PRECISION | Yes | -- | City center latitude |
| `city_longitude` | DOUBLE PRECISION | Yes | -- | City center longitude |
| `validated_places` | JSONB | Yes | `'[]'` | Google Places validated locations |
| `nearby_attractions` | JSONB | Yes | `'[]'` | Nearby tourist attractions |
| `nearby_restaurants` | JSONB | Yes | `'[]'` | Nearby restaurants |
| `nearby_hotels` | JSONB | Yes | `'[]'` | Nearby hotels |
| `highlights` | JSONB | Yes | `'[]'` | Generated rich highlights |
| `created_at` | TIMESTAMPTZ | Yes | `now()` | Creation timestamp |

**Index**: `idx_lr_url` on `url`

### Table 3: `itineraries` (Generated Plans)

Stores generated itineraries with versioning for customization.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | No | `gen_random_uuid()` | Primary key |
| `url` | TEXT | No | -- | Source video URL |
| `session_id` | TEXT | No | -- | Associated session ID |
| `user_preferences` | JSONB | No | `'{}'` | User's preference form data |
| `selected_cities` | JSONB | Yes | `'[]'` | Cities selected for itinerary |
| `itinerary` | JSONB | No | `'{}'` | Complete itinerary JSON |
| `version` | INTEGER | Yes | `1` | Version number (increments on customize) |
| `created_at` | TIMESTAMPTZ | Yes | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Yes | `now()` | Last update timestamp |

**Indexes**: `idx_it_url` on `url`, `idx_it_session` on `session_id`

### Table 4: `sessions` (State Tracking)

Tracks user sessions through the pipeline stages.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | TEXT | No | -- | Primary key (UUID string) |
| `url` | TEXT | Yes | -- | Video URL being processed |
| `stage` | TEXT | No | `'processing'` | Current pipeline stage |
| `preferences` | JSONB | Yes | -- | User preferences (once submitted) |
| `selected_cities` | JSONB | Yes | `'[]'` | Selected cities |
| `chat_history` | JSONB | Yes | `'[]'` | Customization chat messages |
| `itinerary_id` | UUID | Yes | -- | Reference to generated itinerary |
| `created_at` | TIMESTAMPTZ | Yes | `now()` | Session creation time |
| `updated_at` | TIMESTAMPTZ | Yes | `now()` | Last update time |

### Table 5: `place_cache` (Google Places Cache)

Caches Google Places API responses to reduce API costs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `place_id` | TEXT | No | -- | Google Places ID (Primary key) |
| `name` | TEXT | No | -- | Place name |
| `formatted_address` | TEXT | Yes | -- | Full address |
| `latitude` | DOUBLE PRECISION | Yes | -- | Latitude |
| `longitude` | DOUBLE PRECISION | Yes | -- | Longitude |
| `rating` | DOUBLE PRECISION | Yes | -- | Google rating (0-5) |
| `total_ratings` | INTEGER | Yes | -- | Total rating count |
| `price_level` | INTEGER | Yes | -- | Price level (0-4) |
| `types` | JSONB | Yes | `'[]'` | Place type tags |
| `photo_url` | TEXT | Yes | -- | Cached photo URL |
| `website` | TEXT | Yes | -- | Place website |
| `opening_hours` | JSONB | Yes | -- | Opening hours object |
| `cached_at` | TIMESTAMPTZ | Yes | `now()` | Cache timestamp |

### Relationships

```
sessions.itinerary_id --> itineraries.id
video_intelligence.url <--> location_results.url <--> itineraries.url
```

---

## 8. API Endpoints

**Base URL**: `http://localhost:8000`

### `GET /health`

Health check endpoint.

**Response**: `{"status": "ok", "service": "reeltrip-api"}`

---

### `POST /api/v1/process`

Process a video URL through the pipeline (Stages 1-4). Returns an SSE stream.

**Request Body**:
```json
{
  "url": "https://www.instagram.com/reel/..."
}
```

**SSE Events Emitted** (in order):

| Event | Data | Description |
|-------|------|-------------|
| `session` | `{session_id}` | Session created |
| `progress` | `{stage, percent, message}` | Processing progress (5-100%) |
| `metadata` | `{title, thumbnail_url, platform, duration}` | Video metadata extracted |
| `analysis` | `{destination_city, destination_country, location_confidence, dominant_vibe, detected_activities, ...}` | Content analysis complete |
| `highlights` | `{highlights[], primary_city, primary_country, city_latitude, city_longitude}` | Place highlights generated |
| `complete` | `{session_id, destination}` | Pipeline finished |
| `error` | `{message}` | Error occurred |

**Progress Stages**: `extracting` (5-15%) -> `analyzing` (20-42%) -> `locating` (48-68%) -> `highlights` (72-88%)

---

### `GET /api/v1/session/{session_id}`

Retrieve session data from Supabase.

**Response**: Full session object or `404`

---

### `GET /api/v1/highlights?url=...`

Get cached highlights for a previously processed video URL.

**Query Params**: `url` (required) -- the video URL

**Response**:
```json
{
  "highlights": [...],
  "primary_city": "Dubai",
  "primary_country": "UAE",
  "city_latitude": 25.2048,
  "city_longitude": 55.2708
}
```

---

### `POST /api/v1/itinerary/preferences`

Generate a full itinerary from user preferences. Returns an SSE stream.

**Request Body**:
```json
{
  "session_id": "uuid-string",
  "preferences": {
    "trip_duration_days": 5,
    "number_of_travelers": 2,
    "traveling_with": "partner",
    "month_of_travel": "March",
    "total_budget": 150000,
    "budget_currency": "INR",
    "travel_styles": ["cultural", "foodie"],
    "dietary_preferences": ["vegetarian"],
    "accommodation_tier": "mid-range",
    "must_include_places": ["Burj Khalifa"],
    "additional_notes": "",
    "home_city": "Mumbai",
    "home_country": "India"
  },
  "selected_cities": ["Dubai", "Abu Dhabi"]
}
```

**SSE Events Emitted**:

| Event | Data | Description |
|-------|------|-------------|
| `agent_progress` | `{agent, status, message}` | Agent status update |
| `itinerary` | Full TripItinerary JSON | Generated itinerary |
| `complete` | `{itinerary_id, session_id}` | Generation finished |
| `error` | `{message}` | Error occurred |

**Agent names**: `flight`, `hotel`, `weather`, `safety`, `activity`, `transport`, `budget`, `assembler`
**Agent statuses**: `working`, `complete`, `failed`

---

### `POST /api/v1/itinerary/customize`

Customize an existing itinerary via natural language. Returns an SSE stream.

**Request Body**:
```json
{
  "session_id": "...",
  "itinerary_id": "...",
  "request": "Replace the dinner on day 2 with a seafood restaurant"
}
```

**SSE Events**:
| Event | Data |
|-------|------|
| `customizing` | `{message}` |
| `itinerary` | Updated full TripItinerary JSON |
| `complete` | `{itinerary_id, version}` |
| `error` | `{message}` |

---

### `GET /api/v1/itinerary/{itinerary_id}`

Retrieve a saved itinerary by ID.

**Response**:
```json
{
  "id": "uuid",
  "session_id": "...",
  "version": 1,
  "itinerary": { ... },
  "created_at": "...",
  "updated_at": "..."
}
```

---

### `POST /api/v1/cities/suggest`

Suggest additional cities to visit based on the destination.

**Request Body**:
```json
{
  "destination_country": "UAE",
  "destination_city": "Dubai",
  "trip_duration_days": 5,
  "vibe": "luxury and adventure"
}
```

**Response**:
```json
{
  "suggested_cities": [
    {
      "city": "Abu Dhabi",
      "country": "UAE",
      "why": "Home to the Grand Mosque and Ferrari World",
      "recommended_days": 2,
      "distance_from_primary": "1.5 hours by car"
    }
  ]
}
```

---

## 9. 7-Stage Pipeline

### Overview

```
Video URL
  |
  v
[Stage 1: Video Extraction]     -> yt-dlp metadata + ffmpeg audio/frames
  |
  v
[Stage 2: Content Analysis]     -> Whisper transcription + GPT-4o vision + GPT-4o-mini fusion
  |
  v
[Stage 3: Location Validation]  -> GPT-4o-mini detection + Google Places validation
  |
  v
[Stage 4: Highlights]           -> GPT-4o-mini rich highlight generation + photos
  |
  v
[User Preference Collection]    -> Interactive form + city selection
  |
  v
[Stage 5-6: Multi-Agent Planning] -> 8 agents (flight, hotel, weather, safety, activity, transport, budget, assembler)
  |
  v
[Stage 7: Itinerary Assembly]   -> GPT-4o final assembly -> complete TripItinerary
```

### Stage 1: Video Intelligence Extraction

**File**: `backend/pipeline/video_extractor.py`

1. Validates URL format (Instagram Reel, YouTube Short, TikTok)
2. Uses `yt-dlp` to extract metadata (title, description, hashtags, uploader, thumbnail, duration, view count)
3. Downloads the video file temporarily for audio/frame processing
4. Returns a metadata dict + path to downloaded video file

**File**: `backend/pipeline/audio_processor.py`

1. Extracts audio track using `ffmpeg` (video -> WAV)
2. Sends audio to OpenAI Whisper for transcription
3. Returns `{text, language, has_speech}`

**File**: `backend/pipeline/frame_extractor.py`

1. Uses `ffmpeg` to extract 4-6 keyframes at even intervals
2. Converts frames to base64-encoded JPEG
3. Limits to `MAX_FRAME_COUNT` (default 5) to control costs

### Stage 2: Multi-Signal Content Analysis

**File**: `backend/pipeline/vision_analyzer.py`

1. Sends base64 frames to GPT-4o with `detail: "low"` (85 tokens/image)
2. Prompt asks for: locations visible, landmarks, architecture style, signage, landscape type, cuisine visible
3. Returns structured JSON with visual observations

**File**: `backend/pipeline/content_fuser.py`

1. Takes ALL signals: title, description, hashtags, transcript, vision analysis
2. Uses GPT-4o-mini to fuse into a unified analysis
3. Output: `{destination_country, destination_region, destination_city, location_confidence, candidate_locations[], dominant_vibe, content_summary, detected_activities[], target_audience}`

### Stage 3: Location Detection & Validation

**File**: `backend/pipeline/location_detector.py`

1. GPT-4o-mini ranks and deduplicates candidate locations
2. Produces a prioritized list of places to validate

**File**: `backend/pipeline/location_validator.py`

1. Takes candidate locations from the detector
2. Validates each against Google Places API (Text Search)
3. Gets place details (address, coordinates, rating, photos, types)
4. Discovers nearby attractions, restaurants, and hotels using Nearby Search
5. Returns enriched location data with real Google Places IDs

### Stage 4: Highlights Generation

**File**: `backend/pipeline/highlights_generator.py`

1. Takes all validated places + nearby discoveries
2. Uses GPT-4o-mini to generate rich, magazine-quality descriptions
3. For each place: description, vibe_tags, signature_experiences, best_time_to_visit, know_more, estimated_visit_duration, estimated_cost_usd
4. Merges Google Places photo URLs into highlights
5. Returns array of `PlaceHighlight` objects

### Pipeline Orchestrator

**File**: `backend/pipeline/orchestrator.py`

The master coordinator that:
- Validates the URL
- Creates a session in Supabase
- Checks cache at EVERY stage (Stages 1-2 cached together, Stages 3-4 cached together)
- Runs audio extraction and frame extraction **in parallel** via `asyncio.gather`
- Yields SSE progress events at every step
- Handles errors gracefully (yields error events, never raises)
- Cleans up temp video files in `finally` block

---

## 10. Multi-Agent System

### Architecture

**File**: `backend/agents/orchestrator.py`

The agents execute in a carefully ordered batch system:

```
Batch 1 (parallel):  flight + hotel + weather + safety
                          |
Batch 2 (parallel):  activity + transport  (needs weather/flight data from Batch 1)
                          |
Sequential:           budget  (needs all cost data)
                          |
Sequential:           assembler  (needs everything)
```

Each batch uses `asyncio.gather(return_exceptions=True)` -- if one agent fails, the others continue.

### Shared State

**File**: `backend/agents/state.py`

```python
class TravelPlannerState(TypedDict):
    # Inputs
    location_result: dict       # From pipeline stages 3-4
    user_preferences: dict      # From preference form
    highlights: list[dict]      # From pipeline stage 4
    selected_cities: list[str]  # User-selected cities

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

### Agent Details

| Agent | File | Model | Purpose | Data Source |
|-------|------|-------|---------|-------------|
| **Flight** | `flight_agent.py` | fast (gpt-4o-mini) | Find flights from home city to destination(s) | Tavily web search |
| **Hotel** | `hotel_agent.py` | fast | Find hotels matching accommodation tier | Tavily web search |
| **Weather** | `weather_agent.py` | fast | Get weather forecast for travel dates | Open-Meteo API |
| **Safety** | `safety_agent.py` | fast | Safety assessment, visa requirements | Tavily web search |
| **Activity** | `activity_agent.py` | fast | Plan activities using highlights data | Highlights + GPT |
| **Transport** | `transport_agent.py` | fast | Plan inter-city transportation | Tavily web search |
| **Budget** | `budget_agent.py` | fast | Analyze costs, optimize if over budget | All agent data |
| **Assembler** | `itinerary_assembler.py` | reasoning (gpt-4o) | Build final day-by-day itinerary | All agent data |

### Streaming Variant

`run_travel_planner_streaming()` is the SSE-compatible version that yields `agent_progress` events as each agent starts, completes, or fails. This is what the `/api/v1/itinerary/preferences` endpoint uses.

---

## 11. Backend Architecture

### Entry Point (`main.py`)

- FastAPI app with CORS middleware
- 8 API endpoints (see Section 8)
- All streaming endpoints use `StreamingResponse` with `text/event-stream` media type
- Headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`

### Configuration (`config.py`)

- `Settings(BaseSettings)` -- Pydantic v2 settings class
- Loads from `.env` file automatically
- `@lru_cache()` singleton pattern via `get_settings()`
- Groups: Required, Recommended, Optional, Model config, Server config, Feature flags

### Dependencies (`dependencies.py`)

- FastAPI injectable dependencies for shared services

### Services Layer

**`openai_client.py`** -- Central OpenAI wrapper

Key functions:
- `get_model(task)` -- Routes "vision"->gpt-4o, "reasoning"->gpt-4o, "fast"->gpt-4o-mini
- `call_openai_json(task, system_prompt, user_prompt, ...)` -- JSON mode with automatic repair
- `call_openai_vision(system_prompt, text_prompt, images_base64, ...)` -- Vision with `detail: "low"`
- `call_openai_text(task, system_prompt, user_prompt, ...)` -- Free-form text response
- `transcribe_audio(audio_file_path)` -- Whisper transcription
- `_try_repair_json(raw)` -- Attempts to fix truncated JSON by closing open brackets/braces

Features:
- Exponential backoff retry (2^attempt seconds)
- JSON repair for truncated responses (finish_reason=length)
- Configurable retries per call
- Detailed logging of failures

**`google_places_client.py`** -- Google Places API (New)

Functions:
- Text Search: Find places by name/query
- Place Details: Get full place information
- Nearby Search: Discover places within radius
- Photo URL: Get photo URLs from photo references

**`tavily_client.py`** -- Tavily web search

- Wraps Tavily Python SDK
- Used by flight, hotel, safety, and transport agents for real-time data

**`weather_client.py`** -- Open-Meteo API

- Free weather API (no key required)
- Fetches forecast data for specified dates and coordinates

**`exchange_rate_client.py`** -- Currency conversion

- Converts between currencies using ExchangeRate-API
- Used by budget agent

**`supabase_client.py`** -- Database operations

CRUD functions for all 5 tables:
- `get_cached_video(url)` / `store_video(url, data)`
- `get_cached_location(url)` / `store_location(url, data)`
- `create_session(session_id, url)` / `get_session(session_id)` / `update_session(session_id, data)`
- `store_itinerary(data)` / `get_itinerary(itinerary_id)` / `update_itinerary(itinerary_id, data)`

All operations have try/except -- cache failures never crash the pipeline.

### Models Layer

**`video.py`** -- `VideoMetadata`, `TranscriptResult`
**`location.py`** -- `CandidateLocation`, `ValidatedPlace`
**`preferences.py`** -- `UserPreferences`
**`agents.py`** -- Agent-specific output models (`FlightData`, `HotelData`, etc.)
**`itinerary.py`** -- Complete itinerary hierarchy:
- `TripItinerary` (root)
  - `FlightReservation[]`
  - `HotelReservation[]`
  - `ItineraryDay[]` -> `Activity[]`
  - `BudgetBreakdown`
  - `VisaInfo`
  - `WeatherSummary`
  - `CurrencyInfo`
  - `EmergencyInfo`

**`api.py`** -- `HealthResponse` and other API-level models

### Utils Layer

**`url_validator.py`** -- Regex patterns for Instagram Reels, YouTube Shorts, TikTok URLs. Returns `(is_valid, platform)`.

**`currency.py`** -- Currency conversion utilities using exchange rate data.

**`geo.py`** -- Geolocation distance calculations (haversine formula).

---

## 12. Frontend Architecture

### Pages (Next.js App Router)

#### Landing Page (`app/page.tsx`)

- URL input form with real-time validation
- Supports: Instagram Reels, YouTube Shorts, TikTok
- On submit: generates `crypto.randomUUID()` session ID, resets Zustand store, navigates to `/trip/[sessionId]`
- Animated gradient background (Framer Motion)

#### Trip Processing Page (`app/trip/[sessionId]/page.tsx`)

The **central orchestrator** that manages 5 major phases via `flowStep` state:

1. **`"processing"`** -- Displays `ProgressTracker`, `VideoPreview`, `LocationCard`, triggers SSE stream to `/api/v1/process`
2. **`"highlights"`** -- Shows `HighlightsSheet` (right-sliding panel with place cards)
3. **`"bucketList"`** -- Renders `BucketListSelector` (multi-select checklist, auto-selects top 5 by rating)
4. **`"preferences"`** -- Shows `PreferenceForm` (12+ field form with validation)
5. **`"generating"`** -- Displays `GenerationProgress` (8 agent status cards), triggers SSE stream to `/api/v1/itinerary/preferences`

Manages two independent SSE streams with AbortController for cleanup.

#### Itinerary Page (`app/trip/[sessionId]/itinerary/page.tsx`)

- Lazy-fetches itinerary from API if not already in Zustand store
- Tab navigation: `reservations`, `day-1` through `day-N`, `misc`
- Renders appropriate tab content based on `activeTab`
- Floating `CustomizeChat` button (bottom-right)
- Loading skeleton while fetching

### Component Details

#### Processing Components

**`ProgressTracker`**
- 4 stages: extracting -> analyzing -> locating -> highlights
- Each stage shows icon + label + status (complete/active/pending)
- Progress bar with percentage
- Active stage has purple pulse animation

**`VideoPreview`**
- Displays video thumbnail with platform badge (Instagram/YouTube/TikTok)
- Title text + duration
- Skeleton loading state

**`LocationCard`**
- Detected city + country
- Confidence badge (high=green, medium=yellow, low=red)
- Dominant vibe quote
- "See Highlights" CTA button

#### Highlights Components

**`HighlightsSheet`**
- Right-sliding `Sheet` (shadcn) with scrollable list
- Deduplicates places by `place_id`
- Each place rendered as `HighlightCard`
- Sticky "Create Itinerary" CTA at bottom
- Shows count of unique places

**`HighlightCard`**
- `PhotoCarousel` at top
- Place name + `RatingBadge`
- Description text
- Vibe tag badges
- Expandable sections: signature experiences, visit duration, cost, "know more"
- Bookmark toggle + Google Maps link button

**`BucketListSelector`**
- Checkbox list of all discovered places
- Auto-selects top 5 by rating on first render (via `useRef` guard)
- Shows selection count
- "Continue" button proceeds to preferences

#### Preference Components

**`PreferenceForm`**
- Fields:
  - Trip duration (slider: 1-14 days)
  - Number of travelers (slider: 1-10)
  - Traveling with (button group: solo/partner/family/friends)
  - Month of travel (dropdown select)
  - Budget + currency (number input + currency select)
  - Travel styles (badge toggles: 10 options including cultural, adventure, foodie, luxury, nightlife, nature, wellness, photography, shopping, offbeat)
  - Dietary preferences (badge toggles: 6 options)
  - Accommodation tier (button group: budget/mid-range/luxury/ultra-luxury)
  - Home city + country (text inputs)
  - Additional notes (textarea)
- Required field validation with error messages
- Maps bucket list place_ids back to place names for `must_include_places`

**`CitySelector`**
- Modal `Dialog` (shadcn)
- Primary city always included (non-removable)
- Fetches suggestions from `/api/v1/cities/suggest` on open
- Each suggestion shows: city, country, why recommended, recommended days, distance
- Add/remove toggle buttons
- Skeleton loading while fetching

**`GenerationProgress`**
- Displays 8 agent cards with real-time status
- Status icons: working (purple pulse), complete (green check), failed (red X)
- Progress bar calculated from completion count
- "View Itinerary" button appears when all agents done + itineraryId set
- Routes to `/trip/[sessionId]/itinerary`

#### Itinerary Components

**`ItineraryHeader`**
- Trip title with gradient text
- Destination cities (dot-separated)
- Calendar icon + trip dates
- Traveler count + total days
- Share button (Web Share API with clipboard fallback)

**`TabNavigation`**
- Sticky top nav with glass effect
- Tabs: Reservations, Day 1-N (dynamic), Miscellaneous
- Active tab has gradient background + shadow
- Horizontally scrollable with hidden scrollbar

**`ReservationsTab`**
- Renders `FlightCard[]` and `HotelCard[]`
- Pricing disclaimer
- Conditional rendering if lists empty

**`FlightCard`**
- Airport codes (large) with city names below
- Departure/arrival times
- Flight duration + plane icon with dashed connector
- Price per person
- "Book Now" button with external link

**`HotelCard`**
- `PhotoCarousel` for hotel photos
- Hotel name + `RatingBadge`
- Check-in/check-out dates
- Price per night + total price
- Expandable "Why this hotel?" section
- Book + Map buttons

**`DayTimeline`**
- Day number + city badge + theme
- Date display
- Vertical timeline with dashed line + dot indicators
- Renders `ActivityCard` for each activity

**`ActivityCard`**
- Type-based color coding:
  - flight=blue, checkin=green, checkout=orange, meal=amber
  - attraction=purple, activity=pink, transport=cyan, free_time=emerald
- Time (HH:MM) on left
- Type icon + badge + title
- Optional photo thumbnail
- Duration + estimated cost
- `RatingBadge` if available
- Expandable: description + practical tip (boxed)
- Book + Map action buttons

**`BudgetBreakdown`**
- 6 categories with icons (flights, accommodation, food, activities, transport, misc)
- Separator line
- Grand total with gradient text
- Budget status badge (within/over/under)
- Savings tips if over budget

**`MiscellaneousTab`**
- Collapsible accordion sections:
  - Budget Breakdown (via `BudgetBreakdown` component)
  - Visa Requirements
  - Weather Summary (open by default)
  - Packing Suggestions
  - Cultural Tips
  - Currency Info
  - Emergency Info

**`CustomizeChat`**
- Floating action button (bottom-right, sparkle icon)
- Opens a right-side `Sheet`
- Chat message history with auto-scroll
- Quick suggestion chips ("Add more restaurants", "Make it more budget-friendly", etc.)
- Text input with Enter to send
- Sends to `/api/v1/itinerary/customize` via SSE
- Updates itinerary in Zustand store on response
- Typing indicator during processing

#### Shared Components

**`PhotoCarousel`**
- Image carousel with prev/next chevrons
- Dot indicators for navigation
- `AnimatePresence` crossfade transitions
- Gradient fallback on image error
- Skeleton loading state

**`RatingBadge`**
- Star icon + rating number (1 decimal)
- Returns null if rating is null

**`BookButton`**
- External link button
- Opens in new tab with `noopener,noreferrer`
- Customizable label (default: "View on Map")

---

## 13. State Management (Zustand)

**File**: `frontend/lib/store.ts`

Single global store using `zustand/create`. No persistence (in-memory only, resets on page refresh).

### State Fields

```typescript
interface ReelTripState {
  // Session
  url: string;                          // Input video URL
  sessionId: string | null;             // Backend session UUID

  // Processing
  isProcessing: boolean;                // Pipeline running flag
  stage: ProcessingStage;               // idle|extracting|analyzing|locating|highlights|complete|error
  progress: number;                     // 0-100 percent
  stageMessage: string;                 // Current stage description
  error: string | null;                 // Error message

  // Video metadata (from SSE metadata event)
  videoTitle: string;
  thumbnailUrl: string;
  platform: string;                     // instagram|youtube|tiktok
  duration: number;                     // seconds

  // Analysis (from SSE analysis event)
  destinationCity: string;
  destinationCountry: string;
  locationConfidence: string;           // high|medium|low
  dominantVibe: string;
  contentSummary: string;
  detectedActivities: string[];
  candidateLocations: CandidateLocation[];
  targetAudience: string;

  // Highlights (from SSE highlights event)
  highlights: PlaceHighlight[];
  primaryCity: string;
  primaryCountry: string;
  cityLatitude: number | null;
  cityLongitude: number | null;

  // UI
  showHighlightsSheet: boolean;

  // Flow control
  flowStep: FlowStep;                  // processing|highlights|bucketList|preferences|generating|itinerary

  // Bucket list
  bucketListSelections: string[];       // Selected place_ids

  // Preferences
  preferences: UserPreferences | null;

  // City selection
  suggestedCities: CitySuggestion[];
  selectedCities: string[];
  isFetchingCities: boolean;
  showCitySelector: boolean;

  // Generation
  agentStatuses: AgentProgress[];       // 8 agent progress entries
  isGenerating: boolean;

  // Itinerary
  itinerary: TripItinerary | null;
  itineraryId: string | null;

  // Chat
  chatMessages: ChatMessage[];
  isCustomizing: boolean;

  // Itinerary UI
  activeTab: string;                    // "reservations"|"day-1"|"day-2"|...|"misc"
}
```

### Actions (30+)

| Action | Parameters | Description |
|--------|-----------|-------------|
| `setUrl` | `url` | Set video URL |
| `startProcessing` | `sessionId` | Begin processing, set stage to "extracting" |
| `updateProgress` | `stage, percent, message` | Update progress bar |
| `setMetadata` | `MetadataEvent` | Set video metadata |
| `setAnalysis` | `AnalysisEvent` | Set analysis results |
| `setHighlights` | `HighlightsEvent` | Set highlights, auto-open sheet |
| `setComplete` | -- | Mark processing complete |
| `setError` | `message` | Set error state |
| `reset` | -- | Reset entire store to initial state |
| `toggleHighlightsSheet` | -- | Toggle highlights panel |
| `setShowHighlightsSheet` | `show` | Explicitly set highlights sheet visibility |
| `setFlowStep` | `step` | Navigate between flow phases |
| `setBucketListSelections` | `selections[]` | Set selected places |
| `toggleBucketListItem` | `placeName` | Toggle a place selection |
| `setPreferences` | `prefs` | Save user preferences |
| `setSuggestedCities` | `cities[]` | Set city suggestions |
| `setSelectedCities` | `cities[]` | Set selected cities |
| `toggleCity` | `city` | Toggle a city selection |
| `setIsFetchingCities` | `boolean` | Set city fetch loading state |
| `setShowCitySelector` | `show` | Toggle city selector dialog |
| `updateAgentStatus` | `AgentProgress` | Upsert agent status by agent name |
| `setIsGenerating` | `boolean` | Set generation in-flight flag |
| `setItinerary` | `TripItinerary` | Store final itinerary |
| `setItineraryId` | `id` | Store itinerary backend ID |
| `addChatMessage` | `ChatMessage` | Append chat message |
| `setIsCustomizing` | `boolean` | Set customization loading state |
| `setActiveTab` | `tab` | Switch itinerary tab |

---

## 14. Type System (TypeScript)

**File**: `frontend/lib/types.ts`

### Processing Types

```typescript
type ProcessingStage = "idle" | "extracting" | "analyzing" | "locating" | "highlights" | "complete" | "error";
type FlowStep = "processing" | "highlights" | "bucketList" | "preferences" | "citySelector" | "generating" | "itinerary";
```

### SSE Event Interfaces

```typescript
interface SessionEvent { session_id: string }
interface ProgressEvent { stage: string; percent: number; message: string }
interface MetadataEvent { title: string; thumbnail_url: string; platform: string; duration: number }
interface AnalysisEvent {
  destination_country: string; destination_region: string; destination_city: string;
  location_confidence: string; candidate_locations: CandidateLocation[];
  dominant_vibe: string; content_summary: string; detected_activities: string[];
  target_audience: string;
}
interface HighlightsEvent { highlights: PlaceHighlight[]; primary_city: string; primary_country: string; city_latitude: number; city_longitude: number }
interface CompleteEvent { session_id: string; destination: string }
interface ErrorEvent { message: string }
```

### Place & Location Types

```typescript
interface PlaceHighlight {
  place_name: string; place_id: string; photo_url: string | null;
  latitude: number; longitude: number; formatted_address: string;
  rating: number | null; description: string; vibe_tags: string[];
  signature_experiences: string[]; best_time_to_visit: string;
  know_more: string; estimated_visit_duration: string;
  estimated_cost_usd: number; google_maps_url: string; source: string;
}

interface CandidateLocation {
  name: string; type: string; mentioned_in: string[]; confidence: string;
}
```

### User Preferences

```typescript
interface UserPreferences {
  trip_duration_days: number;
  number_of_travelers: number;
  traveling_with: "solo" | "partner" | "family" | "friends";
  month_of_travel: string;
  total_budget: number;
  budget_currency: string;
  travel_styles: string[];
  dietary_preferences: string[];
  accommodation_tier: "budget" | "mid-range" | "luxury" | "ultra-luxury";
  must_include_places: string[];
  additional_notes: string;
  home_city: string;
  home_country: string;
}
```

### Itinerary Types

```typescript
interface TripItinerary {
  trip_title: string; destination_country: string; destination_cities: string[];
  start_date: string; end_date: string; total_days: number; total_travelers: number;
  flights: FlightReservation[]; hotels: HotelReservation[];
  days: ItineraryDay[]; budget_breakdown: BudgetBreakdown;
  visa_requirements: VisaInfo | null; weather_summary: WeatherSummary;
  packing_suggestions: string[]; cultural_tips: string[];
  emergency_info: EmergencyInfo; currency_info: CurrencyInfo;
}

interface FlightReservation {
  type: string; from_city: string; from_airport_code: string;
  to_city: string; to_airport_code: string;
  departure_datetime: string; arrival_datetime: string;
  duration: string; estimated_price: number; price_currency: string;
  booking_url: string; notes: string | null; day_number: number;
}

interface HotelReservation {
  hotel_name: string; city: string; address: string;
  check_in_date: string; check_out_date: string; nights: number;
  price_per_night: number; total_price: number; price_currency: string;
  rating: number; photo_url: string | null; why_recommended: string;
  booking_url: string; latitude: number; longitude: number;
}

interface Activity {
  time: string; title: string;
  type: "flight" | "checkin" | "checkout" | "meal" | "attraction" | "activity" | "transport" | "free_time";
  venue_name: string | null; venue_address: string | null;
  latitude: number | null; longitude: number | null;
  photo_url: string | null; rating: number | null;
  duration_minutes: number; estimated_cost: number; cost_currency: string;
  description: string; practical_tip: string | null;
  booking_url: string | null; google_maps_url: string | null;
}

interface ItineraryDay {
  day_number: number; date: string; city: string;
  theme: string; activities: Activity[];
}

interface BudgetBreakdown {
  flights_total: number; accommodation_total: number;
  food_total: number; activities_total: number;
  transportation_total: number; miscellaneous_buffer: number;
  grand_total: number; currency: string;
  budget_status: "within_budget" | "over_budget" | "under_budget";
  savings_tips: string[] | null;
}

interface VisaInfo {
  required: boolean; visa_type: string; processing_time: string;
  estimated_cost: string; documents_needed: string[]; notes: string;
}

interface WeatherSummary {
  overview: string; avg_high_celsius: number; avg_low_celsius: number;
  precipitation_chance: string; pack_suggestions: string[];
}

interface CurrencyInfo {
  local_currency: string; local_currency_name: string;
  exchange_rate: string; tips: string[];
}

interface EmergencyInfo {
  police: string; ambulance: string; fire: string;
  tourist_police: string; embassy_phone: string; emergency_notes: string[];
}
```

### UI Types

```typescript
interface AgentProgress {
  agent: string;
  status: "working" | "complete" | "failed";
  message: string;
}

interface CitySuggestion {
  city: string; country: string; why: string;
  recommended_days: number; distance_from_primary: string;
}

interface ChatMessage {
  id: string; role: "user" | "assistant";
  content: string; timestamp: number;
}
```

---

## 15. SSE Streaming

### How It Works

ReelTrip uses **Server-Sent Events (SSE)** for real-time communication between backend and frontend. Unlike WebSockets, SSE is:
- Unidirectional (server -> client)
- Built on standard HTTP
- Auto-reconnects
- Simpler to implement

### Backend (FastAPI)

All streaming endpoints return `StreamingResponse` with `media_type="text/event-stream"`:

```python
async def event_stream():
    async for event in run_pipeline(url):
        event_name = event.get("event", "message")
        event_data = json.dumps(event.get("data", {}))
        yield f"event: {event_name}\ndata: {event_data}\n\n"

return StreamingResponse(event_stream(), media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
```

### Frontend SSE Client (`lib/sse.ts`)

```typescript
export async function streamPost(
  url: string,
  body: object,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
  signal?: AbortSignal
): Promise<void>
```

Key features:
- Uses `fetch` with `ReadableStream` reader (not `EventSource` -- allows POST method)
- Persists event names across chunk boundaries (handles split SSE messages)
- Parses each SSE message: `event: name\ndata: json\n\n`
- Distinguishes `AbortError` from real failures
- Console logging for debugging

### Three SSE Streams

1. **Processing Stream** (`POST /api/v1/process`)
   - Events: `session`, `progress`, `metadata`, `analysis`, `highlights`, `complete`, `error`

2. **Generation Stream** (`POST /api/v1/itinerary/preferences`)
   - Events: `agent_progress` (x8), `itinerary`, `complete`, `error`

3. **Customization Stream** (`POST /api/v1/itinerary/customize`)
   - Events: `customizing`, `itinerary`, `complete`, `error`

### Cleanup

Frontend uses `AbortController` to cancel active streams when components unmount:

```typescript
const abortRef = useRef<AbortController | null>(null);

useEffect(() => {
  return () => { abortRef.current?.abort(); };
}, []);
```

---

## 16. User Flow

```
1. LANDING PAGE (/)
   |-- User pastes video URL (Instagram Reel / YouTube Short / TikTok)
   |-- URL validation (client-side regex)
   |-- Generate sessionId (crypto.randomUUID())
   |-- Reset Zustand store
   |-- Navigate to /trip/[sessionId]
   |
2. VIDEO PROCESSING (/trip/[sessionId], flowStep="processing")
   |-- SSE stream to POST /api/v1/process
   |-- Display: ProgressTracker (4 stages)
   |-- Display: VideoPreview (thumbnail, title, platform, duration)
   |-- Display: LocationCard (detected city, confidence, vibe)
   |-- When highlights arrive -> auto-open HighlightsSheet
   |
3. HIGHLIGHTS BROWSING (flowStep="highlights")
   |-- Right-sliding sheet with scrollable place cards
   |-- Each card: photo carousel, rating, description, vibe tags
   |-- Expandable sections: experiences, duration, cost, know_more
   |-- Click "Create Itinerary" -> proceed
   |
4. BUCKET LIST SELECTION (flowStep="bucketList")
   |-- Checkbox list of all discovered places
   |-- Top 5 auto-selected by Google rating
   |-- User refines selection
   |-- Click "Continue" -> proceed
   |
5. PREFERENCE FORM (flowStep="preferences")
   |-- 12+ fields: duration, travelers, budget, styles, dietary, etc.
   |-- Required field validation
   |-- Click "Save" -> open CitySelector dialog
   |
6. CITY SELECTOR (dialog overlay)
   |-- Primary city always included
   |-- Fetch city suggestions from POST /api/v1/cities/suggest
   |-- Each suggestion: city, why, recommended days, distance
   |-- Add/remove cities
   |-- Click "Proceed" -> start generation
   |
7. ITINERARY GENERATION (flowStep="generating")
   |-- SSE stream to POST /api/v1/itinerary/preferences
   |-- Display: 8 agent cards with live status
   |   - flight (Searching for flights...)
   |   - hotel (Finding hotels...)
   |   - weather (Checking weather...)
   |   - safety (Reviewing safety...)
   |   - activity (Planning activities...)
   |   - transport (Researching transportation...)
   |   - budget (Optimizing budget...)
   |   - assembler (Assembling your itinerary...)
   |-- Progress bar based on completion count
   |-- "View Itinerary" button appears on completion
   |
8. ITINERARY VIEW (/trip/[sessionId]/itinerary)
   |-- ItineraryHeader: title, cities, dates, share
   |-- TabNavigation: Reservations | Day 1 | Day 2 | ... | Miscellaneous
   |
   |-- Reservations Tab:
   |   |-- FlightCard(s): route, times, price, book button
   |   |-- HotelCard(s): photos, rating, price, why recommended
   |
   |-- Day Tabs:
   |   |-- DayTimeline: vertical timeline with ActivityCards
   |   |-- Each activity: time, type icon, title, venue, cost, expandable details
   |
   |-- Miscellaneous Tab:
   |   |-- Budget Breakdown (6 categories + total + status)
   |   |-- Visa Requirements
   |   |-- Weather Summary
   |   |-- Packing Suggestions
   |   |-- Cultural Tips
   |   |-- Currency Info
   |   |-- Emergency Info
   |
9. CUSTOMIZATION (floating chat button)
   |-- Natural language requests: "Add more restaurants", "Replace day 3 activity"
   |-- SSE stream to POST /api/v1/itinerary/customize
   |-- Itinerary updates in real-time
   |-- Version increments in database
```

---

## 17. Styling & Design System

### Theme

- **Dark mode only** (HTML has `class="dark"`)
- **Design language**: Glassmorphism with purple accent

### Color Palette (CSS Variables in `globals.css`)

```css
/* Primary */
--primary-purple: #8b5cf6;
--primary-purple-light: #a78bfa;
--primary-purple-lighter: #c4b5fd;

/* Background */
--bg-dark: #0a0a14;
--bg-card: #12121f;
--bg-surface: #1a1a2e;

/* Text */
--text-primary: #f5f5f5;
--text-secondary: #a0a0b0;
--text-accent: #c4b5fd;

/* Status */
--success: #34d399;
--warning: #fbbf24;
--error: #f87171;
```

### Custom CSS Utilities

```css
.glass-card         /* Glassmorphism: bg-white/5, backdrop-blur-md, border white/10 */
.glass-card-hover   /* Interactive glass card with hover effects */
.gradient-text      /* Purple-to-pink gradient text via background-clip */
.accent-gradient    /* Purple linear-gradient background */
.animated-gradient-bg /* Animated radial gradient with @keyframes */
.input-glow         /* Purple box-shadow glow on input focus */
.pulse-glow         /* Pulsing box-shadow animation for active states */
.spin-slow          /* Slower rotation animation (3s) */
.scrollbar-hide     /* Hides scrollbars while preserving scroll functionality */
```

### Fonts

- **Inter** from Google Fonts (loaded in `layout.tsx`)
- Monospace fallback: system fonts

### shadcn/ui Configuration

```json
{
  "style": "base-nova",
  "rsc": true,
  "tailwind": {
    "baseColor": "neutral",
    "cssVariables": true
  },
  "iconLibrary": "lucide"
}
```

### Animations

- **Framer Motion**: Page transitions, card reveals, list staggering, expand/collapse
- **CSS**: Pulse glow, gradient animation, spin, skeleton shimmer
- **Transitions**: Crossfade for photo carousel, slide for sheets/dialogs

---

## 18. Component Hierarchy

```
app/layout.tsx
|
|-- app/page.tsx (Landing)
|   |-- URL input form
|   |-- Framer Motion animated background
|
|-- app/trip/[sessionId]/page.tsx (Trip Processing)
|   |-- [flowStep="processing"]
|   |   |-- ProgressTracker
|   |   |-- VideoPreview
|   |   |-- LocationCard
|   |   |-- HighlightsSheet
|   |       |-- HighlightCard (multiple)
|   |           |-- PhotoCarousel
|   |           |-- RatingBadge
|   |           |-- BookButton
|   |
|   |-- [flowStep="bucketList"]
|   |   |-- BucketListSelector
|   |       |-- RatingBadge (per item)
|   |
|   |-- [flowStep="preferences"]
|   |   |-- PreferenceForm
|   |
|   |-- [showCitySelector=true]
|   |   |-- CitySelector (Dialog)
|   |
|   |-- [flowStep="generating"]
|       |-- GenerationProgress
|
|-- app/trip/[sessionId]/itinerary/page.tsx (Itinerary)
    |-- ItineraryHeader
    |-- TabNavigation
    |-- [activeTab="reservations"]
    |   |-- ReservationsTab
    |       |-- FlightCard (multiple)
    |       |   |-- BookButton
    |       |-- HotelCard (multiple)
    |           |-- PhotoCarousel
    |           |-- RatingBadge
    |           |-- BookButton
    |
    |-- [activeTab="day-N"]
    |   |-- DayTimeline
    |       |-- ActivityCard (multiple)
    |           |-- RatingBadge
    |           |-- BookButton
    |
    |-- [activeTab="misc"]
    |   |-- MiscellaneousTab
    |       |-- BudgetBreakdown
    |
    |-- CustomizeChat (floating)
```

---

## 19. External Service Integrations

### OpenAI API

**File**: `backend/services/openai_client.py`

| Function | Model | Purpose | Cost |
|----------|-------|---------|------|
| `call_openai_vision()` | gpt-4o | Frame analysis (detail: low) | ~$0.0004/frame |
| `call_openai_json(task="reasoning")` | gpt-4o | Complex itinerary assembly | ~$0.01/call |
| `call_openai_json(task="fast")` | gpt-4o-mini | Content fusion, location detection, highlights, agents | ~$0.00015/call |
| `transcribe_audio()` | whisper-1 | Audio transcription | ~$0.006/minute |

Features: Model routing, JSON repair for truncated responses, exponential backoff retries.

### Google Places API (New)

**File**: `backend/services/google_places_client.py`

| Operation | Purpose |
|-----------|---------|
| Text Search | Find places by name/query, get place_id |
| Place Details | Full details (address, rating, photos, hours) |
| Nearby Search | Discover attractions/restaurants/hotels within radius |
| Photo URL | Resolve photo references to URLs |

Results cached in `place_cache` table.

### Tavily Web Search

**File**: `backend/services/tavily_client.py`

Used by agents to get real-time data that AI models don't have:
- Flight prices and routes
- Hotel availability and pricing
- Safety advisories and visa requirements
- Transportation options between cities

### Open-Meteo (Weather)

**File**: `backend/services/weather_client.py`

- Free API, no key required
- Provides temperature, precipitation, and general weather data
- Used by weather agent for travel date forecasts

### ExchangeRate-API

**File**: `backend/services/exchange_rate_client.py`

- Currency conversion for budget calculations
- Converts prices from various currencies to user's preferred currency

### Supabase

**File**: `backend/services/supabase_client.py`

- PostgreSQL database via REST API
- Used for: session state, pipeline caching, itinerary storage, place caching
- Anonymous access (no user auth required)

---

## 20. Cost Optimization

### Model Routing Strategy

| Task | Model | Cost per 1K tokens | When Used |
|------|-------|-------------------|-----------|
| Vision analysis | gpt-4o | ~$0.01 input, $0.03 output | Frame analysis only |
| Complex reasoning | gpt-4o | ~$0.01 input, $0.03 output | Final itinerary assembly, customization |
| Fast tasks | gpt-4o-mini | ~$0.00015 input, $0.0006 output | Everything else (fusion, detection, agents, highlights) |
| Transcription | whisper-1 | ~$0.006/minute | Audio processing |

### Frame Cost Control

- Vision uses `detail: "low"` = 85 tokens per image (vs 1,105 for "high")
- Max 5 frames per video (`MAX_FRAME_COUNT=5`)
- Total vision cost per video: ~$0.002 (vs ~$0.025 with "high" detail)

### Caching Strategy

- **Stage 1-2 results**: Cached in `video_intelligence` by URL
- **Stage 3-4 results**: Cached in `location_results` by URL
- **Google Places**: Cached in `place_cache` by place_id
- Same URL never processed twice (saves 100% of costs on repeat requests)
- Feature flag `ENABLE_CACHE=true` controls caching

### Estimated Cost Per Trip

| Scenario | Cost |
|----------|------|
| First-time video processing + itinerary | $0.10 - $0.20 |
| Cached video + new itinerary | $0.06 - $0.11 |
| Itinerary customization | $0.01 - $0.03 |

---

## 21. Error Handling

### Backend Patterns

**Pipeline Orchestrator**:
- Wraps entire pipeline in try/except
- Yields `error` SSE events instead of raising exceptions
- `finally` block cleans up temp files
- Cache failures never crash the pipeline (silently ignored)

**Agent Orchestrator**:
- `asyncio.gather(return_exceptions=True)` -- one failing agent doesn't stop others
- Failed agents recorded in `agent_errors` list
- Assembler works with whatever data is available

**OpenAI Client**:
- Exponential backoff retry: `2^attempt` second delays
- JSON repair for truncated responses
- Configurable retry count per call
- Returns `None` on total failure (callers handle gracefully)

**Supabase Client**:
- All operations wrapped in try/except
- Returns `None` on failure
- Logging of all errors

### Frontend Patterns

- **SSE streams**: AbortController for cleanup on unmount
- **Error state**: Displayed with retry button
- **Loading states**: Skeleton components prevent layout shift
- **Image fallbacks**: Gradient backgrounds on image load failure
- **Fetch failures**: User-friendly error messages with retry option

### Feature Flags

```env
ENABLE_CACHE=true      # Disable to skip Supabase caching during dev
ENABLE_VISION=true     # Disable to skip expensive GPT-4o vision calls
ENABLE_TAVILY=true     # Disable if no Tavily key
ENABLE_WEATHER=true    # Disable if weather not needed
```

---

## 22. Deployment

### Backend (Python FastAPI)

**Recommended**: Railway or Render

1. Set environment variables (all from Section 5)
2. Install system dependency: `ffmpeg`
3. Install Python packages: `pip install -r requirements.txt`
4. Start command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

**Docker example**:
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Next.js)

**Recommended**: Vercel

1. Connect GitHub repo to Vercel
2. Set root directory to `frontend/`
3. Set environment variable: `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
4. Build command: `npm run build`
5. Start command: `npm start`

### Database (Supabase)

1. Create project on supabase.com
2. Run `backend/database/schema.sql` in SQL Editor
3. Copy project URL and anon key to backend .env

### CORS Configuration

Backend `main.py` allows:
- `FRONTEND_URL` from env (e.g., `https://your-app.vercel.app`)
- `http://localhost:3000` (always allowed for dev)

Update `FRONTEND_URL` env var to match your deployed frontend URL.

---

## 23. Known Limitations & Future Roadmap

### Current Limitations

1. **No user authentication** -- Sessions are anonymous, identified only by UUID
2. **No persistent user accounts** -- Itineraries can't be saved to a user profile
3. **No test suite** -- No Jest/Vitest/Pytest tests exist
4. **Instagram private videos** -- Requires cookies file for private content
5. **Single currency display** -- Budget shown in one currency only
6. **No booking integration** -- Links go to Google Flights/Hotels search, not direct booking
7. **No offline support** -- Requires active internet connection
8. **No rate limiting** -- API endpoints have no request throttling
9. **Frontend state is ephemeral** -- Page refresh loses all progress (Zustand in-memory only)
10. **No i18n** -- English only

### Future Roadmap

1. **User authentication** (Supabase Auth with email/Google OAuth)
2. **Saved trips** (user dashboard with trip history)
3. **Collaborative planning** (share and co-edit itineraries)
4. **Direct booking API** (Amadeus, Skyscanner, Booking.com)
5. **Real-time price tracking** (flight/hotel price alerts)
6. **Mobile app** (React Native or PWA)
7. **Multi-language support** (i18n framework)
8. **Social features** (share itineraries, community reviews)
9. **AI itinerary chat** (conversational modification beyond simple requests)
10. **Map view** (interactive map showing all activities with routing)
11. **Budget tracker** (real-time expense tracking during trip)
12. **Push notifications** (price drops, weather changes, booking reminders)

---

## Quick Reference: Key File Paths

| What | Path |
|------|------|
| Backend entry | `backend/main.py` |
| Backend config | `backend/config.py` |
| Pipeline orchestrator | `backend/pipeline/orchestrator.py` |
| Agent orchestrator | `backend/agents/orchestrator.py` |
| Agent state | `backend/agents/state.py` |
| OpenAI client | `backend/services/openai_client.py` |
| Supabase client | `backend/services/supabase_client.py` |
| Itinerary models | `backend/models/itinerary.py` |
| DB schema | `backend/database/schema.sql` |
| Frontend landing | `frontend/app/page.tsx` |
| Trip processing page | `frontend/app/trip/[sessionId]/page.tsx` |
| Itinerary page | `frontend/app/trip/[sessionId]/itinerary/page.tsx` |
| TypeScript types | `frontend/lib/types.ts` |
| Zustand store | `frontend/lib/store.ts` |
| SSE client | `frontend/lib/sse.ts` |
| Global styles | `frontend/app/globals.css` |

---

*Last updated: March 2026*
*Generated for comprehensive project onboarding and modification reference.*
