"use client";

import { motion } from "framer-motion";
import {
  Plane,
  Hotel,
  Utensils,
  Star,
  Car,
  Package,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { BudgetBreakdown as BudgetBreakdownType } from "@/lib/types";

const CATEGORIES = [
  { key: "flights_total", label: "Flights", icon: Plane },
  { key: "accommodation_total", label: "Accommodation", icon: Hotel },
  { key: "food_total", label: "Food & Dining", icon: Utensils },
  { key: "activities_total", label: "Activities", icon: Star },
  { key: "transportation_total", label: "Transportation", icon: Car },
  { key: "miscellaneous_buffer", label: "Miscellaneous", icon: Package },
] as const;

export function BudgetBreakdown({
  budget,
}: {
  budget: BudgetBreakdownType;
}) {
  if (!budget) return null;

  const isOver = budget.budget_status === "over_budget";
  const isUnder = budget.budget_status === "under_budget";

  return (
    <motion.div
      className="glass-card p-5"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base font-semibold text-text-primary">
          Budget Breakdown
        </h4>
        <Badge
          variant="outline"
          className={`text-xs ${
            isOver
              ? "border-error/30 bg-error/10 text-error"
              : "border-success/30 bg-success/10 text-success"
          }`}
        >
          {isOver && <AlertTriangle className="h-3 w-3 mr-1" />}
          {!isOver && <CheckCircle className="h-3 w-3 mr-1" />}
          {isOver
            ? "Over Budget"
            : isUnder
              ? "Under Budget"
              : "Within Budget"}
        </Badge>
      </div>

      <div className="space-y-3">
        {CATEGORIES.map(({ key, label, icon: Icon }) => {
          const amount = (budget as unknown as Record<string, number>)[key] ?? 0;
          return (
            <div key={key} className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <Icon className="h-4 w-4 shrink-0 text-text-secondary" />
                <span className="text-sm text-text-secondary truncate">{label}</span>
              </div>
              <span className="text-sm font-medium text-text-primary shrink-0">
                {budget.currency ?? ""} {(amount ?? 0).toLocaleString()}
              </span>
            </div>
          );
        })}
      </div>

      <Separator className="my-4 bg-glass-border" />

      <div className="flex items-center justify-between">
        <span className="text-base font-bold text-text-primary">
          Grand Total
        </span>
        <span className="text-lg font-bold gradient-text">
          {budget.currency ?? ""} {(budget.grand_total ?? 0).toLocaleString()}
        </span>
      </div>

      <p className="text-xs text-text-secondary mt-2 italic">
        * All prices are estimates and may vary at time of booking.
      </p>

      {/* Savings tips */}
      {isOver && budget.savings_tips && budget.savings_tips.length > 0 && (
        <div className="mt-4 rounded-lg bg-error/5 border border-error/20 p-3">
          <p className="text-xs font-medium text-error mb-2">
            Optimization Tips
          </p>
          <ul className="space-y-1">
            {budget.savings_tips.map((tip, i) => (
              <li
                key={i}
                className="text-xs text-text-secondary flex items-start gap-2"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-error" />
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
