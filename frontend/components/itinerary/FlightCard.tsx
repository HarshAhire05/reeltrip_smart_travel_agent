"use client";

import { motion } from "framer-motion";
import { Plane } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { BookButton } from "@/components/shared/BookButton";
import type { FlightReservation } from "@/lib/types";

function formatTime(datetime: string) {
  try {
    const d = new Date(datetime);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return datetime;
  }
}

export function FlightCard({
  flight,
  index = 0,
}: {
  flight: FlightReservation;
  index?: number;
}) {
  return (
    <motion.div
      className="glass-card-hover p-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      {/* Type badge */}
      <div className="flex items-center justify-between mb-3">
        <Badge
          variant="outline"
          className="border-accent-purple/30 bg-accent-purple/10 text-text-accent text-xs capitalize"
        >
          {flight.type}
        </Badge>
        {flight.notes && (
          <span className="text-xs text-text-secondary">{flight.notes}</span>
        )}
      </div>

      {/* Flight route */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Departure */}
        <div className="flex-1 text-center min-w-0">
          <p className="text-xl sm:text-2xl font-bold text-text-primary truncate">
            {flight.from_airport_code ?? "???"}
          </p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">
            {flight.from_city ?? ""}
          </p>
          <p className="text-sm font-medium text-text-accent mt-1">
            {formatTime(flight.departure_datetime)}
          </p>
        </div>

        {/* Center line with plane */}
        <div className="flex-1 flex flex-col items-center gap-1">
          <p className="text-xs text-text-secondary">{flight.duration ?? ""}</p>
          <div className="relative w-full flex items-center">
            <div className="flex-1 border-t-2 border-dashed border-glass-border" />
            <Plane className="h-4 w-4 text-accent-purple mx-1 -rotate-0" />
            <div className="flex-1 border-t-2 border-dashed border-glass-border" />
          </div>
        </div>

        {/* Arrival */}
        <div className="flex-1 text-center min-w-0">
          <p className="text-xl sm:text-2xl font-bold text-text-primary truncate">
            {flight.to_airport_code ?? "???"}
          </p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">
            {flight.to_city ?? ""}
          </p>
          <p className="text-sm font-medium text-text-accent mt-1">
            {formatTime(flight.arrival_datetime)}
          </p>
        </div>
      </div>

      {/* Bottom row */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-glass-border gap-2">
        <p className="text-sm font-semibold text-text-primary min-w-0 truncate">
          ~{flight.price_currency ?? ""}{" "}
          {(flight.estimated_price ?? 0).toLocaleString()}
          <span className="text-xs text-text-secondary font-normal ml-1">
            /person
          </span>
        </p>
        {flight.booking_url && (
          <BookButton url={flight.booking_url} label="Book Now" />
        )}
      </div>
    </motion.div>
  );
}
