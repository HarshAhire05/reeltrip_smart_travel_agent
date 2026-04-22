"use client";

import { Info } from "lucide-react";
import { FlightCard } from "./FlightCard";
import { HotelCard } from "./HotelCard";
import type { FlightReservation, HotelReservation } from "@/lib/types";

export function ReservationsTab({
  flights,
  hotels,
  itineraryStartDate,
  itineraryEndDate,
}: {
  flights: FlightReservation[];
  hotels: HotelReservation[];
  itineraryStartDate?: string;
  itineraryEndDate?: string;
}) {
  const flightList = flights ?? [];
  const hotelList = hotels ?? [];

  return (
    <div className="space-y-8">
      <p className="text-xs text-text-secondary italic flex items-center gap-1">
        <Info className="h-3 w-3 shrink-0" /> Prices are estimates and may vary at time of booking.
      </p>

      {/* Flights */}
      {flightList.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Flights
          </h3>
          <div className="space-y-4">
            {flightList.map((f, i) => (
              <FlightCard
                key={`${f.from_airport_code}-${f.to_airport_code}-${i}`}
                flight={f}
                index={i}
                flightLegIndex={i}
                itineraryStartDate={itineraryStartDate}
                itineraryEndDate={itineraryEndDate}
              />
            ))}
          </div>
        </div>
      )}

      {/* Hotels */}
      {hotelList.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Hotels
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {hotelList.map((h, i) => (
              <HotelCard
                key={`${h.hotel_name}-${i}`}
                hotel={h}
                index={i}
              />
            ))}
          </div>
        </div>
      )}

      {flightList.length === 0 && hotelList.length === 0 && (
        <p className="text-sm text-text-secondary text-center py-8">
          No reservations in this itinerary.
        </p>
      )}
    </div>
  );
}
