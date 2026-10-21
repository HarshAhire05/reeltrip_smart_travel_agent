"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Plane, Link2, MessageSquare } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";

export default function LandingPage() {
  const [url, setUrl] = useState("");
  const [textInput, setTextInput] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const {
    setUrl: storeSetUrl,
    setTextInput: storeSetTextInput,
    setInputMode,
    reset,
  } = useStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const trimmedUrl = url.trim();
    const trimmedText = textInput.trim();

    // Check if both or neither are filled
    if (!trimmedUrl && !trimmedText) {
      setError(
        "Please provide either a URL or describe your travel destination",
      );
      return;
    }

    if (trimmedUrl && trimmedText) {
      setError("Please use either URL or text input, not both");
      return;
    }

    // URL mode validation
    if (trimmedUrl) {
      if (
        !trimmedUrl.startsWith("http://") &&
        !trimmedUrl.startsWith("https://")
      ) {
        setError("Please paste a valid URL starting with https://");
        return;
      }

      reset();
      storeSetUrl(trimmedUrl);
      setInputMode("url");
      const sessionId = crypto.randomUUID();
      router.push(`/trip/${sessionId}`);
      return;
    }

    // Text mode validation
    if (trimmedText) {
      if (trimmedText.length < 3) {
        setError("Please provide a more detailed travel description");
        return;
      }

      reset();
      storeSetTextInput(trimmedText);
      setInputMode("text");
      const sessionId = crypto.randomUUID();
      router.push(`/trip/${sessionId}`);
      return;
    }
  };

  return (
    <div className="animated-gradient-bg flex min-h-screen flex-col items-center justify-center px-4 py-12">
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
          Paste a travel reel or describe your dream destination
        </p>

        {/* Input Form */}
        <motion.form
          onSubmit={handleSubmit}
          className="mt-10 w-full max-w-xl space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          {/* URL Input */}
          <div className="glass-card p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-text-secondary">
              <Link2 className="h-4 w-4" />
              <span className="font-medium">Paste a video link</span>
            </div>
            <Input
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError("");
              }}
              placeholder="Instagram, YouTube, or TikTok URL..."
              className="border-glass-border bg-bg-secondary/60 text-text-primary placeholder:text-text-secondary/60 input-glow"
              suppressHydrationWarning
            />
          </div>

          {/* OR Divider */}
          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-accent-purple/30 to-transparent"></div>
            <span className="text-sm font-medium text-text-secondary">OR</span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-accent-purple/30 to-transparent"></div>
          </div>

          {/* Text Input */}
          <div className="glass-card p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-text-secondary">
              <MessageSquare className="h-4 w-4" />
              <span className="font-medium">Describe your travel dream</span>
            </div>
            <Textarea
              value={textInput}
              onChange={(e) => {
                setTextInput(e.target.value);
                if (error) setError("");
              }}
              placeholder='e.g., "I want to visit Dubai" or "Show me beaches in Thailand"'
              className="border-glass-border bg-bg-secondary/60 text-text-primary placeholder:text-text-secondary/60 input-glow min-h-[100px] resize-none"
              rows={3}
              suppressHydrationWarning
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="accent-gradient w-full gap-2 font-semibold text-white shadow-lg shadow-accent-purple/20 hover:opacity-90"
            size="lg"
            suppressHydrationWarning
          >
            Plan My Trip
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
          Supports Instagram Reels, YouTube Shorts, TikTok videos, or natural
          language descriptions
        </p>
      </motion.div>
    </div>
  );
}
