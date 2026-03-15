import { create } from "zustand";
import type {
  PlaceHighlight,
  ProcessingStage,
  MetadataEvent,
  AnalysisEvent,
  HighlightsEvent,
  CandidateLocation,
  FlowStep,
  UserPreferences,
  TripItinerary,
  AgentProgress,
  CitySuggestion,
  ChatMessage,
} from "./types";

interface ReelTripState {
  // Session
  url: string;
  sessionId: string | null;

  // Processing
  isProcessing: boolean;
  stage: ProcessingStage;
  progress: number;
  stageMessage: string;
  error: string | null;

  // Video metadata
  videoTitle: string;
  thumbnailUrl: string;
  platform: string;
  duration: number;

  // Analysis
  destinationCity: string;
  destinationCountry: string;
  locationConfidence: string;
  dominantVibe: string;
  contentSummary: string;
  detectedActivities: string[];
  candidateLocations: CandidateLocation[];
  targetAudience: string;

  // Highlights
  highlights: PlaceHighlight[];
  primaryCity: string;
  primaryCountry: string;
  cityLatitude: number | null;
  cityLongitude: number | null;

  // UI
  showHighlightsSheet: boolean;

  // Phase 5: Flow
  flowStep: FlowStep;

  // Phase 5: Bucket list
  bucketListSelections: string[];

  // Phase 5: Preferences
  preferences: UserPreferences | null;

  // Phase 5: City selection
  suggestedCities: CitySuggestion[];
  selectedCities: string[];
  isFetchingCities: boolean;
  showCitySelector: boolean;

  // Phase 5: Generation
  agentStatuses: AgentProgress[];
  isGenerating: boolean;

  // Phase 5: Itinerary
  itinerary: TripItinerary | null;
  itineraryId: string | null;

  // Phase 5: Chat
  chatMessages: ChatMessage[];
  isCustomizing: boolean;

  // Phase 5: Itinerary UI
  activeTab: string;

  // Existing actions
  setUrl: (url: string) => void;
  startProcessing: (sessionId: string) => void;
  updateProgress: (stage: string, percent: number, message: string) => void;
  setMetadata: (data: MetadataEvent) => void;
  setAnalysis: (data: AnalysisEvent) => void;
  setHighlights: (data: HighlightsEvent) => void;
  setComplete: () => void;
  setError: (message: string) => void;
  reset: () => void;
  toggleHighlightsSheet: () => void;
  setShowHighlightsSheet: (show: boolean) => void;

  // Phase 5 actions
  setFlowStep: (step: FlowStep) => void;
  setBucketListSelections: (selections: string[]) => void;
  toggleBucketListItem: (placeName: string) => void;
  setPreferences: (prefs: UserPreferences) => void;
  setSuggestedCities: (cities: CitySuggestion[]) => void;
  setSelectedCities: (cities: string[]) => void;
  toggleCity: (city: string) => void;
  setIsFetchingCities: (val: boolean) => void;
  setShowCitySelector: (show: boolean) => void;
  updateAgentStatus: (progress: AgentProgress) => void;
  setIsGenerating: (val: boolean) => void;
  setItinerary: (itinerary: TripItinerary) => void;
  setItineraryId: (id: string) => void;
  addChatMessage: (msg: ChatMessage) => void;
  setIsCustomizing: (val: boolean) => void;
  setActiveTab: (tab: string) => void;
}

const initialState = {
  url: "",
  sessionId: null,
  isProcessing: false,
  stage: "idle" as ProcessingStage,
  progress: 0,
  stageMessage: "",
  error: null,
  videoTitle: "",
  thumbnailUrl: "",
  platform: "",
  duration: 0,
  destinationCity: "",
  destinationCountry: "",
  locationConfidence: "",
  dominantVibe: "",
  contentSummary: "",
  detectedActivities: [] as string[],
  candidateLocations: [] as CandidateLocation[],
  targetAudience: "",
  highlights: [] as PlaceHighlight[],
  primaryCity: "",
  primaryCountry: "",
  cityLatitude: null,
  cityLongitude: null,
  showHighlightsSheet: false,
  // Phase 5
  flowStep: "processing" as FlowStep,
  bucketListSelections: [] as string[],
  preferences: null as UserPreferences | null,
  suggestedCities: [] as CitySuggestion[],
  selectedCities: [] as string[],
  isFetchingCities: false,
  showCitySelector: false,
  agentStatuses: [] as AgentProgress[],
  isGenerating: false,
  itinerary: null as TripItinerary | null,
  itineraryId: null as string | null,
  chatMessages: [] as ChatMessage[],
  isCustomizing: false,
  activeTab: "reservations",
};

export const useStore = create<ReelTripState>((set) => ({
  ...initialState,

  setUrl: (url) => set({ url }),

  startProcessing: (sessionId) =>
    set({ sessionId, isProcessing: true, stage: "extracting", error: null }),

  updateProgress: (stage, percent, message) =>
    set({
      stage: stage as ProcessingStage,
      progress: percent,
      stageMessage: message,
    }),

  setMetadata: (data) =>
    set({
      videoTitle: data.title,
      thumbnailUrl: data.thumbnail_url,
      platform: data.platform,
      duration: data.duration,
    }),

  setAnalysis: (data) =>
    set({
      destinationCity: data.destination_city,
      destinationCountry: data.destination_country,
      locationConfidence: data.location_confidence,
      dominantVibe: data.dominant_vibe,
      contentSummary: data.content_summary,
      detectedActivities: data.detected_activities,
      candidateLocations: data.candidate_locations,
      targetAudience: data.target_audience,
    }),

  setHighlights: (data) =>
    set({
      highlights: data.highlights,
      primaryCity: data.primary_city,
      primaryCountry: data.primary_country,
      cityLatitude: data.city_latitude,
      cityLongitude: data.city_longitude,
      showHighlightsSheet: true,
    }),

  setComplete: () =>
    set({ isProcessing: false, stage: "complete", progress: 100 }),

  setError: (message) =>
    set({ error: message, isProcessing: false, stage: "error" }),

  reset: () => set(initialState),

  toggleHighlightsSheet: () =>
    set((state) => ({ showHighlightsSheet: !state.showHighlightsSheet })),

  setShowHighlightsSheet: (show) => set({ showHighlightsSheet: show }),

  // Phase 5 actions
  setFlowStep: (step) => set({ flowStep: step }),

  setBucketListSelections: (selections) =>
    set({ bucketListSelections: selections }),

  toggleBucketListItem: (placeName) =>
    set((state) => {
      const exists = state.bucketListSelections.includes(placeName);
      return {
        bucketListSelections: exists
          ? state.bucketListSelections.filter((n) => n !== placeName)
          : [...state.bucketListSelections, placeName],
      };
    }),

  setPreferences: (prefs) => set({ preferences: prefs }),

  setSuggestedCities: (cities) => set({ suggestedCities: cities }),

  setSelectedCities: (cities) => set({ selectedCities: cities }),

  toggleCity: (city) =>
    set((state) => {
      const exists = state.selectedCities.includes(city);
      return {
        selectedCities: exists
          ? state.selectedCities.filter((c) => c !== city)
          : [...state.selectedCities, city],
      };
    }),

  setIsFetchingCities: (val) => set({ isFetchingCities: val }),

  setShowCitySelector: (show) => set({ showCitySelector: show }),

  updateAgentStatus: (progress) =>
    set((state) => {
      const idx = state.agentStatuses.findIndex(
        (a) => a.agent === progress.agent
      );
      const updated = [...state.agentStatuses];
      if (idx >= 0) updated[idx] = progress;
      else updated.push(progress);
      return { agentStatuses: updated };
    }),

  setIsGenerating: (val) => set({ isGenerating: val }),

  setItinerary: (itinerary) => set({ itinerary }),

  setItineraryId: (id) => set({ itineraryId: id }),

  addChatMessage: (msg) =>
    set((state) => ({ chatMessages: [...state.chatMessages, msg] })),

  setIsCustomizing: (val) => set({ isCustomizing: val }),

  setActiveTab: (tab) => set({ activeTab: tab }),
}));
