"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, Clock, DollarSign, Bookmark } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PhotoCarousel } from "@/components/shared/PhotoCarousel";
import { RatingBadge } from "@/components/shared/RatingBadge";
import { BookButton } from "@/components/shared/BookButton";
import type { PlaceHighlight } from "@/lib/types";

interface HighlightCardProps {
  highlight: PlaceHighlight;
  index?: number;
}

export function HighlightCard({ highlight, index = 0 }: HighlightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  const photos = highlight.photo_url ? [highlight.photo_url] : [];

  return (
    <motion.div
      className="glass-card-hover overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      layout
    >
      {/* Photo */}
      <PhotoCarousel photos={photos} alt={highlight.place_name} />

      <div className="p-4 space-y-3">
        {/* Name + Rating */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold text-text-primary leading-tight">
            {highlight.place_name}
          </h3>
          <RatingBadge rating={highlight.rating} />
        </div>

        {/* Address */}
        {highlight.formatted_address && (
          <p className="text-xs text-text-secondary line-clamp-1">
            {highlight.formatted_address}
          </p>
        )}

        {/* Vibe tags */}
        <div className="flex flex-wrap gap-1.5">
          {highlight.vibe_tags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="border-accent-purple/30 bg-accent-purple/10 text-text-accent text-xs"
            >
              {tag}
            </Badge>
          ))}
        </div>

        {/* Description */}
        <p className={`text-sm text-text-secondary leading-relaxed ${!isExpanded ? "line-clamp-3" : ""}`}>
          {highlight.description}
        </p>

        {/* Expandable section */}
        {isExpanded && (
          <motion.div
            className="space-y-3 pt-1"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
          >
            {/* Signature experiences */}
            {highlight.signature_experiences.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-text-accent uppercase tracking-wide mb-1.5">
                  Must-Do Experiences
                </p>
                <ul className="space-y-1">
                  {highlight.signature_experiences.map((exp, i) => (
                    <li
                      key={i}
                      className="text-sm text-text-secondary flex items-start gap-2"
                    >
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-purple" />
                      {exp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Best time + duration + cost */}
            <div className="flex flex-wrap gap-3 text-xs text-text-secondary">
              {highlight.best_time_to_visit && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-accent-purple-light" />
                  {highlight.best_time_to_visit}
                </span>
              )}
              {highlight.estimated_visit_duration && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-accent-purple-light" />
                  {highlight.estimated_visit_duration}
                </span>
              )}
              {highlight.estimated_cost_usd > 0 && (
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3.5 w-3.5 text-accent-purple-light" />
                  ~${highlight.estimated_cost_usd}
                </span>
              )}
            </div>

            {/* Know more */}
            {highlight.know_more && (
              <div>
                <p className="text-xs font-semibold text-text-accent uppercase tracking-wide mb-1">
                  Know More
                </p>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {highlight.know_more}
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* Actions row */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            {highlight.google_maps_url && (
              <BookButton url={highlight.google_maps_url} label="Map" />
            )}
            <button
              onClick={() => setIsBookmarked(!isBookmarked)}
              className={`rounded-md p-1.5 transition-colors ${
                isBookmarked
                  ? "bg-accent-purple/20 text-accent-purple"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Bookmark
                className={`h-4 w-4 ${isBookmarked ? "fill-accent-purple" : ""}`}
              />
            </button>
          </div>

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
        </div>
      </div>
    </motion.div>
  );
}
