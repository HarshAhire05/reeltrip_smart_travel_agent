"use client";

import { motion } from "framer-motion";
import { MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useStore } from "@/lib/store";

const confidenceColors: Record<string, string> = {
  high: "bg-success/20 text-success border-success/30",
  medium: "bg-warning/20 text-warning border-warning/30",
  low: "bg-error/20 text-error border-error/30",
};

export function LocationCard() {
  const {
    destinationCity,
    destinationCountry,
    locationConfidence,
    dominantVibe,
    highlights,
    toggleHighlightsSheet,
  } = useStore();

  if (!destinationCity) return null;

  return (
    <motion.div
      className="glass-card-hover w-full max-w-sm p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-purple/20">
          <MapPin className="h-5 w-5 text-accent-purple" />
        </div>
        <div className="min-w-0">
          <h3 className="text-xl font-bold text-text-primary">
            {destinationCity}
          </h3>
          <p className="text-sm text-text-secondary">{destinationCountry}</p>
        </div>
      </div>

      {locationConfidence && (
        <Badge
          variant="outline"
          className={`mt-3 capitalize ${confidenceColors[locationConfidence] || ""}`}
        >
          {locationConfidence} confidence
        </Badge>
      )}

      {dominantVibe && (
        <p className="mt-3 text-sm italic text-text-accent">
          &ldquo;{dominantVibe}&rdquo;
        </p>
      )}

      {highlights.length > 0 && (
        <button
          onClick={toggleHighlightsSheet}
          className="mt-4 w-full rounded-lg accent-gradient px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          See Highlights &rarr;
        </button>
      )}
    </motion.div>
  );
}
