"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Plane } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";

export default function LandingPage() {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const { setUrl: storeSetUrl, reset } = useStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please paste a URL");
      return;
    }

    if (
      !trimmed.startsWith("http://") &&
      !trimmed.startsWith("https://")
    ) {
      setError("Please paste a valid URL starting with https://");
      return;
    }

    reset();
    storeSetUrl(trimmed);
    const sessionId = crypto.randomUUID();
    router.push(`/trip/${sessionId}`);
  };

  return (
    <div className="animated-gradient-bg flex min-h-screen flex-col items-center justify-center px-4">
      <motion.div
        className="flex flex-col items-center text-center"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
      >
        {/* Logo icon */}
        <motion.div
          className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl accent-gradient shadow-lg shadow-accent-purple/30"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2, type: "spring" }}
        >
          <Plane className="h-8 w-8 text-white" />
        </motion.div>

        {/* Title */}
        <h1 className="gradient-text text-5xl font-extrabold tracking-tight sm:text-6xl md:text-7xl">
          ReelTrip
        </h1>

        {/* Tagline */}
        <p className="mt-4 max-w-md text-lg text-text-secondary sm:text-xl">
          Paste a travel reel. Get a complete trip plan.
        </p>

        {/* URL Input */}
        <motion.form
          onSubmit={handleSubmit}
          className="glass-card mt-10 flex w-full max-w-xl flex-col gap-3 p-4 sm:flex-row sm:gap-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Input
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (error) setError("");
            }}
            placeholder="Paste an Instagram, YouTube, or TikTok URL..."
            className="flex-1 border-glass-border bg-bg-secondary/60 text-text-primary placeholder:text-text-secondary/60 input-glow"
          />
          <Button
            type="submit"
            className="accent-gradient shrink-0 gap-2 font-semibold text-white shadow-lg shadow-accent-purple/20 hover:opacity-90"
          >
            Go
            <ArrowRight className="h-4 w-4" />
          </Button>
        </motion.form>

        {error && (
          <motion.p
            className="mt-3 text-sm text-error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {error}
          </motion.p>
        )}

        {/* Supported platforms */}
        <p className="mt-6 text-xs text-text-secondary/60">
          Supports Instagram Reels, YouTube Shorts, and TikTok videos
        </p>
      </motion.div>
    </div>
  );
}
