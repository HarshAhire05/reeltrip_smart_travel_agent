"""
Pydantic models for video intelligence and content analysis (Pipeline Stages 1-2).
"""
from pydantic import BaseModel, Field


class FrameObservation(BaseModel):
    frame_index: int
    landmarks: list[str] = Field(default_factory=list)
    visible_text: list[str] = Field(default_factory=list)
    text_languages: list[str] = Field(default_factory=list)
    architecture_style: str = ""
    landscape_type: str = ""
    country_indicators: list[str] = Field(default_factory=list)
    location_guess: str = ""
    confidence: str = "low"  # "high" | "medium" | "low"


class CandidateLocation(BaseModel):
    name: str
    type: str = "city"  # "city" | "landmark" | "area" | "beach" | "restaurant" | "hotel" | "market"
    mentioned_in: list[str] = Field(default_factory=list)  # ["vision", "hashtags", "transcript", ...]
    confidence: str = "medium"  # "high" | "medium" | "low"


class ContentAnalysis(BaseModel):
    destination_country: str = ""
    destination_region: str = ""
    destination_city: str = ""
    location_confidence: str = "low"  # "high" | "medium" | "low"
    candidate_locations: list[CandidateLocation] = Field(default_factory=list)
    dominant_vibe: str = ""
    content_summary: str = ""
    detected_activities: list[str] = Field(default_factory=list)
    target_audience: str = ""


class VideoIntelligence(BaseModel):
    url: str
    platform: str = "unknown"  # "instagram" | "youtube" | "tiktok"
    title: str = ""
    description: str = ""
    caption_text: str = ""
    hashtags: list[str] = Field(default_factory=list)
    uploader: str = ""
    duration_seconds: int = 0
    view_count: int | None = None
    thumbnail_url: str = ""
    transcript: str = ""
    transcript_language: str = ""
    has_speech: bool = False
    frames_base64: list[str] = Field(default_factory=list)
    frame_count: int = 0
    extracted_at: str = ""
    content_analysis: ContentAnalysis | None = None
    vision_observations: list[FrameObservation] = Field(default_factory=list)
