"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PhotoCarousel } from "@/components/shared/PhotoCarousel";
import { RatingBadge } from "@/components/shared/RatingBadge";
import { BookButton } from "@/components/shared/BookButton";
import type { HotelReservation } from "@/lib/types";

export function HotelCard({
  hotel,
  index = 0,
}: {
  hotel: HotelReservation;
  index?: number;
}) {
  const [showWhy, setShowWhy] = useState(false);
  const photos = hotel.photo_url ? [hotel.photo_url] : [];
  const mapsUrl = hotel.latitude && hotel.longitude
    ? `https://www.google.com/maps/search/?api=1&query=${hotel.latitude},${hotel.longitude}`
    : null;

  return (
    <motion.div
      className="glass-card-hover overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      <PhotoCarousel photos={photos} alt={hotel.hotel_name ?? "Hotel"} />

      <div className="p-4 space-y-3">
        {/* Name + Rating */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <h4 className="text-base font-semibold text-text-primary leading-tight">
              {hotel.hotel_name ?? "Hotel"}
            </h4>
            <p className="text-xs text-text-secondary mt-0.5 flex items-center gap-1">
              <MapPin className="h-3 w-3 shrink-0" />
              {hotel.city ?? ""}
            </p>
          </div>
          <RatingBadge rating={hotel.rating ?? 0} />
        </div>

        {/* Price */}
        <div className="flex flex-wrap items-baseline gap-1">
          <span className="text-lg font-bold text-text-primary">
            ~{hotel.price_currency ?? ""}{" "}
            {(hotel.price_per_night ?? 0).toLocaleString()}
          </span>
          <span className="text-xs text-text-secondary">/night</span>
          <span className="text-xs text-text-secondary">
            x {hotel.nights ?? 0} night{(hotel.nights ?? 0) !== 1 ? "s" : ""} ={" "}
            <span className="font-medium text-text-accent">
              ~{hotel.price_currency ?? ""} {(hotel.total_price ?? 0).toLocaleString()}
            </span>
          </span>
        </div>

        {/* Why this hotel */}
        <button
          onClick={() => setShowWhy(!showWhy)}
          className="flex items-center gap-1 text-xs text-text-accent hover:text-accent-purple-light transition-colors"
        >
          Why this hotel?
          {showWhy ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>

        {showWhy && (
          <motion.p
            className="text-sm text-text-secondary leading-relaxed"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
          >
            {hotel.why_recommended}
          </motion.p>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          {hotel.booking_url && (
            <BookButton url={hotel.booking_url} label="Book" />
          )}
          {mapsUrl && <BookButton url={mapsUrl} label="Map" />}
        </div>
      </div>
    </motion.div>
  );
}
