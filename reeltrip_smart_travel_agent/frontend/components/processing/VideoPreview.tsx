"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useStore } from "@/lib/store";

const platformColors: Record<string, string> = {
  instagram: "bg-pink-600 text-white",
  youtube: "bg-red-600 text-white",
  tiktok: "bg-neutral-800 text-white",
};

export function VideoPreview() {
  const { videoTitle, thumbnailUrl, platform, duration } = useStore();

  if (!videoTitle && !thumbnailUrl) return null;

  const formatDuration = (seconds: number) => {
    if (!seconds) return "";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <motion.div
      className="glass-card-hover w-full max-w-sm overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video w-full bg-bg-tertiary">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={videoTitle || "Video thumbnail"}
            className="h-full w-full object-cover"
          />
        ) : (
          <Skeleton className="h-full w-full" />
        )}

        {/* Platform badge */}
        {platform && (
          <Badge
            className={`absolute right-2 top-2 text-xs capitalize ${platformColors[platform] || "bg-bg-tertiary text-text-primary"}`}
          >
            {platform}
          </Badge>
        )}

        {/* Duration */}
        {duration > 0 && (
          <span className="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 text-xs text-white">
            {formatDuration(duration)}
          </span>
        )}
      </div>

      {/* Title */}
      <div className="p-4">
        {videoTitle ? (
          <p className="line-clamp-2 text-sm font-medium text-text-primary">
            {videoTitle}
          </p>
        ) : (
          <Skeleton className="h-4 w-3/4" />
        )}
      </div>
    </motion.div>
  );
}
