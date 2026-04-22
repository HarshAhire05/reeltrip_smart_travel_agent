"""
ReelTrip API — FastAPI application entry point.
"""
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from config import get_settings
from models.api import HealthResponse
from models.text_input import TextInputRequest
from models.preferences import UserPreferences
from models.itinerary import TripItinerary
from models.replan import ReplanRequest
from pipeline.orchestrator import run_pipeline
from pipeline.text_processor import TextProcessor
from agents.orchestrator import run_travel_planner_streaming
from agents.replan_orchestrator import run_replan_orchestrator
from agents.state import TravelPlannerState
from services.supabase_client import (
    get_session, get_cached_location, update_session,
    store_itinerary, get_itinerary, update_itinerary,
)
from services.openai_client import call_openai_json
import json
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="ReelTrip API",
    description="AI-powered travel planning from short-form travel videos",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="reeltrip-api")


@app.post("/api/v1/process")
async def process_video(request: Request):
    """
    Process a video URL through the pipeline (Stages 1-4).
    Returns SSE stream with progress events.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    url = body.get("url", "").strip()

    if not url:
        return JSONResponse(status_code=400, content={"error": "URL is required"})

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
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/process-text")
async def process_text_input(request: Request):
    """
    Process text-based travel intent (alternative to video processing).
    Returns SSE stream with progress events and highlights.
    
    Body: {"text": "I want to visit Dubai", "session_id": "optional-uuid"}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    text_input = body.get("text", "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())
    
    if not text_input:
        return JSONResponse(status_code=400, content={"error": "text is required"})
    
    if len(text_input) < 3:
        return JSONResponse(
            status_code=400,
            content={"error": "Please provide a more detailed travel description"}
        )
    
    # Initialize text processor
    text_processor = TextProcessor()
    
    async def event_stream():
        try:
            # Stream SSE events from text processor
            async for event_str in text_processor.process_stream(text_input, session_id):
                yield event_str
        except Exception as e:
            logger.error(f"Text processing stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/session/{session_id}")
async def get_session_data(session_id: str):
    """Return session data from Supabase."""
    session = await get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return session


@app.get("/api/v1/highlights")
async def get_highlights(url: str = Query(..., description="Video URL to get highlights for")):
    """Return cached highlights by URL."""
    location = await get_cached_location(url)
    if not location:
        return JSONResponse(status_code=404, content={"error": "No highlights found for this URL"})

    highlights = location.get("highlights", [])
    if isinstance(highlights, str):
        highlights = json.loads(highlights)

    return {
        "highlights": highlights,
        "primary_city": location.get("primary_city", ""),
        "primary_country": location.get("primary_country", ""),
        "city_latitude": location.get("city_latitude"),
        "city_longitude": location.get("city_longitude"),
    }


# =============================================
# PHASE 4: ITINERARY PLANNING ENDPOINTS
# =============================================


@app.post("/api/v1/itinerary/preferences")
async def create_itinerary(request: Request):
    """
    Generate a full itinerary from user preferences.
    Returns SSE stream with agent progress events and final itinerary.

    Body: {"session_id": "...", "preferences": {...}, "selected_cities": [...]}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    session_id = body.get("session_id", "").strip()
    preferences = body.get("preferences", {})
    selected_cities = body.get("selected_cities", [])

    if not session_id:
        return JSONResponse(status_code=400, content={"error": "session_id is required"})
    if not preferences:
        return JSONResponse(status_code=400, content={"error": "preferences are required"})

    # Load session to get the video URL
    session = await get_session(session_id)
    if not session:
        # If Supabase is down, allow the request to proceed without session data
        # The agents can still work with just preferences and selected_cities
        logger.warning(f"Could not load session {session_id}, proceeding without session data")
        url = ""
    else:
        url = session.get("url", "")

    # Load cached location result
    location_result = await get_cached_location(url) if url else None
    if not location_result:
        # Create a minimal location result if cache is unavailable
        logger.warning("No location data found, creating minimal location context")
        location_result = {
            "primary_city": selected_cities[0] if selected_cities else "Unknown",
            "primary_country": "Unknown",
            "city_latitude": 0.0,
            "city_longitude": 0.0,
            "highlights": []
        }

    # Parse highlights
    highlights = location_result.get("highlights", [])
    if isinstance(highlights, str):
        highlights = json.loads(highlights)

    # If no selected_cities, use primary city
    if not selected_cities:
        primary_city = location_result.get("primary_city", "")
        if primary_city:
            selected_cities = [primary_city]

    # Build initial state
    state: TravelPlannerState = {
        "location_result": location_result,
        "user_preferences": preferences,
        "highlights": highlights,
        "selected_cities": selected_cities,
        "flight_data": None,
        "hotel_data": None,
        "weather_data": None,
        "safety_data": None,
        "activity_data": None,
        "transport_data": None,
        "budget_analysis": None,
        "itinerary": None,
        "agent_errors": [],
        "progress_updates": [],
    }

    # Update session with preferences
    await update_session(session_id, {
        "preferences": json.dumps(preferences) if isinstance(preferences, dict) else preferences,
        "selected_cities": json.dumps(selected_cities) if isinstance(selected_cities, list) else selected_cities,
        "stage": "planning",
    })

    async def event_stream():
        itinerary_id = None
        try:
            async for event in run_travel_planner_streaming(state):
                event_name = event.get("event", "message")
                event_data = json.dumps(event.get("data", {}))
                yield f"event: {event_name}\ndata: {event_data}\n\n"

                # If itinerary was generated, try to store it
                if event_name == "itinerary" and event.get("data"):
                    try:
                        stored_id = await store_itinerary({
                            "url": url,
                            "session_id": session_id,
                            "user_preferences": preferences,
                            "selected_cities": selected_cities,
                            "itinerary": event["data"],
                        })
                        if stored_id:
                            itinerary_id = stored_id
                            await update_session(session_id, {
                                "itinerary_id": itinerary_id,
                                "stage": "itinerary",
                            })
                            logger.info(f"Stored itinerary with ID: {itinerary_id}")
                    except Exception as e:
                        # Storage failed but don't block the response
                        logger.warning(f"Could not store itinerary (Supabase unavailable): {e}")
                        # Generate a temporary ID so the frontend can still work
                        itinerary_id = f"temp-{session_id}"
                        logger.info(f"Using temporary itinerary ID: {itinerary_id}")

            # ALWAYS send completion event even if storage failed
            # Ensure itinerary_id is never None
            final_itinerary_id = itinerary_id if itinerary_id else f"temp-{session_id}"
            completion_data = {
                "itinerary_id": final_itinerary_id,
                "session_id": session_id
            }
            yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
            logger.info(f"Itinerary generation complete for session {session_id}, itinerary_id: {final_itinerary_id}")

        except Exception as e:
            logger.error(f"Itinerary generation error: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/itinerary/customize")
async def customize_itinerary(request: Request):
    """
    Customize an existing itinerary based on a natural language request.
    Returns SSE stream with the updated itinerary.

    Body: {"session_id": "...", "itinerary_id": "...", "request": "..."}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    session_id = body.get("session_id", "").strip()
    itinerary_id = body.get("itinerary_id", "").strip()
    user_request = body.get("request", "").strip()

    if not itinerary_id:
        return JSONResponse(status_code=400, content={"error": "itinerary_id is required"})
    if not user_request:
        return JSONResponse(status_code=400, content={"error": "request is required"})

    # Load existing itinerary
    itinerary_record = await get_itinerary(itinerary_id)
    if not itinerary_record:
        return JSONResponse(status_code=404, content={"error": "Itinerary not found"})

    current_itinerary = itinerary_record.get("itinerary", {})
    if isinstance(current_itinerary, str):
        current_itinerary = json.loads(current_itinerary)

    current_version = itinerary_record.get("version", 1)
    preferences = itinerary_record.get("user_preferences", {})
    if isinstance(preferences, str):
        preferences = json.loads(preferences)

    async def event_stream():
        yield f"event: customizing\ndata: {json.dumps({'message': 'Understanding your request...'})}\n\n"

        system_prompt = """You are an expert travel itinerary modifier.
Given an existing itinerary and a modification request, update the itinerary accordingly.

RULES:
1. Only modify what the user asks — keep everything else the same
2. Recalculate affected timings, costs, and budget breakdown
3. Maintain the same JSON structure as the input
4. Ensure the modified itinerary is still physically possible
5. If replacing an activity, ensure the replacement fits the time slot

Respond in JSON format ONLY. Return the COMPLETE updated itinerary."""

        user_prompt = f"""Current itinerary:
{json.dumps(current_itinerary, indent=2)[:8000]}

User preferences:
{json.dumps(preferences, indent=2)[:1000]}

MODIFICATION REQUEST: {user_request}

Return the COMPLETE updated itinerary JSON with the modification applied.
Maintain the exact same schema structure."""

        yield f"event: customizing\ndata: {json.dumps({'message': 'Updating your itinerary...'})}\n\n"

        updated = await call_openai_json(
            task="reasoning",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192,
            temperature=0.3,
        )

        if updated:
            new_version = current_version + 1
            await update_itinerary(itinerary_id, {
                "itinerary": updated,
                "version": new_version,
            })

            yield f"event: itinerary\ndata: {json.dumps(updated)}\n\n"
            yield f"event: complete\ndata: {json.dumps({'itinerary_id': itinerary_id, 'version': new_version})}\n\n"
        else:
            yield f"event: error\ndata: {json.dumps({'message': 'Could not process your customization request. Please try again.'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/itinerary/replan")
async def replan_itinerary(request: Request):
    """
    Re-plan an existing itinerary by selectively re-running agents based on changed fields.
    Returns SSE stream with agent progress events and updated itinerary.
    
    Body: {
        "session_id": "...",
        "original_params": {...UserPreferences...},
        "updated_params": {...UserPreferences...},
        "changed_fields": ["total_budget", "accommodation_tier"],
        "existing_itinerary": {...TripItinerary...},
        "selected_cities": [...]
    }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    session_id = body.get("session_id", "").strip()
    original_params_dict = body.get("original_params", {})
    updated_params_dict = body.get("updated_params", {})
    changed_fields = body.get("changed_fields", [])
    existing_itinerary_dict = body.get("existing_itinerary", {})
    selected_cities = body.get("selected_cities", [])
    
    # Validation
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "session_id is required"})
    if not updated_params_dict:
        return JSONResponse(status_code=400, content={"error": "updated_params is required"})
    if not existing_itinerary_dict:
        return JSONResponse(status_code=400, content={"error": "existing_itinerary is required"})
    if not changed_fields:
        return JSONResponse(status_code=400, content={"error": "changed_fields is required (must specify what changed)"})
    
    # Parse Pydantic models
    try:
        original_params = UserPreferences(**original_params_dict)
        updated_params = UserPreferences(**updated_params_dict)
        existing_itinerary = TripItinerary(**existing_itinerary_dict)
    except Exception as e:
        logger.error(f"Failed to parse re-plan request: {e}")
        return JSONResponse(status_code=400, content={"error": f"Invalid data format: {str(e)}"})
    
    # Load session to get location data
    session = await get_session(session_id)
    if not session:
        logger.warning(f"Could not load session {session_id} for re-plan, using provided data only")
        url = ""
    else:
        url = session.get("url", "")
    
    # Load cached location result (needed for agent context)
    location_result = await get_cached_location(url) if url else None
    if not location_result:
        # Create minimal location context if unavailable
        logger.warning("No location data found for re-plan, creating minimal context")
        location_result = {
            "primary_city": selected_cities[0] if selected_cities else existing_itinerary.destination_cities[0] if existing_itinerary.destination_cities else "Unknown",
            "primary_country": existing_itinerary.destination_country or "Unknown",
            "city_latitude": 0.0,
            "city_longitude": 0.0,
            "highlights": []
        }
    
    # Parse highlights
    highlights = location_result.get("highlights", [])
    if isinstance(highlights, str):
        highlights = json.loads(highlights)
    
    # If no selected_cities provided, extract from existing itinerary
    if not selected_cities:
        selected_cities = existing_itinerary.destination_cities or []
    
    # Get current itinerary version (handle None session gracefully)
    current_itinerary_id = session.get("itinerary_id") if session else None
    current_version = 1
    if current_itinerary_id:
        try:
            current_record = await get_itinerary(current_itinerary_id)
            if current_record:
                current_version = current_record.get("version", 1)
        except Exception as e:
            logger.warning(f"Could not fetch itinerary version: {e}")
    
    logger.info(f"Re-plan request for session {session_id}: changed_fields={changed_fields}, current_version={current_version}")
    
    async def event_stream():
        itinerary_id = None
        new_version = current_version + 1
        
        try:
            async for event in run_replan_orchestrator(
                session_id=session_id,
                original_params=original_params,
                updated_params=updated_params,
                changed_fields=changed_fields,
                existing_itinerary=existing_itinerary,
                location_result=location_result,
                highlights=highlights,
                selected_cities=selected_cities,
            ):
                event_name = event.get("event", "message")
                event_data = event.get("data", {})
                
                # If this is the itinerary event, store it
                if event_name == "itinerary" and event_data.get("itinerary"):
                    # Update version in the data
                    event_data["version"] = new_version
                    
                    # Try to store updated itinerary in Supabase
                    try:
                        itinerary_id = await store_itinerary({
                            "url": url,
                            "session_id": session_id,
                            "user_preferences": updated_params.model_dump(),
                            "selected_cities": selected_cities,
                            "itinerary": event_data["itinerary"],
                            "version": new_version,
                        })
                        
                        if itinerary_id:
                            await update_session(session_id, {
                                "itinerary_id": itinerary_id,
                                "preferences": json.dumps(updated_params.model_dump()),
                                "stage": "itinerary",
                            })
                    except Exception as e:
                        # Storage failed but don't block the response
                        logger.warning(f"Could not store re-planned itinerary (Supabase unavailable): {e}")
                        # Generate a temporary ID so the frontend can still work
                        itinerary_id = f"temp-replan-{session_id}-v{new_version}"
                
                # Stream event to frontend
                yield f"event: {event_name}\ndata: {json.dumps(event_data)}\n\n"
            
            # Send completion event
            yield f"event: complete\ndata: {json.dumps({'itinerary_id': itinerary_id, 'session_id': session_id, 'version': new_version})}\n\n"
        
        except Exception as e:
            logger.error(f"Re-plan error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': f'Re-plan failed: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/itinerary/{itinerary_id}")
async def get_itinerary_data(itinerary_id: str):
    """Return itinerary JSON from Supabase."""
    record = await get_itinerary(itinerary_id)
    if not record:
        return JSONResponse(status_code=404, content={"error": "Itinerary not found"})

    itinerary = record.get("itinerary", {})
    if isinstance(itinerary, str):
        itinerary = json.loads(itinerary)

    return {
        "id": record.get("id", itinerary_id),
        "session_id": record.get("session_id", ""),
        "version": record.get("version", 1),
        "itinerary": itinerary,
        "created_at": record.get("created_at", ""),
        "updated_at": record.get("updated_at", ""),
    }


@app.post("/api/v1/cities/suggest")
async def suggest_cities(request: Request):
    """
    Suggest additional cities to visit based on destination and preferences.

    Body: {"destination_country": "...", "destination_city": "...", "trip_duration_days": 5, "vibe": "..."}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    country = body.get("destination_country", "")
    city = body.get("destination_city", "")
    duration = body.get("trip_duration_days", 3)
    vibe = body.get("vibe", "")

    if not country and not city:
        return JSONResponse(status_code=400, content={"error": "destination_country or destination_city required"})

    result = await call_openai_json(
        task="fast",
        system_prompt="You are a travel destination expert. Suggest cities to visit based on the destination and trip details. Respond in JSON format ONLY.",
        user_prompt=f"""Suggest additional cities to visit for a {duration}-day trip.

Primary destination: {city}, {country}
Trip vibe: {vibe}
Duration: {duration} days

Return JSON:
{{
    "suggested_cities": [
        {{
            "city": "City Name",
            "country": "{country}",
            "why": "1 sentence why this city pairs well with {city}",
            "recommended_days": number_of_days_to_spend,
            "distance_from_primary": "approximate distance/travel time from {city}"
        }}
    ]
}}

Suggest 3-5 cities that:
- Are in {country} or a neighboring country
- Can be reached from {city} within 2-3 hours
- Complement the {vibe} vibe
- Are realistic to visit within a {duration}-day trip""",
        max_tokens=1024,
        temperature=0.5,
    )

    if result:
        return result

    return {"suggested_cities": []}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
