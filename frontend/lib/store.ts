import { create } from "zustand";
import { persist } from "zustand/middleware";
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
  InputMode,
  IntentClassification,
  ClarificationOption,
  PassengerContactInfo,
} from "./types";

interface ReelTripState {
  // Session
  url: string;
  textInput: string; // Text-based travel intent
  inputMode: InputMode; // "url" or "text"
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
  highlightsSummary: string; // For text mode: excitement paragraph about destination
  primaryCity: string;
  primaryCountry: string;
  cityLatitude: number | null;
  cityLongitude: number | null;

  // Text mode specific
  intentClassification: IntentClassification | null;
  needsClarification: boolean;
  clarificationOptions: ClarificationOption[];

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

  // Re-plan feature
  originalPreferences: UserPreferences | null;
  itineraryVersions: TripItinerary[];
  isReplanning: boolean;
  replanAgentStatuses: AgentProgress[];
  changedFields: string[];

  // Phase 5: Chat
  chatMessages: ChatMessage[];
  isCustomizing: boolean;

  // Phase 5: Itinerary UI
  activeTab: string;

  // Flight Agent Integration — passenger contact (zero re-entry)
  passengerContact: PassengerContactInfo | null;

  // Existing actions
  setUrl: (url: string) => void;
  setTextInput: (text: string) => void;
  setInputMode: (mode: InputMode) => void;
  startProcessing: (sessionId: string) => void;
  updateProgress: (stage: string, percent: number, message: string) => void;
  setMetadata: (data: MetadataEvent) => void;
  setAnalysis: (data: AnalysisEvent) => void;
  setHighlights: (data: HighlightsEvent) => void;
  setIntentClassification: (data: IntentClassification) => void;
  setClarificationOptions: (options: ClarificationOption[]) => void;
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
  
  // Re-plan actions
  saveOriginalPreferences: () => void;
  pushItineraryVersion: (itinerary: TripItinerary) => void;
  undoItinerary: () => void;
  setChangedFields: (fields: string[]) => void;
  updateReplanAgentStatus: (progress: AgentProgress) => void;
  setReplanning: (val: boolean) => void;
  clearVersions: () => void;

  // Flight Agent actions
  setPassengerContact: (contact: PassengerContactInfo) => void;
}

const initialState = {
  url: "",
  textInput: "",
  inputMode: "url" as InputMode,
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
  highlightsSummary: "",
  primaryCity: "",
  primaryCountry: "",
  cityLatitude: null,
  cityLongitude: null,
  intentClassification: null as IntentClassification | null,
  needsClarification: false,
  clarificationOptions: [] as ClarificationOption[],
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
  // Re-plan
  originalPreferences: null as UserPreferences | null,
  itineraryVersions: [] as TripItinerary[],
  isReplanning: false,
  replanAgentStatuses: [] as AgentProgress[],
  changedFields: [] as string[],
  // Flight Agent
  passengerContact: null as PassengerContactInfo | null,
};

export const useStore = create<ReelTripState>((set) => ({
  ...initialState,

  setUrl: (url) => set({ url }),

  setTextInput: (text) => set({ textInput: text }),

  setInputMode: (mode) => set({ inputMode: mode }),

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

  setIntentClassification: (data) =>
    set({
      intentClassification: data,
      needsClarification: data.needs_clarification,
    }),

  setClarificationOptions: (options) => set({ clarificationOptions: options }),

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
        (a) => a.agent === progress.agent,
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
  
  // Re-plan actions
  saveOriginalPreferences: () =>
    set((state) => ({
      originalPreferences: state.preferences ? { ...state.preferences } : null,
    })),

  pushItineraryVersion: (itinerary) =>
    set((state) => {
      const versions = [...state.itineraryVersions, itinerary];
      // Keep max 5 versions (LIFO stack)
      if (versions.length > 5) {
        versions.shift(); // Remove oldest
      }
      return { itineraryVersions: versions };
    }),

  undoItinerary: () =>
    set((state) => {
      if (state.itineraryVersions.length === 0) return state;
      
      const versions = [...state.itineraryVersions];
      const previousItinerary = versions.pop();
      
      return {
        itinerary: previousItinerary || null,
        itineraryVersions: versions,
      };
    }),

  setChangedFields: (fields) => set({ changedFields: fields }),

  updateReplanAgentStatus: (progress) =>
    set((state) => {
      const existing = state.replanAgentStatuses.find(
        (s) => s.agent === progress.agent
      );
      if (existing) {
        return {
          replanAgentStatuses: state.replanAgentStatuses.map((s) =>
            s.agent === progress.agent ? progress : s
          ),
        };
      } else {
        return {
          replanAgentStatuses: [...state.replanAgentStatuses, progress],
        };
      }
    }),

  setReplanning: (val) => set({ isReplanning: val, replanAgentStatuses: val ? [] : [] }),

  clearVersions: () => set({ itineraryVersions: [], originalPreferences: null }),

  // Flight Agent actions
  setPassengerContact: (contact) => set({ passengerContact: contact }),
}));

// Separate persisted store for version history (sessionStorage)
interface VersionHistoryState {
  itineraryVersions: Record<string, TripItinerary[]>; // Keyed by sessionId
  originalPreferences: Record<string, UserPreferences>; // Keyed by sessionId
  getVersions: (sessionId: string) => TripItinerary[];
  saveVersion: (sessionId: string, itinerary: TripItinerary) => void;
  popVersion: (sessionId: string) => TripItinerary | null;
  saveOriginal: (sessionId: string, preferences: UserPreferences) => void;
  getOriginal: (sessionId: string) => UserPreferences | null;
  clearSession: (sessionId: string) => void;
}

export const useVersionHistory = create<VersionHistoryState>()(
  persist(
    (set, get) => ({
      itineraryVersions: {},
      originalPreferences: {},

      getVersions: (sessionId) => {
        return get().itineraryVersions[sessionId] || [];
      },

      saveVersion: (sessionId, itinerary) => {
        set((state) => {
          const versions = state.itineraryVersions[sessionId] || [];
          const updated = [...versions, itinerary];
          
          // Keep max 5 versions (LIFO)
          if (updated.length > 5) {
            updated.shift();
          }

          return {
            itineraryVersions: {
              ...state.itineraryVersions,
              [sessionId]: updated,
            },
          };
        });
      },

      popVersion: (sessionId) => {
        const versions = get().itineraryVersions[sessionId] || [];
        if (versions.length === 0) return null;

        const updated = [...versions];
        const previous = updated.pop();

        set((state) => ({
          itineraryVersions: {
            ...state.itineraryVersions,
            [sessionId]: updated,
          },
        }));

        return previous || null;
      },

      saveOriginal: (sessionId, preferences) => {
        set((state) => ({
          originalPreferences: {
            ...state.originalPreferences,
            [sessionId]: preferences,
          },
        }));
      },

      getOriginal: (sessionId) => {
        return get().originalPreferences[sessionId] || null;
      },

      clearSession: (sessionId) => {
        set((state) => {
          const { [sessionId]: _, ...restVersions } = state.itineraryVersions;
          const { [sessionId]: __, ...restOriginals } = state.originalPreferences;
          return {
            itineraryVersions: restVersions,
            originalPreferences: restOriginals,
          };
        });
      },
    }),
    {
      name: "reeltrip-version-history",
      storage: {
        getItem: (name) => {
          const str = sessionStorage.getItem(name);
          return str ? JSON.parse(str) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
    }
  )
);
