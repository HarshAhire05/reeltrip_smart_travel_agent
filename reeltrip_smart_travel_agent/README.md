# ReelTrip

ReelTrip is an AI-powered travel planning app that transforms travel videos (Instagram Reels, YouTube Shorts, TikTok) into complete, personalized trip itineraries. Paste a video URL, and ReelTrip extracts destinations using computer vision and audio transcription, then generates a day-by-day itinerary with flights, hotels, activities, restaurants, budget breakdown, and booking links — all streamed in real-time.

## Tech Stack

**Backend**
- Python 3.11+ with FastAPI + Uvicorn
- OpenAI GPT-4o (vision, reasoning) + GPT-4o-mini (fast tasks) + Whisper (transcription)
- yt-dlp for video extraction
- ffmpeg for audio/frame processing
- Google Places API for location validation
- Tavily for real-time web search (flights, prices, safety)
- Open-Meteo for weather forecasts (free, no key needed)
- Supabase (PostgreSQL) for caching and persistence
- Server-Sent Events (SSE) for real-time streaming

**Frontend**
- Next.js 16 (App Router) with React 19
- TypeScript
- Tailwind CSS 4 with glass-morphism design
- Zustand for state management
- Framer Motion for animations
- shadcn/ui components

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **ffmpeg** — must be installed and available on PATH
- **Supabase** account (free tier works)
- **API Keys** — OpenAI, Google Places, Tavily (optional), ExchangeRate-API (optional)

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Supabase Database

Create a new Supabase project and run the schema SQL:

```bash
# Copy the contents of backend/database/schema.sql
# and execute it in your Supabase SQL Editor
```

### 4. Environment Variables

**Backend** — create `backend/.env`:

```env
OPENAI_API_KEY=sk-...
GOOGLE_PLACES_API_KEY=AIza...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
TAVILY_API_KEY=tvly-...          # Optional but recommended
EXCHANGERATE_API_KEY=...         # Optional
```

**Frontend** — create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for GPT-4o, GPT-4o-mini, Whisper |
| `GOOGLE_PLACES_API_KEY` | Yes | — | Google Places API (New) for location search |
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | — | Supabase anonymous/public key |
| `TAVILY_API_KEY` | No | — | Tavily web search for flight/hotel pricing |
| `EXCHANGERATE_API_KEY` | No | — | ExchangeRate-API for currency conversion |
| `INSTAGRAM_COOKIES_PATH` | No | `./cookies.txt` | Path to Instagram cookies file |
| `DEFAULT_CURRENCY` | No | `INR` | Default currency for budget |
| `DEFAULT_HOME_CITY` | No | `Mumbai` | Default departure city |
| `MAX_FRAME_COUNT` | No | `5` | Max video frames to extract for vision |
| `VISION_MODEL` | No | `gpt-4o` | OpenAI model for vision analysis |
| `REASONING_MODEL` | No | `gpt-4o` | OpenAI model for complex reasoning |
| `FAST_MODEL` | No | `gpt-4o-mini` | OpenAI model for fast/cheap tasks |
| `ENABLE_CACHE` | No | `true` | Enable Supabase caching |
| `ENABLE_VISION` | No | `true` | Enable GPT-4o vision analysis |
| `ENABLE_TAVILY` | No | `true` | Enable Tavily web search |
| `ENABLE_WEATHER` | No | `true` | Enable weather integration |
| `BACKEND_HOST` | No | `0.0.0.0` | Backend server host |
| `BACKEND_PORT` | No | `8000` | Backend server port |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for CORS |

## How to Run

**Start the backend:**

```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

**Start the frontend (in a separate terminal):**

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser, paste a travel video URL, and let ReelTrip plan your trip.
