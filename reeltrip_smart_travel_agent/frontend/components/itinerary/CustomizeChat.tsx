"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Send, Loader2, RotateCcw } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { useStore } from "@/lib/store";
import { streamPost } from "@/lib/sse";
import { API_BASE } from "@/lib/api";

const SUGGESTIONS = [
  "Add more restaurants",
  "Make it more budget-friendly",
  "Add cultural experiences",
  "Change hotel to luxury",
  "Add a day trip",
  "Swap an activity",
];

export function CustomizeChat() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const lastMessageRef = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const {
    chatMessages,
    isCustomizing,
    itineraryId,
    sessionId,
    addChatMessage,
    setIsCustomizing,
    setItinerary,
  } = useStore();

  console.log("[Customize] sessionId:", sessionId, "itineraryId:", itineraryId);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages, isCustomizing]);

  const handleSend = (text?: string) => {
    const message = text || input.trim();
    if (!message) return;
    if (!sessionId || !itineraryId) {
      addChatMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Unable to customize — session data is missing. Please regenerate your itinerary.",
        timestamp: Date.now(),
      });
      return;
    }

    lastMessageRef.current = message;

    // Add user message
    addChatMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: message,
      timestamp: Date.now(),
    });
    setInput("");
    setIsCustomizing(true);

    // Stream customization
    streamPost(
      `${API_BASE}/api/v1/itinerary/customize`,
      {
        session_id: sessionId,
        itinerary_id: itineraryId,
        request: message,
      },
      (event) => {
        switch (event.event) {
          case "itinerary":
            setItinerary(
              event.data as Parameters<typeof setItinerary>[0]
            );
            setIsCustomizing(false);
            break;
          case "complete":
            addChatMessage({
              id: crypto.randomUUID(),
              role: "assistant",
              content:
                "Itinerary updated! Scroll through tabs to see changes.",
              timestamp: Date.now(),
            });
            setIsCustomizing(false);
            break;
          case "error":
            addChatMessage({
              id: crypto.randomUUID(),
              role: "assistant",
              content: `Sorry, I couldn't make that change: ${(event.data as { message: string }).message}`,
              timestamp: Date.now(),
            });
            setIsCustomizing(false);
            break;
        }
      },
      (err) => {
        addChatMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Error: ${err.message}`,
          timestamp: Date.now(),
        });
        setIsCustomizing(false);
      }
    );
  };

  const handleRetry = () => {
    if (lastMessageRef.current) {
      handleSend(lastMessageRef.current);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Show suggestions when no messages or after last assistant message
  const lastMsg = chatMessages[chatMessages.length - 1];
  const showSuggestions =
    !isCustomizing &&
    (chatMessages.length === 0 ||
      (lastMsg && lastMsg.role === "assistant"));

  return (
    <>
      {/* Floating button */}
      <motion.button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full accent-gradient shadow-lg shadow-accent-purple/30 text-white"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.5 }}
      >
        <MessageSquare className="h-6 w-6" />
      </motion.button>

      {/* Chat sheet */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="right"
          className="w-full border-glass-border bg-bg-primary sm:max-w-md p-0 flex flex-col overflow-hidden"
        >
          <SheetHeader className="shrink-0 px-6 pt-6 pb-2">
            <SheetTitle className="text-lg font-bold text-text-primary">
              Customise Itinerary
            </SheetTitle>
            <p className="text-sm text-text-secondary">
              Tell me what you&apos;d like to change.
            </p>
          </SheetHeader>

          {/* Messages */}
          <div
            ref={scrollRef}
            className="flex-1 min-h-0 overflow-y-auto px-6 py-4"
          >
            <div className="space-y-4">
              {chatMessages.length === 0 && (
                <p className="text-sm text-text-secondary text-center py-8">
                  Ask me to modify your itinerary — change hotels, add
                  activities, adjust the budget, and more.
                </p>
              )}

              {chatMessages.map((msg) => {
                const isError =
                  msg.role === "assistant" &&
                  msg.content.startsWith("Error:");

                return (
                  <motion.div
                    key={msg.id}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div
                      className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                        msg.role === "user"
                          ? "accent-gradient text-white"
                          : isError
                            ? "glass-card text-error border border-error/20"
                            : "glass-card text-text-primary"
                      }`}
                    >
                      {msg.content}
                      {isError && (
                        <button
                          onClick={handleRetry}
                          className="mt-2 flex items-center gap-1 text-xs text-text-accent hover:text-accent-purple-light transition-colors"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Retry
                        </button>
                      )}
                    </div>
                  </motion.div>
                );
              })}

              {/* Typing indicator */}
              {isCustomizing && (
                <motion.div
                  className="flex justify-start"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="glass-card px-4 py-2.5 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 text-accent-purple spin-slow" />
                    <span className="text-sm text-text-secondary">
                      Updating itinerary...
                    </span>
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Suggestion chips + input */}
          <div className="shrink-0 border-t border-glass-border bg-bg-primary/90 backdrop-blur-sm p-4">
            {/* Suggestions */}
            {showSuggestions && (
              <div className="flex flex-wrap gap-2 mb-3">
                {SUGGESTIONS.map((s) => (
                  <Badge
                    key={s}
                    variant="outline"
                    className="cursor-pointer border-glass-border text-text-secondary hover:bg-accent-purple/10 hover:text-text-accent transition-colors"
                    onClick={() => handleSend(s)}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your change request..."
                rows={1}
                className="flex-1 resize-none rounded-xl border border-glass-border bg-bg-secondary px-4 py-2.5 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none input-glow"
                disabled={isCustomizing}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isCustomizing}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl accent-gradient text-white transition-opacity disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
