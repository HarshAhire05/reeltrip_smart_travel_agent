"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Cloud,
  Luggage,
  Globe,
  Coins,
  Phone,
} from "lucide-react";
import { BudgetBreakdown } from "./BudgetBreakdown";
import type { TripItinerary } from "@/lib/types";

function Section({
  icon: Icon,
  title,
  children,
  defaultOpen = false,
}: {
  icon: typeof FileText;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="glass-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-accent-purple" />
          <span className="text-sm font-semibold text-text-primary">
            {title}
          </span>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-text-secondary" />
        ) : (
          <ChevronDown className="h-4 w-4 text-text-secondary" />
        )}
      </button>
      {open && (
        <motion.div
          className="px-4 pb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          {children}
        </motion.div>
      )}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li
          key={i}
          className="text-sm text-text-secondary flex items-start gap-2"
        >
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-purple" />
          {item}
        </li>
      ))}
    </ul>
  );
}

export function MiscellaneousTab({
  itinerary,
}: {
  itinerary: TripItinerary;
}) {
  return (
    <div className="space-y-4">
      {/* Budget */}
      {itinerary.budget_breakdown && (
        <BudgetBreakdown budget={itinerary.budget_breakdown} />
      )}

      {/* Visa */}
      {itinerary.visa_requirements && (
        <Section icon={FileText} title="Visa Requirements">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Required</span>
              <span className="text-text-primary">
                {itinerary.visa_requirements.required ? "Yes" : "No"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Type</span>
              <span className="text-text-primary">
                {itinerary.visa_requirements.visa_type ?? "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Processing Time</span>
              <span className="text-text-primary">
                {itinerary.visa_requirements.processing_time ?? "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Estimated Cost</span>
              <span className="text-text-primary">
                {itinerary.visa_requirements.estimated_cost ?? "N/A"}
              </span>
            </div>
            {(itinerary.visa_requirements.documents_needed ?? []).length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-text-accent mb-1.5">
                  Documents Needed
                </p>
                <BulletList
                  items={itinerary.visa_requirements.documents_needed ?? []}
                />
              </div>
            )}
            {itinerary.visa_requirements.notes && (
              <p className="text-xs text-text-secondary mt-2 italic">
                {itinerary.visa_requirements.notes}
              </p>
            )}
          </div>
        </Section>
      )}

      {/* Weather */}
      {itinerary.weather_summary && (
        <Section icon={Cloud} title="Weather Summary" defaultOpen>
          <div className="space-y-2 text-sm">
            <p className="text-text-secondary">
              {itinerary.weather_summary.overview ?? "No weather data available"}
            </p>
            <div className="flex gap-4 text-xs text-text-secondary">
              <span>
                High:{" "}
                <span className="text-text-primary font-medium">
                  {itinerary.weather_summary.avg_high_celsius ?? "N/A"}°C
                </span>
              </span>
              <span>
                Low:{" "}
                <span className="text-text-primary font-medium">
                  {itinerary.weather_summary.avg_low_celsius ?? "N/A"}°C
                </span>
              </span>
              <span>
                Rain:{" "}
                <span className="text-text-primary font-medium capitalize">
                  {itinerary.weather_summary.precipitation_chance ?? "N/A"}
                </span>
              </span>
            </div>
            {(itinerary.weather_summary.pack_suggestions ?? []).length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-text-accent mb-1.5">
                  Pack Suggestions
                </p>
                <BulletList items={itinerary.weather_summary.pack_suggestions ?? []} />
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Packing */}
      {(itinerary.packing_suggestions ?? []).length > 0 && (
        <Section icon={Luggage} title="Packing Suggestions">
          <BulletList items={itinerary.packing_suggestions ?? []} />
        </Section>
      )}

      {/* Cultural Tips */}
      {(itinerary.cultural_tips ?? []).length > 0 && (
        <Section icon={Globe} title="Cultural Tips">
          <BulletList items={itinerary.cultural_tips ?? []} />
        </Section>
      )}

      {/* Currency */}
      {itinerary.currency_info && (
        <Section icon={Coins} title="Currency Info">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Local Currency</span>
              <span className="text-text-primary">
                {itinerary.currency_info.local_currency_name ?? "N/A"} (
                {itinerary.currency_info.local_currency ?? ""})
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Exchange Rate</span>
              <span className="text-text-primary">
                {itinerary.currency_info.exchange_rate ?? "N/A"}
              </span>
            </div>
            {(itinerary.currency_info.tips ?? []).length > 0 && (
              <div className="mt-2">
                <BulletList items={itinerary.currency_info.tips ?? []} />
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Emergency */}
      {itinerary.emergency_info && (
        <Section icon={Phone} title="Emergency Info">
          <div className="space-y-2 text-sm">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="flex justify-between">
                <span className="text-text-secondary">Police</span>
                <span className="text-text-primary font-medium">
                  {itinerary.emergency_info.police ?? "N/A"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Ambulance</span>
                <span className="text-text-primary font-medium">
                  {itinerary.emergency_info.ambulance ?? "N/A"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Fire</span>
                <span className="text-text-primary font-medium">
                  {itinerary.emergency_info.fire ?? "N/A"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Tourist Police</span>
                <span className="text-text-primary font-medium">
                  {itinerary.emergency_info.tourist_police ?? "N/A"}
                </span>
              </div>
            </div>
            {itinerary.emergency_info.embassy_phone && (
              <div className="flex justify-between">
                <span className="text-text-secondary">Embassy</span>
                <span className="text-text-primary font-medium">
                  {itinerary.emergency_info.embassy_phone}
                </span>
              </div>
            )}
            {(itinerary.emergency_info.emergency_notes ?? []).length > 0 && (
              <div className="mt-2">
                <BulletList items={itinerary.emergency_info.emergency_notes ?? []} />
              </div>
            )}
          </div>
        </Section>
      )}
    </div>
  );
}
