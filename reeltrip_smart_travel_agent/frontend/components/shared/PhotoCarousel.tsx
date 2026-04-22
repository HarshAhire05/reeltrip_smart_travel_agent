"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";

interface PhotoCarouselProps {
  photos: string[];
  alt: string;
}

export function PhotoCarousel({ photos, alt }: PhotoCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);

  if (photos.length === 0) {
    return (
      <div className="aspect-video w-full rounded-t-lg bg-gradient-to-br from-accent-purple/20 to-bg-tertiary" />
    );
  }

  const showControls = photos.length > 1;

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-t-lg bg-bg-tertiary">
      {!imageLoaded && (
        <Skeleton className="absolute inset-0 h-full w-full" />
      )}
      <AnimatePresence mode="wait">
        <motion.img
          key={currentIndex}
          src={photos[currentIndex]}
          alt={`${alt} - ${currentIndex + 1}`}
          className="h-full w-full object-cover"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          onLoad={() => setImageLoaded(true)}
          onError={(e) => {
            (e.target as HTMLImageElement).src = "";
            (e.target as HTMLImageElement).className =
              "h-full w-full bg-gradient-to-br from-accent-purple/20 to-bg-tertiary";
          }}
        />
      </AnimatePresence>

      {showControls && (
        <>
          <button
            onClick={() =>
              setCurrentIndex((i) => (i - 1 + photos.length) % photos.length)
            }
            className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-1 text-white hover:bg-black/70"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() =>
              setCurrentIndex((i) => (i + 1) % photos.length)
            }
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-1 text-white hover:bg-black/70"
          >
            <ChevronRight className="h-4 w-4" />
          </button>

          <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
            {photos.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentIndex(i)}
                className={`h-1.5 rounded-full transition-all ${
                  i === currentIndex
                    ? "w-4 bg-white"
                    : "w-1.5 bg-white/50"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
