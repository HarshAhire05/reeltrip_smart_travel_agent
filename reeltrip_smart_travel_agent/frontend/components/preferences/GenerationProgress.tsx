"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Plane,
  Hotel,
  Cloud,
  Shield,
  MapPin,
  Car,
  DollarSign,
  Sparkles,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { useStore } from "@/lib/store";

const AGENTS = [
  { key: "flight", label: "Flights", icon: Plane },
  { key: "hotel", label: "Hotels", icon: Hotel },
  { key: "weather", label: "Weather", icon: Cloud },
  { key: "safety", label: "Safety", icon: Shield },
  { key: "activity", label: "Activities", icon: MapPin },
  { key: "transport", label: "Transport", icon: Car },
  { key: "budget", label: "Budget", icon: DollarSign },
  { key: "assembler", label: "Assembling", icon: Sparkles },
];

export function GenerationProgress() {
  const router = useRouter();
  const { agentStatuses, sessionId, itineraryId } = useStore();

  const completedCount = useMemo(
    () => agentStatuses.filter((a) => a.status === "complete").length,
    [agentStatuses],
  );

  const progressPercent = Math.round((completedCount / AGENTS.length) * 100);
  const isComplete = completedCount === AGENTS.length && itineraryId;

  console.log("[GenerationProgress] Render:", {
    completedCount,
    totalAgents: AGENTS.length,
    itineraryId,
    isComplete,
    agentStatuses: agentStatuses.map((a) => ({
      agent: a.agent,
      status: a.status,
    })),
  });

  const getStatus = (agentKey: string) => {
    return agentStatuses.find((a) => a.agent === agentKey);
  };

  return (
    <motion.div
      className="glass-card w-full max-w-md p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h3 className="gradient-text text-xl font-bold mb-2">
        Planning Your Trip
      </h3>
      <p className="text-sm text-text-secondary mb-6">
        Our AI agents are researching and planning your perfect itinerary.
      </p>

      {/* Progress bar */}
      <div className="h-2 rounded-full bg-bg-tertiary mb-6 overflow-hidden">
        <motion.div
          className="h-full rounded-full accent-gradient"
          initial={{ width: 0 }}
          animate={{ width: `${progressPercent}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Agent list */}
      <div className="space-y-3">
        {AGENTS.map((agent, i) => {
          const status = getStatus(agent.key);
          const Icon = agent.icon;
          const isWorking = status?.status === "working";
          const isDone = status?.status === "complete";
          const isFailed = status?.status === "failed";

          return (
            <motion.div
              key={agent.key}
              className={`flex items-center gap-3 rounded-xl p-3 transition-colors ${
                isWorking ? "bg-accent-purple/10 pulse-glow" : ""
              }`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                  isDone
                    ? "bg-success/20"
                    : isFailed
                      ? "bg-error/20"
                      : isWorking
                        ? "bg-accent-purple/20"
                        : "bg-bg-tertiary"
                }`}
              >
                <Icon
                  className={`h-4 w-4 ${
                    isDone
                      ? "text-success"
                      : isFailed
                        ? "text-error"
                        : isWorking
                          ? "text-accent-purple"
                          : "text-text-secondary"
                  }`}
                />
              </div>

              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm font-medium ${
                    isDone || isWorking
                      ? "text-text-primary"
                      : "text-text-secondary"
                  }`}
                >
                  {agent.label}
                </p>
                {status?.message && (
                  <p className="text-xs text-text-secondary truncate">
                    {status.message}
                  </p>
                )}
              </div>

              <div className="shrink-0">
                {isDone && <Check className="h-4 w-4 text-success" />}
                {isFailed && <X className="h-4 w-4 text-error" />}
                {isWorking && (
                  <Loader2 className="h-4 w-4 text-accent-purple spin-slow" />
                )}
                {!status && (
                  <div className="h-3 w-3 rounded-full border-2 border-bg-tertiary" />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* View Itinerary button */}
      {isComplete && (
        <motion.div
          className="mt-6"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <button
            onClick={() => router.push(`/trip/${sessionId}/itinerary`)}
            className="w-full rounded-xl accent-gradient px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-accent-purple/20 transition-opacity hover:opacity-90"
          >
            View Itinerary
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}
