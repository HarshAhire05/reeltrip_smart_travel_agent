"use client";

import { useCallback } from "react";
import { useStore } from "@/lib/store";
import { EditTripPanel } from "./EditTripPanel";
import { ReplanProgressTracker } from "./ReplanProgressTracker";
import { ChangeSummary } from "./ChangeSummary";
import { replanItinerary, validateReplanPayload } from "@/lib/replan";
import { calculateChangedFields } from "@/lib/validation";
import type { UserPreferences } from "@/lib/types";
import { toast } from "sonner";

export function EditTripPanelContainer() {
  const {
    sessionId,
    preferences,
    originalPreferences,
    itinerary,
    selectedCities,
    isReplanning,
    replanAgentStatuses,
    changedFields,
    setReplanning,
    updateReplanAgentStatus,
    setChangedFields,
    setItinerary,
    setItineraryId,
    pushItineraryVersion,
    setPreferences,
    saveOriginalPreferences,
  } = useStore();

  const handleReplan = useCallback(
    async (updatedPreferences: UserPreferences, fields: string[]) => {
      // Derive sessionId from URL if not in store
      const effectiveSessionId =
        sessionId ||
        (typeof window !== "undefined"
          ? window.location.pathname.split("/")[2]
          : null);

      // Derive selectedCities from itinerary if not in store
      const effectiveCities =
        selectedCities?.length > 0
          ? selectedCities
          : itinerary?.destination_cities || [];

      // Use effective preferences (from store or derived from itinerary)
      const effectivePreferences =
        preferences ||
        (itinerary
          ? {
              total_budget:
                (itinerary.budget_breakdown as any)?.total_budget_inr || 50000,
              currency: "INR",
              number_of_travelers: itinerary.total_travelers || 2,
              month_of_travel: new Date(itinerary.start_date).toLocaleString(
                "en",
                { month: "long" },
              ),
              travel_styles: ["relaxation"],
              dietary_preferences: "none",
              traveling_with: "partner" as const,
              accommodation_tier: "mid-range" as const,
              additional_notes: "",
            }
          : null);

      if (!effectiveSessionId || !itinerary || !effectivePreferences) {
        toast.error("Missing required data for re-plan");
        return;
      }

      // Save original preferences if not already saved
      if (!originalPreferences) {
        saveOriginalPreferences();
      }

      const payload = {
        session_id: effectiveSessionId,
        original_params: originalPreferences || effectivePreferences,
        updated_params: updatedPreferences,
        changed_fields: fields,
        existing_itinerary: itinerary,
        selected_cities: effectiveCities,
      };

      // Validate payload
      const validation = validateReplanPayload(payload);
      if (!validation.valid) {
        toast.error("Validation failed", {
          description: validation.error,
        });
        return;
      }

      // Push current itinerary to version stack before re-planning
      pushItineraryVersion(itinerary);

      // Set re-planning state
      setReplanning(true);
      setChangedFields(fields);

      // Show initial toast
      toast.info("Re-planning itinerary", {
        description: `Updating ${fields.length} changed ${fields.length === 1 ? "field" : "fields"}...`,
      });

      try {
        let updatedItinerary: any = null;
        let warningMessage: string | null = null;

        await replanItinerary(payload, {
          onAgentProgress: (progress) => {
            updateReplanAgentStatus(progress);
          },
          onWarning: (warning) => {
            warningMessage = warning.message;
            toast.warning(
              warning.type === "low_budget" ? "Low Budget Warning" : "Warning",
              {
                description: warning.message,
                duration: 8000,
              },
            );
          },
          onAgentError: (error) => {
            toast.error(`${error.agent} failed`, {
              description: error.message,
            });
          },
          onItinerary: (data) => {
            updatedItinerary = data.itinerary;
            setItinerary(data.itinerary);
          },
          onComplete: (data) => {
            setReplanning(false);
            setItineraryId(data.itinerary_id);

            // Update preferences to the new values
            setPreferences(updatedPreferences);

            // Show success toast
            toast.success("Itinerary updated!", {
              description: `Successfully re-planned based on your changes.`,
            });
          },
          onError: (error) => {
            console.error("[Replan Error]", error);
            setReplanning(false);

            // Rollback to previous itinerary from version stack
            const { itineraryVersions, undoItinerary } = useStore.getState();
            if (itineraryVersions.length > 0) {
              undoItinerary();
              toast.error("Re-plan failed", {
                description:
                  "Your previous itinerary has been restored. " + error.message,
                duration: 8000,
              });
            } else {
              toast.error("Re-plan failed", {
                description: error.message,
              });
            }
          },
        });
      } catch (error) {
        console.error("[Replan Error]", error);
        setReplanning(false);

        // Rollback
        const { itineraryVersions, undoItinerary } = useStore.getState();
        if (itineraryVersions.length > 0) {
          undoItinerary();
        }

        toast.error("Re-plan failed", {
          description: "An unexpected error occurred. Please try again.",
        });
      }
    },
    [
      sessionId,
      itinerary,
      preferences,
      originalPreferences,
      selectedCities,
      saveOriginalPreferences,
      pushItineraryVersion,
      setReplanning,
      setChangedFields,
      updateReplanAgentStatus,
      setItinerary,
      setItineraryId,
      setPreferences,
    ],
  );

  // Don't show if no itinerary
  if (!itinerary) {
    console.log("[EditTripPanelContainer] No itinerary - returning null");
    return null;
  }

  console.log("[EditTripPanelContainer] Rendering edit panel", {
    hasPreferences: !!preferences,
    hasItinerary: !!itinerary,
    hasSessionId: !!sessionId,
  });

  // If preferences are missing, we can still show the button
  // The edit panel will derive initial values from the itinerary
  return (
    <>
      <EditTripPanel onReplan={handleReplan} isReplanning={isReplanning} />

      {/* Re-plan Progress Modal */}
      <ReplanProgressTracker
        open={isReplanning}
        agentStatuses={replanAgentStatuses}
      />

      {/* Change Summary Banner (shown after successful re-plan) */}
      {changedFields.length > 0 && !isReplanning && (
        <ChangeSummary
          changedFields={changedFields}
          originalPreferences={originalPreferences || preferences}
          updatedPreferences={preferences}
          mode="banner"
        />
      )}
    </>
  );
}
