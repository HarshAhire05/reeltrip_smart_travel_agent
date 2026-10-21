"use client";

import { motion } from "framer-motion";
import { MapPin, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { ClarificationOption } from "@/lib/types";

interface ClarificationCardProps {
  message: string;
  options: ClarificationOption[];
  onSelect: (destination: string) => void;
}

export function ClarificationCard({
  message,
  options,
  onSelect,
}: ClarificationCardProps) {
  return (
    <motion.div
      className="glass-card w-full max-w-2xl p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Header */}
      <div className="mb-6 text-center">
        <div className="mb-3 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-purple/20">
            <MapPin className="h-6 w-6 text-accent-purple" />
          </div>
        </div>
        <h3 className="text-xl font-semibold text-text-primary">
          {message || "Which destination sounds right for you?"}
        </h3>
        <p className="mt-2 text-sm text-text-secondary">
          Select one to start planning your trip
        </p>
      </div>

      {/* Destination Options */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {options.map((option, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card
              className="group cursor-pointer border-glass-border bg-bg-secondary/40 p-4 transition-all hover:border-accent-purple/50 hover:bg-bg-secondary/60 hover:shadow-lg"
              onClick={() => onSelect(option.destination_name)}
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold text-text-primary">
                      {option.destination_name}
                    </h4>
                    {option.country && (
                      <p className="text-xs text-text-secondary">
                        {option.country}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="h-4 w-4 text-accent-purple opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <p className="text-sm text-text-secondary">
                  {option.description}
                </p>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Back to input option */}
      <div className="mt-6 text-center">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            // Go back to landing page
            window.location.href = "/";
          }}
          className="text-text-secondary hover:text-text-primary"
        >
          ← Start over with a different description
        </Button>
      </div>
    </motion.div>
  );
}
