"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { X, Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ChangeSummary, ChangeBadge } from "./ChangeSummary";
import { DestinationOverrideModal } from "./DestinationOverrideModal";
import { useStore } from "@/lib/store";
import { calculateChangedFields, fieldValidators } from "@/lib/validation";
import type { UserPreferences } from "@/lib/types";


const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD", "THB", "JPY"];

const TRAVEL_STYLES = [
  "adventure",
  "relaxation",
  "culture",
  "food",
  "nightlife",
  "nature",
  "photography",
  "shopping",
  "luxury",
  "budget",
];

const DIETARY_OPTIONS = [
  "none",
  "vegetarian",
  "vegan",
  "halal",
  "kosher",
  "gluten-free",
];

const TRAVELING_WITH = ["solo", "partner", "family", "friends"] as const;

const ACCOMMODATION_TIERS = [
  "budget",
  "mid-range",
  "luxury",
  "ultra-luxury",
] as const;

interface EditTripPanelProps {
  onReplan: (
    updatedPreferences: UserPreferences,
    changedFields: string[],
  ) => void;
  isReplanning: boolean;
}

export function EditTripPanel({ onReplan, isReplanning }: EditTripPanelProps) {
  const { preferences, originalPreferences, selectedCities, itinerary } = useStore();

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<UserPreferences | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showDestinationModal, setShowDestinationModal] = useState(false);
  const [pendingDestinationChange, setPendingDestinationChange] = useState<
    string | null
  >(null);

  // Derive preferences from itinerary if not in store
  const effectivePreferences = preferences || (itinerary ? {
    total_budget: itinerary.budget_breakdown.total_budget_inr || 50000,
    currency: "INR",
    number_of_travelers: itinerary.total_travelers || 2,
    month_of_travel: new Date(itinerary.start_date).toLocaleString('en', { month: 'long' }),
    travel_styles: ["relaxation"],
    dietary_preferences: "none",
    traveling_with: "partner" as const,
    accommodation_tier: "mid-range" as const,
    additional_notes: "",
  } : null);

  console.log("[EditTripPanel] Render check:", {
    hasPreferences: !!preferences,
    hasItinerary: !!itinerary,
    hasEffectivePreferences: !!effectivePreferences,
    willRender: !!effectivePreferences || !!form
  });

  // Initialize form when panel opens
  useEffect(() => {
    if (open && effectivePreferences) {
      console.log("[EditTripPanel] Initializing form with preferences");
      setForm({ ...effectivePreferences });
      setErrors({});
    }
  }, [open, effectivePreferences]);

  if (!effectivePreferences) {
    console.log("[EditTripPanel] Returning null - no preferences available");
    return null;
  }

  // Only calculate changes if form is initialized (panel has been opened)
  const changedFields = form ? calculateChangedFields(
    originalPreferences || effectivePreferences,
    form,
  ) : [];

  const hasChanges = changedFields.length > 0;

  const toggleArrayField = (
    field: "travel_styles" | "dietary_preferences",
    value: string,
  ) => {
    if (!form) return;
    setForm((prev) => {
      if (!prev) return prev;
      const arr = prev[field];
      return {
        ...prev,
        [field]: arr.includes(value)
          ? arr.filter((v) => v !== value)
          : [...arr, value],
      };
    });
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    const budgetError = fieldValidators.budget(form.total_budget);
    if (budgetError) newErrors.total_budget = budgetError;

    const travelersError = fieldValidators.travelers(form.number_of_travelers);
    if (travelersError) newErrors.number_of_travelers = travelersError;

    const durationError = fieldValidators.duration(form.trip_duration_days);
    if (durationError) newErrors.trip_duration_days = durationError;

    const homeCityError = fieldValidators.requiredString(
      form.home_city,
      "Home city",
    );
    if (homeCityError) newErrors.home_city = homeCityError;

    const homeCountryError = fieldValidators.requiredString(
      form.home_country,
      "Home country",
    );
    if (homeCountryError) newErrors.home_country = homeCountryError;

    const stylesError = fieldValidators.requiredArray(
      form.travel_styles,
      "Travel style",
    );
    if (stylesError) newErrors.travel_styles = stylesError;

    // Date validation (if dates are provided)
    if (form.start_date && form.end_date) {
      const dateError = fieldValidators.dateRange(
        form.start_date,
        form.end_date,
      );
      if (dateError) newErrors.dates = dateError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleReplan = () => {
    if (!hasChanges) {
      setErrors({ general: "No changes detected" });
      return;
    }

    if (!validateForm()) {
      return;
    }

    // Check if destination changed
    const destinationChanged = changedFields.includes("destination");
    if (destinationChanged && pendingDestinationChange) {
      setShowDestinationModal(true);
      return;
    }

    // Proceed with re-plan
    setOpen(false);
    onReplan(form, changedFields);
  };

  const handleDestinationChangeConfirm = () => {
    setShowDestinationModal(false);
    setOpen(false);
    onReplan(form, changedFields);
  };

  return (
    <>
      {/* Floating Action Button - Always visible */}
      <motion.div
        role="button"
        tabIndex={0}
        aria-label="Edit trip details"
        onClick={() => setOpen(true)}
        onKeyDown={(e) => e.key === "Enter" && setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-gradient-to-r from-accent-purple to-accent-pink px-6 py-3.5 text-base font-bold text-white shadow-2xl shadow-accent-purple/40 transition-all hover:scale-105 hover:shadow-accent-purple/60 cursor-pointer"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        suppressHydrationWarning
      >
        <span className="text-xl">✏️</span>
        <span className="hidden sm:inline">Edit Trip Details</span>
        <span className="sm:hidden">Edit</span>
      </motion.div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Edit Trip Details</SheetTitle>
            <SheetDescription>
              Adjust your trip — change what you need and we&apos;ll re-plan
              instantly.
            </SheetDescription>
          </SheetHeader>

          {!form ? (
            <div className="py-12 text-center text-text-secondary">
              Initializing form...
            </div>
          ) : (
          <div className="space-y-6 py-6">{/* Budget */}
            <div>
              <Label htmlFor="budget">Total Budget</Label>
              <div className="flex gap-2 mt-2">
                <Select
                  value={form.budget_currency}
                  onValueChange={(val) =>
                    setForm((p) => (p ? { ...p, budget_currency: val } : p))
                  }
                >
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map((currency) => (
                      <SelectItem key={currency} value={currency}>
                        {currency}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <ChangeBadge isChanged={changedFields.includes("total_budget")}>
                  <Input
                    id="budget"
                    type="number"
                    value={form.total_budget}
                    onChange={(e) =>
                      setForm((p) =>
                        p
                          ? {
                              ...p,
                              total_budget: parseFloat(e.target.value) || 0,
                            }
                          : p,
                      )
                    }
                    className="flex-1"
                  />
                </ChangeBadge>
              </div>
              {errors.total_budget && (
                <p className="text-xs text-destructive mt-1">
                  {errors.total_budget}
                </p>
              )}
            </div>

            {/* Accommodation Tier */}
            <div>
              <Label>Accommodation Tier</Label>
              <ChangeBadge
                isChanged={changedFields.includes("accommodation_tier")}
              >
                <div className="flex gap-2 mt-2 flex-wrap">
                  {ACCOMMODATION_TIERS.map((tier) => (
                    <Button
                      key={tier}
                      type="button"
                      variant={
                        form.accommodation_tier === tier ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() =>
                        setForm((p) =>
                          p ? { ...p, accommodation_tier: tier } : p,
                        )
                      }
                      className="capitalize"
                    >
                      {tier}
                    </Button>
                  ))}
                </div>
              </ChangeBadge>
            </div>

            {/* Number of Travelers */}
            <div>
              <Label htmlFor="number_of_travelers">Number of Travelers</Label>
              <ChangeBadge
                isChanged={changedFields.includes("number_of_travelers")}
              >
                <Input
                  id="number_of_travelers"
                  type="number"
                  min={1}
                  max={20}
                  value={form.number_of_travelers}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 1;
                    setForm((p) =>
                      p ? { ...p, number_of_travelers: Math.max(1, Math.min(20, val)) } : p
                    );
                  }}
                  className="mt-2"
                  placeholder="e.g., 2"
                />
              </ChangeBadge>
              {errors.number_of_travelers && (
                <p className="text-xs text-destructive mt-1">
                  {errors.number_of_travelers}
                </p>
              )}
            </div>

            {/* Trip Duration */}
            <div>
              <Label htmlFor="trip_duration_days">Trip Duration (days)</Label>
              <ChangeBadge
                isChanged={changedFields.includes("trip_duration_days")}
              >
                <Input
                  id="trip_duration_days"
                  type="number"
                  min={1}
                  max={30}
                  value={form.trip_duration_days}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 1;
                    setForm((p) =>
                      p ? { ...p, trip_duration_days: Math.max(1, Math.min(30, val)) } : p
                    );
                  }}
                  className="mt-2"
                  placeholder="e.g., 7"
                />
              </ChangeBadge>
              {errors.trip_duration_days && (
                <p className="text-xs text-destructive mt-1">
                  {errors.trip_duration_days}
                </p>
              )}
            </div>

            {/* Traveling With */}
            <div>
              <Label>Traveling With</Label>
              <ChangeBadge isChanged={changedFields.includes("traveling_with")}>
                <div className="flex gap-2 mt-2 flex-wrap">
                  {TRAVELING_WITH.map((type) => (
                    <Button
                      key={type}
                      type="button"
                      variant={
                        form.traveling_with === type ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() =>
                        setForm((p) => (p ? { ...p, traveling_with: type } : p))
                      }
                      className="capitalize"
                    >
                      {type}
                    </Button>
                  ))}
                </div>
              </ChangeBadge>
            </div>

            {/* Month of Travel */}
            <div>
              <Label htmlFor="month">Month of Travel</Label>
              <ChangeBadge
                isChanged={changedFields.includes("month_of_travel")}
              >
                <Select
                  value={form.month_of_travel}
                  onValueChange={(val) =>
                    setForm((p) => (p ? { ...p, month_of_travel: val } : p))
                  }
                >
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Select month" />
                  </SelectTrigger>
                  <SelectContent>
                    {MONTHS.map((month) => (
                      <SelectItem key={month} value={month}>
                        {month}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </ChangeBadge>
            </div>

            {/* Travel Styles */}
            <div>
              <Label>Travel Styles</Label>
              <ChangeBadge isChanged={changedFields.includes("travel_styles")}>
                <div className="flex flex-wrap gap-2 mt-2">
                  {TRAVEL_STYLES.map((style) => (
                    <Badge
                      key={style}
                      variant={
                        form.travel_styles.includes(style)
                          ? "default"
                          : "outline"
                      }
                      className="cursor-pointer capitalize"
                      onClick={() => toggleArrayField("travel_styles", style)}
                    >
                      {style}
                    </Badge>
                  ))}
                </div>
              </ChangeBadge>
              {errors.travel_styles && (
                <p className="text-xs text-destructive mt-1">
                  {errors.travel_styles}
                </p>
              )}
            </div>

            {/* Dietary Preferences */}
            <div>
              <Label>Dietary Preferences</Label>
              <ChangeBadge
                isChanged={changedFields.includes("dietary_preferences")}
              >
                <div className="flex flex-wrap gap-2 mt-2">
                  {DIETARY_OPTIONS.map((option) => (
                    <Badge
                      key={option}
                      variant={
                        form.dietary_preferences.includes(option)
                          ? "default"
                          : "outline"
                      }
                      className="cursor-pointer capitalize"
                      onClick={() =>
                        toggleArrayField("dietary_preferences", option)
                      }
                    >
                      {option}
                    </Badge>
                  ))}
                </div>
              </ChangeBadge>
            </div>

            {/* Home City & Country */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="home_city">Home City</Label>
                <ChangeBadge isChanged={changedFields.includes("home_city")}>
                  <Input
                    id="home_city"
                    value={form.home_city}
                    onChange={(e) =>
                      setForm((p) =>
                        p ? { ...p, home_city: e.target.value } : p,
                      )
                    }
                    className="mt-2"
                  />
                </ChangeBadge>
                {errors.home_city && (
                  <p className="text-xs text-destructive mt-1">
                    {errors.home_city}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="home_country">Home Country</Label>
                <ChangeBadge isChanged={changedFields.includes("home_country")}>
                  <Input
                    id="home_country"
                    value={form.home_country}
                    onChange={(e) =>
                      setForm((p) =>
                        p ? { ...p, home_country: e.target.value } : p,
                      )
                    }
                    className="mt-2"
                  />
                </ChangeBadge>
                {errors.home_country && (
                  <p className="text-xs text-destructive mt-1">
                    {errors.home_country}
                  </p>
                )}
              </div>
            </div>

            {/* Special Requests */}
            <div>
              <Label htmlFor="additional_notes">Special Requests</Label>
              <ChangeBadge
                isChanged={changedFields.includes("additional_notes")}
              >
                <Textarea
                  id="additional_notes"
                  value={form.additional_notes}
                  onChange={(e) =>
                    setForm((p) =>
                      p ? { ...p, additional_notes: e.target.value } : p,
                    )
                  }
                  className="mt-2"
                  rows={3}
                  placeholder="Any special requests or preferences..."
                />
              </ChangeBadge>
            </div>

            {/* Destination (read-only) */}
            <div>
              <Label>Destination</Label>
              <Input
                value={selectedCities.join(", ") || "Not set"}
                disabled
                className="mt-2 bg-muted"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Changing destination will rebuild your full itinerary
              </p>
            </div>

            {/* Change Summary */}
            <ChangeSummary
              changedFields={changedFields}
              originalPreferences={originalPreferences || preferences}
              updatedPreferences={form}
              mode="inline"
            />

            {/* Error Message */}
            {errors.general && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg">
                {errors.general}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => setOpen(false)}
                className="flex-1"
                disabled={isReplanning}
              >
                Cancel
              </Button>
              <Button
                onClick={handleReplan}
                className="flex-1"
                disabled={!hasChanges || isReplanning}
              >
                {isReplanning ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Re-Planning...
                  </>
                ) : (
                  "Re-Plan Itinerary"
                )}
              </Button>
            </div>
          </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Destination Override Modal */}
      <DestinationOverrideModal
        open={showDestinationModal}
        onOpenChange={setShowDestinationModal}
        onConfirm={handleDestinationChangeConfirm}
        originalDestination={selectedCities.join(", ")}
        newDestination={pendingDestinationChange || ""}
      />
    </>
  );
}
