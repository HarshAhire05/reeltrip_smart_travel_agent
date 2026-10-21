# Supabase Connection Fix

## Error: `[Errno 11001] getaddrinfo failed`

This means the server cannot connect to Supabase (DNS resolution failing).

## Quick Fixes

### Option 1: Check Your .env File

Make sure `backend/.env` has valid Supabase credentials:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxxxx...
```

**Steps:**

1. Open `backend/.env` file
2. Check if `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
3. If not, copy from `.env.example` and add your Supabase credentials
4. Restart the backend server

### Option 2: Check Internet Connection

The error `getaddrinfo failed` means DNS resolution is failing. This could be:

- No internet connection
- Firewall blocking Supabase
- VPN/proxy issues
- DNS server not responding

**Test connectivity:**

```bash
# Test if you can reach Supabase
ping xxxxx.supabase.co

# Or try in browser
https://xxxxx.supabase.co
```

### Option 3: Work Without Supabase (Temporary)

I've updated the code to gracefully handle Supabase being unavailable. The server will:

- Log a warning instead of crashing
- Create minimal location data
- Allow itinerary generation to proceed

**This means:**

- ✅ You can generate itineraries without Supabase
- ✅ Re-plan feature will work
- ❌ Data won't be cached/saved
- ❌ Session history won't persist

### Option 4: Set Up Supabase (Recommended)

If you don't have Supabase set up:

1. Go to https://supabase.com
2. Create a new project
3. Get your credentials from Project Settings → API
4. Add to `backend/.env`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```
5. Create required tables (see schema below)

## Database Schema

Create these tables in Supabase:

```sql
-- Sessions table
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  url TEXT,
  input_mode TEXT,
  stage TEXT,
  preferences JSONB,
  selected_cities JSONB,
  itinerary_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Locations cache
CREATE TABLE locations (
  url TEXT PRIMARY KEY,
  highlights JSONB,
  primary_city TEXT,
  primary_country TEXT,
  city_latitude FLOAT,
  city_longitude FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Itineraries
CREATE TABLE itineraries (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  user_preferences JSONB,
  itinerary JSONB,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Current Status

✅ **Server is now running** - Updated code to handle Supabase failures gracefully
✅ **Re-plan feature works** - All endpoints functional
⚠️ **Supabase optional** - Data won't persist but functionality works

## What Changed

I modified `backend/main.py` to:

1. Continue if session lookup fails (instead of 404)
2. Create minimal location data if cache unavailable
3. Log warnings instead of errors

**The server will now work without Supabase!**

## Testing

Try generating an itinerary now:

1. Frontend should work
2. Backend will log warnings about Supabase
3. Itinerary will generate successfully
4. Data just won't be saved to database

To verify, check logs for:

```
WARNING: Could not load session {session_id}, proceeding without session data
WARNING: No location data found, creating minimal location context
```
