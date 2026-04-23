"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { formatChangedField } from "@/lib/validation";
import type { UserPreferences } from "@/lib/types";

interface ChangeSummaryProps {
  changedFields: string[];
  originalPreferences: UserPreferences | null;
  updatedPreferences: Partial<UserPreferences> | null;
  mode?: "inline" | "banner";
}

export function ChangeSummary({
  changedFields,
  originalPreferences,
  updatedPreferences,
  mode = "inline",
}: ChangeSummaryProps) {
  if (
    changedFields.length === 0 ||
    !originalPreferences ||
    !updatedPreferences
  ) {
    return null;
  }

  if (mode === "banner") {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4 mb-4"
      >
        <div className="flex items-start gap-3">
          <div className="text-2xl">✅</div>
          <div className="flex-1">
            <h4 className="font-semibold text-emerald-900 dark:text-emerald-100 mb-1">
              Your itinerary has been updated
            </h4>
            <p className="text-sm text-emerald-700 dark:text-emerald-300">
              Based on your changes to:{" "}
              {changedFields.slice(0, 3).map((field, index) => {
                if (!originalPreferences) return null;
                const formatted = formatChangedField(
                  field,
                  (originalPreferences as any)[field],
                  (updatedPreferences as any)[field],
                );
                return (
                  <span key={field}>
                    {index > 0 && ", "}
                    <span className="font-medium">{formatted.label}</span>
                  </span>
                );
              })}
              {changedFields.length > 3 &&
                `, and ${changedFields.length - 3} more`}
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  // Inline mode (for EditTripPanel)
  return (
    <div className="border-t pt-4 mt-4">
      <div className="flex items-center gap-2 mb-3">
        <h4 className="text-sm font-semibold">Changes Summary</h4>
        <Badge variant="secondary" className="text-xs">
          {changedFields.length}{" "}
          {changedFields.length === 1 ? "change" : "changes"}
        </Badge>
      </div>

      <AnimatePresence mode="popLayout">
        {changedFields.map((field) => {
          if (!originalPreferences) return null;

          const formatted = formatChangedField(
            field,
            (originalPreferences as any)[field],
            (updatedPreferences as any)[field],
          );

          return (
            <motion.div
              key={field}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="flex items-center gap-2 py-2 text-sm border-b last:border-0"
            >
              <span className="font-medium text-muted-foreground min-w-[140px]">
                {formatted.label}:
              </span>
              <div className="flex items-center gap-2 flex-1">
                <span className="text-muted-foreground line-through">
                  {formatted.before || "—"}
                </span>
                <span className="text-muted-foreground">→</span>
                <span className="font-medium text-foreground">
                  {formatted.after || "—"}
                </span>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

interface ChangeBadgeProps {
  children: React.ReactNode;
  isChanged: boolean;
}

export function ChangeBadge({ children, isChanged }: ChangeBadgeProps) {
  return (
    <div className="relative">
      {children}
      <AnimatePresence>
        {isChanged && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            className="absolute -top-1 -right-1"
          >
            <Badge
              variant="default"
              className="h-5 px-1.5 text-[10px] bg-blue-500 hover:bg-blue-600"
            >
              edited
            </Badge>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
