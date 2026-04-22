"use client";

import { motion } from "framer-motion";
import { Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useStore } from "@/lib/store";
import { toast } from "sonner";

export function UndoButton() {
  const { itineraryVersions, undoItinerary } = useStore();

  const hasVersions = itineraryVersions.length > 0;

  const handleUndo = () => {
    if (!hasVersions) return;

    undoItinerary();
    toast.success("Reverted to previous version", {
      description: "Your itinerary has been restored",
    });
  };

  if (!hasVersions) {
    return null;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <Button
              variant="outline"
              size="sm"
              onClick={handleUndo}
              disabled={!hasVersions}
              className="gap-2"
            >
              <Undo2 className="h-4 w-4" />
              <span className="hidden sm:inline">Undo Last Change</span>
              <span className="sm:hidden">Undo</span>
            </Button>
          </motion.div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Revert to previous itinerary version</p>
          {itineraryVersions.length > 1 && (
            <p className="text-xs text-muted-foreground">
              {itineraryVersions.length} versions available
            </p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
