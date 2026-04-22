"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { MapPin, Plus, Check, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useStore } from "@/lib/store";
import { API_BASE } from "@/lib/api";

export function CitySelector({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}) {
  const {
    primaryCity,
    primaryCountry,
    destinationCountry,
    dominantVibe,
    preferences,
    selectedCities,
    suggestedCities,
    isFetchingCities,
    toggleCity,
    setSuggestedCities,
    setIsFetchingCities,
  } = useStore();

  useEffect(() => {
    if (!open || suggestedCities.length > 0 || isFetchingCities) return;

    const fetchCities = async () => {
      setIsFetchingCities(true);
      try {
        const res = await fetch(`${API_BASE}/api/v1/cities/suggest`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            destination_country: destinationCountry || primaryCountry,
            destination_city: primaryCity,
            trip_duration_days: preferences?.trip_duration_days ?? 3,
            vibe: dominantVibe,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          setSuggestedCities(data.suggested_cities || []);
        }
      } catch {
        // Silently handle — user can proceed without suggestions
      } finally {
        setIsFetchingCities(false);
      }
    };
    fetchCities();
  }, [
    open,
    suggestedCities.length,
    isFetchingCities,
    primaryCity,
    primaryCountry,
    destinationCountry,
    dominantVibe,
    preferences,
    setSuggestedCities,
    setIsFetchingCities,
  ]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-glass-border bg-bg-primary text-text-primary max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="gradient-text text-xl font-bold">
            Select Cities
          </DialogTitle>
          <p className="text-sm text-text-secondary">
            Choose which cities to include in your trip.
          </p>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Selected Cities */}
          <div>
            <h4 className="text-sm font-medium text-text-accent mb-3">
              Selected Cities
            </h4>
            <div className="space-y-2">
              {/* Primary city — always included */}
              <div className="glass-card flex items-center gap-3 p-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-purple/20">
                  <MapPin className="h-4 w-4 text-accent-purple" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-primary">
                    {primaryCity}
                  </p>
                  <p className="text-xs text-text-secondary">
                    {primaryCountry || destinationCountry}
                  </p>
                </div>
                <Badge className="bg-accent-purple/20 border-accent-purple/30 text-text-accent text-xs">
                  Primary
                </Badge>
              </div>

              {/* Other selected cities */}
              {selectedCities
                .filter((c) => c !== primaryCity)
                .map((city) => (
                  <motion.div
                    key={city}
                    className="glass-card-hover flex items-center gap-3 p-3"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success/20">
                      <Check className="h-4 w-4 text-success" />
                    </div>
                    <p className="flex-1 text-sm font-medium text-text-primary">
                      {city}
                    </p>
                    <button
                      onClick={() => toggleCity(city)}
                      className="text-xs text-error hover:text-error/80 transition-colors"
                    >
                      Remove
                    </button>
                  </motion.div>
                ))}
            </div>
          </div>

          {/* Suggested Cities */}
          <div>
            <h4 className="text-sm font-medium text-text-accent mb-3">
              Suggested Cities
            </h4>

            {isFetchingCities && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="glass-card p-3 space-y-2">
                    <Skeleton className="h-4 w-32 bg-bg-tertiary" />
                    <Skeleton className="h-3 w-48 bg-bg-tertiary" />
                  </div>
                ))}
              </div>
            )}

            {!isFetchingCities && suggestedCities.length === 0 && (
              <p className="text-sm text-text-secondary italic">
                No additional cities suggested for this trip.
              </p>
            )}

            <div className="space-y-2">
              {suggestedCities.map((city, i) => {
                const isAdded = selectedCities.includes(city.city);
                return (
                  <motion.div
                    key={city.city}
                    className="glass-card-hover p-3"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-bg-tertiary">
                        <MapPin className="h-4 w-4 text-text-secondary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-text-primary">
                            {city.city}
                          </p>
                          <span className="text-xs text-text-secondary">
                            {city.country}
                          </span>
                        </div>
                        <p className="text-xs text-text-secondary mt-1">
                          {city.why}
                        </p>
                        <div className="flex gap-2 mt-1.5">
                          <Badge
                            variant="outline"
                            className="border-glass-border text-text-secondary text-xs"
                          >
                            {city.recommended_days} day
                            {city.recommended_days !== 1 ? "s" : ""}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="border-glass-border text-text-secondary text-xs"
                          >
                            {city.distance_from_primary}
                          </Badge>
                        </div>
                      </div>
                      <button
                        onClick={() => toggleCity(city.city)}
                        className={`shrink-0 flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                          isAdded
                            ? "bg-success/20 text-success"
                            : "bg-accent-purple/20 text-text-accent hover:bg-accent-purple/30"
                        }`}
                      >
                        {isAdded ? (
                          <>
                            <Check className="h-3 w-3" /> Added
                          </>
                        ) : (
                          <>
                            <Plus className="h-3 w-3" /> Add
                          </>
                        )}
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Proceed button */}
        <div className="mt-6">
          <button
            onClick={onConfirm}
            className="w-full rounded-xl accent-gradient px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-accent-purple/20 transition-opacity hover:opacity-90"
          >
            Proceed
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
