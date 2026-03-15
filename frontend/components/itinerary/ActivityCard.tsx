"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Plane,
  LogIn,
  LogOut,
  Utensils,
  Camera,
  Star,
  Car,
  Coffee,
  ChevronDown,
  ChevronUp,
  Clock,
  DollarSign,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { RatingBadge } from "@/components/shared/RatingBadge";
import { BookButton } from "@/components/shared/BookButton";
import type { Activity } from "@/lib/types";

const TYPE_CONFIG: Record<
  string,
  { icon: typeof Plane; color: string; bg: string }
> = {
  flight: { icon: Plane, color: "text-blue-400", bg: "bg-blue-400/20" },
  checkin: { icon: LogIn, color: "text-green-400", bg: "bg-green-400/20" },
  checkout: { icon: LogOut, color: "text-orange-400", bg: "bg-orange-400/20" },
  meal: { icon: Utensils, color: "text-amber-400", bg: "bg-amber-400/20" },
  attraction: { icon: Camera, color: "text-purple-400", bg: "bg-purple-400/20" },
  activity: { icon: Star, color: "text-pink-400", bg: "bg-pink-400/20" },
  transport: { icon: Car, color: "text-cyan-400", bg: "bg-cyan-400/20" },
  free_time: { icon: Coffee, color: "text-emerald-400", bg: "bg-emerald-400/20" },
};

export function ActivityCard({
  activity,
  index = 0,
}: {
  activity: Activity;
  index?: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [photoError, setPhotoError] = useState(false);
  const config = TYPE_CONFIG[activity.type] || TYPE_CONFIG.activity;
  const Icon = config.icon;

  return (
    <motion.div
      className="glass-card-hover p-3"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06 }}
      layout
    >
      <div className="flex gap-3">
        {/* Time */}
        <div className="shrink-0 w-14 text-right">
          <p className="text-sm font-bold text-accent-purple">{activity.time}</p>
        </div>

        {/* Icon */}
        <div
          className={`shrink-0 flex h-8 w-8 items-center justify-center rounded-lg ${config.bg}`}
        >
          <Icon className={`h-4 w-4 ${config.color}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="text-sm font-semibold text-text-primary leading-tight">
                {activity.title}
              </h4>
              <Badge
                variant="outline"
                className={`mt-1 text-xs capitalize ${config.color} border-current/30`}
              >
                {(activity.type ?? "activity").replace("_", " ")}
              </Badge>
            </div>
            {activity.rating && <RatingBadge rating={activity.rating} />}
          </div>

          {/* Photo thumbnail */}
          {activity.photo_url && !photoError && (
            <div className="mt-2 rounded-lg overflow-hidden h-24">
              <img
                src={activity.photo_url}
                alt={activity.title ?? ""}
                className="w-full h-full object-cover"
                onError={() => setPhotoError(true)}
              />
            </div>
          )}

          {/* Venue + meta */}
          {activity.venue_name && (
            <p className="text-xs text-text-secondary mt-2">
              {activity.venue_name}
              {activity.venue_address && ` · ${activity.venue_address}`}
            </p>
          )}

          <div className="flex flex-wrap gap-3 mt-2 text-xs text-text-secondary">
            {(activity.duration_minutes ?? 0) > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3 text-accent-purple-light" />
                {activity.duration_minutes} min
              </span>
            )}
            {(activity.estimated_cost ?? 0) > 0 && (
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3 text-accent-purple-light" />
                {activity.cost_currency ?? ""} {(activity.estimated_cost ?? 0).toLocaleString()}
              </span>
            )}
          </div>

          {/* Expandable */}
          {isExpanded && (
            <motion.div
              className="space-y-2 mt-2"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              transition={{ duration: 0.3 }}
            >
              {activity.description && (
                <p className="text-sm text-text-secondary leading-relaxed">
                  {activity.description}
                </p>
              )}
              {activity.practical_tip && (
                <div className="rounded-lg bg-accent-purple/10 border border-accent-purple/20 p-2.5">
                  <p className="text-xs font-medium text-text-accent">Tip</p>
                  <p className="text-xs text-text-secondary mt-0.5">
                    {activity.practical_tip}
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {/* Actions row */}
          <div className="flex items-center justify-between mt-2 pt-1">
            <div className="flex items-center gap-2">
              {activity.booking_url && (
                <BookButton url={activity.booking_url} label="Book" />
              )}
              {activity.google_maps_url && (
                <BookButton url={activity.google_maps_url} label="Map" />
              )}
            </div>
            {(activity.description || activity.practical_tip) && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1 text-xs text-text-accent hover:text-accent-purple-light transition-colors"
              >
                {isExpanded ? "Less" : "More"}
                {isExpanded ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
