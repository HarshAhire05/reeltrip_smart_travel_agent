/**
 * API client for itinerary re-planning
 */
import { streamPost } from "./sse";
import { API_BASE } from "./api";
import type { UserPreferences, TripItinerary, AgentProgress } from "./types";

export interface ReplanPayload {
  session_id: string;
  original_params: UserPreferences;
  updated_params: UserPreferences;
  changed_fields: string[];
  existing_itinerary: TripItinerary;
  selected_cities?: string[];
}

export interface ReplanEventHandlers {
  onAgentProgress?: (progress: AgentProgress) => void;
  onWarning?: (warning: { type: string; message: string }) => void;
  onAgentError?: (error: { agent: string; message: string }) => void;
  onItinerary?: (data: {
    itinerary: TripItinerary;
    changed_sections: string[];
    version: number;
  }) => void;
  onComplete?: (data: {
    itinerary_id: string;
    session_id: string;
    version: number;
  }) => void;
  onError?: (error: Error) => void;
}

/**
 * Call the re-plan endpoint with SSE streaming
 */
export async function replanItinerary(
  payload: ReplanPayload,
  handlers: ReplanEventHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const url = `${API_BASE}/api/v1/itinerary/replan`;

  return streamPost(
    url,
    payload,
    (event) => {
      switch (event.event) {
        case "replan_start": {
          const data = event.data as {
            changed_fields: string[];
            skip_agents: string[];
            run_agents: string[];
            reason: string;
          };
          console.log("[Replan] Starting:", data.reason);
          break;
        }

        case "agent_progress": {
          const data = event.data as AgentProgress;
          handlers.onAgentProgress?.(data);
          break;
        }

        case "warning": {
          const data = event.data as {
            type: string;
            message: string;
            minimum_budget?: number;
            current_budget?: number;
          };
          handlers.onWarning?.(data);
          break;
        }

        case "agent_error": {
          const data = event.data as {
            agent: string;
            message: string;
          };
          handlers.onAgentError?.(data);
          break;
        }

        case "itinerary": {
          const data = event.data as {
            itinerary: TripItinerary;
            changed_sections: string[];
            version: number;
          };
          handlers.onItinerary?.(data);
          break;
        }

        case "complete": {
          const data = event.data as {
            itinerary_id: string;
            session_id: string;
            version: number;
            summary?: string;
          };
          handlers.onComplete?.(data);
          break;
        }

        case "error": {
          const data = event.data as { message: string };
          handlers.onError?.(new Error(data.message));
          break;
        }

        default:
          console.log("[Replan] Unknown event:", event.event, event.data);
      }
    },
    handlers.onError,
    undefined,
    signal,
  );
}

/**
 * Helper to check if re-plan is needed (has changes)
 */
export function hasPreferenceChanges(
  original: UserPreferences | null,
  updated: UserPreferences | null,
): boolean {
  if (!original || !updated) return false;

  // Simple JSON comparison (not perfect but works for most cases)
  return JSON.stringify(original) !== JSON.stringify(updated);
}

/**
 * Helper to validate re-plan payload before sending
 */
export function validateReplanPayload(payload: ReplanPayload): {
  valid: boolean;
  error?: string;
} {
  if (!payload.session_id?.trim()) {
    return { valid: false, error: "Session ID is required" };
  }

  if (!payload.updated_params) {
    return { valid: false, error: "Updated preferences are required" };
  }

  if (!payload.existing_itinerary) {
    return { valid: false, error: "Existing itinerary is required" };
  }

  if (!payload.changed_fields || payload.changed_fields.length === 0) {
    return { valid: false, error: "No changes detected" };
  }

  return { valid: true };
}
