"use client";

import { useMemo } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { HighlightCard } from "./HighlightCard";
import { useStore } from "@/lib/store";

export function HighlightsSheet() {
  const { highlights, primaryCity, showHighlightsSheet, setShowHighlightsSheet, setFlowStep } =
    useStore();

  // Deduplicate by place_id — backend can return duplicates
  const uniqueHighlights = useMemo(
    () =>
      highlights.filter(
        (h, i, arr) => arr.findIndex((x) => x.place_id === h.place_id) === i
      ),
    [highlights]
  );

  return (
    <Sheet open={showHighlightsSheet} onOpenChange={setShowHighlightsSheet}>
      <SheetContent
        side="right"
        className="w-full border-glass-border bg-bg-primary sm:max-w-md md:max-w-lg p-0 flex flex-col overflow-hidden"
      >
        <SheetHeader className="shrink-0 px-6 pt-6 pb-2">
          <SheetTitle className="text-lg font-bold text-text-primary">
            Places in {primaryCity || "this destination"}
          </SheetTitle>
          <p className="text-sm text-text-secondary">
            {uniqueHighlights.length} places discovered from the video
          </p>
        </SheetHeader>

        {/* Scrollable card list — min-h-0 allows flex child to shrink & overflow */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6">
          <div className="space-y-4 pb-24">
            {uniqueHighlights.map((h, i) => (
              <HighlightCard
                key={`${h.place_id}-${i}`}
                highlight={h}
                index={i}
              />
            ))}
          </div>
        </div>

        {/* Sticky CTA at bottom */}
        <div className="shrink-0 border-t border-glass-border bg-bg-primary/90 backdrop-blur-sm p-4">
          <button
            onClick={() => {
              setShowHighlightsSheet(false);
              setFlowStep("bucketList");
            }}
            className="w-full rounded-xl accent-gradient px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-accent-purple/20 transition-opacity hover:opacity-90"
          >
            Create Itinerary
          </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
