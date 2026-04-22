"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useStore } from "@/lib/store";
import type { UserPreferences } from "@/lib/types";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD", "THB", "JPY"];

const TRAVEL_STYLES = [
  "adventure", "relaxation", "culture", "food", "nightlife",
  "nature", "photography", "shopping", "luxury", "budget",
];

const DIETARY_OPTIONS = [
  "none", "vegetarian", "vegan", "halal", "kosher", "gluten-free",
];

const TRAVELING_WITH = ["solo", "partner", "family", "friends"] as const;

const ACCOMMODATION_TIERS = [
  "budget", "mid-range", "luxury", "ultra-luxury",
] as const;

export function PreferenceForm() {
  const {
    bucketListSelections,
    highlights,
    primaryCity,
    setPreferences,
    setSelectedCities,
    setShowCitySelector,
    setPassengerContact,
  } = useStore();

  const [form, setForm] = useState({
    trip_duration_days: 4,
    number_of_travelers: 2,
    traveling_with: "partner" as UserPreferences["traveling_with"],
    month_of_travel: "",
    total_budget: 0,
    budget_currency: "INR",
    travel_styles: [] as string[],
    dietary_preferences: [] as string[],
    accommodation_tier: "mid-range" as UserPreferences["accommodation_tier"],
    home_city: "",
    home_country: "",
    additional_notes: "",
  });

  // Passenger contact info for zero-re-entry flight booking
  const [contact, setContact] = useState({
    name: "",
    email: "",
    phone: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const toggleArrayField = (
    field: "travel_styles" | "dietary_preferences",
    value: string
  ) => {
    setForm((prev) => {
      const arr = prev[field];
      return {
        ...prev,
        [field]: arr.includes(value)
          ? arr.filter((v) => v !== value)
          : [...arr, value],
      };
    });
  };

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (form.trip_duration_days < 1) e.duration = "At least 1 day";
    if (form.number_of_travelers < 1) e.travelers = "At least 1 traveler";
    if (!form.month_of_travel) e.month = "Select a month";
    if (form.total_budget <= 0) e.budget = "Enter a budget";
    if (!form.home_city.trim()) e.home_city = "Enter your home city";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    // Map place_ids back to place_names for the backend
    const mustIncludePlaces = bucketListSelections
      .map((id) => highlights.find((h) => h.place_id === id)?.place_name)
      .filter((name): name is string => !!name);
    const prefs: UserPreferences = {
      ...form,
      must_include_places: mustIncludePlaces,
      home_country: form.home_country || "India",
    };
    setPreferences(prefs);
    // Store passenger contact for zero-re-entry flight booking
    if (contact.name || contact.email || contact.phone) {
      setPassengerContact({
        name: contact.name,
        email: contact.email,
        phone: contact.phone,
        num_people: form.number_of_travelers,
      });
    }
    setSelectedCities([primaryCity]);
    setShowCitySelector(true);
  };

  return (
    <motion.div
      className="glass-card w-full max-w-2xl p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h3 className="gradient-text text-xl font-bold mb-6">
        Trip Preferences
      </h3>

      <div className="space-y-6">
        {/* Trip Duration */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Trip Duration: {form.trip_duration_days} day
            {form.trip_duration_days !== 1 ? "s" : ""}
          </Label>
          <Slider
            value={[form.trip_duration_days]}
            onValueChange={(val) => {
              const v = Array.isArray(val) ? val[0] : val;
              setForm((p) => ({ ...p, trip_duration_days: v }));
            }
            }
            min={1}
            max={14}
            step={1}
            className="mt-2"
          />
          {errors.duration && (
            <p className="text-xs text-error mt-1">{errors.duration}</p>
          )}
        </div>

        {/* Travelers */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Travelers: {form.number_of_travelers}
          </Label>
          <Slider
            value={[form.number_of_travelers]}
            onValueChange={(val) => {
              const v = Array.isArray(val) ? val[0] : val;
              setForm((p) => ({ ...p, number_of_travelers: v }));
            }
            }
            min={1}
            max={10}
            step={1}
            className="mt-2"
          />
        </div>

        {/* Traveling With */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Traveling With
          </Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {TRAVELING_WITH.map((opt) => (
              <button
                key={opt}
                onClick={() => setForm((p) => ({ ...p, traveling_with: opt }))}
                className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  form.traveling_with === opt
                    ? "accent-gradient text-white"
                    : "bg-bg-tertiary text-text-secondary hover:text-text-primary"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Month */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Month of Travel
          </Label>
          <Select
            value={form.month_of_travel}
            onValueChange={(v) =>
              setForm((p) => ({ ...p, month_of_travel: v ?? "" }))
            }
          >
            <SelectTrigger className="mt-2 border-glass-border bg-bg-secondary text-text-primary">
              <SelectValue placeholder="Select month" />
            </SelectTrigger>
            <SelectContent className="border-glass-border bg-bg-secondary">
              {MONTHS.map((m) => (
                <SelectItem key={m} value={m} className="text-text-primary">
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.month && (
            <p className="text-xs text-error mt-1">{errors.month}</p>
          )}
        </div>

        {/* Budget */}
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <Label className="text-text-primary text-sm font-medium">
              Total Budget
            </Label>
            <Input
              type="number"
              min={0}
              value={form.total_budget || ""}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  total_budget: Number(e.target.value),
                }))
              }
              placeholder="e.g. 100000"
              className="mt-2 border-glass-border bg-bg-secondary text-text-primary input-glow"
            />
            {errors.budget && (
              <p className="text-xs text-error mt-1">{errors.budget}</p>
            )}
          </div>
          <div>
            <Label className="text-text-primary text-sm font-medium">
              Currency
            </Label>
            <Select
              value={form.budget_currency}
              onValueChange={(v) =>
                setForm((p) => ({ ...p, budget_currency: v ?? "INR" }))
              }
            >
              <SelectTrigger className="mt-2 border-glass-border bg-bg-secondary text-text-primary">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="border-glass-border bg-bg-secondary">
                {CURRENCIES.map((c) => (
                  <SelectItem key={c} value={c} className="text-text-primary">
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Travel Styles */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Travel Styles
          </Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {TRAVEL_STYLES.map((style) => {
              const selected = form.travel_styles.includes(style);
              return (
                <Badge
                  key={style}
                  variant="outline"
                  className={`cursor-pointer capitalize transition-colors ${
                    selected
                      ? "bg-accent-purple/20 border-accent-purple text-text-accent"
                      : "border-glass-border text-text-secondary hover:text-text-primary"
                  }`}
                  onClick={() => toggleArrayField("travel_styles", style)}
                >
                  {style}
                </Badge>
              );
            })}
          </div>
        </div>

        {/* Dietary */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Dietary Preferences
          </Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {DIETARY_OPTIONS.map((diet) => {
              const selected = form.dietary_preferences.includes(diet);
              return (
                <Badge
                  key={diet}
                  variant="outline"
                  className={`cursor-pointer capitalize transition-colors ${
                    selected
                      ? "bg-accent-purple/20 border-accent-purple text-text-accent"
                      : "border-glass-border text-text-secondary hover:text-text-primary"
                  }`}
                  onClick={() => toggleArrayField("dietary_preferences", diet)}
                >
                  {diet}
                </Badge>
              );
            })}
          </div>
        </div>

        {/* Accommodation */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Accommodation
          </Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {ACCOMMODATION_TIERS.map((tier) => (
              <button
                key={tier}
                onClick={() =>
                  setForm((p) => ({ ...p, accommodation_tier: tier }))
                }
                className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  form.accommodation_tier === tier
                    ? "accent-gradient text-white"
                    : "bg-bg-tertiary text-text-secondary hover:text-text-primary"
                }`}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        {/* Home City + Country */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-text-primary text-sm font-medium">
              Home City
            </Label>
            <Input
              value={form.home_city}
              onChange={(e) =>
                setForm((p) => ({ ...p, home_city: e.target.value }))
              }
              placeholder="e.g. Mumbai"
              className="mt-2 border-glass-border bg-bg-secondary text-text-primary input-glow"
            />
            {errors.home_city && (
              <p className="text-xs text-error mt-1">{errors.home_city}</p>
            )}
          </div>
          <div>
            <Label className="text-text-primary text-sm font-medium">
              Home Country
            </Label>
            <Input
              value={form.home_country}
              onChange={(e) =>
                setForm((p) => ({ ...p, home_country: e.target.value }))
              }
              placeholder="e.g. India"
              className="mt-2 border-glass-border bg-bg-secondary text-text-primary input-glow"
            />
          </div>
        </div>

        {/* Additional Notes */}
        <div>
          <Label className="text-text-primary text-sm font-medium">
            Additional Notes
          </Label>
          <Textarea
            value={form.additional_notes}
            onChange={(e) =>
              setForm((p) => ({ ...p, additional_notes: e.target.value }))
            }
            placeholder="Any special requests or requirements..."
            className="mt-2 border-glass-border bg-bg-secondary text-text-primary input-glow resize-none"
            rows={3}
          />
        </div>

        {/* Passenger Contact (for flight booking — optional) */}
        <div className="border-t border-glass-border pt-4">
          <Label className="text-text-primary text-sm font-semibold">
            ✈️ Passenger Details{" "}
            <span className="text-text-secondary font-normal text-xs">
              (optional — used to auto-fill flight booking)
            </span>
          </Label>
          <div className="grid grid-cols-1 gap-3 mt-3">
            <div>
              <Label className="text-text-secondary text-xs">Full Name</Label>
              <Input
                id="passenger-name"
                value={contact.name}
                onChange={(e) =>
                  setContact((p) => ({ ...p, name: e.target.value }))
                }
                placeholder="e.g. Rahul Sharma"
                className="mt-1 border-glass-border bg-bg-secondary text-text-primary input-glow"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-text-secondary text-xs">Email</Label>
                <Input
                  id="passenger-email"
                  type="email"
                  value={contact.email}
                  onChange={(e) =>
                    setContact((p) => ({ ...p, email: e.target.value }))
                  }
                  placeholder="rahul@example.com"
                  className="mt-1 border-glass-border bg-bg-secondary text-text-primary input-glow"
                />
              </div>
              <div>
                <Label className="text-text-secondary text-xs">Phone</Label>
                <Input
                  id="passenger-phone"
                  type="tel"
                  value={contact.phone}
                  onChange={(e) =>
                    setContact((p) => ({ ...p, phone: e.target.value }))
                  }
                  placeholder="9876543210"
                  className="mt-1 border-glass-border bg-bg-secondary text-text-primary input-glow"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Submit */}
      <div className="mt-8">
        <button
          onClick={handleSubmit}
          className="w-full rounded-xl accent-gradient px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-accent-purple/20 transition-opacity hover:opacity-90"
        >
          Save Preferences
        </button>
      </div>
    </motion.div>
  );
}
