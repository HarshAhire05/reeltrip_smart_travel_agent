"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProgressTracker } from "@/components/processing/ProgressTracker";
import { VideoPreview } from "@/components/processing/VideoPreview";
import { LocationCard } from "@/components/processing/LocationCard";
import { HighlightsSheet } from "@/components/highlights/HighlightsSheet";
import { BucketListSelector } from "@/components/highlights/BucketListSelector";
import { PreferenceForm } from "@/components/preferences/PreferenceForm";
import { CitySelector } from "@/components/preferences/CitySelector";
import { GenerationProgress } from "@/components/preferences/GenerationProgress";
import { useStore } from "@/lib/store";
import { streamPost } from "@/lib/sse";
import { API_BASE } from "@/lib/api";
import type { AnalysisEvent, HighlightsEvent } from "@/lib/types";

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
    setError,
    reset,
    setFlowStep,
    setShowCitySelector,
    setIsGenerating,
    updateAgentStatus,
    setItinerary,
    setItineraryId,
  } = useStore();

  console.log("[TripPage] Render — url:", useStore.getState().url, "flowStep:", flowStep);

  // Video processing SSE
  useEffect(() => {
    const videoUrl = useStore.getState().url;
    if (!videoUrl) {
      router.push("/");
      return;
    }

    console.log("[TripPage] Starting pipeline for:", videoUrl);
    const abortController = new AbortController();
    processingAbortRef.current = abortController;

    const store = useStore.getState;

    streamPost(
      `${API_BASE}/api/v1/process`,
      { url: videoUrl },
      (event) => {
        console.log("[TripPage] SSE event received:", event.event);
        switch (event.event) {
          case "session":
            store().startProcessing(
              (event.data as { session_id: string }).session_id
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
            store().setMetadata(
              event.data as {
                title: string;
                thumbnail_url: string;
                platform: string;
                duration: number;
              }
            );
            break;
          case "analysis":
            store().setAnalysis(event.data as AnalysisEvent);
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
      abortController.signal
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
              }
            );
            break;
          case "itinerary":
            setItinerary(
              event.data as Parameters<typeof setItinerary>[0]
            );
            break;
          case "complete": {
            const d = event.data as {
              itinerary_id: string;
              session_id: string;
            };
            setItineraryId(d.itinerary_id);
            setIsGenerating(false);
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
      abortController.signal
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
    reset();
    useStore.getState().setUrl(savedUrl);
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

        {/* Processing / highlights state */}
        {showProcessingUI && !error && (
          <>
            {(isProcessing || stage === "idle") && <ProgressTracker />}
            {videoTitle && <VideoPreview />}
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
