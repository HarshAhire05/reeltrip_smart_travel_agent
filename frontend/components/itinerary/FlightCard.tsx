"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plane, ExternalLink, AlertCircle, CheckCircle2, Loader2, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useStore } from "@/lib/store";
import type { FlightReservation, FlightBookingStatus, FlightStatusResponse } from "@/lib/types";

const TRIGGER_API = "http://localhost:8001";
const POLL_INTERVAL_MS = 2000;
const AGENT_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes

// ── Status display config ──────────────────────────────────────────────────────
// Keys match the backend write_status() calls exactly, in order
const STATUS_STEPS: { key: FlightBookingStatus; label: string }[] = [
  { key: "initializing",           label: "Opening browser" },
  { key: "opening_browser",        label: "Opening Google Flights" },
  { key: "opening_google_flights", label: "Opening Google Flights" },  // alias
  { key: "searching_flights",      label: "Searching flights" },
  { key: "filling_cities",         label: "Filling route details" },
  { key: "filling_route_details",  label: "Filling route details" },  // alias
  { key: "selecting_date",         label: "Setting travel date" },
  { key: "setting_travel_date",    label: "Setting travel date" },    // alias
  { key: "picking_cheapest",       label: "Selecting best option" },
  { key: "selecting_best_option",  label: "Selecting best option" },
  { key: "proceeding_to_booking",  label: "Proceeding to booking page" },
  { key: "booking_page_open",      label: "Booking page is ready! ✅" },
];

// Show unique labels only
const STATUS_STEPS_DISPLAY = STATUS_STEPS.filter(
  (step, idx, arr) => arr.findIndex((s) => s.label === step.label) === idx
);

const STATUS_ORDER = STATUS_STEPS.map((s) => s.key);

function getStepState(stepKey: FlightBookingStatus, currentStatus: FlightBookingStatus) {
  const stepIdx    = STATUS_ORDER.indexOf(stepKey);
  const currentIdx = STATUS_ORDER.indexOf(currentStatus);
  if (currentIdx === -1) return "pending";
  if (stepIdx < currentIdx)  return "done";
  if (stepIdx === currentIdx) return "active";
  return "pending";
}

// ── Date helpers ───────────────────────────────────────────────────────────────

/** Returns next N months as { value: "YYYY-MM", label: "Month YYYY" } */
function getNextMonths(count = 14): { value: string; label: string }[] {
  const months: { value: string; label: string }[] = [];
  const now = new Date();
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
    months.push({
      value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
      label: d.toLocaleString("default", { month: "long", year: "numeric" }),
    });
  }
  return months;
}

/** Returns number of days in a given "YYYY-MM" month string */
function daysInMonth(monthValue: string): number {
  if (!monthValue) return 31;
  const [year, month] = monthValue.split("-").map(Number);
  return new Date(year, month, 0).getDate();
}

/** Build "YYYY-MM-DD" string from month value + day number */
function buildDate(monthValue: string, day: string): string {
  if (!monthValue || !day) return "";
  const [year, month] = monthValue.split("-");
  return `${year}-${month}-${String(day).padStart(2, "0")}`;
}

// ── Formatters ─────────────────────────────────────────────────────────────────

function formatTime(datetime: string) {
  try {
    const d = new Date(datetime);
    return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch { return datetime; }
}

function formatDate(datetime: string): string {
  try {
    return new Date(datetime).toISOString().split("T")[0];
  } catch { return datetime; }
}

// ── Date Form internal state type ─────────────────────────────────────────────

interface DateFormState {
  tripType:     "round_trip" | "one_way";
  travelMonth:  string; // "YYYY-MM"
  travelDay:    string; // "1"–"31"
  returnMonth:  string;
  returnDay:    string;
}

// ── Main component ─────────────────────────────────────────────────────────────

export function FlightCard({
  flight,
  index = 0,
  itineraryStartDate,
  itineraryEndDate,
  flightLegIndex = 0,
}: {
  flight: FlightReservation;
  index?: number;
  itineraryStartDate?: string;
  itineraryEndDate?: string;
  flightLegIndex?: number;
}) {
  const { sessionId, passengerContact, preferences, setPassengerContact } = useStore();

  // ── Booking UI state ────────────────────────────────────────────────────────
  const [bookingStatus, setBookingStatus] = useState<"idle" | "date_form" | "contact_form" | "triggered" | "done" | "error">("idle");
  const [agentStatus,  setAgentStatus]    = useState<FlightBookingStatus>("initializing");
  const [statusMessage,setStatusMessage]  = useState("");
  const [errorDetail,  setErrorDetail]    = useState<string | null>(null);
  const [timedOut,     setTimedOut]       = useState(false);

  // ── Contact form state (shown when phone missing) ───────────────────────────
  const [inlineContact, setInlineContact] = useState({ name: "", email: "", phone: "" });
  const [contactError,  setContactError]  = useState("");

  // ── Date form state (shown before triggering agent) ─────────────────────────
  const [dateForm, setDateForm] = useState<DateFormState>({
    tripType:    "round_trip",
    travelMonth: "",
    travelDay:   "",
    returnMonth: "",
    returnDay:   "",
  });
  const [dateError, setDateError] = useState("");

  const pollTimer    = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutTimer = useRef<ReturnType<typeof setTimeout>  | null>(null);
  const flightId     = `leg_${flightLegIndex + 1}`;

  const MONTHS = useMemo(() => getNextMonths(14), []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollTimer.current)    clearInterval(pollTimer.current);
      if (timeoutTimer.current) clearTimeout(timeoutTimer.current);
    };
  }, []);

  // ── Polling ─────────────────────────────────────────────────────────────────
  const startPolling = useCallback((sid: string, fid: string) => {
    let lastStatusTime = Date.now();
    const silenceThreshold = 60000; // 60 seconds

    pollTimer.current = setInterval(async () => {
      try {
        const res  = await fetch(`${TRIGGER_API}/flight-status/${sid}/${fid}`);
        if (!res.ok) throw new Error("Agent unreachable");
        const data: FlightStatusResponse = await res.json();

        lastStatusTime = Date.now();

        setAgentStatus(data.status);
        setStatusMessage(data.message || "");

        if (data.status === "booking_page_open") {
          setBookingStatus("done");
          clearInterval(pollTimer.current!);
          clearTimeout(timeoutTimer.current!);
        } else if (data.status === "error") {
          setBookingStatus("error");
          setErrorDetail(data.error_detail ?? null);
          clearInterval(pollTimer.current!);
          clearTimeout(timeoutTimer.current!);
        }
      } catch {
        // transient or agent crashed
        const timeSilent = Date.now() - lastStatusTime;
        if (timeSilent > silenceThreshold) {
          setBookingStatus("error");
          setErrorDetail("⚠️ The agent stopped responding. The Chrome browser may have closed. Use 'Open Google Flights manually' to continue.");
          clearInterval(pollTimer.current!);
          clearTimeout(timeoutTimer.current!);
        }
      }
    }, POLL_INTERVAL_MS);

    timeoutTimer.current = setTimeout(() => {
      setTimedOut(true);
      clearInterval(pollTimer.current!);
    }, AGENT_TIMEOUT_MS);
  }, []);

  // ── Core trigger: fire the agent with dates ─────────────────────────────────
  const triggerAgent = useCallback(
    async (
      contact:    { name: string; email: string; phone: string; num_people: number },
      travelDate: string,
      returnDate: string | null,
      tripType:   string,
    ) => {
      const sid = sessionId || crypto.randomUUID();
      const budgetToType: Record<string, string> = {
        budget: "budget", "mid-range": "medium", luxury: "luxury", "ultra-luxury": "luxury",
      };
      const budgetType = budgetToType[preferences?.accommodation_tier ?? "mid-range"] ?? "medium";

      const payload = {
        flight_id:         flightId,
        flight_type:       flight.type?.toLowerCase().includes("international") ? "international" : "domestic",
        origin:            { city: flight.from_city ?? "", iata: flight.from_airport_code ?? "" },
        destination:       { city: flight.to_city   ?? "", iata: flight.to_airport_code   ?? "" },
        departure_time:    formatTime(flight.departure_datetime),
        arrival_time:      formatTime(flight.arrival_datetime),
        duration:          flight.duration ?? "",
        travel_date:       travelDate,        // ← from date form ✅
        return_date:       returnDate,         // ← from date form ✅
        trip_type:         tripType,           // ← from date form ✅
        num_passengers:    preferences?.number_of_travelers ?? contact.num_people ?? 1,
        price_per_person:  flight.estimated_price ?? 0,
        currency:          flight.price_currency ?? "INR",
        budget_type:       budgetType,
        passenger_details: { name: contact.name, email: contact.email, phone: contact.phone },
        session_id:        sid,
      };

      try {
        const res = await fetch(`${TRIGGER_API}/trigger-flight`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        const data = await res.json();

        if (data.status === "agent_started") {
          setBookingStatus("triggered");
          setAgentStatus("initializing");
          startPolling(sid, flightId);
        } else {
          throw new Error(data.error || "Unexpected response from trigger API");
        }
      } catch (err) {
        setBookingStatus("error");
        setErrorDetail(String(err));
      }
    },
    [flight, flightId, sessionId, preferences, startPolling]
  );

  // ── Date form validation + submit ─────────────────────────────────────────
  const handleDateConfirm = useCallback(() => {
    setDateError("");

    const travelDate = buildDate(dateForm.travelMonth, dateForm.travelDay);
    if (!travelDate) {
      setDateError("Please select a departure month and day.");
      return;
    }

    let returnDate: string | null = null;
    if (dateForm.tripType === "round_trip") {
      returnDate = buildDate(dateForm.returnMonth, dateForm.returnDay);
      if (!returnDate) {
        setDateError("Please select a return month and day.");
        return;
      }
      if (returnDate <= travelDate) {
        setDateError("Return date must be after departure date.");
        return;
      }
    }

    // Dates valid — check if we have contact info
    const contact = passengerContact;
    if (!contact || !contact.phone) {
      setBookingStatus("contact_form");
      // Store dates so contact form submit can use them
      (window as any).__pendingDates = { travelDate, returnDate, tripType: dateForm.tripType };
      return;
    }

    triggerAgent(
      { name: contact.name, email: contact.email, phone: contact.phone, num_people: contact.num_people },
      travelDate,
      returnDate,
      dateForm.tripType,
    );
  }, [dateForm, passengerContact, triggerAgent]);

  // ── Contact form submit ────────────────────────────────────────────────────
  const handleContactSubmit = useCallback(() => {
    if (!inlineContact.phone.trim()) {
      setContactError("Phone number is required for flight booking");
      return;
    }
    setContactError("");
    const contactData = {
      name:       inlineContact.name,
      email:      inlineContact.email,
      phone:      inlineContact.phone,
      num_people: preferences?.number_of_travelers ?? 1,
    };
    setPassengerContact(contactData);

    // Retrieve pending dates
    const pending = (window as any).__pendingDates ?? {};
    const travelDate = pending.travelDate || formatDate(flight.departure_datetime) || (itineraryStartDate ?? "");
    const returnDate = pending.returnDate ?? (itineraryEndDate ?? null);
    const tripType   = pending.tripType   ?? (returnDate ? "round_trip" : "one_way");

    triggerAgent(contactData, travelDate, returnDate, tripType);
  }, [inlineContact, preferences, setPassengerContact, triggerAgent, flight, itineraryStartDate, itineraryEndDate]);

  // ── Book Now click ─────────────────────────────────────────────────────────
  const handleBookNow = useCallback(() => {
    if (bookingStatus !== "idle") return;
    setBookingStatus("date_form");
  }, [bookingStatus]);

  const fallbackUrl =
    flight.booking_url ||
    `https://www.google.com/travel/flights?q=Flights+from+${flight.from_airport_code}+to+${flight.to_airport_code}`;

  // Day options for a given month selection
  const travelDays = useMemo(
    () => Array.from({ length: daysInMonth(dateForm.travelMonth) }, (_, i) => i + 1),
    [dateForm.travelMonth]
  );
  const returnDays = useMemo(
    () => Array.from({ length: daysInMonth(dateForm.returnMonth) }, (_, i) => i + 1),
    [dateForm.returnMonth]
  );

  const selectClass =
    "w-full h-8 text-xs bg-bg-secondary border border-glass-border text-text-primary rounded-md px-2 focus:outline-none focus:ring-1 focus:ring-accent-purple/50";

  return (
    <motion.div
      className="glass-card-hover p-4 relative overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      {/* Type badge */}
      <div className="flex items-center justify-between mb-3">
        <Badge
          variant="outline"
          className="border-accent-purple/30 bg-accent-purple/10 text-text-accent text-xs capitalize"
        >
          {flight.type}
        </Badge>
        {flight.notes && (
          <span className="text-xs text-text-secondary">{flight.notes}</span>
        )}
      </div>

      {/* Flight route */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Departure */}
        <div className="flex-1 text-center min-w-0">
          <p className="text-xl sm:text-2xl font-bold text-text-primary truncate">
            {flight.from_airport_code ?? "???"}
          </p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">{flight.from_city ?? ""}</p>
          <p className="text-sm font-medium text-text-accent mt-1">
            {formatTime(flight.departure_datetime)}
          </p>
        </div>

        {/* Center line with plane */}
        <div className="flex-1 flex flex-col items-center gap-1">
          <p className="text-xs text-text-secondary">{flight.duration ?? ""}</p>
          <div className="relative w-full flex items-center">
            <div className="flex-1 border-t-2 border-dashed border-glass-border" />
            <Plane className="h-4 w-4 text-accent-purple mx-1" />
            <div className="flex-1 border-t-2 border-dashed border-glass-border" />
          </div>
        </div>

        {/* Arrival */}
        <div className="flex-1 text-center min-w-0">
          <p className="text-xl sm:text-2xl font-bold text-text-primary truncate">
            {flight.to_airport_code ?? "???"}
          </p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">{flight.to_city ?? ""}</p>
          <p className="text-sm font-medium text-text-accent mt-1">
            {formatTime(flight.arrival_datetime)}
          </p>
        </div>
      </div>

      {/* ── DATE SELECTION MINI-FORM ── */}
      <AnimatePresence>
        {bookingStatus === "date_form" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-3 border-t border-glass-border space-y-3 overflow-hidden"
          >
            <div className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-accent-purple" />
              <p className="text-xs font-semibold text-text-accent">When do you want to fly?</p>
            </div>

            {/* Trip type radio */}
            <div className="flex gap-4">
              {(["round_trip", "one_way"] as const).map((type) => (
                <label key={type} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name={`trip-type-${flightId}`}
                    value={type}
                    checked={dateForm.tripType === type}
                    onChange={() => setDateForm((f) => ({ ...f, tripType: type }))}
                    className="accent-purple-500"
                  />
                  <span className="text-xs text-text-secondary capitalize">
                    {type === "round_trip" ? "Round Trip" : "One Way"}
                  </span>
                </label>
              ))}
            </div>

            {/* Departure date row */}
            <div>
              <p className="text-xs text-text-secondary mb-1">Departure date</p>
              <div className="grid grid-cols-2 gap-2">
                <select
                  id={`travel-month-${flightId}`}
                  value={dateForm.travelMonth}
                  onChange={(e) =>
                    setDateForm((f) => ({ ...f, travelMonth: e.target.value, travelDay: "" }))
                  }
                  className={selectClass}
                >
                  <option value="">Month</option>
                  {MONTHS.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
                <select
                  id={`travel-day-${flightId}`}
                  value={dateForm.travelDay}
                  onChange={(e) => setDateForm((f) => ({ ...f, travelDay: e.target.value }))}
                  disabled={!dateForm.travelMonth}
                  className={selectClass}
                >
                  <option value="">Day</option>
                  {travelDays.map((d) => (
                    <option key={d} value={String(d)}>{d}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Return date row (hidden for one-way) */}
            {dateForm.tripType === "round_trip" && (
              <div>
                <p className="text-xs text-text-secondary mb-1">Return date</p>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    id={`return-month-${flightId}`}
                    value={dateForm.returnMonth}
                    onChange={(e) =>
                      setDateForm((f) => ({ ...f, returnMonth: e.target.value, returnDay: "" }))
                    }
                    className={selectClass}
                  >
                    <option value="">Month</option>
                    {MONTHS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                  <select
                    id={`return-day-${flightId}`}
                    value={dateForm.returnDay}
                    onChange={(e) => setDateForm((f) => ({ ...f, returnDay: e.target.value }))}
                    disabled={!dateForm.returnMonth}
                    className={selectClass}
                  >
                    <option value="">Day</option>
                    {returnDays.map((d) => (
                      <option key={d} value={String(d)}>{d}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Validation error */}
            {dateError && (
              <p className="text-xs text-red-400">{dateError}</p>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                id={`confirm-dates-${flightId}`}
                size="sm"
                className="flex-1 h-7 text-xs accent-gradient text-white"
                onClick={handleDateConfirm}
              >
                Confirm &amp; Search Flights →
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs border-glass-border text-text-secondary"
                onClick={() => setBookingStatus("idle")}
              >
                Cancel
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── CONTACT FORM (shown when phone missing + dates already collected) ── */}
      <AnimatePresence>
        {bookingStatus === "contact_form" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-3 border-t border-glass-border space-y-2 overflow-hidden"
          >
            <p className="text-xs text-text-secondary font-medium">
              ✈️ Enter contact details to confirm booking:
            </p>
            <Input
              id={`contact-name-${flightId}`}
              placeholder="Full name (optional)"
              value={inlineContact.name}
              onChange={(e) => setInlineContact((p) => ({ ...p, name: e.target.value }))}
              className="h-8 text-xs border-glass-border bg-bg-secondary text-text-primary"
            />
            <div className="grid grid-cols-2 gap-2">
              <Input
                id={`contact-email-${flightId}`}
                type="email"
                placeholder="Email (optional)"
                value={inlineContact.email}
                onChange={(e) => setInlineContact((p) => ({ ...p, email: e.target.value }))}
                className="h-8 text-xs border-glass-border bg-bg-secondary text-text-primary"
              />
              <Input
                id={`contact-phone-${flightId}`}
                type="tel"
                placeholder="Phone *"
                value={inlineContact.phone}
                onChange={(e) => setInlineContact((p) => ({ ...p, phone: e.target.value }))}
                className="h-8 text-xs border-glass-border bg-bg-secondary text-text-primary"
              />
            </div>
            {contactError && <p className="text-xs text-red-400">{contactError}</p>}
            <div className="flex gap-2">
              <Button
                size="sm"
                className="flex-1 h-7 text-xs accent-gradient text-white"
                onClick={handleContactSubmit}
              >
                Book with Agent
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs border-glass-border text-text-secondary"
                onClick={() => setBookingStatus("date_form")}
              >
                Back
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── PROGRESS OVERLAY (shown after agent triggered) ── */}
      <AnimatePresence>
        {(bookingStatus === "triggered" || bookingStatus === "done" || bookingStatus === "error") && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 pt-3 border-t border-glass-border"
          >
            {/* Steps */}
            <div className="space-y-1.5 mb-3">
              {STATUS_STEPS_DISPLAY.map((step) => {
                const state = getStepState(step.key, agentStatus);
                return (
                  <div key={step.key} className="flex items-center gap-2">
                    {state === "done" && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-400 shrink-0" />
                    )}
                    {state === "active" && (
                      <Loader2 className="h-3.5 w-3.5 text-accent-purple shrink-0 animate-spin" />
                    )}
                    {state === "pending" && (
                      <div className="h-3.5 w-3.5 rounded-full border border-glass-border shrink-0" />
                    )}
                    <span
                      className={`text-xs ${
                        state === "done"
                          ? "text-green-400"
                          : state === "active"
                          ? "text-text-accent font-medium"
                          : "text-text-secondary/50"
                      }`}
                    >
                      {step.label}
                      {state === "active" && statusMessage && (
                        <span className="ml-1 text-text-secondary font-normal">
                          — {statusMessage}
                        </span>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Error state */}
            {bookingStatus === "error" && (
              <div className="rounded-lg border border-red-500/30 bg-red-950/30 p-4 mb-2">
                <div className="flex items-center gap-2 text-red-400 font-medium mb-1">
                  <span>⚠️</span>
                  <span>Automated booking hit an issue.</span>
                </div>
                <p className="text-red-300 text-sm ml-6">
                  {statusMessage || errorDetail || "An unexpected error occurred. Please use the manual Google Flights link below."}
                </p>
                <p className="text-red-400/60 text-xs ml-6 mt-1">
                  A screenshot has been saved to ./debug_screenshots/ for debugging.
                </p>
              </div>
            )}

            {/* Timeout notice */}
            {timedOut && bookingStatus !== "done" && bookingStatus !== "error" && (
              <p className="text-xs text-yellow-400 mt-2 mb-1">
                ⌛ Taking longer than expected. Check your Chrome window.
              </p>
            )}

            {/* Fallback link — always visible */}
            <a
              href={fallbackUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary transition-colors mt-1"
            >
              <ExternalLink className="h-3 w-3" />
              Open Google Flights manually
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── BOTTOM ROW — price + Book Now / status button ── */}
      {(bookingStatus === "idle" || bookingStatus === "triggered" || bookingStatus === "done" || bookingStatus === "error") && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-glass-border gap-2">
          <p className="text-sm font-semibold text-text-primary min-w-0 truncate">
            ~{flight.price_currency ?? ""}{" "}
            {(flight.estimated_price ?? 0).toLocaleString()}
            <span className="text-xs text-text-secondary font-normal ml-1">/person</span>
          </p>

          {bookingStatus === "idle" && (
            <Button
              id={`book-now-${flightId}`}
              size="sm"
              className="gap-1.5 accent-gradient text-white shrink-0 hover:opacity-90"
              onClick={handleBookNow}
            >
              Book Now
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          )}

          {bookingStatus === "triggered" && (
            <Button
              size="sm"
              variant="outline"
              disabled
              className="gap-1.5 border-glass-border text-text-secondary shrink-0"
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Agent Running...
            </Button>
          )}

          {bookingStatus === "done" && (
            <span className="text-xs text-green-400 font-medium shrink-0">
              ✅ Booking page open
            </span>
          )}

          {bookingStatus === "error" && (
            <a href={fallbackUrl} target="_blank" rel="noopener noreferrer">
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 border-glass-border text-text-secondary shrink-0"
              >
                Book Manually
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </a>
          )}
        </div>
      )}
    </motion.div>
  );
}
