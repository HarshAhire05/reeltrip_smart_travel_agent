"use client";

import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BookButtonProps {
  url: string;
  label?: string;
}

export function BookButton({ url, label = "View on Map" }: BookButtonProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      className="gap-1.5 border-glass-border text-text-secondary hover:text-text-primary"
      onClick={() => window.open(url, "_blank", "noopener,noreferrer")}
    >
      {label}
      <ExternalLink className="h-3.5 w-3.5" />
    </Button>
  );
}
