"use client";

import { useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import { MapPin, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { RatingBadge } from "@/components/shared/RatingBadge";
import { useStore } from "@/lib/store";

export function BucketListSelector() {
  const {
    highlights,
    bucketListSelections,
    toggleBucketListItem,
    setBucketListSelections,
    setFlowStep,
  } = useStore();
  const initialized = useRef(false);

  const uniqueHighlights = useMemo(
    () =>
      highlights.filter(
        (h, i, arr) => arr.findIndex((x) => x.place_id === h.place_id) === i
      ),
    [highlights]
  );

  // Pre-select top 5 by rating on mount
  useEffect(() => {
    if (initialized.current || uniqueHighlights.length === 0) return;
    initialized.current = true;
    const sorted = [...uniqueHighlights].sort(
      (a, b) => (b.rating ?? 0) - (a.rating ?? 0)
    );
    setBucketListSelections(sorted.slice(0, 5).map((h) => h.place_id));
  }, [uniqueHighlights, setBucketListSelections]);

  return (
    <motion.div
      className="glass-card w-full max-w-2xl p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="mb-6">
        <h3 className="gradient-text text-xl font-bold">
          Select Your Bucket List
        </h3>
        <p className="mt-1 text-sm text-text-secondary">
          Choose the places you don&apos;t want to miss. These will be
          prioritized in your itinerary.
        </p>
      </div>

      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
        {uniqueHighlights.map((h, i) => {
          const isSelected = bucketListSelections.includes(h.place_id);
          return (
            <motion.div
              key={h.place_id}
              onClick={() => toggleBucketListItem(h.place_id)}
              className={`flex items-start gap-3 rounded-xl p-3 cursor-pointer transition-colors ${
                isSelected
                  ? "bg-accent-purple/10 border border-accent-purple/30"
                  : "border border-transparent hover:bg-bg-tertiary/50"
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
            >
              {/* Custom checkbox indicator */}
              <div
                className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors ${
                  isSelected
                    ? "bg-accent-purple border-accent-purple"
                    : "border-glass-border bg-transparent"
                }`}
              >
                {isSelected && <Check className="h-3.5 w-3.5 text-white" />}
              </div>

              {/* Photo thumbnail */}
              {h.photo_url ? (
                <div className="h-10 w-10 shrink-0 rounded-lg overflow-hidden bg-bg-tertiary">
                  <img
                    src={h.photo_url}
                    alt={h.place_name}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="h-10 w-10 shrink-0 rounded-lg bg-bg-tertiary flex items-center justify-center">
                  <MapPin className="h-4 w-4 text-text-secondary" />
                </div>
              )}

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-text-primary truncate">
                    {h.place_name}
                  </span>
                  <RatingBadge rating={h.rating} />
                </div>
                {h.formatted_address && (
                  <p className="text-xs text-text-secondary mt-0.5 flex items-center gap-1">
                    <MapPin className="h-3 w-3 shrink-0" />
                    <span className="truncate">{h.formatted_address}</span>
                  </p>
                )}
                {h.vibe_tags.length > 0 && (
                  <div className="flex gap-1.5 mt-1.5">
                    {h.vibe_tags.slice(0, 2).map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="border-accent-purple/30 bg-accent-purple/10 text-text-accent text-xs"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <p className="text-xs text-text-secondary">
          {bucketListSelections.length} of {uniqueHighlights.length} selected
        </p>
        <button
          onClick={() => setFlowStep("preferences")}
          className="rounded-xl accent-gradient px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-accent-purple/20 transition-opacity hover:opacity-90"
        >
          Continue
        </button>
      </div>
    </motion.div>
  );
}
