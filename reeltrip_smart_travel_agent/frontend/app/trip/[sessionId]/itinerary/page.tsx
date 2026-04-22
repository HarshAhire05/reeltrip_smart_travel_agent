"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2, AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ItineraryHeader } from "@/components/itinerary/ItineraryHeader";
import { TabNavigation } from "@/components/itinerary/TabNavigation";
import { ReservationsTab } from "@/components/itinerary/ReservationsTab";
import { DayTimeline } from "@/components/itinerary/DayTimeline";
import { MiscellaneousTab } from "@/components/itinerary/MiscellaneousTab";
import { CustomizeChat } from "@/components/itinerary/CustomizeChat";
import { EditTripPanelContainer } from "@/components/itinerary/EditTripPanelContainer";
import { useStore } from "@/lib/store";
import { API_BASE } from "@/lib/api";

export default function ItineraryPage() {
  const router = useRouter();
  const contentRef = useRef<HTMLDivElement>(null);
  const fetchedRef = useRef(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const {
    itinerary,
    itineraryId,
    sessionId,
    activeTab,
    setItinerary,
    setActiveTab,
  } = useStore();

  console.log("[ItineraryPage] Itinerary loaded:", !!itinerary, "days:", itinerary?.days?.length);

  // Fetch itinerary if not in store
  useEffect(() => {
    if (itinerary || fetchedRef.current) return;
    fetchedRef.current = true;

    if (!itineraryId) {
      if (sessionId) {
        router.push(`/trip/${sessionId}`);
      } else {
        router.push("/");
      }
      return;
    }

    const fetchItinerary = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/itinerary/${itineraryId}`
        );
        if (res.ok) {
          const data = await res.json();
          setItinerary(data.itinerary);
        } else {
          setFetchError("Failed to load itinerary. The server returned an error.");
        }
      } catch {
        setFetchError("Could not connect to the server. Please check your connection.");
      }
    };

    fetchItinerary();
  }, [itinerary, itineraryId, sessionId, router, setItinerary]);

  // Scroll to top on tab change
  useEffect(() => {
    contentRef.current?.scrollTo(0, 0);
  }, [activeTab]);

  const handleRetry = () => {
    setFetchError(null);
    fetchedRef.current = false;
  };

  // Error state
  if (fetchError) {
    return (
      <div className="animated-gradient-bg min-h-screen flex items-center justify-center px-4">
        <motion.div
          className="glass-card flex w-full max-w-sm flex-col items-center gap-4 p-6 text-center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/20">
            <AlertCircle className="h-6 w-6 text-error" />
          </div>
          <p className="text-sm text-text-secondary">{fetchError}</p>
          <Button
            onClick={handleRetry}
            variant="outline"
            className="gap-2 border-glass-border"
          >
            <RotateCcw className="h-4 w-4" />
            Try Again
          </Button>
        </motion.div>
      </div>
    );
  }

  // Loading state
  if (!itinerary) {
    return (
      <div className="animated-gradient-bg min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 text-accent-purple spin-slow" />
          <p className="text-sm text-text-secondary">Loading itinerary...</p>
        </div>
      </div>
    );
  }

  // Determine which day to show
  const activeDayNumber = activeTab.startsWith("day-")
    ? parseInt(activeTab.split("-")[1], 10)
    : null;
  const activeDay = activeDayNumber
    ? (itinerary.days ?? []).find((d) => d.day_number === activeDayNumber)
    : null;

  return (
    <div className="animated-gradient-bg min-h-screen">
      <div className="mx-auto max-w-3xl px-4 py-8">
        {/* Header */}
        <ItineraryHeader itinerary={itinerary} />

        {/* Tabs */}
        <div className="mt-4">
          <TabNavigation
            days={itinerary.days ?? []}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </div>

        {/* Content */}
        <motion.div
          ref={contentRef}
          className="mt-6"
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "reservations" && (
            <ReservationsTab
              flights={itinerary.flights ?? []}
              hotels={itinerary.hotels ?? []}
              itineraryStartDate={itinerary.start_date}
              itineraryEndDate={itinerary.end_date}
            />
          )}

          {activeDay && <DayTimeline day={activeDay} />}

          {activeTab === "misc" && (
            <MiscellaneousTab itinerary={itinerary} />
          )}
        </motion.div>
      </div>

      {/* Customize chat overlay */}
      <CustomizeChat />

      {/* Edit Trip Details Panel */}
      <EditTripPanelContainer />
    </div>
  );
}
