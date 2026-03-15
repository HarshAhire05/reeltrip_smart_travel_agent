export interface PlaceHighlight {
  place_name: string;
  place_id: string;
  photo_url: string | null;
  latitude: number;
  longitude: number;
  formatted_address: string;
  rating: number | null;
  description: string;
  vibe_tags: string[];
  signature_experiences: string[];
  best_time_to_visit: string;
  know_more: string;
  estimated_visit_duration: string;
  estimated_cost_usd: number;
  google_maps_url: string;
  source: string;
}

export interface CandidateLocation {
  name: string;
  type: string;
  mentioned_in: string[];
  confidence: string;
}

export interface MetadataEvent {
  title: string;
  thumbnail_url: string;
  platform: string;
  duration: number;
}

export interface AnalysisEvent {
  destination_country: string;
  destination_region: string;
  destination_city: string;
  location_confidence: string;
  candidate_locations: CandidateLocation[];
  dominant_vibe: string;
  content_summary: string;
  detected_activities: string[];
  target_audience: string;
}

export interface HighlightsEvent {
  highlights: PlaceHighlight[];
  primary_city: string;
  primary_country: string;
  city_latitude: number;
  city_longitude: number;
}

export interface CompleteEvent {
  session_id: string;
  destination: string;
}

export interface SessionEvent {
  session_id: string;
}

export interface ProgressEvent {
  stage: string;
  percent: number;
  message: string;
}

export interface ErrorEvent {
  message: string;
}

export type ProcessingStage =
  | "idle"
  | "extracting"
  | "analyzing"
  | "locating"
  | "highlights"
  | "complete"
  | "error";

// --- Phase 5 Types ---

export type FlowStep =
  | "processing"
  | "highlights"
  | "bucketList"
  | "preferences"
  | "citySelector"
  | "generating"
  | "itinerary";

export interface UserPreferences {
  trip_duration_days: number;
  number_of_travelers: number;
  traveling_with: "solo" | "partner" | "family" | "friends";
  month_of_travel: string;
  total_budget: number;
  budget_currency: string;
  travel_styles: string[];
  dietary_preferences: string[];
  accommodation_tier: "budget" | "mid-range" | "luxury" | "ultra-luxury";
  must_include_places: string[];
  additional_notes: string;
  home_city: string;
  home_country: string;
}

export interface FlightReservation {
  type: string;
  from_city: string;
  from_airport_code: string;
  to_city: string;
  to_airport_code: string;
  departure_datetime: string;
  arrival_datetime: string;
  duration: string;
  estimated_price: number;
  price_currency: string;
  booking_url: string;
  notes: string | null;
  day_number: number;
}

export interface HotelReservation {
  hotel_name: string;
  city: string;
  address: string;
  check_in_date: string;
  check_out_date: string;
  nights: number;
  price_per_night: number;
  total_price: number;
  price_currency: string;
  rating: number;
  photo_url: string | null;
  why_recommended: string;
  booking_url: string;
  latitude: number;
  longitude: number;
}

export interface Activity {
  time: string;
  title: string;
  type:
    | "flight"
    | "checkin"
    | "checkout"
    | "meal"
    | "attraction"
    | "activity"
    | "transport"
    | "free_time";
  venue_name: string | null;
  venue_address: string | null;
  latitude: number | null;
  longitude: number | null;
  photo_url: string | null;
  rating: number | null;
  duration_minutes: number;
  estimated_cost: number;
  cost_currency: string;
  description: string;
  practical_tip: string | null;
  booking_url: string | null;
  google_maps_url: string | null;
}

export interface ItineraryDay {
  day_number: number;
  date: string;
  city: string;
  theme: string;
  activities: Activity[];
}

export interface BudgetBreakdown {
  flights_total: number;
  accommodation_total: number;
  food_total: number;
  activities_total: number;
  transportation_total: number;
  miscellaneous_buffer: number;
  grand_total: number;
  currency: string;
  budget_status: "within_budget" | "over_budget" | "under_budget";
  savings_tips: string[] | null;
}

export interface VisaInfo {
  required: boolean;
  visa_type: string;
  processing_time: string;
  estimated_cost: string;
  documents_needed: string[];
  notes: string;
}

export interface WeatherSummary {
  overview: string;
  avg_high_celsius: number;
  avg_low_celsius: number;
  precipitation_chance: string;
  pack_suggestions: string[];
}

export interface CurrencyInfo {
  local_currency: string;
  local_currency_name: string;
  exchange_rate: string;
  tips: string[];
}

export interface EmergencyInfo {
  police: string;
  ambulance: string;
  fire: string;
  tourist_police: string;
  embassy_phone: string;
  emergency_notes: string[];
}

export interface TripItinerary {
  trip_title: string;
  destination_country: string;
  destination_cities: string[];
  start_date: string;
  end_date: string;
  total_days: number;
  total_travelers: number;
  flights: FlightReservation[];
  hotels: HotelReservation[];
  days: ItineraryDay[];
  budget_breakdown: BudgetBreakdown;
  visa_requirements: VisaInfo | null;
  weather_summary: WeatherSummary;
  packing_suggestions: string[];
  cultural_tips: string[];
  emergency_info: EmergencyInfo;
  currency_info: CurrencyInfo;
}

export interface AgentProgress {
  agent: string;
  status: "working" | "complete" | "failed";
  message: string;
}

export interface CitySuggestion {
  city: string;
  country: string;
  why: string;
  recommended_days: number;
  distance_from_primary: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}
