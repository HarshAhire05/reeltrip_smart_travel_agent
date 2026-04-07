"use client";

import { motion } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2, Check, AlertCircle, SkipForward } from "lucide-react";
import type { AgentProgress } from "@/lib/types";

interface ReplanProgressTrackerProps {
  open: boolean;
  agentStatuses: AgentProgress[];
  onOpenChange?: (open: boolean) => void;
}

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  flight: "Flights",
  hotel: "Hotels",
  weather: "Weather",
  safety: "Safety Info",
  activity: "Activities",
  transport: "Transportation",
  budget: "Budget",
  assembler: "Final Assembly",
};

const AGENT_ORDER = [
  "flight",
  "hotel",
  "weather",
  "safety",
  "activity",
  "transport",
  "budget",
  "assembler",
];

export function ReplanProgressTracker({
  open,
  agentStatuses,
  onOpenChange,
}: ReplanProgressTrackerProps) {
  // Sort agents by defined order
  const sortedAgents = [...agentStatuses].sort((a, b) => {
    const indexA = AGENT_ORDER.indexOf(a.agent);
    const indexB = AGENT_ORDER.indexOf(b.agent);
    return indexA - indexB;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "working":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case "complete":
        return <Check className="h-4 w-4 text-emerald-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "skipped":
        return <SkipForward className="h-4 w-4 text-muted-foreground" />;
      default:
        return <div className="h-4 w-4 rounded-full border-2 border-muted" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "working":
        return "text-blue-600 dark:text-blue-400";
      case "complete":
        return "text-emerald-600 dark:text-emerald-400";
      case "failed":
        return "text-red-600 dark:text-red-400";
      case "skipped":
        return "text-muted-foreground";
      default:
        return "text-muted-foreground";
    }
  };

  const allComplete = sortedAgents.every(
    (agent) => agent.status === "complete" || agent.status === "skipped",
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {allComplete ? "✅ Re-Plan Complete" : "🔄 Updating Your Itinerary"}
          </DialogTitle>
          <DialogDescription>
            {allComplete
              ? "Your itinerary has been successfully updated"
              : "Selectively updating affected sections..."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {sortedAgents.map((agent) => (
            <motion.div
              key={agent.agent}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start gap-3"
            >
              <div className="mt-0.5">{getStatusIcon(agent.status)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">
                    {AGENT_DISPLAY_NAMES[agent.agent] || agent.agent}
                  </span>
                  {agent.status === "skipped" && (
                    <span className="text-xs text-muted-foreground italic">
                      (unchanged)
                    </span>
                  )}
                </div>
                <p className={`text-xs mt-0.5 ${getStatusColor(agent.status)}`}>
                  {agent.message}
                </p>
              </div>
            </motion.div>
          ))}

          {sortedAgents.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
              <p className="text-sm">Initializing re-plan...</p>
            </div>
          )}
        </div>

        {allComplete && (
          <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-3 text-center">
            <p className="text-sm text-emerald-700 dark:text-emerald-300">
              Only affected sections were updated. Everything else remains the
              same.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

interface ReplanProgressToastProps {
  agentStatuses: AgentProgress[];
}

export function ReplanProgressToast({
  agentStatuses,
}: ReplanProgressToastProps) {
  const activeAgent = agentStatuses.find((a) => a.status === "working");

  if (!activeAgent) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="fixed bottom-4 right-4 bg-background border rounded-lg shadow-lg p-4 max-w-sm z-50"
    >
      <div className="flex items-center gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
        <div className="flex-1">
          <p className="font-medium text-sm">Updating Itinerary</p>
          <p className="text-xs text-muted-foreground">
            {AGENT_DISPLAY_NAMES[activeAgent.agent]}: {activeAgent.message}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
