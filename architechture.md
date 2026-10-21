# ReelTrip — Master System Architecture & Implementation Documentation

**Version:** 2.0 (Complete Redesign)
**Last Updated:** March 2026
**Status:** Production-Ready Architecture Specification

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Vision](#2-problem-statement--vision)
3. [Core Philosophy & Design Principles](#3-core-philosophy--design-principles)
4. [Complete User Journey](#4-complete-user-journey)
5. [System Architecture Overview](#5-system-architecture-overview)
6. [Technology Stack](#6-technology-stack)
7. [AI Model Strategy & Cost Optimization](#7-ai-model-strategy--cost-optimization)
8. [Pipeline Stage 1 — Video Intelligence Extraction](#8-pipeline-stage-1--video-intelligence-extraction)
9. [Pipeline Stage 2 — Multi-Signal Content Analysis](#9-pipeline-stage-2--multi-signal-content-analysis)
10. [Pipeline Stage 3 — Location Detection & Validation](#10-pipeline-stage-3--location-detection--validation)
11. [Pipeline Stage 4 — Travel Highlights Generation](#11-pipeline-stage-4--travel-highlights-generation)
12. [Pipeline Stage 5 — Interactive Preference Collection](#12-pipeline-stage-5--interactive-preference-collection)
13. [Pipeline Stage 6 — Multi-Agent Travel Planning](#13-pipeline-stage-6--multi-agent-travel-planning)
14. [Pipeline Stage 7 — Itinerary Assembly & Delivery](#14-pipeline-stage-7--itinerary-assembly--delivery)
15. [Multi-Agent Orchestration System](#15-multi-agent-orchestration-system)
16. [Agent Definitions & Responsibilities](#16-agent-definitions--responsibilities)
17. [Real-Time Data Integration](#17-real-time-data-integration)
18. [Database Schema (Supabase)](#18-database-schema-supabase)
19. [API Design & Endpoints](#19-api-design--endpoints)
20. [Frontend Architecture](#20-frontend-architecture)
21. [Streaming & Real-Time UX](#21-streaming--real-time-ux)
22. [Caching Strategy](#22-caching-strategy)
23. [Error Handling & Fallback Strategy](#23-error-handling--fallback-strategy)
24. [Project Structure](#24-project-structure)
25. [Environment Variables](#25-environment-variables)
26. [Deployment Architecture](#26-deployment-architecture)
27. [Security Considerations](#27-security-considerations)
28. [Testing Strategy](#28-testing-strategy)
29. [What Makes ReelTrip Different](#29-what-makes-reeltrip-different)
30. [Future Roadmap](#30-future-roadmap)

---

## 1. Executive Summary

ReelTrip is an AI-powered travel planning system that transforms short-form travel videos (Instagram Reels, YouTube Shorts, TikTok) into complete, executable travel itineraries.

The system is not a simple "video to text" converter. It is a multi-agent intelligent travel assistant that:

- Extracts location intelligence from video using audio, visual, and metadata signals
- Validates locations against real-world data via Google Places API
- Generates rich, magazine-quality destination highlights
- Collects user preferences through an interactive conversational UI
- Deploys specialized AI agents (flight, hotel, transportation, activity, budget, safety, weather) to plan every aspect of the trip
- Produces a day-by-day itinerary with real costs, real places, real timings, and real logistics
- Allows full customization and dynamic editing of the generated plan

The entire system is designed to feel alive, responsive, and genuinely useful — not like a demo.

**Key Differentiator:** ReelTrip is the only system that starts from a travel video and produces a complete, bookable travel plan. No other open-source or commercial system does this end-to-end pipeline.

---

## 2. Problem Statement & Vision

### The Problem

Every day, hundreds of millions of people watch travel content on social media. They see beautiful destinations in 30-60 second reels and think: "I want to go there."

But then nothing happens. The gap between travel inspiration and travel execution is enormous:

- The viewer does not know exactly where the location is
- They do not know what else is nearby
- They have no idea about costs, logistics, visa requirements, or timing
- Manually researching all of this takes hours or days
- By the time they finish researching, the inspiration has faded

### The Vision

ReelTrip closes this gap in under 60 seconds.

User watches a travel reel → pastes the URL → gets a complete trip plan.

The vision is that ReelTrip should feel like having a world-class travel agent who watched the same reel you did and instantly prepared a detailed, personalized trip plan.

### What "Done Right" Looks Like

A successfully built ReelTrip produces itineraries that a real human would actually follow. This means:

- Real hotel names with real approximate prices (not invented ones)
- Real restaurant recommendations with cuisine types and cost ranges
- Accurate flight routing from the user's home city
- Realistic time estimates between attractions
- Local transportation options that actually exist
- Weather-appropriate activity scheduling
- Budget breakdowns in the user's local currency
- Visa and documentation requirements for international travel
- Safety advisories when relevant

---

## 3. Core Philosophy & Design Principles

### 3.1 Zero Hallucination Policy

Every factual claim in the output must be grounded in data. Locations come from Google Places API. Flight routes come from real airline data via web search. Hotel recommendations come from verified sources. The system must never invent a hotel that does not exist or suggest a restaurant that has closed.

When the system is uncertain, it must say so explicitly: "Approximate cost: $80-$120/night based on typical rates for this area" rather than presenting a fabricated exact number.

### 3.2 Progressive Disclosure

The system does not dump all information at once. It follows a carefully designed flow:

1. First, show what the video is about (quick, visual, exciting)
2. Then, show rich highlights about the destination (inspiring, educational)
3. Then, collect preferences (interactive, personalized)
4. Finally, deliver the full itinerary (comprehensive, actionable)

Each stage should feel like a natural next step, not a wall of text.

### 3.3 Cost-Conscious AI Usage

Every OpenAI API call costs money. The system is designed so that:

- Simple classification tasks use `gpt-4o-mini` (cheap, fast)
- Structured data extraction uses `gpt-4o-mini` with JSON mode
- Complex reasoning (itinerary planning, multi-constraint optimization) uses `gpt-4o`
- Vision analysis uses `gpt-4o` (only model with vision capability)
- Web search for real-time data uses Tavily API (not OpenAI)

The rule: use the cheapest model that can reliably do the job. Never use `gpt-4o` for a task that `gpt-4o-mini` handles correctly.

### 3.4 Real Data, Not Template Data

The system must fetch real, current data wherever possible:

- Google Places API for place verification, photos, ratings, opening hours
- Tavily web search for current hotel prices, flight routes, local events
- OpenWeatherMap or similar for real weather data
- Country-specific visa databases for travel documentation

When real-time data is unavailable, the system must use well-sourced estimates and clearly label them as estimates.

### 3.5 Every Button Works

There should be no non-functional UI element. If there is a "Book Now" button, it should link to an actual booking page (Google Hotels, Skyscanner, etc.). If there is a "Map" button, it should open Google Maps at the correct coordinates. If there is a "Share" button, it should produce a shareable link or downloadable PDF.

---

## 4. Complete User Journey

This section describes exactly what the user experiences from start to finish.

### Step 1: Landing Page

The user arrives at the ReelTrip homepage. They see:

- A clean, dark-themed interface with a prominent URL input field
- A tagline: "Paste a travel reel. Get a complete trip plan."
- Example thumbnails of recently processed reels (optional, for inspiration)
- The input field accepts Instagram Reel URLs, YouTube Shorts URLs, and TikTok URLs

### Step 2: URL Submission & Video Processing

The user pastes a travel video URL and hits "Go" or presses Enter.

Immediately, a real-time progress indicator appears showing the pipeline stages:

```
[■■□□□□□] Extracting video data...
[■■■□□□□] Analyzing content...
[■■■■□□□] Detecting locations...
[■■■■■□□] Validating places...
[■■■■■■□] Generating highlights...
[■■■■■■■] Ready!
```

Each stage transitions smoothly with animated progress. The user sees the video thumbnail and title appear as soon as metadata is extracted (within 2-3 seconds), so they know the system is working.

### Step 3: Location Intelligence Display

Once processing completes, the user sees:

- The detected destination (e.g., "Dubai, United Arab Emirates") with a confidence indicator
- A hero image from Google Places
- Key metadata: country, region, detected vibe (e.g., "Luxury Urban Experience")
- A "See Highlights" button that opens a rich, scrollable highlights panel

### Step 4: Highlights Exploration

The highlights panel presents magazine-quality cards for each notable place at the destination:

Each highlight card contains:
- High-quality photo from Google Places
- Place name and exact location
- 2-3 sentence engaging description
- Vibe tags (e.g., "Iconic", "Family-friendly", "Romantic")
- Best time to visit
- Signature experiences (e.g., "Watch sunset from the 148th floor observation deck")
- A "Know More" expandable section with deeper information
- Map link (opens Google Maps)
- Bookmark button (saves to user's trip wishlist)
- "Book Now" link (for bookable experiences, links to relevant booking site)

The user can scroll through 10-20 highlight cards, getting inspired and educated about the destination.

### Step 5: Create Itinerary (User-Initiated)

At the bottom of the highlights panel, there is a prominent floating action button: "Create Itinerary".

This is critical: the itinerary generation does NOT start automatically. It only begins when the user explicitly clicks this button. This saves API costs and respects the user's intent.

### Step 6: Preference Collection

After clicking "Create Itinerary", a conversational interface collects travel preferences. This is NOT a static form — it is an intelligent, adaptive conversation:

The system presents a structured form embedded in the chat:

**Travel Preferences Form:**

| Field | Type | Options |
|-------|------|---------|
| Trip Duration | Dropdown | 1-14 days |
| Number of Travelers | Dropdown | 1-10+ |
| Traveling With | Radio buttons | Solo / Partner / Family / Friends |
| Month of Travel | Dropdown | January - December |
| Budget (in user's currency) | Text input | Free text (e.g., "₹500,000" or "$5,000") |
| Travel Style | Multi-select chips | Adventure / Relaxation / Culture / Food / Shopping / Nature / Nightlife / Photography |
| Dietary Preferences | Multi-select chips | No restriction / Vegetarian / Vegan / Halal / Kosher / Gluten-free |
| Accommodation Preference | Single-select | Budget / Mid-range / Luxury / Ultra-luxury |
| Additional Notes | Text area | Free text for special requests |

The form also shows:
- **Bucket List Items**: Pre-populated based on the detected destination's top attractions. The user can select/deselect items they definitely want to include.

### Step 7: City/Region Selection

For destinations that span multiple cities or regions (e.g., UAE → Dubai + Abu Dhabi + Sharjah), the system presents a city selection screen:

- **Selected cities**: Cities detected from the video, shown with images and "Added" badges
- **Suggested cities**: Additional cities the AI recommends based on trip duration and preferences
- Each city card shows a photo, name, country, and tap-to-add/remove functionality
- A "Proceed" button to continue

### Step 8: Itinerary Generation (The Magic Moment)

Once preferences and cities are confirmed, the multi-agent system begins working. The user sees a generation screen:

```
🛫 Planning your flights...
🏨 Finding the best hotels...
🗺️ Designing your daily activities...
🍽️ Curating dining experiences...
💰 Optimizing your budget...
✅ Finalizing your itinerary...
```

Each step updates in real-time as agents complete their work. This typically takes 15-30 seconds.

### Step 9: Itinerary Delivery

The final itinerary is presented in a rich, interactive format:

**Header:**
- Trip title (e.g., "UAE Romantic Family Escape")
- Date range and traveler count
- Bookmark and Share buttons

**Tab Navigation:**
- Reservations | Day 1 | Day 2 | Day 3 | ... | Miscellaneous

**Reservations Tab:**
- Flight cards with departure/arrival cities, airports (IATA codes), times, duration, and prices
- Each flight has a "Book Now" button linking to a flight search (Google Flights or Skyscanner)
- Hotel cards with photos, ratings, price per night, total cost, and "Why this hotel?" explanation
- Each hotel has a "Book" button and "View other hotels" link
- Transportation overview (inter-city transfers if applicable)

**Day Tabs (Day 1, Day 2, etc.):**

Each day shows a timeline of activities:

```
Day 1 — Dubai

08:00  Flight from Mumbai to Dubai
       Mumbai (BOM) → Dubai (DXB)
       Duration: 3h 30m · ₹22,642

12:00  Check-in at Atlantis The Palm
       [Hotel photo carousel]
       Rating: 4.7 · ₹18,500/night
       [Book button] [Map button]

13:30  Lunch at Nobu Dubai
       [Restaurant photo]
       Rating: 4.6 · ₹2,500 for 2
       Signature: Black Cod Miso
       [Book button] [Map button]

15:00  Visit Ain Dubai (Observation Wheel)
       [Attraction photo]
       Duration: 1.5 hours · ₹800/person
       Best time: Evening for sunset views
       Tip: Book online for 15% discount
       [Book button] [Map button]

18:00  Desert Safari & Dune Bashing
       [Activity photo]
       Duration: 4 hours · ₹3,500/person
       Includes: Pickup, BBQ dinner, camel ride
       [Book button] [Map button]

22:00  Return to hotel
```

Each activity item includes:
- Time slot
- Activity name and type
- Venue photo (from Google Places)
- Duration and cost
- Practical tips
- Map link (Google Maps)
- Book button (links to booking page where available)

**Miscellaneous Tab:**
- Budget breakdown (Flights, Accommodation, Food, Activities, Transportation, Miscellaneous Buffer, Total)
- Visa requirements (if international travel)
- Weather forecast summary for the travel period
- Packing suggestions
- Cultural tips and etiquette notes
- Emergency contacts and useful phrases
- Currency information and exchange rate tips
- Travel insurance recommendation

### Step 10: Customization

A floating "Customise" button is always visible. Clicking it opens a chat interface where the user can make changes:

- "Can you replace the desert safari with a yacht cruise?"
- "I want to add a day trip to Abu Dhabi"
- "Can you suggest cheaper hotel options?"
- "I'm vegetarian, please update all restaurant suggestions"

The system dynamically updates the itinerary based on these requests. Each change recalculates affected parts (timing, budget, transportation) without regenerating the entire plan.

---

## 5. System Architecture Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  Landing → Processing → Highlights → Preferences → Itinerary    │
└──────────────┬───────────────────────────────────┬───────────────┘
               │ REST + SSE                        │ WebSocket
               ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              PIPELINE ORCHESTRATOR                        │    │
│  │                                                          │    │
│  │  Stage 1: Video Intelligence Extraction                  │    │
│  │      ├── yt-dlp (metadata, captions, hashtags)           │    │
│  │      ├── Audio Transcription (OpenAI Whisper)            │    │
│  │      └── Frame Extraction (ffmpeg)                       │    │
│  │                                                          │    │
│  │  Stage 2: Multi-Signal Content Analysis                  │    │
│  │      ├── Vision Analysis (gpt-4o, frames → locations)    │    │
│  │      └── Content Fusion (gpt-4o-mini, merge all signals) │    │
│  │                                                          │    │
│  │  Stage 3: Location Detection & Validation                │    │
│  │      ├── Location Ranking (gpt-4o-mini)                  │    │
│  │      ├── Google Places Geocoding & Validation            │    │
│  │      └── Nearby Places Discovery                         │    │
│  │                                                          │    │
│  │  Stage 4: Highlights Generation                          │    │
│  │      └── Rich Highlights (gpt-4o-mini + Google Places)   │    │
│  │                                                          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │           MULTI-AGENT TRAVEL PLANNER (LangGraph)         │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────┐        │    │
│  │  │         ORCHESTRATOR AGENT (gpt-4o)          │        │    │
│  │  │  Coordinates all specialist agents            │        │    │
│  │  │  Resolves conflicts, ensures consistency      │        │    │
│  │  └───────────────────┬──────────────────────────┘        │    │
│  │                      │                                    │    │
│  │    ┌─────────────────┼─────────────────────┐             │    │
│  │    ▼                 ▼                     ▼             │    │
│  │  ┌──────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │Flight│  │    Hotel     │  │Transportation│           │    │
│  │  │Agent │  │    Agent     │  │    Agent     │           │    │
│  │  └──────┘  └──────────────┘  └──────────────┘           │    │
│  │    ▼                 ▼                     ▼             │    │
│  │  ┌──────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │Activ.│  │   Budget     │  │   Weather    │           │    │
│  │  │Agent │  │   Agent      │  │   Agent      │           │    │
│  │  └──────┘  └──────────────┘  └──────────────┘           │    │
│  │    ▼                 ▼                                    │    │
│  │  ┌──────┐  ┌──────────────┐                              │    │
│  │  │Safety│  │  Itinerary   │                              │    │
│  │  │Agent │  │  Assembler   │                              │    │
│  │  └──────┘  └──────────────┘                              │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              EXTERNAL SERVICES LAYER                      │    │
│  │                                                          │    │
│  │  OpenAI API  │  Google Places  │  Tavily Search          │    │
│  │  Supabase DB │  OpenWeatherMap │  ExchangeRate API       │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

```
Video URL
  → [Extract] → VideoMetadata
  → [Analyze] → ContentAnalysis (transcript, vision, candidate_locations, vibe)
  → [Locate]  → LocationResult (validated places, coordinates, photos, nearby)
  → [Highlight] → PlaceHighlight[] (rich descriptions, tips, experiences)
  
  -- USER CLICKS "Create Itinerary" --
  
  → [Preferences] → UserPreferences (dates, budget, style, dietary, etc.)
  → [Plan]        → AgentOutputs (flights, hotels, transport, activities, weather, safety)
  → [Assemble]    → TripItinerary (complete day-by-day plan with all logistics)
```

---

## 6. Technology Stack

### Backend

| Component | Technology | Why This Choice |
|-----------|-----------|-----------------|
| Web Framework | **FastAPI** (Python) | Async-native, SSE support, auto-docs, Pydantic integration |
| ASGI Server | **Uvicorn** | Production-grade async server |
| Agent Orchestration | **LangGraph** | Stateful multi-agent workflows with conditional routing |
| AI Provider | **OpenAI API** | Best vision model (gpt-4o), reliable structured output, wide model range |
| Video Extraction | **yt-dlp** | Most reliable open-source video metadata extractor |
| Audio Processing | **ffmpeg** | Extract audio tracks from video files |
| Audio Transcription | **OpenAI Whisper API** (`whisper-1`) | High accuracy transcription, supports many languages |
| Web Search | **Tavily API** | Purpose-built for AI agents, returns structured results |
| Location Data | **Google Places API** (New) | Geocoding, place details, nearby search, photos |
| Weather Data | **OpenWeatherMap API** (free tier) | Current weather + 5-day forecast |
| Currency Data | **ExchangeRate-API** (free tier) | Real-time currency conversion |
| Database | **Supabase** (PostgreSQL) | Free tier, real-time, REST API, auth, storage |
| Data Validation | **Pydantic v2** | Type-safe request/response schemas |
| Task Queue | **asyncio** (built-in) | Parallel agent execution without extra infrastructure |

### Frontend

| Component | Technology | Why This Choice |
|-----------|-----------|-----------------|
| Framework | **Next.js 14** (App Router) | SSR, file-based routing, API routes, excellent DX |
| UI Library | **React 18** | Component-based, hooks, suspense |
| Styling | **Tailwind CSS** | Utility-first, dark theme, responsive |
| UI Components | **shadcn/ui** | High-quality, accessible, customizable components |
| Animations | **Framer Motion** | Smooth page transitions, card animations |
| Maps | **Leaflet.js** or **Google Maps JS API** | Interactive maps with markers and routes |
| State Management | **Zustand** | Lightweight, no boilerplate |
| HTTP Client | **fetch** (native) + **EventSource** | REST + SSE streaming |
| Icons | **Lucide React** | Clean, consistent icon set |

### Infrastructure

| Component | Technology | Why This Choice |
|-----------|-----------|-----------------|
| Database | **Supabase** | PostgreSQL + REST API + Auth + Storage, generous free tier |
| Hosting (Backend) | **Railway** or **Render** | Easy Python deployment, free tier available |
| Hosting (Frontend) | **Vercel** | Native Next.js support, edge functions, free tier |
| File Storage | **Supabase Storage** | Store extracted frames, generated PDFs |
| Monitoring | **Supabase Dashboard** + application logs | Query performance, error tracking |

---

## 7. AI Model Strategy & Cost Optimization

This is one of the most critical sections. Incorrect model selection wastes money. Correct selection saves 60-80% of costs without quality loss.

### Model Assignment Matrix

| Task | Model | Input | Output | Approx Cost per Call | Reasoning |
|------|-------|-------|--------|---------------------|-----------|
| Audio Transcription | `whisper-1` | Audio file | Text | $0.006/min | Only option for transcription |
| Vision Analysis (frames) | `gpt-4o` | Images + prompt | JSON | $0.01-0.03 | Only model with strong vision |
| Content Fusion | `gpt-4o-mini` | Text (transcript + captions + vision output) | JSON | $0.0003 | Text-only merge, simple task |
| Location Ranking | `gpt-4o-mini` | Text (candidate locations) | JSON | $0.0002 | Simple ranking/dedup |
| Highlights Generation | `gpt-4o-mini` | Text (place data from Google) | JSON | $0.0005 | Creative writing, not reasoning |
| Preference Interpretation | `gpt-4o-mini` | Text (user message) | JSON | $0.0001 | Simple form parsing |
| Flight Research | `gpt-4o-mini` + Tavily | Search queries | JSON | $0.001 + search cost | Web search does the heavy lifting |
| Hotel Research | `gpt-4o-mini` + Tavily | Search queries | JSON | $0.001 + search cost | Web search does the heavy lifting |
| Activity Planning | `gpt-4o-mini` | Text (place data + preferences) | JSON | $0.0005 | Moderate reasoning |
| Weather Analysis | `gpt-4o-mini` | Text (weather data) | JSON | $0.0001 | Simple interpretation |
| Safety Assessment | `gpt-4o-mini` + Tavily | Search queries | JSON | $0.001 | Web search + simple analysis |
| Itinerary Assembly | `gpt-4o` | All agent outputs | JSON | $0.02-0.05 | Complex multi-constraint reasoning |
| Itinerary Customization | `gpt-4o` | Existing itinerary + user request | JSON | $0.02-0.04 | Complex modification reasoning |
| Budget Optimization | `gpt-4o-mini` | Numbers + constraints | JSON | $0.0003 | Mathematical, not creative |

### Cost Estimation Per Trip

Assuming a typical flow (1 video processed, 1 itinerary generated):

| Stage | Estimated Cost |
|-------|---------------|
| Video Processing (Whisper + Vision + Fusion) | $0.04 - $0.08 |
| Location & Highlights | $0.002 |
| Travel Planning (all agents) | $0.03 - $0.06 |
| Itinerary Assembly | $0.03 - $0.05 |
| **Total per trip** | **$0.10 - $0.20** |

With caching (same video URL reuses Stages 1-4), subsequent itineraries for the same video cost only $0.06 - $0.11.

### Cost Optimization Rules

1. **Cache aggressively**: Every pipeline stage result is cached in Supabase. Same URL never processed twice.
2. **Batch prompts**: Instead of 10 separate calls for 10 highlight cards, make 1 call that generates all 10 at once.
3. **Use structured outputs**: `gpt-4o-mini` with `response_format: { type: "json_object" }` is cheaper and more reliable than asking for JSON in freeform mode.
4. **Minimize vision calls**: Extract only 3-5 key frames, not every frame. Vision is the most expensive per-call.
5. **Parallelize independent tasks**: Run flight, hotel, and activity agents simultaneously. Does not save money but saves time.
6. **Use Tavily for data, LLM for synthesis**: Do not ask the LLM to "search" — use Tavily to get facts, then ask the LLM to organize them.

---

## 8. Pipeline Stage 1 — Video Intelligence Extraction

### Purpose

Extract all available metadata and raw content from the video URL before any AI processing.

### Input

A video URL string. Supported formats:

```
https://www.instagram.com/reel/ABC123/
https://www.instagram.com/p/ABC123/
https://www.youtube.com/shorts/ABC123
https://youtube.com/shorts/ABC123
https://www.tiktok.com/@user/video/123456789
```

### Process

**Step 1.1: URL Validation**

Validate the URL format using regex patterns. Reject URLs that do not match any supported platform pattern. Return a clear error message: "Please paste a valid Instagram Reel, YouTube Short, or TikTok URL."

**Step 1.2: Metadata Extraction (yt-dlp)**

Use yt-dlp to extract:

```python
{
    "title": "Amazing sunset in Santorini! 🇬🇷",
    "description": "Best views in Greece. Must visit Oia village! #santorini #greece #travel",
    "uploader": "@travelwithsarah",
    "duration": 28,                    # seconds
    "view_count": 1250000,
    "like_count": 95000,
    "thumbnail_url": "https://...",
    "hashtags": ["santorini", "greece", "travel", "sunset", "oia"],
    "upload_date": "2026-02-15",
    "platform": "instagram",           # or "youtube" or "tiktok"
    "video_url": "https://...",         # direct video download URL
    "caption_text": "Amazing sunset in Santorini! Best views in Greece..."
}
```

For Instagram Reels: yt-dlp may require cookies for authentication. The system supports cookie-based auth via a cookies.txt file.

**Step 1.3: Audio Extraction (ffmpeg)**

Extract the audio track from the video file:

```bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
```

If the video has no audio track, skip transcription and note: "No audio track detected."

**Step 1.4: Audio Transcription (OpenAI Whisper)**

Transcribe the audio using OpenAI's Whisper API:

```python
# Using OpenAI API
from openai import OpenAI
client = OpenAI()

with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json"  # includes language detection
    )
```

The response includes:
- `text`: Full transcript
- `language`: Detected language (e.g., "en", "hi", "es")
- `segments`: Timestamped segments

If the audio is music-only (no speech), the transcript will be empty or contain only music lyrics. The system should detect this: if the transcript is fewer than 5 meaningful words after removing music lyrics, mark it as "Music only — no speech detected."

**Step 1.5: Frame Extraction (ffmpeg)**

Extract 4-6 key frames evenly distributed across the video duration:

```bash
# For a 30-second video, extract frames at 5s, 10s, 15s, 20s, 25s
ffmpeg -i video.mp4 -vf "select=eq(n\,150)+eq(n\,300)+eq(n\,450)+eq(n\,600)+eq(n\,750)" -vsync vfr frame_%d.jpg
```

Simpler approach: extract every N-th second:

```bash
ffmpeg -i video.mp4 -vf fps=1/6 frame_%d.jpg  # 1 frame every 6 seconds
```

Resize frames to reduce vision API costs:

```bash
ffmpeg -i video.mp4 -vf "fps=1/6,scale=768:-1" frame_%d.jpg
```

Convert frames to base64 for API submission.

### Output

```python
class VideoIntelligence:
    url: str
    platform: str                    # "instagram" | "youtube" | "tiktok"
    title: str
    description: str
    caption_text: str
    hashtags: list[str]
    uploader: str
    duration_seconds: int
    view_count: int | None
    thumbnail_url: str
    transcript: str                  # Full audio transcript
    transcript_language: str         # Detected language code
    has_speech: bool                 # Whether meaningful speech was detected
    frames_base64: list[str]         # Base64-encoded key frames
    frame_count: int
    extracted_at: str                # ISO timestamp
```

### Caching

The entire `VideoIntelligence` object (excluding `frames_base64` which are large) is cached in Supabase table `video_intelligence` keyed by URL. The frames themselves are stored in Supabase Storage bucket `frames/` if needed for re-processing.

---

## 9. Pipeline Stage 2 — Multi-Signal Content Analysis

### Purpose

Analyze all extracted signals (metadata, audio transcript, video frames) using AI to understand what the video is about and identify candidate locations.

### Process

**Step 2.1: Vision Analysis (gpt-4o)**

Send the extracted frames to GPT-4o with a carefully crafted prompt:

```
System: You are a travel location detection expert. Analyze these video frames 
and identify any travel-related locations, landmarks, or geographical indicators.

For each frame, report:
- Any recognizable landmarks, monuments, or famous buildings
- Text visible on signs, boards, or storefronts (including language)
- Architectural style indicators (Islamic, European, Asian, etc.)
- Natural landscape features (beaches, mountains, deserts, etc.)
- Any flags, license plates, or country-specific indicators
- Brand names or chains that indicate a specific country/region

Respond in JSON format:
{
    "frame_observations": [
        {
            "frame_index": 0,
            "landmarks": ["Burj Khalifa"],
            "visible_text": ["Dubai Mall", "Welcome to Dubai"],
            "text_languages": ["English", "Arabic"],
            "architecture_style": "Modern/Gulf",
            "landscape": "Urban desert cityscape",
            "country_indicators": ["UAE flag visible"],
            "confidence": "high"
        }
    ],
    "overall_location_guess": {
        "country": "United Arab Emirates",
        "city": "Dubai",
        "confidence": "high",
        "reasoning": "Burj Khalifa clearly visible, Arabic text, Dubai Mall signage"
    }
}
```

This is the most expensive call in the pipeline but also the most valuable. It provides visual ground truth that other signals cannot.

**Step 2.2: Content Fusion (gpt-4o-mini)**

Merge all signals into a unified analysis:

```
System: You are a travel content analyst. Given the following signals from a 
travel video, produce a unified analysis of the travel destination and content.

Signals:
1. Video title: "{title}"
2. Description: "{description}"
3. Hashtags: {hashtags}
4. Audio transcript: "{transcript}"
5. Vision analysis: {vision_output}

Produce a JSON response:
{
    "destination_country": "string",
    "destination_state_or_region": "string",
    "destination_city": "string",
    "confidence": "high|medium|low",
    "candidate_locations": [
        {
            "name": "string",
            "type": "city|landmark|area|beach|restaurant|hotel",
            "mentioned_in": ["title", "hashtags", "transcript", "vision"],
            "confidence": "high|medium|low"
        }
    ],
    "dominant_vibe": "string",  // e.g., "luxury urban experience"
    "content_summary": "string",  // 2-3 sentence summary
    "detected_activities": ["string"],  // e.g., ["desert safari", "fine dining", "sightseeing"]
    "target_audience": "string"  // e.g., "couples", "families", "solo adventurers"
}
```

### Critical Rule: No Hallucination

The content fusion step must ONLY include locations that were explicitly mentioned in at least one signal. If the video is about "Dubai" but never mentions "Abu Dhabi", the system must NOT add Abu Dhabi as a candidate location. Additional cities can be suggested later in the city selection step, but the initial detection must be strictly grounded in the video content.

### Output

```python
class ContentAnalysis:
    destination_country: str
    destination_region: str
    destination_city: str
    location_confidence: str          # "high" | "medium" | "low"
    candidate_locations: list[CandidateLocation]
    dominant_vibe: str
    content_summary: str
    detected_activities: list[str]
    target_audience: str
    transcript: str
    has_speech: bool
    vision_observations: list[FrameObservation]
```

---

## 10. Pipeline Stage 3 — Location Detection & Validation

### Purpose

Take the AI-detected candidate locations and validate them against real-world data using Google Places API. Remove false positives. Enrich validated locations with coordinates, photos, ratings, and nearby places.

### Process

**Step 3.1: Location Ranking & Deduplication (gpt-4o-mini)**

The content fusion may produce duplicates or ambiguous names. This step cleans them:

```
Input: ["Dubai", "Burj Khalifa", "Dubai Mall", "DXB", "United Arab Emirates"]

Output:
{
    "primary_destination": {
        "country": "United Arab Emirates",
        "region": "Dubai",
        "city": "Dubai"
    },
    "ranked_places": [
        {"name": "Burj Khalifa", "type": "landmark", "priority": 1},
        {"name": "Dubai Mall", "type": "landmark", "priority": 2}
    ],
    "removed": [
        {"name": "DXB", "reason": "Airport code, not a tourist destination"},
        {"name": "Dubai", "reason": "Duplicate of primary city"},
        {"name": "United Arab Emirates", "reason": "Country-level, too broad"}
    ]
}
```

**Step 3.2: Google Places Validation**

For each ranked place, validate using Google Places API:

```python
# Geocode the primary destination
geocode_result = google_places.geocode("Dubai, United Arab Emirates")
# Returns: lat, lng, formatted_address, place_id, types

# Validate each specific place
for place in ranked_places:
    result = google_places.find_place(
        input=f"{place.name}, {primary_destination.city}",
        input_type="textquery",
        fields=["place_id", "name", "formatted_address", "geometry", 
                "rating", "user_ratings_total", "photos", "types",
                "opening_hours", "website", "price_level"]
    )
    if result.status == "OK":
        place.validated = True
        place.google_data = result
    else:
        place.validated = False
        # Remove unvalidated places
```

**Step 3.3: Nearby Places Discovery**

For the primary destination, find nearby attractions, restaurants, and accommodations:

```python
# Attractions near the city center
attractions = google_places.nearby_search(
    location=f"{city_lat},{city_lng}",
    radius=15000,  # 15km
    type="tourist_attraction",
    rank_by="prominence"
)

# Restaurants
restaurants = google_places.nearby_search(
    location=f"{city_lat},{city_lng}",
    radius=10000,
    type="restaurant",
    rank_by="prominence"
)

# Hotels/Stays
hotels = google_places.nearby_search(
    location=f"{city_lat},{city_lng}",
    radius=15000,
    type="lodging",
    rank_by="prominence"
)
```

For each result, fetch a photo URL:

```python
if place.photos:
    photo_url = google_places.get_photo_url(
        photo_reference=place.photos[0].photo_reference,
        max_width=800
    )
```

**Step 3.4: Place Data Enrichment**

Combine validated places with nearby discoveries into a rich location dataset:

```python
class ValidatedPlace:
    name: str
    place_id: str
    formatted_address: str
    latitude: float
    longitude: float
    rating: float | None
    total_ratings: int | None
    price_level: int | None           # 0-4 (Google's scale)
    photo_url: str | None
    types: list[str]                  # Google Place types
    website: str | None
    opening_hours: dict | None
    source: str                       # "video_detected" | "nearby_attraction" | "nearby_restaurant" | "nearby_hotel"
```

### Output

```python
class LocationResult:
    primary_destination: PrimaryDestination
    validated_places: list[ValidatedPlace]    # Places from the video, confirmed real
    nearby_attractions: list[ValidatedPlace]  # Top 15 nearby tourist attractions
    nearby_restaurants: list[ValidatedPlace]  # Top 10 nearby restaurants
    nearby_hotels: list[ValidatedPlace]       # Top 10 nearby hotels
    all_photos: list[PhotoReference]          # All available photo URLs
    city_coordinates: Coordinates
    processed_at: str
```

---

## 11. Pipeline Stage 4 — Travel Highlights Generation

### Purpose

Transform raw location data into rich, engaging, magazine-quality content that inspires the user and helps them understand the destination before planning.

### Process

**Single Batch Call (gpt-4o-mini)**

Send all validated places and nearby attractions in a single API call:

```
System: You are an expert travel writer and destination specialist.
Generate rich, engaging highlight cards for each place listed below.

For each place, create:
1. description: 2-3 engaging sentences about what makes this place special.
   Write as if you're a knowledgeable local friend giving insider tips.
2. vibe_tags: Exactly 3 single-word tags (e.g., "Iconic", "Romantic", "Historic")
3. signature_experiences: 2-3 must-do activities at this specific place
4. best_time_to_visit: When to visit for the best experience (time of day or season)
5. know_more: 3-4 sentences of deeper context — history, insider tips, lesser-known facts
6. estimated_visit_duration: How long a typical visit takes (e.g., "2-3 hours")
7. estimated_cost_usd: Approximate entry/experience cost in USD (0 if free)

Use the Google Places data provided (ratings, types, price_level) to ensure accuracy.
Do NOT invent facts. If you are unsure about a specific detail, keep it general.

Places to describe:
{json_list_of_places_with_google_data}

Respond as a JSON array of highlight objects.
```

### Output

```python
class PlaceHighlight:
    place_name: str
    place_id: str
    photo_url: str | None
    latitude: float
    longitude: float
    formatted_address: str
    rating: float | None
    description: str
    vibe_tags: list[str]              # Exactly 3 tags
    signature_experiences: list[str]   # 2-3 experiences
    best_time_to_visit: str
    know_more: str
    estimated_visit_duration: str
    estimated_cost_usd: float
    google_maps_url: str              # Direct Google Maps link
    source: str                       # "video_detected" | "nearby_attraction" | etc.
```

### Fallback

If the highlight generation call fails (rate limit, timeout, etc.), the system falls back to basic highlights using only Google Places data:

```python
# Fallback highlight — no AI, just Google data
PlaceHighlight(
    place_name=place.name,
    description=f"A popular {place.types[0].replace('_', ' ')} in {city_name}.",
    vibe_tags=["Popular", "Recommended", place.types[0].replace('_', ' ').title()],
    signature_experiences=["Visit and explore"],
    best_time_to_visit="Check local timings",
    know_more="Visit the official website for more details.",
    ...
)
```

---

## 12. Pipeline Stage 5 — Interactive Preference Collection

### Purpose

Collect the user's travel preferences through an interactive, conversational interface. This stage only begins when the user clicks "Create Itinerary."

### Preference Schema

```python
class UserPreferences:
    trip_duration_days: int              # 1-14
    number_of_travelers: int             # 1-10
    traveling_with: str                  # "solo" | "partner" | "family" | "friends"
    month_of_travel: str                 # "January" - "December"
    total_budget: float                  # In user's local currency
    budget_currency: str                 # "INR", "USD", "EUR", etc.
    travel_styles: list[str]             # ["adventure", "relaxation", "culture", ...]
    dietary_preferences: list[str]       # ["vegetarian", "halal", "none", ...]
    accommodation_tier: str              # "budget" | "mid-range" | "luxury" | "ultra-luxury"
    must_include_places: list[str]       # From bucket list selection
    additional_notes: str                # Free text special requests
    home_city: str                       # For flight routing
    home_country: str                    # For visa requirements
```

### Home City Detection

The system should attempt to detect the user's home city:

1. If the user is logged in and has a saved profile, use their saved city
2. If available, use IP-based geolocation as a suggestion
3. Otherwise, ask the user in the preference form

The home city is critical for:
- Flight routing (e.g., Mumbai → Dubai)
- Visa requirements (Indian passport → Schengen visa needed)
- Currency conversion
- Time zone calculations

### Bucket List Feature

Before the main form, present a bucket list based on the destination's highlights:

```
Here are popular experiences at this destination.
Select the ones you definitely want to include:

[x] Burj Khalifa observation deck
[x] Desert Safari with BBQ dinner  
[ ] Dubai Mall shopping
[x] Dhow cruise dinner
[ ] Gold Souk market
[x] Atlantis Aquaventure Waterpark
```

Pre-selected items are those with the highest ratings or that match the video's vibe. The user can add/remove as they wish.

---

## 13. Pipeline Stage 6 — Multi-Agent Travel Planning

### Purpose

Deploy specialized AI agents to research and plan every aspect of the trip. This is the core intelligence of the system.

### Agent Execution Flow

```
User Preferences + Location Data
        │
        ▼
  ┌─────────────┐
  │ Orchestrator │ ← Coordinates all agents
  └──────┬──────┘
         │
    ┌────┴────┐ (Parallel Batch 1: Research)
    ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Flight │ │ Hotel  │ │Weather │ │Safety  │
│ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     ▼          ▼          ▼          ▼
   Flights    Hotels    Weather    Safety
   Data       Data      Data       Data
     │          │          │          │
     └──────────┴────┬─────┴──────────┘
                     │
              (Parallel Batch 2: Planning)
                     ▼
           ┌────────────────┐ ┌────────┐
           │ Activity Agent │ │Transport│
           │                │ │ Agent   │
           └───────┬────────┘ └───┬────┘
                   │              │
                   ▼              ▼
               Activities    Transport
               Data          Data
                   │              │
                   └──────┬───────┘
                          │
                    ┌─────▼─────┐
                    │  Budget   │
                    │  Agent    │
                    └─────┬─────┘
                          │
                    ┌─────▼──────────┐
                    │   Itinerary    │
                    │   Assembler    │
                    │   (gpt-4o)    │
                    └────────────────┘
```

### Why This Execution Order

1. **Batch 1 (Parallel)**: Flight, Hotel, Weather, and Safety agents can all run simultaneously because they are independent research tasks.
2. **Batch 2 (Parallel)**: Activity and Transport agents need weather data (to avoid scheduling outdoor activities during bad weather) and flight data (to know arrival/departure times).
3. **Budget Agent**: Runs after all other agents to calculate total costs and optimize if over budget.
4. **Itinerary Assembler**: Runs last because it needs all agent outputs to construct the final plan.

---

## 14. Pipeline Stage 7 — Itinerary Assembly & Delivery

### Purpose

Take all agent outputs and assemble them into a coherent, time-sequenced, day-by-day itinerary.

### Itinerary Assembly Prompt (gpt-4o)

This is the most complex prompt in the system and uses `gpt-4o` because it requires multi-constraint reasoning:

```
System: You are an expert travel itinerary planner. Given the following data 
from specialized research agents, assemble a detailed day-by-day itinerary.

CONSTRAINTS:
1. The itinerary must be physically possible — check travel times between locations
2. Morning activities should start no earlier than 8:00 AM (unless it's a sunrise activity)
3. Evening activities should end by 11:00 PM
4. Include meal times: breakfast (7:30-9:00), lunch (12:00-14:00), dinner (19:00-21:00)
5. Each activity must include realistic travel time from the previous location
6. The first day accounts for flight arrival time
7. The last day accounts for flight departure time
8. Budget must not exceed the user's stated budget
9. Respect dietary preferences for ALL restaurant recommendations
10. Prioritize must-include places from the bucket list
11. Group nearby attractions to minimize travel time
12. Balance busy and relaxing activities — no more than 4 major activities per day

DATA FROM AGENTS:
- Flights: {flight_agent_output}
- Hotels: {hotel_agent_output}
- Activities: {activity_agent_output}
- Transport: {transport_agent_output}
- Weather: {weather_agent_output}
- Safety: {safety_agent_output}

USER PREFERENCES:
{user_preferences}

Respond with a complete JSON itinerary following this exact schema:
{itinerary_json_schema}
```

### Itinerary Output Schema

```python
class TripItinerary:
    trip_title: str
    destination_country: str
    destination_cities: list[str]
    start_date: str                     # e.g., "March 7, 2026"
    end_date: str
    total_days: int
    total_travelers: int
    
    # Reservations
    flights: list[FlightReservation]
    hotels: list[HotelReservation]
    
    # Day-by-day plan
    days: list[ItineraryDay]
    
    # Budget
    budget_breakdown: BudgetBreakdown
    
    # Miscellaneous
    visa_requirements: VisaInfo | None
    weather_summary: WeatherSummary
    packing_suggestions: list[str]
    cultural_tips: list[str]
    emergency_info: EmergencyInfo
    currency_info: CurrencyInfo

class FlightReservation:
    type: str                           # "international" | "domestic"
    from_city: str
    from_airport_code: str
    to_city: str
    to_airport_code: str
    departure_datetime: str
    arrival_datetime: str
    duration: str
    estimated_price: float
    price_currency: str
    booking_url: str                    # Link to Google Flights search
    notes: str | None

class HotelReservation:
    hotel_name: str
    city: str
    address: str
    check_in_date: str
    check_out_date: str
    nights: int
    price_per_night: float
    total_price: float
    price_currency: str
    rating: float
    photo_url: str | None
    why_recommended: str                # 1-2 sentences
    booking_url: str                    # Link to Google Hotels or Booking.com search
    latitude: float
    longitude: float

class ItineraryDay:
    day_number: int
    date: str
    city: str
    theme: str                          # e.g., "Dubai Iconic Landmarks"
    activities: list[Activity]

class Activity:
    time: str                           # "08:00" format
    title: str
    type: str                           # "flight" | "checkin" | "checkout" | "meal" | "attraction" | "activity" | "transport" | "free_time"
    venue_name: str | None
    venue_address: str | None
    latitude: float | None
    longitude: float | None
    photo_url: str | None
    rating: float | None
    duration_minutes: int
    estimated_cost: float
    cost_currency: str
    description: str                    # 1-2 sentence description
    practical_tip: str | None           # Insider tip
    booking_url: str | None             # Booking link where available
    google_maps_url: str | None
    # Transport-specific
    transport_mode: str | None          # "flight" | "car" | "metro" | "taxi" | "walk"
    transport_from: str | None
    transport_to: str | None

class BudgetBreakdown:
    flights_total: float
    accommodation_total: float
    food_total: float
    activities_total: float
    transportation_total: float
    miscellaneous_buffer: float
    grand_total: float
    currency: str
    budget_status: str                  # "within_budget" | "over_budget" | "under_budget"
    savings_tips: list[str] | None      # If over budget, suggest savings
```

---

## 15. Multi-Agent Orchestration System

### Architecture: LangGraph StateGraph

The multi-agent system uses LangGraph for orchestration. LangGraph provides:

- Stateful execution: agents share a common state object
- Conditional routing: the orchestrator decides which agent runs next
- Error recovery: failed agents can be retried or skipped
- Streaming: agent progress can be streamed to the frontend in real-time

### LangGraph State Definition

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class TravelPlannerState(TypedDict):
    # Input
    location_result: LocationResult
    user_preferences: UserPreferences
    highlights: list[PlaceHighlight]
    
    # Agent outputs
    flight_data: FlightResearchOutput | None
    hotel_data: HotelResearchOutput | None
    weather_data: WeatherResearchOutput | None
    safety_data: SafetyResearchOutput | None
    activity_data: ActivityResearchOutput | None
    transport_data: TransportResearchOutput | None
    budget_analysis: BudgetAnalysisOutput | None
    
    # Final output
    itinerary: TripItinerary | None
    
    # Orchestration
    current_phase: str                  # "researching" | "planning" | "assembling" | "complete"
    agent_errors: list[str]
    progress_updates: list[str]
```

### Graph Construction

```python
workflow = StateGraph(TravelPlannerState)

# Add agent nodes
workflow.add_node("flight_agent", flight_agent_node)
workflow.add_node("hotel_agent", hotel_agent_node)
workflow.add_node("weather_agent", weather_agent_node)
workflow.add_node("safety_agent", safety_agent_node)
workflow.add_node("activity_agent", activity_agent_node)
workflow.add_node("transport_agent", transport_agent_node)
workflow.add_node("budget_agent", budget_agent_node)
workflow.add_node("itinerary_assembler", itinerary_assembler_node)

# Parallel Batch 1: Research
workflow.add_edge("__start__", "flight_agent")
workflow.add_edge("__start__", "hotel_agent")
workflow.add_edge("__start__", "weather_agent")
workflow.add_edge("__start__", "safety_agent")

# Batch 2: Planning (after research completes)
workflow.add_edge("flight_agent", "activity_agent")
workflow.add_edge("hotel_agent", "activity_agent")
workflow.add_edge("weather_agent", "activity_agent")
workflow.add_edge("weather_agent", "transport_agent")
workflow.add_edge("flight_agent", "transport_agent")

# Budget after all planning
workflow.add_edge("activity_agent", "budget_agent")
workflow.add_edge("transport_agent", "budget_agent")
workflow.add_edge("hotel_agent", "budget_agent")
workflow.add_edge("flight_agent", "budget_agent")

# Assembly after budget
workflow.add_edge("budget_agent", "itinerary_assembler")
workflow.add_edge("itinerary_assembler", END)

app = workflow.compile()
```

---

## 16. Agent Definitions & Responsibilities

### 16.1 Flight Agent

**Model:** `gpt-4o-mini` + Tavily web search
**Purpose:** Find realistic flight options for the trip

**Process:**
1. Determine if flights are needed (domestic trips might use trains/cars)
2. Search Tavily for flight routes and approximate prices:
   ```
   Query: "flights from Mumbai to Dubai March 2026 cheapest"
   Query: "Mumbai BOM to Dubai DXB flight duration airlines"
   ```
3. Parse search results to extract flight options
4. Structure output with airline names, approximate times, and price ranges

**Output:**
```python
class FlightResearchOutput:
    flights_needed: bool
    route_type: str                     # "international" | "domestic" | "none"
    outbound_options: list[FlightOption]
    return_options: list[FlightOption]
    recommended_outbound: FlightOption
    recommended_return: FlightOption
    booking_search_url: str             # Google Flights pre-filled URL
    
class FlightOption:
    airline: str
    from_airport: str                   # IATA code
    to_airport: str
    departure_time: str                 # Approximate
    arrival_time: str
    duration: str
    stops: int
    estimated_price: float
    price_currency: str
    source: str                         # Where the price came from
```

### 16.2 Hotel Agent

**Model:** `gpt-4o-mini` + Tavily web search + Google Places
**Purpose:** Find suitable accommodation options

**Process:**
1. Determine accommodation needs based on preferences (budget tier, traveling style)
2. Use Google Places nearby_search for hotels in the destination
3. Use Tavily to search for approximate pricing:
   ```
   Query: "best luxury hotels Dubai March 2026 price per night"
   Query: "family-friendly hotels near Burj Khalifa Dubai rates"
   ```
4. Match hotels to the user's budget and preferences
5. Recommend the best option with a "Why this hotel?" explanation

**Output:**
```python
class HotelResearchOutput:
    recommended_hotels: list[HotelOption]  # 1 per city, primary recommendation
    alternative_hotels: list[HotelOption]  # 2-3 alternatives per city
    
class HotelOption:
    name: str
    city: str
    address: str
    latitude: float
    longitude: float
    rating: float
    price_per_night_estimate: float
    currency: str
    photo_url: str | None
    why_recommended: str
    traveler_type_match: str            # "family" | "couple" | "solo" | "friends"
    booking_search_url: str
    amenities: list[str]
```

### 16.3 Weather Agent

**Model:** `gpt-4o-mini` + OpenWeatherMap API
**Purpose:** Assess weather conditions for the travel dates and suggest adjustments

**Process:**
1. Call OpenWeatherMap API for the destination:
   - If travel is within 5 days: use forecast API for exact predictions
   - If travel is further out: use historical averages for the month
2. Identify any weather concerns (extreme heat, monsoon season, cold snaps)
3. Suggest activity timing adjustments based on weather

**Output:**
```python
class WeatherResearchOutput:
    destination_city: str
    travel_month: str
    avg_high_celsius: float
    avg_low_celsius: float
    precipitation_chance: str           # "low" | "moderate" | "high"
    weather_description: str            # "Warm and sunny with occasional humidity"
    warnings: list[str]                 # e.g., ["Extreme heat expected, stay hydrated"]
    recommendations: list[str]          # e.g., ["Schedule outdoor activities for morning/evening"]
    best_time_for_outdoor: str          # "early morning and evening"
    pack_suggestions: list[str]         # ["sunscreen", "light clothing", "hat"]
```

### 16.4 Safety Agent

**Model:** `gpt-4o-mini` + Tavily web search
**Purpose:** Assess destination safety and provide travel advisories

**Process:**
1. Search for current travel advisories:
   ```
   Query: "UAE travel advisory 2026 safety"
   Query: "Dubai tourist safety tips 2026"
   ```
2. Check for any ongoing issues (political instability, natural disasters, health advisories)
3. Provide general safety tips specific to the destination

**Output:**
```python
class SafetyResearchOutput:
    overall_safety_rating: str          # "very safe" | "safe" | "moderate" | "use caution" | "avoid"
    travel_advisory_summary: str
    specific_warnings: list[str]        # e.g., ["Avoid public displays of affection"]
    health_advisories: list[str]        # e.g., ["No special vaccinations required"]
    emergency_numbers: dict             # {"police": "999", "ambulance": "998"}
    cultural_etiquette: list[str]       # e.g., ["Dress modestly in public areas"]
    scam_warnings: list[str]            # Common tourist scams
    areas_to_avoid: list[str]           # If any
```

### 16.5 Activity Agent

**Model:** `gpt-4o-mini` + Google Places + Tavily
**Purpose:** Plan activities for each day, accounting for preferences, weather, and logistics

**Process:**
1. Start with must-include items from the user's bucket list
2. Add popular attractions from the highlights
3. Match restaurant recommendations to dietary preferences
4. Check activity availability for the travel month
5. Estimate costs for each activity using Tavily:
   ```
   Query: "Burj Khalifa observation deck ticket price 2026"
   Query: "Dubai desert safari tour price per person"
   ```
6. Group activities by geographic proximity to minimize transit time
7. Assign activities to morning/afternoon/evening slots based on optimal visiting times

**Output:**
```python
class ActivityResearchOutput:
    planned_activities: list[PlannedActivity]
    restaurant_recommendations: list[RestaurantRecommendation]
    
class PlannedActivity:
    name: str
    type: str                           # "attraction" | "experience" | "show" | "tour"
    city: str
    address: str
    latitude: float
    longitude: float
    photo_url: str | None
    rating: float | None
    suggested_day: int | None           # Which day this fits best
    suggested_time_slot: str            # "morning" | "afternoon" | "evening"
    duration_minutes: int
    estimated_cost_per_person: float
    currency: str
    booking_url: str | None
    description: str
    tip: str | None
    weather_dependent: bool             # True for outdoor activities

class RestaurantRecommendation:
    name: str
    cuisine: str
    city: str
    address: str
    latitude: float
    longitude: float
    photo_url: str | None
    rating: float | None
    price_range: str                    # "$" to "$$$$"
    estimated_cost_per_person: float
    currency: str
    signature_dishes: list[str]
    dietary_suitable: list[str]         # ["vegetarian", "halal", etc.]
    meal_type: str                      # "breakfast" | "lunch" | "dinner"
    booking_url: str | None
    google_maps_url: str
```

### 16.6 Transportation Agent

**Model:** `gpt-4o-mini` + Tavily
**Purpose:** Plan local transportation between all activities

**Process:**
1. For inter-city travel within the trip (e.g., Dubai → Abu Dhabi):
   - Search for options: driving, bus, train
   - Estimate costs and times
2. For intra-city travel:
   - Determine the best transport mode (metro, taxi, walking)
   - Estimate costs
3. Airport transfers: how to get from airport to hotel

**Output:**
```python
class TransportResearchOutput:
    inter_city_options: list[InterCityTransport]
    airport_transfers: list[AirportTransfer]
    local_transport_summary: LocalTransportSummary
    
class InterCityTransport:
    from_city: str
    to_city: str
    mode: str                           # "car" | "bus" | "train" | "flight"
    duration: str
    estimated_cost: float
    currency: str
    recommended: bool
    notes: str
    
class AirportTransfer:
    airport: str
    hotel: str
    recommended_mode: str               # "taxi" | "metro" | "shuttle"
    estimated_cost: float
    estimated_duration: str
    
class LocalTransportSummary:
    city: str
    best_option: str                    # "metro" | "taxi" | "ride_hailing" | "walking"
    metro_available: bool
    ride_hailing_apps: list[str]        # ["Uber", "Careem"]
    avg_taxi_cost_per_km: float
    daily_transport_budget: float
    tips: list[str]
```

### 16.7 Budget Agent

**Model:** `gpt-4o-mini`
**Purpose:** Calculate total trip cost and optimize if over budget

**Process:**
1. Sum all costs from other agents (flights, hotels, activities, food, transport)
2. Add a 10% miscellaneous buffer
3. Convert all costs to the user's preferred currency using ExchangeRate API
4. Compare total to user's stated budget
5. If over budget, suggest specific optimizations:
   - Downgrade hotel tier
   - Replace expensive activities with free alternatives
   - Suggest cheaper flight timings
   - Recommend budget restaurants instead of fine dining

**Output:**
```python
class BudgetAnalysisOutput:
    total_estimated_cost: float
    currency: str
    user_budget: float
    budget_status: str                  # "within" | "over" | "under"
    breakdown: dict[str, float]         # Category → total cost
    exchange_rate_used: float | None
    optimization_suggestions: list[str] # If over budget
    potential_savings: float            # How much could be saved
```

---

## 17. Real-Time Data Integration

### Google Places API (New)

**Endpoints Used:**
- `Place Search (Text)`: Find places by name
- `Place Details`: Get full information about a place
- `Nearby Search`: Find attractions/restaurants/hotels near coordinates
- `Place Photos`: Get high-quality photos

**Cost Management:**
- Cache all Place Details responses in Supabase (places rarely change)
- Use field masks to only request needed fields (reduces cost per call)
- Photo URLs from Nearby Search are free; only Place Details photos cost extra

### Tavily API

**Purpose:** Real-time web search for current pricing, availability, and information that Google Places does not provide (flight prices, hotel rates, visa info).

**Cost:** ~$0.01 per search query

**Usage Pattern:**
```python
from tavily import TavilyClient
tavily = TavilyClient(api_key=TAVILY_API_KEY)

result = tavily.search(
    query="flights Mumbai to Dubai March 2026 price",
    search_depth="basic",       # "basic" is cheaper, "advanced" for complex queries
    max_results=5,
    include_answer=True         # Get a synthesized answer
)
```

### OpenWeatherMap API

**Free tier:** 1,000 calls/day, 5-day forecast

```python
import requests

# 5-day forecast
response = requests.get(
    "https://api.openweathermap.org/data/2.5/forecast",
    params={
        "lat": destination_lat,
        "lon": destination_lng,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
)

# Historical monthly averages (for trips more than 5 days out)
# Use climate data from the World Weather API or similar
```

### ExchangeRate API

**Free tier:** 1,500 calls/month

```python
response = requests.get(
    f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/USD/INR"
)
rate = response.json()["conversion_rate"]
```

---

## 18. Database Schema (Supabase)

### Tables

**Table: `video_intelligence`** (Stage 1-2 cache)
```sql
CREATE TABLE video_intelligence (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL,
    title TEXT,
    description TEXT,
    caption_text TEXT,
    hashtags JSONB DEFAULT '[]',
    uploader TEXT,
    duration_seconds INTEGER,
    view_count BIGINT,
    thumbnail_url TEXT,
    transcript TEXT,
    transcript_language TEXT,
    has_speech BOOLEAN DEFAULT false,
    content_analysis JSONB,           -- Full ContentAnalysis object
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_video_url ON video_intelligence(url);
```

**Table: `location_results`** (Stage 3-4 cache)
```sql
CREATE TABLE location_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE REFERENCES video_intelligence(url),
    primary_country TEXT NOT NULL,
    primary_region TEXT,
    primary_city TEXT NOT NULL,
    city_latitude FLOAT,
    city_longitude FLOAT,
    validated_places JSONB DEFAULT '[]',
    nearby_attractions JSONB DEFAULT '[]',
    nearby_restaurants JSONB DEFAULT '[]',
    nearby_hotels JSONB DEFAULT '[]',
    highlights JSONB DEFAULT '[]',    -- PlaceHighlight[] array
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_location_url ON location_results(url);
```

**Table: `itineraries`** (Stage 7 output)
```sql
CREATE TABLE itineraries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL REFERENCES video_intelligence(url),
    session_id TEXT NOT NULL,
    user_preferences JSONB NOT NULL,
    selected_cities JSONB DEFAULT '[]',
    itinerary JSONB NOT NULL,         -- Full TripItinerary object
    version INTEGER DEFAULT 1,        -- Incremented on customization
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_itinerary_url ON itineraries(url);
CREATE INDEX idx_itinerary_session ON itineraries(session_id);
```

**Table: `sessions`** (Chat state)
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,              -- UUID session ID
    url TEXT REFERENCES video_intelligence(url),
    stage TEXT NOT NULL DEFAULT 'processing',  -- processing | highlights | preferences | planning | itinerary | customizing
    preferences JSONB,
    selected_cities JSONB DEFAULT '[]',
    chat_history JSONB DEFAULT '[]',
    itinerary_id UUID REFERENCES itineraries(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Table: `place_cache`** (Google Places cache)
```sql
CREATE TABLE place_cache (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    formatted_address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    rating FLOAT,
    total_ratings INTEGER,
    price_level INTEGER,
    types JSONB DEFAULT '[]',
    photo_url TEXT,
    website TEXT,
    opening_hours JSONB,
    cached_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 19. API Design & Endpoints

### Base URL: `/api/v1`

**Video Processing:**

```
POST /api/v1/process
Body: { "url": "https://www.instagram.com/reel/..." }
Response: SSE stream with progress events

SSE Events:
  event: progress
  data: {"stage": "extracting", "message": "Extracting video metadata...", "percent": 15}
  
  event: metadata
  data: {"title": "...", "thumbnail_url": "...", "platform": "instagram"}
  
  event: progress
  data: {"stage": "analyzing", "message": "Analyzing video content...", "percent": 35}
  
  event: analysis
  data: {"destination": "Dubai, UAE", "vibe": "Luxury Urban", "confidence": "high"}
  
  event: progress
  data: {"stage": "locating", "message": "Validating locations...", "percent": 60}
  
  event: locations
  data: {"primary_city": "Dubai", "places_count": 12, "photos_count": 24}
  
  event: progress
  data: {"stage": "highlights", "message": "Generating highlights...", "percent": 85}
  
  event: highlights
  data: {"highlights": [...]}  // PlaceHighlight[] array
  
  event: complete
  data: {"session_id": "abc-123", "location_result_id": "..."}
```

**Preference & Itinerary:**

```
POST /api/v1/itinerary/preferences
Body: {
    "session_id": "abc-123",
    "preferences": { ...UserPreferences },
    "selected_cities": ["Dubai", "Abu Dhabi"]
}
Response: SSE stream with agent progress

SSE Events:
  event: agent_progress
  data: {"agent": "flight", "status": "working", "message": "Searching for flights..."}
  
  event: agent_progress
  data: {"agent": "flight", "status": "complete", "message": "Found 3 flight options"}
  
  event: agent_progress
  data: {"agent": "hotel", "status": "working", "message": "Finding hotels..."}
  
  ... (similar for each agent)
  
  event: itinerary
  data: { ...TripItinerary }  // Complete itinerary
  
  event: complete
  data: {"itinerary_id": "..."}
```

**Customization:**

```
POST /api/v1/itinerary/customize
Body: {
    "session_id": "abc-123",
    "itinerary_id": "...",
    "request": "Replace desert safari with yacht cruise"
}
Response: SSE stream with updated itinerary

SSE Events:
  event: customizing
  data: {"message": "Understanding your request..."}
  
  event: customizing
  data: {"message": "Searching for yacht cruise options..."}
  
  event: itinerary
  data: { ...UpdatedTripItinerary }
  
  event: complete
  data: {"itinerary_id": "...", "version": 2}
```

**Utility:**

```
GET /api/v1/session/{session_id}
Response: Current session state

GET /api/v1/itinerary/{itinerary_id}
Response: Full itinerary data

GET /api/v1/highlights/{url_encoded}
Response: Cached highlights for a URL
```

---

## 20. Frontend Architecture

### Pages & Routes (Next.js App Router)

```
app/
├── page.tsx                    # Landing page with URL input
├── trip/
│   └── [sessionId]/
│       ├── page.tsx            # Processing → Highlights → Preferences flow
│       └── itinerary/
│           └── page.tsx        # Full itinerary view
├── layout.tsx                  # Root layout with dark theme
└── globals.css                 # Tailwind + custom styles
```

### Component Architecture

```
components/
├── landing/
│   ├── URLInput.tsx            # URL paste field with validation
│   └── HeroSection.tsx         # Landing page hero
├── processing/
│   ├── ProgressTracker.tsx     # 7-stage progress with animations
│   ├── VideoPreview.tsx        # Thumbnail + title preview
│   └── LocationCard.tsx        # Detected destination display
├── highlights/
│   ├── HighlightsSheet.tsx     # Bottom sheet with highlight cards
│   ├── HighlightCard.tsx       # Individual place card
│   └── BucketListSelector.tsx  # Select must-include places
├── preferences/
│   ├── PreferenceForm.tsx      # Complete preference collection form
│   ├── CitySelector.tsx        # City selection modal
│   └── TravelStyleChips.tsx    # Multi-select style chips
├── itinerary/
│   ├── ItineraryHeader.tsx     # Trip title, dates, actions
│   ├── TabNavigation.tsx       # Reservations | Day 1 | Day 2 | ...
│   ├── ReservationsTab.tsx     # Flights + Hotels
│   ├── FlightCard.tsx          # Flight reservation card
│   ├── HotelCard.tsx           # Hotel card with photos
│   ├── DayTimeline.tsx         # Timeline view of activities
│   ├── ActivityCard.tsx        # Individual activity in timeline
│   ├── RestaurantCard.tsx      # Restaurant recommendation card
│   ├── TransportCard.tsx       # Transit/transport card
│   ├── BudgetBreakdown.tsx     # Cost summary table
│   ├── MiscellaneousTab.tsx    # Visa, weather, tips, etc.
│   └── CustomizeChat.tsx       # Chat interface for modifications
├── shared/
│   ├── MapView.tsx             # Leaflet map with markers
│   ├── PhotoCarousel.tsx       # Swipeable photo gallery
│   ├── RatingBadge.tsx         # Star rating display
│   ├── PriceBadge.tsx          # Price display with currency
│   └── BookButton.tsx          # External booking link button
└── ui/                         # shadcn/ui components
```

### Theme & Design Language

The UI should follow these design principles:

**Color Palette:**
```css
--bg-primary: #0a0a14;          /* Deep dark blue-black */
--bg-secondary: #12121f;        /* Card backgrounds */
--bg-tertiary: #1a1a2e;         /* Elevated surfaces */
--accent-primary: #8b5cf6;      /* Purple — primary actions */
--accent-secondary: #a78bfa;    /* Light purple — secondary */
--accent-gradient: linear-gradient(135deg, #7c3aed, #a855f7);
--text-primary: #f5f5f5;        /* White text */
--text-secondary: #a0a0b0;     /* Muted text */
--text-accent: #c4b5fd;         /* Purple-tinted text */
--success: #34d399;             /* Green for success states */
--warning: #fbbf24;             /* Yellow for warnings */
--error: #f87171;               /* Red for errors */
--border: rgba(139, 92, 246, 0.2); /* Subtle purple borders */
--glass: rgba(18, 18, 31, 0.8); /* Glass-morphism background */
--glass-blur: 12px;
```

**Design Elements:**
- Glass-morphism cards with subtle purple border glow
- Smooth page transitions (Framer Motion)
- Skeleton loading states for every data-dependent component
- Photo carousels with dot indicators
- Timeline views with connected dots for itinerary days
- Floating action buttons for primary actions
- Bottom sheets for mobile-friendly modal content
- Responsive: mobile-first design, beautiful on all screen sizes

---

## 21. Streaming & Real-Time UX

### SSE (Server-Sent Events) Architecture

The system uses SSE for all long-running operations:

**Backend (FastAPI):**
```python
from fastapi.responses import StreamingResponse
import json

@app.post("/api/v1/process")
async def process_video(request: ProcessRequest):
    async def event_stream():
        # Stage 1
        yield f"event: progress\ndata: {json.dumps({'stage': 'extracting', 'percent': 10})}\n\n"
        metadata = await extract_video_metadata(request.url)
        yield f"event: metadata\ndata: {json.dumps(metadata.dict())}\n\n"
        
        # Stage 2
        yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing', 'percent': 30})}\n\n"
        analysis = await analyze_content(metadata)
        yield f"event: analysis\ndata: {json.dumps(analysis.dict())}\n\n"
        
        # ... continue for each stage
        
        yield f"event: complete\ndata: {json.dumps({'session_id': session_id})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**Frontend (React):**
```typescript
const eventSource = new EventSource(`/api/v1/process`, {
    method: 'POST',
    body: JSON.stringify({ url }),
});

eventSource.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data);
    setProgress(data.percent);
    setStage(data.stage);
});

eventSource.addEventListener('highlights', (e) => {
    const data = JSON.parse(e.data);
    setHighlights(data.highlights);
});
```

---

## 22. Caching Strategy

### Multi-Layer Cache

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| L1: In-Memory | Python dict | Session lifetime | Active session state |
| L2: Supabase | PostgreSQL | 30 days | Video intelligence, locations, highlights |
| L3: Place Cache | PostgreSQL | 7 days | Google Places data |
| L4: Itinerary | PostgreSQL | Permanent | Generated itineraries |

### Cache Hit Flow

```
Request for URL "https://instagram.com/reel/ABC123"
  │
  ├── Check video_intelligence table
  │   ├── HIT → Skip Stages 1-2, return cached analysis
  │   └── MISS → Run Stages 1-2, cache result
  │
  ├── Check location_results table
  │   ├── HIT → Skip Stages 3-4, return cached locations + highlights
  │   └── MISS → Run Stages 3-4, cache result
  │
  └── Itinerary always generated fresh (different preferences each time)
      └── But cached after generation for retrieval
```

Second request for the same URL skips all video processing (~$0.05 saved) and goes straight to highlights display.

---

## 23. Error Handling & Fallback Strategy

### Principle: Never Show a Blank Screen

Every failure mode has a graceful degradation path:

| Failure | Fallback |
|---------|----------|
| yt-dlp fails to extract video | Show error: "Could not access this video. It may be private or unavailable." |
| Whisper transcription fails | Continue without transcript. Vision + metadata may be sufficient. |
| Vision analysis fails | Continue with metadata + transcript only. Location detection quality reduced. |
| Google Places geocoding fails | Use the AI's best guess for coordinates. Mark as "approximate location." |
| Google Places nearby search fails | Skip nearby places. Show only video-detected places. |
| Highlight generation fails | Use basic highlights from Google Places data (name, photo, rating only). |
| Tavily search fails | Use Google Places data and AI estimates instead of real-time pricing. |
| Individual agent fails | Skip that agent. Orchestrator continues with partial data. Note limitations in output. |
| Itinerary assembly fails | Retry once with a simpler prompt. If still fails, show agent outputs separately. |
| OpenAI API rate limit | Exponential backoff with 3 retries. If exhausted, queue request. |
| Supabase unavailable | Continue without caching. All results computed fresh. |

### User-Facing Error Messages

Error messages should be:
- Clear and specific (not "Something went wrong")
- Actionable (tell the user what to do next)
- Honest about limitations (not pretending everything is fine)

Example:
```
"We couldn't find flight pricing data for this route. The itinerary includes 
estimated costs based on typical fares. We recommend checking Google Flights 
for current prices."
```

---

## 24. Project Structure

```
reeltrip/
├── backend/
│   ├── main.py                              # FastAPI app, route definitions
│   ├── config.py                            # Environment variables, settings
│   ├── dependencies.py                      # FastAPI dependencies (DB, clients)
│   │
│   ├── pipeline/                            # Video processing pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py                  # Pipeline orchestrator (Stages 1-4)
│   │   ├── video_extractor.py               # yt-dlp wrapper
│   │   ├── audio_processor.py               # ffmpeg + Whisper transcription
│   │   ├── frame_extractor.py               # ffmpeg frame extraction
│   │   ├── vision_analyzer.py               # GPT-4o vision analysis
│   │   ├── content_fuser.py                 # GPT-4o-mini content fusion
│   │   ├── location_detector.py             # GPT-4o-mini location ranking
│   │   ├── location_validator.py            # Google Places validation
│   │   └── highlights_generator.py          # GPT-4o-mini highlight generation
│   │
│   ├── agents/                              # Multi-agent travel planner
│   │   ├── __init__.py
│   │   ├── orchestrator.py                  # LangGraph workflow definition
│   │   ├── state.py                         # TravelPlannerState TypedDict
│   │   ├── flight_agent.py                  # Flight research agent
│   │   ├── hotel_agent.py                   # Hotel research agent
│   │   ├── weather_agent.py                 # Weather assessment agent
│   │   ├── safety_agent.py                  # Safety & advisory agent
│   │   ├── activity_agent.py                # Activity planning agent
│   │   ├── transport_agent.py               # Transportation planning agent
│   │   ├── budget_agent.py                  # Budget optimization agent
│   │   └── itinerary_assembler.py           # Final itinerary assembly (GPT-4o)
│   │
│   ├── services/                            # External service clients
│   │   ├── __init__.py
│   │   ├── openai_client.py                 # OpenAI API wrapper (model routing)
│   │   ├── google_places_client.py          # Google Places API wrapper
│   │   ├── tavily_client.py                 # Tavily search wrapper
│   │   ├── weather_client.py                # OpenWeatherMap wrapper
│   │   ├── exchange_rate_client.py          # Currency conversion
│   │   └── supabase_client.py               # Supabase DB + Storage client
│   │
│   ├── models/                              # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── video.py                         # VideoIntelligence, ContentAnalysis
│   │   ├── location.py                      # LocationResult, ValidatedPlace, PlaceHighlight
│   │   ├── preferences.py                   # UserPreferences
│   │   ├── agents.py                        # All agent output models
│   │   ├── itinerary.py                     # TripItinerary, ItineraryDay, Activity
│   │   └── api.py                           # Request/Response models
│   │
│   ├── utils/                               # Utilities
│   │   ├── __init__.py
│   │   ├── url_validator.py                 # URL format validation
│   │   ├── currency.py                      # Currency formatting helpers
│   │   ├── geo.py                           # Coordinate calculations
│   │   └── prompts.py                       # All AI prompt templates
│   │
│   └── database/                            # SQL schemas
│       ├── schema.sql                       # All table definitions
│       └── migrations/                      # Future migrations
│
├── frontend/                                # Next.js 14 app
│   ├── app/
│   │   ├── page.tsx                         # Landing page
│   │   ├── layout.tsx                       # Root layout
│   │   ├── globals.css                      # Global styles
│   │   └── trip/
│   │       └── [sessionId]/
│   │           ├── page.tsx                 # Processing + Highlights
│   │           └── itinerary/
│   │               └── page.tsx             # Itinerary view
│   ├── components/                          # React components (see Section 20)
│   ├── lib/                                 # Utility functions
│   │   ├── api.ts                           # API client
│   │   ├── sse.ts                           # SSE handler
│   │   └── store.ts                         # Zustand store
│   ├── public/                              # Static assets
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── .env.example                             # Environment variable template
├── requirements.txt                         # Python dependencies
├── package.json                             # Root package.json (if monorepo)
├── docker-compose.yml                       # Local development
└── README.md                                # Project README
```

---

## 25. Environment Variables

```bash
# === REQUIRED ===

# OpenAI API Key — Used for all AI processing (vision, text, whisper)
OPENAI_API_KEY=sk-...

# Google Places API Key — Used for location validation, nearby search, photos
GOOGLE_PLACES_API_KEY=AIza...

# Supabase — Database and storage
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # For server-side operations

# === RECOMMENDED ===

# Tavily API Key — Real-time web search for pricing and travel info
TAVILY_API_KEY=tvly-...

# OpenWeatherMap API Key — Weather data
OPENWEATHER_API_KEY=...

# ExchangeRate API Key — Currency conversion
EXCHANGERATE_API_KEY=...

# === OPTIONAL ===

# Instagram cookies file path (for Instagram Reels access)
INSTAGRAM_COOKIES_PATH=./cookies.txt

# Default user currency (fallback)
DEFAULT_CURRENCY=INR

# Default user home city (fallback)
DEFAULT_HOME_CITY=Mumbai

# Max frames to extract from video
MAX_FRAME_COUNT=5

# OpenAI model overrides (for testing/cost control)
VISION_MODEL=gpt-4o
REASONING_MODEL=gpt-4o
FAST_MODEL=gpt-4o-mini

# Server configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 26. Deployment Architecture

### Development

```
docker-compose up
```

Docker Compose runs:
- Backend (FastAPI) on port 8000
- Frontend (Next.js) on port 3000
- Both connect to Supabase cloud (no local DB needed)

### Production

**Backend:** Deploy to Railway or Render
- Python 3.11+ runtime
- yt-dlp and ffmpeg pre-installed (use custom Dockerfile or buildpack)
- Environment variables set in platform dashboard

**Frontend:** Deploy to Vercel
- Automatic Next.js optimization
- Edge functions for API proxying if needed
- Environment variables for API URL

**Database:** Supabase Cloud (free tier supports up to 500MB, 50,000 rows)

### Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install yt-dlp
RUN pip install yt-dlp

COPY backend/ /app/backend/
WORKDIR /app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 27. Security Considerations

- **API Keys:** Never expose API keys to the frontend. All external API calls go through the backend.
- **Rate Limiting:** Implement rate limiting on all endpoints (e.g., 10 requests/minute per IP for `/process`).
- **Input Sanitization:** Validate all URL inputs strictly. Do not pass unsanitized URLs to yt-dlp.
- **CORS:** Restrict CORS origins to the frontend domain only.
- **Supabase RLS:** Enable Row Level Security on all tables. Anon key should only read public data.
- **File Cleanup:** Delete extracted video files and audio files after processing. Do not store user-uploaded videos permanently.
- **Cookie Security:** Instagram cookies file should be stored securely, not committed to git.

---

## 28. Testing Strategy

### Unit Tests

Test each service independently:
- `test_url_validator.py` — Test URL pattern matching for all platforms
- `test_video_extractor.py` — Mock yt-dlp, test metadata parsing
- `test_content_fuser.py` — Mock OpenAI, test JSON parsing
- `test_location_validator.py` — Mock Google Places, test validation logic
- `test_budget_agent.py` — Test cost calculations with known inputs

### Integration Tests

Test the full pipeline with real URLs:
- Test with a known YouTube Short (stable, public video)
- Test with a known Instagram Reel (requires cookies)
- Test end-to-end from URL to itinerary with a simple destination

### Agent Tests

Test each agent independently with mocked dependencies:
- Flight agent with pre-defined Tavily responses
- Hotel agent with pre-defined Google Places + Tavily responses
- Budget agent with pre-defined cost inputs

### Manual Testing Checklist

- [ ] YouTube Short URL processes successfully
- [ ] Instagram Reel URL processes successfully (with cookies)
- [ ] TikTok URL processes successfully
- [ ] Location detection is accurate for 5 different destinations
- [ ] Highlights display correctly with photos
- [ ] Preference form collects all fields
- [ ] City selection works with add/remove
- [ ] Itinerary generates within 60 seconds
- [ ] All booking links lead to real booking pages
- [ ] All map links open correct locations in Google Maps
- [ ] Budget breakdown totals correctly
- [ ] Customization request modifies itinerary correctly
- [ ] Mobile layout is usable
- [ ] Same URL returns cached results on second request

---

## 29. What Makes ReelTrip Different

### vs. Generic AI Travel Planners (ChatGPT, Gemini, etc.)

Generic AI planners require the user to type a detailed prompt. ReelTrip starts from a 30-second video — zero typing required for initial inspiration. The video provides rich visual context that text prompts cannot capture.

### vs. Rahee AI (Screenshots Provided)

Rahee AI is a travel planning chatbot. ReelTrip adds the critical first step: video understanding. Rahee requires the user to already know their destination. ReelTrip discovers the destination from the video.

Additionally, ReelTrip's multi-agent architecture produces more researched itineraries because each aspect (flights, hotels, weather, safety) is handled by a specialist agent with access to real-time web data.

### vs. GitHub Projects Referenced

Most open-source travel planners are CLI-only or have basic UIs. ReelTrip has a full production-quality frontend with interactive components, photo carousels, maps, and real-time streaming. It is designed to be deployed and used by real users, not just demonstrated in a notebook.

### Unique Features

1. **Video-first input** — No other system starts from social media videos
2. **Multi-signal location detection** — Fuses audio, visual, and metadata signals
3. **Magazine-quality highlights** — Inspired by travel media, not database dumps
4. **Multi-agent planning** — 7 specialized agents working in coordinated parallel
5. **Real-time data grounding** — Prices and availability from web search, not hallucination
6. **Full customization** — Chat-based itinerary modification with smart updates
7. **Production-ready frontend** — Mobile-first, animated, interactive

---

## 30. Future Roadmap

### Phase 2 Features

- **User Accounts** — Save trips, build a travel wishlist from multiple videos
- **PDF Export** — Download complete itinerary as a beautifully formatted PDF
- **Collaborative Planning** — Share trip plan with travel companions, collect preferences from multiple people
- **Memory Agent** — Remember user preferences across trips (preferred airlines, hotel chains, dietary restrictions)
- **Scene-to-Experience Agent** — Detect specific activities in video frames (cliff diving, street food eating, parasailing) and automatically include them in the itinerary
- **Cultural Intelligence Agent** — Deep cultural briefings: dress codes, tipping customs, common phrases in local language, bargaining expectations
- **Visa Agent** — Check visa requirements based on user's passport, provide application links and document checklists
- **Real Booking Integration** — Partner with booking platforms for in-app booking (affiliate model)
- **Trip Execution Mode** — During the trip, show today's itinerary with real-time updates, navigation, and check-in tracking

### Phase 3 Features

- **Social Features** — Share trips on a public feed, see what others planned from the same video
- **AI Trip Advisor** — Post-trip, ask "What should I do right now?" and get real-time suggestions based on your location and remaining itinerary
- **Multi-Video Trips** — Combine multiple reels from different destinations into a multi-city trip
- **Price Alerts** — Set budget alerts for flights and hotels, notify when prices drop

---

## End of Documentation

This document is the complete specification for the ReelTrip system. Any developer or AI system reading this document should have a full understanding of:

1. What ReelTrip does and why it exists
2. The exact user experience from start to finish
3. The complete technical architecture
4. Every AI model used and why
5. Every external API integrated and how
6. The full database schema
7. The complete API specification
8. The frontend component architecture
9. The multi-agent system design
10. Error handling, caching, security, and testing strategies
11. What makes this system unique and superior

This system is designed to be:
- **Implementable** — Every component is specified with clear inputs, outputs, and technologies
- **Cost-efficient** — Model selection is optimized, caching is aggressive
- **Production-quality** — Not a demo, but a real product that real users would use
- **Extensible** — Clean architecture allows adding new agents, platforms, and features

---

*End of ReelTrip Master Documentation v2.0*
