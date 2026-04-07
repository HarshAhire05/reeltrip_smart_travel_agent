"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProgressTracker } from "@/components/processing/ProgressTracker";
import { VideoPreview } from "@/components/processing/VideoPreview";
import { LocationCard } from "@/components/processing/LocationCard";
import { ClarificationCard } from "@/components/processing/ClarificationCard";
import { HighlightsSheet } from "@/components/highlights/HighlightsSheet";
import { BucketListSelector } from "@/components/highlights/BucketListSelector";
import { PreferenceForm } from "@/components/preferences/PreferenceForm";
import { CitySelector } from "@/components/preferences/CitySelector";
import { GenerationProgress } from "@/components/preferences/GenerationProgress";
import { useStore } from "@/lib/store";
import { streamPost } from "@/lib/sse";
import { API_BASE } from "@/lib/api";
import type {
  AnalysisEvent,
  HighlightsEvent,
  IntentClassification,
  ClarificationOption,
} from "@/lib/types";

export default function TripPage() {
  const router = useRouter();
  const processingAbortRef = useRef<AbortController | null>(null);
  const generationAbortRef = useRef<AbortController | null>(null);

  const {
    isProcessing,
    stage,
    error,
    highlights,
    videoTitle,
    destinationCity,
    flowStep,
    showCitySelector,
    sessionId,
    preferences,
    selectedCities,
    inputMode, // NEW: Track input mode
    textInput, // NEW: Text input
    needsClarification, // NEW: Clarification needed
    clarificationOptions, // NEW: Clarification options
    setError,
    reset,
    setFlowStep,
    setShowCitySelector,
    setIsGenerating,
    updateAgentStatus,
    setItinerary,
    setItineraryId,
    setIntentClassification, // NEW
    setClarificationOptions, // NEW
  } = useStore();

  console.log(
    "[TripPage] Render — inputMode:",
    inputMode,
    "flowStep:",
    flowStep,
  );

  // Processing SSE - handles both URL and text modes
  useEffect(() => {
    const videoUrl = useStore.getState().url;
    const userTextInput = useStore.getState().textInput;
    const mode = useStore.getState().inputMode;

    // Redirect if no input
    if (!videoUrl && !userTextInput) {
      router.push("/");
      return;
    }

    console.log("[TripPage] Starting pipeline for mode:", mode);
    const abortController = new AbortController();
    processingAbortRef.current = abortController;

    const store = useStore.getState;

    // Determine which endpoint to call based on input mode
    const endpoint =
      mode === "text"
        ? `${API_BASE}/api/v1/process-text`
        : `${API_BASE}/api/v1/process`;

    const requestBody =
      mode === "text" ? { text: userTextInput } : { url: videoUrl };

    streamPost(
      endpoint,
      requestBody,
      (event) => {
        console.log("[TripPage] SSE event received:", event.event);
        switch (event.event) {
          case "session":
            store().startProcessing(
              (event.data as { session_id: string }).session_id,
            );
            break;
          case "progress": {
            const p = event.data as {
              stage: string;
              percent: number;
              message: string;
            };
            store().updateProgress(p.stage, p.percent, p.message);
            break;
          }
          case "metadata":
            // Only for URL mode
            if (mode === "url") {
              store().setMetadata(
                event.data as {
                  title: string;
                  thumbnail_url: string;
                  platform: string;
                  duration: number;
                },
              );
            }
            break;
          case "analysis":
            // Only for URL mode
            if (mode === "url") {
              store().setAnalysis(event.data as AnalysisEvent);
            }
            break;
          case "intent_analysis":
            // Only for text mode
            if (mode === "text") {
              store().setIntentClassification(
                event.data as IntentClassification,
              );
            }
            break;
          case "clarification_needed":
            // Text mode clarification
            if (mode === "text") {
              const data = event.data as {
                message: string;
                options: ClarificationOption[];
              };
              store().setClarificationOptions(data.options);
              // TODO: Show clarification UI
              console.log("Clarification needed:", data.message, data.options);
            }
            break;
          case "highlights":
            store().setHighlights(event.data as HighlightsEvent);
            break;
          case "complete":
            store().setComplete();
            break;
          case "error":
            store().setError((event.data as { message: string }).message);
            break;
        }
      },
      (err) => {
        console.error("[TripPage] SSE error:", err.message);
        useStore.getState().setError(err.message);
      },
      undefined,
      abortController.signal,
    );

    return () => {
      console.log("[TripPage] Cleaning up SSE stream");
      abortController.abort();
    };
  }, [router]);

  // Start itinerary generation SSE
  const startGeneration = useCallback(() => {
    if (!sessionId || !preferences) return;
    console.log("[TripPage] Starting generation for session:", sessionId);
    setIsGenerating(true);
    setFlowStep("generating");

    // Abort any previous generation stream
    generationAbortRef.current?.abort();
    const abortController = new AbortController();
    generationAbortRef.current = abortController;

    streamPost(
      `${API_BASE}/api/v1/itinerary/preferences`,
      {
        session_id: sessionId,
        preferences,
        selected_cities: selectedCities,
      },
      (event) => {
        console.log("[TripPage] Generation event:", event.event);
        switch (event.event) {
          case "agent_progress":
            updateAgentStatus(
              event.data as {
                agent: string;
                status: "working" | "complete" | "failed";
                message: string;
              },
            );
            break;
          case "itinerary":
            setItinerary(event.data as Parameters<typeof setItinerary>[0]);
            break;
          case "complete": {
            const d = event.data as {
              itinerary_id: string;
              session_id: string;
            };
            console.log("[TripPage] Complete event received, itinerary_id:", d.itinerary_id);
            setItineraryId(d.itinerary_id);
            setIsGenerating(false);
            console.log("[TripPage] Itinerary ID set, flowStep should remain:", useStore.getState().flowStep);
            break;
          }
          case "error":
            setError((event.data as { message: string }).message);
            setIsGenerating(false);
            break;
        }
      },
      (err) => {
        setError(err.message);
        setIsGenerating(false);
      },
      undefined,
      abortController.signal,
    );
  }, [
    sessionId,
    preferences,
    selectedCities,
    setIsGenerating,
    setFlowStep,
    updateAgentStatus,
    setItinerary,
    setItineraryId,
    setError,
  ]);

  // Cleanup generation stream on unmount
  useEffect(() => {
    return () => {
      generationAbortRef.current?.abort();
    };
  }, []);

  const handleRetry = () => {
    const savedUrl = useStore.getState().url;
    const savedText = useStore.getState().textInput;
    const mode = useStore.getState().inputMode;
    reset();
    if (mode === "url") {
      useStore.getState().setUrl(savedUrl);
    } else {
      useStore.getState().setTextInput(savedText);
    }
    useStore.getState().setInputMode(mode);
    router.push(`/trip/${crypto.randomUUID()}`);
  };

  const handleClarificationSelect = async (destination: string) => {
    // User selected a destination - restart processing with refined text
    const store = useStore.getState();
    store.reset();
    store.setTextInput(`I want to visit ${destination}`);
    store.setInputMode("text");
    router.push(`/trip/${crypto.randomUUID()}`);
  };

  const handleCityConfirm = () => {
    setShowCitySelector(false);
    startGeneration();
  };

  const showProcessingUI =
    flowStep === "processing" || flowStep === "highlights";

  return (
    <div className="animated-gradient-bg min-h-screen px-4 py-12">
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-8">
        {/* Header */}
        <motion.h2
          className="gradient-text text-2xl font-bold"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          ReelTrip
        </motion.h2>

        {/* Error state */}
        {error && (
          <motion.div
            className="glass-card flex w-full max-w-sm flex-col items-center gap-4 p-6 text-center"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/20">
              <AlertCircle className="h-6 w-6 text-error" />
            </div>
            <p className="text-sm text-text-secondary">{error}</p>
            <Button
              onClick={handleRetry}
              variant="outline"
              className="gap-2 border-glass-border"
            >
              <RotateCcw className="h-4 w-4" />
              Try Again
            </Button>
          </motion.div>
        )}

        {/* Clarification needed (text mode only) */}
        {needsClarification && clarificationOptions.length > 0 && !error && (
          <ClarificationCard
            message="Which destination sounds right for you?"
            options={clarificationOptions}
            onSelect={handleClarificationSelect}
          />
        )}

        {/* Processing / highlights state */}
        {showProcessingUI && !error && !needsClarification && (
          <>
            {(isProcessing || stage === "idle") && <ProgressTracker />}
            {/* Only show video preview in URL mode */}
            {inputMode === "url" && videoTitle && <VideoPreview />}
            {destinationCity && <LocationCard />}
            {stage === "complete" && highlights.length === 0 && (
              <motion.div
                className="glass-card p-6 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <p className="text-text-secondary">Processing complete!</p>
              </motion.div>
            )}
            <HighlightsSheet />
          </>
        )}

        {/* Bucket list selection */}
        {flowStep === "bucketList" && !error && <BucketListSelector />}

        {/* Preference form */}
        {flowStep === "preferences" && !error && <PreferenceForm />}

        {/* Generation progress */}
        {flowStep === "generating" && !error && <GenerationProgress />}

        {/* City selector dialog */}
        <CitySelector
          open={showCitySelector}
          onOpenChange={setShowCitySelector}
          onConfirm={handleCityConfirm}
        />
      </div>
    </div>
  );
}
