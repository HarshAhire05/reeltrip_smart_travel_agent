# Bug Fix: "View Itinerary" Button Not Showing

## Issue

After all agents completed itinerary generation, the "View Itinerary" button was not appearing.

## Root Cause

The `complete` SSE event was being sent by the backend, but the `itinerary_id` was sometimes `None` when Supabase storage failed. This caused the frontend condition to fail:

```typescript
const isComplete = completedCount === AGENTS.length && itineraryId;
```

Even though all 8 agents completed successfully, `itineraryId` was falsy, so the button didn't render.

## Fix Applied

### Backend (`backend/main.py` lines 263-295)

**Before:**

- When Supabase storage failed, `itinerary_id` was set to temp value
- But the `complete` event could still send `None` if no storage was attempted
- The completion event might send `{"itinerary_id": null, ...}`

**After:**

```python
# ALWAYS send completion event even if storage failed
# Ensure itinerary_id is never None
final_itinerary_id = itinerary_id if itinerary_id else f"temp-{session_id}"
completion_data = {
    "itinerary_id": final_itinerary_id,
    "session_id": session_id
}
yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
logger.info(f"Itinerary generation complete for session {session_id}, itinerary_id: {final_itinerary_id}")
```

**Key Changes:**

1. ✅ **Guaranteed non-null ID**: Added fallback to ensure `itinerary_id` is ALWAYS set to either:
   - Real Supabase ID (when storage succeeds)
   - Temp ID `temp-{session_id}` (when storage fails or wasn't attempted)

2. ✅ **Better Logging**: Added info log with the final itinerary_id to help debugging

3. ✅ **Explicit Temp ID on Storage Failure**: When Supabase storage fails, explicitly set `itinerary_id = f"temp-{session_id}"` and log it

### Frontend (Debug Logging Added)

Added console logging to help diagnose future issues:

**`frontend/app/trip/[sessionId]/page.tsx`** (lines 212-220):

```typescript
case "complete": {
  const d = event.data as { itinerary_id: string; session_id: string; };
  console.log("[TripPage] Complete event received, itinerary_id:", d.itinerary_id);
  setItineraryId(d.itinerary_id);
  setIsGenerating(false);
  console.log("[TripPage] Itinerary ID set, flowStep should remain:", useStore.getState().flowStep);
  break;
}
```

**`frontend/components/preferences/GenerationProgress.tsx`** (lines 32-51):

```typescript
console.log("[GenerationProgress] Render:", {
  completedCount,
  totalAgents: AGENTS.length,
  itineraryId,
  isComplete,
  agentStatuses: agentStatuses.map((a) => ({
    agent: a.agent,
    status: a.status,
  })),
});
```

## How to Verify Fix

1. **Start backend server:**

   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start frontend dev server:**

   ```bash
   cd frontend
   npm run dev
   ```

3. **Generate an itinerary:**
   - Enter text: "I want to visit Goa"
   - Complete the preference form
   - Click "Plan My Trip"

4. **Check console logs:**
   - You should see: `[TripPage] Complete event received, itinerary_id: temp-xxxxx` or `itinerary_id: <uuid>`
   - You should see: `[GenerationProgress] Render: { completedCount: 8, itineraryId: "temp-..." }`

5. **Verify button appears:**
   - After all 8 agents show ✅ complete
   - The "View Itinerary" button should appear at the bottom
   - Button should navigate to `/trip/{sessionId}/itinerary`

## Expected Behavior

✅ **With Supabase Working:**

- Backend stores itinerary successfully
- Sends `complete` event with real UUID
- Button appears immediately after assembler finishes

✅ **Without Supabase (Current State):**

- Backend attempts storage, fails with warning
- Generates temp ID: `temp-{session_id}`
- Sends `complete` event with temp ID
- Button still appears (because ID is truthy)
- User can view itinerary (data is in store, just not persisted)

## Files Modified

1. `backend/main.py` - Fixed completion event to always send valid itinerary_id
2. `frontend/app/trip/[sessionId]/page.tsx` - Added debug logging
3. `frontend/components/preferences/GenerationProgress.tsx` - Added debug logging

## Related Issues

- ✅ Supabase connection errors (non-blocking fallbacks already implemented)
- ✅ Async/await error in hotel agent (already fixed)
- ✅ Pydantic validation error for estimated_cost_usd (already fixed)
