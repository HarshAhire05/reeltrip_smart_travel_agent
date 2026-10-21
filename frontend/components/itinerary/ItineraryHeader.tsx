"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Share2,
  Bookmark,
  Calendar,
  Users,
  MapPin,
} from "lucide-react";
import type { TripItinerary } from "@/lib/types";

export function ItineraryHeader({
  itinerary,
}: {
  itinerary: TripItinerary;
}) {
  const [isBookmarked, setIsBookmarked] = useState(false);

  const handleShare = async () => {
    const shareData = {
      title: itinerary.trip_title,
      text: `Check out my ${itinerary.total_days ?? 0}-day trip to ${(itinerary.destination_cities ?? []).join(", ") || "your destination"}!`,
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
      }
    } catch {
      // User cancelled share
    }
  };

  return (
    <motion.div
      className="glass-card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="gradient-text text-2xl font-bold leading-tight">
            {itinerary.trip_title ?? "Your Trip"}
          </h1>

          <div className="flex items-center gap-1.5 mt-2 text-sm text-text-secondary">
            <MapPin className="h-4 w-4 text-accent-purple" />
            <span>{(itinerary.destination_cities ?? []).join(" · ") || "Destination"}</span>
          </div>

          <div className="flex flex-wrap gap-4 mt-3 text-xs text-text-secondary">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 text-accent-purple-light" />
              {itinerary.start_date ?? "TBD"} — {itinerary.end_date ?? "TBD"}
            </span>
            <span className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5 text-accent-purple-light" />
              {itinerary.total_travelers ?? 1} traveler
              {(itinerary.total_travelers ?? 1) !== 1 ? "s" : ""} ·{" "}
              {itinerary.total_days ?? 0} day{(itinerary.total_days ?? 0) !== 1 ? "s" : ""}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleShare}
            className="rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
          >
            <Share2 className="h-5 w-5" />
          </button>
          <button
            onClick={() => setIsBookmarked(!isBookmarked)}
            className={`rounded-lg p-2 transition-colors ${
              isBookmarked
                ? "bg-accent-purple/20 text-accent-purple"
                : "text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
            }`}
          >
            <Bookmark
              className={`h-5 w-5 ${isBookmarked ? "fill-accent-purple" : ""}`}
            />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
