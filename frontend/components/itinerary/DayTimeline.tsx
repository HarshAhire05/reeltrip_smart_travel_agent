"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { ActivityCard } from "./ActivityCard";
import type { ItineraryDay } from "@/lib/types";

export function DayTimeline({ day }: { day: ItineraryDay }) {
  return (
    <div>
      {/* Day header */}
      <motion.div
        className="mb-6"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3">
          <h3 className="gradient-text text-xl font-bold">
            Day {day.day_number ?? "?"}
          </h3>
          <Badge
            variant="outline"
            className="border-glass-border text-text-secondary text-xs"
          >
            {day.city ?? "Unknown"}
          </Badge>
        </div>
        {day.theme && <p className="text-sm text-text-accent mt-1">{day.theme}</p>}
        {day.date && <p className="text-xs text-text-secondary mt-0.5">{day.date}</p>}
      </motion.div>

      {/* Timeline */}
      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-glass-border" />

        <div className="space-y-4">
          {(day.activities ?? []).map((activity, i) => (
            <div key={`${activity.time}-${activity.title}-${i}`} className="relative">
              {/* Timeline dot */}
              <div className="absolute -left-6 top-4 h-3 w-3 rounded-full border-2 border-accent-purple bg-bg-primary" />
              <ActivityCard activity={activity} index={i} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
