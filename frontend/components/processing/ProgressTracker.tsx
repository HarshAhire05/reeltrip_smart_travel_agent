"use client";

import { motion } from "framer-motion";
import {
  Download,
  Brain,
  MapPin,
  Sparkles,
  Check,
  Loader2,
} from "lucide-react";
import { useStore } from "@/lib/store";

const STAGES = [
  { key: "extracting", label: "Extracting", icon: Download },
  { key: "analyzing", label: "Analyzing", icon: Brain },
  { key: "locating", label: "Locating", icon: MapPin },
  { key: "highlights", label: "Highlights", icon: Sparkles },
] as const;

const stageOrder = STAGES.map((s) => s.key);

function getStageStatus(
  stageKey: string,
  currentStage: string
): "pending" | "active" | "complete" {
  const currentIdx = stageOrder.indexOf(currentStage as typeof stageOrder[number]);
  const stageIdx = stageOrder.indexOf(stageKey as typeof stageOrder[number]);

  if (currentIdx === -1) {
    if (currentStage === "complete") return "complete";
    return "pending";
  }
  if (stageIdx < currentIdx) return "complete";
  if (stageIdx === currentIdx) return "active";
  return "pending";
}

export function ProgressTracker() {
  const { stage, progress, stageMessage } = useStore();

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Stage indicators */}
      <div className="flex items-center justify-between mb-6">
        {STAGES.map((s, i) => {
          const status = getStageStatus(s.key, stage);
          const Icon = s.icon;

          return (
            <div key={s.key} className="flex items-center">
              <div className="flex flex-col items-center gap-2">
                <motion.div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                    status === "complete"
                      ? "border-success bg-success/20"
                      : status === "active"
                        ? "border-accent-purple bg-accent-purple/20 pulse-glow"
                        : "border-text-secondary/30 bg-bg-tertiary"
                  }`}
                  initial={{ scale: 0.8 }}
                  animate={{ scale: status === "active" ? 1.1 : 1 }}
                  transition={{ duration: 0.3 }}
                >
                  {status === "complete" ? (
                    <Check className="h-5 w-5 text-success" />
                  ) : status === "active" ? (
                    <Loader2 className="h-5 w-5 text-accent-purple spin-slow" />
                  ) : (
                    <Icon className="h-5 w-5 text-text-secondary/50" />
                  )}
                </motion.div>
                <span
                  className={`text-xs font-medium ${
                    status === "complete"
                      ? "text-success"
                      : status === "active"
                        ? "text-accent-purple-light"
                        : "text-text-secondary/50"
                  }`}
                >
                  {s.label}
                </span>
              </div>

              {/* Connector line */}
              {i < STAGES.length - 1 && (
                <div
                  className={`mx-2 h-0.5 w-8 sm:w-12 rounded-full transition-colors ${
                    getStageStatus(STAGES[i + 1].key, stage) !== "pending"
                      ? "bg-success"
                      : status === "active" || status === "complete"
                        ? "bg-accent-purple/40"
                        : "bg-text-secondary/20"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-bg-tertiary">
        <motion.div
          className="h-full rounded-full accent-gradient"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Stage message */}
      {stageMessage && (
        <motion.p
          className="mt-3 text-center text-sm text-text-secondary"
          key={stageMessage}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {stageMessage}
        </motion.p>
      )}
    </div>
  );
}
