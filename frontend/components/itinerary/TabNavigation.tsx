"use client";

import type { ItineraryDay } from "@/lib/types";

export function TabNavigation({
  days,
  activeTab,
  onTabChange,
}: {
  days: ItineraryDay[];
  activeTab: string;
  onTabChange: (tab: string) => void;
}) {
  console.log("[TabNav] Rendering tabs for days:", days?.length);

  const tabs = [
    { key: "reservations", label: "Reservations" },
    ...(days ?? []).map((d, index) => ({
      key: `day-${d.day_number ?? index}`,
      label: `Day ${d.day_number ?? index + 1}`,
    })),
    { key: "misc", label: "Miscellaneous" },
  ];

  return (
    <div className="sticky top-0 z-10 bg-bg-primary/90 backdrop-blur-sm border-b border-glass-border -mx-4 px-4">
      <div className="flex gap-1 overflow-x-auto scrollbar-hide py-2">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`shrink-0 rounded-lg px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? "accent-gradient text-white shadow-md shadow-accent-purple/20"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
