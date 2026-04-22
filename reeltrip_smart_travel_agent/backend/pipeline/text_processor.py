"""
Text Processor - Main orchestrator for text-based travel intent processing.
Coordinates intent analysis → destination enrichment → result formatting with SSE streaming.
"""
import logging
import asyncio
from datetime import datetime
from typing import AsyncGenerator
import json

from models.text_input import (
    TextInputRequest,
    TextProcessingResult,
    IntentClassification,
    ClarificationOption,
)
from models.location import PlaceHighlight, PrimaryDestination, LocationResult, Coordinates
from pipeline.intent_analyzer import IntentAnalyzer
from pipeline.destination_enricher import DestinationEnricher

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Main text processing pipeline - alternative to video pipeline.
    Converts natural language travel intent into structured highlights.
    """

    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.destination_enricher = DestinationEnricher()

    async def process_stream(
        self,
        text_input: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Process text input and yield SSE events for real-time progress updates.

        Args:
            text_input: User's natural language travel intent
            session_id: Session identifier

        Yields:
            SSE formatted event strings (event: type\\ndata: json\\n\\n)
        """
        try:
            # Event 1: Session created
            yield self._sse_event("session", {"session_id": session_id})

            # Event 2: Progress - Analyzing intent
            yield self._sse_event(
                "progress",
                {
                    "stage": "analyzing",
                    "percent": 10,
                    "message": "Understanding your travel intent...",
                },
            )

            # Step 1: Analyze intent
            intent = await self.intent_analyzer.analyze(text_input)

            # Check for non-travel input
            if intent.intent_type == "NON_TRAVEL":
                yield self._sse_event(
                    "error",
                    {
                        "message": intent.error_message
                        or "This doesn't seem to be a travel request. Please describe where you'd like to go."
                    },
                )
                return

            # Event 3: Intent analysis complete
            yield self._sse_event(
                "intent_analysis",
                {
                    "intent_type": intent.intent_type,
                    "destination": {
                        "primary": intent.destination.primary,
                        "country": intent.destination.country,
                        "region": intent.destination.region,
                        "secondary": intent.destination.secondary,
                    },
                    "travel_theme": intent.travel_theme,
                    "needs_clarification": intent.needs_clarification,
                    "clarification_message": intent.clarification_message,
                },
            )

            # Check if clarification needed
            if intent.needs_clarification:
                # Convert string options to structured ClarificationOption objects
                structured_options = []
                for option_str in intent.clarification_options:
                    # Parse "Maldives (Luxury tropical paradise)" format
                    if "(" in option_str and ")" in option_str:
                        name_part = option_str.split("(")[0].strip()
                        desc_part = option_str.split("(")[1].split(")")[0].strip()
                    else:
                        name_part = option_str.strip()
                        desc_part = "Popular travel destination"

                    # Try to extract country if format is "City, Country"
                    if "," in name_part:
                        parts = name_part.split(",")
                        city = parts[0].strip()
                        country = parts[1].strip() if len(parts) > 1 else ""
                        structured_options.append(
                            ClarificationOption(
                                destination_name=city,
                                country=country,
                                region="",
                                description=desc_part,
                                image_url=None,
                            )
                        )
                    else:
                        structured_options.append(
                            ClarificationOption(
                                destination_name=name_part,
                                country="",
                                region="",
                                description=desc_part,
                                image_url=None,
                            )
                        )

                yield self._sse_event(
                    "clarification_needed",
                    {
                        "message": intent.clarification_message
                        or "Which destination sounds right for you?",
                        "options": [
                            {
                                "destination_name": opt.destination_name,
                                "country": opt.country,
                                "description": opt.description,
                            }
                            for opt in structured_options
                        ],
                    },
                )
                # Stop here - frontend will re-call with selected destination
                return

            # Event 4: Progress - Detecting destination
            yield self._sse_event(
                "progress",
                {
                    "stage": "locating",
                    "percent": 35,
                    "message": f"Finding top attractions in {intent.destination.primary}...",
                },
            )

            # Step 2: Enrich destination with places and highlights
            enrichment = await self.destination_enricher.enrich(
                destination_info=intent.destination,
                travel_theme=intent.travel_theme,
            )

            if not enrichment.places:
                yield self._sse_event(
                    "error",
                    {
                        "message": f"Sorry, I couldn't find information about {intent.destination.primary}. "
                        "Please try a different destination."
                    },
                )
                return

            # Event 5: Progress - Generating highlights
            yield self._sse_event(
                "progress",
                {
                    "stage": "highlights",
                    "percent": 70,
                    "message": "Creating your personalized highlights...",
                },
            )

            # Convert TextHighlightPlace to PlaceHighlight format
            highlights = []
            for place in enrichment.places:
                highlights.append({
                    "place_name": place.place_name,
                    "place_id": place.place_id,
                    "photo_url": place.photo_url,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "formatted_address": place.formatted_address,
                    "rating": place.rating,
                    "description": place.description,
                    "vibe_tags": place.vibe_tags,
                    "signature_experiences": place.signature_experiences,
                    "best_time_to_visit": place.best_time_to_visit,
                    "know_more": place.know_more,
                    "estimated_visit_duration": place.estimated_visit_duration,
                    "estimated_cost_usd": place.estimated_cost_usd,
                    "google_maps_url": place.google_maps_url,
                    "source": "text_generated",
                })

            # Event 6: Highlights complete
            yield self._sse_event(
                "highlights",
                {
                    "highlights": highlights,
                    "highlights_summary": enrichment.highlights_summary,
                    "primary_city": enrichment.destination_name,
                    "primary_country": enrichment.country,
                    "city_latitude": enrichment.city_coordinates.get("latitude", 0.0),
                    "city_longitude": enrichment.city_coordinates.get("longitude", 0.0),
                },
            )

            # Event 7: Complete
            yield self._sse_event(
                "complete",
                {
                    "session_id": session_id,
                    "destination": f"{enrichment.destination_name}, {enrichment.country}",
                },
            )

            logger.info(
                f"Text processing complete for session {session_id}: "
                f"{enrichment.destination_name}, {len(highlights)} highlights"
            )

        except Exception as e:
            logger.error(f"Text processing error for session {session_id}: {e}", exc_info=True)
            yield self._sse_event(
                "error",
                {
                    "message": "Sorry, something went wrong while processing your request. Please try again."
                },
            )

    async def process(
        self,
        text_input: str,
        session_id: str,
    ) -> TextProcessingResult:
        """
        Process text input synchronously (non-streaming).
        Returns complete TextProcessingResult.

        Args:
            text_input: User's natural language travel intent
            session_id: Session identifier

        Returns:
            TextProcessingResult with all data
        """
        logger.info(f"Processing text input (sync): {text_input[:100]}")

        # Step 1: Analyze intent
        intent = await self.intent_analyzer.analyze(text_input)

        # Handle non-travel input
        if intent.intent_type == "NON_TRAVEL":
            return TextProcessingResult(
                session_id=session_id,
                raw_text_input=text_input,
                intent_classification=intent,
                needs_clarification=False,
                processed_at=datetime.utcnow().isoformat(),
            )

        # Handle clarification needed
        if intent.needs_clarification:
            # Convert string options to structured
            structured_options = []
            for opt_str in intent.clarification_options:
                if "(" in opt_str:
                    name = opt_str.split("(")[0].strip()
                    desc = opt_str.split("(")[1].split(")")[0].strip()
                else:
                    name = opt_str
                    desc = "Popular destination"

                structured_options.append(
                    ClarificationOption(
                        destination_name=name,
                        country="",
                        region="",
                        description=desc,
                        image_url=None,
                    )
                )

            return TextProcessingResult(
                session_id=session_id,
                raw_text_input=text_input,
                intent_classification=intent,
                needs_clarification=True,
                clarification_options=structured_options,
                processed_at=datetime.utcnow().isoformat(),
            )

        # Step 2: Enrich destination
        enrichment = await self.destination_enricher.enrich(
            destination_info=intent.destination,
            travel_theme=intent.travel_theme,
        )

        # Convert to highlights format
        highlights_list = []
        for place in enrichment.places:
            highlights_list.append({
                "place_name": place.place_name,
                "place_id": place.place_id,
                "photo_url": place.photo_url,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "formatted_address": place.formatted_address,
                "rating": place.rating,
                "description": place.description,
                "vibe_tags": place.vibe_tags,
                "signature_experiences": place.signature_experiences,
                "best_time_to_visit": place.best_time_to_visit,
                "know_more": place.know_more,
                "estimated_visit_duration": place.estimated_visit_duration,
                "estimated_cost_usd": place.estimated_cost_usd,
                "google_maps_url": place.google_maps_url,
                "source": "text_generated",
            })

        return TextProcessingResult(
            session_id=session_id,
            raw_text_input=text_input,
            intent_classification=intent,
            primary_destination={
                "country": enrichment.country,
                "region": enrichment.region,
                "city": enrichment.destination_name,
            },
            primary_country=enrichment.country,
            primary_region=enrichment.region,
            primary_city=enrichment.destination_name,
            city_latitude=enrichment.city_coordinates.get("latitude"),
            city_longitude=enrichment.city_coordinates.get("longitude"),
            highlights=highlights_list,
            highlights_summary=enrichment.highlights_summary,
            travel_theme=enrichment.travel_theme,
            needs_clarification=False,
            processed_at=datetime.utcnow().isoformat(),
        )

    def _sse_event(self, event_type: str, data: dict) -> str:
        """Format data as Server-Sent Event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
