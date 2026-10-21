"use client";

import { Star } from "lucide-react";

interface RatingBadgeProps {
  rating: number | null;
}

export function RatingBadge({ rating }: RatingBadgeProps) {
  if (rating === null || rating === undefined) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-bg-tertiary px-2 py-0.5 text-sm">
      <Star className="h-3.5 w-3.5 fill-warning text-warning" />
      <span className="font-medium text-text-primary">{rating.toFixed(1)}</span>
    </span>
  );
}
