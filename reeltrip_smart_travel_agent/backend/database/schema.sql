-- ============================================================
-- ReelTrip Database Schema
-- Run this ONCE in the Supabase SQL Editor (Dashboard -> SQL)
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
