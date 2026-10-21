"""
Destination Enricher - Generates places and highlights from a text-based destination.
Uses Google Places API + GPT-4o-mini to create rich highlight content.
"""
import logging
from models.text_input import (
    DestinationEnrichmentResult,
    TextHighlightPlace,
    DestinationInfo,
)
from models.location import PlaceHighlight
from services.google_places_client import text_search, nearby_search, get_photo_url
from services.openai_client import call_openai_json
import json

logger = logging.getLogger(__name__)


DESTINATION_SUMMARY_PROMPT = """You are a travel content writer creating exciting destination summaries.

Given a destination, write a compelling 3-4 line paragraph that would excite someone to visit.
Focus on what makes this place unique, its vibe, and top experiences.

Keep it engaging, specific, and aspirational.

Respond in JSON format:
{
  "summary": "Your 3-4 line excitement paragraph here",
  "theme": "luxury | adventure | cultural | beach | food | nature | urban"
}
"""


class DestinationEnricher:
    """Enriches a destination with must-visit places and generates highlights"""

    async def enrich(
        self,
        destination_info: DestinationInfo,
        travel_theme: str = "",
    ) -> DestinationEnrichmentResult:
        """
        Enrich a destination with top places and highlights.

        Args:
            destination_info: Extracted destination information
            travel_theme: Optional theme hint from intent analysis

        Returns:
            DestinationEnrichmentResult with places, highlights, and summary
        """
        destination_name = destination_info.primary
        country = destination_info.country

        logger.info(f"Enriching destination: {destination_name}, {country}")

        # Step 1: Get city coordinates and top attractions from Google Places
        city_coords = await self._get_city_coordinates(destination_name, country)

        if not city_coords:
            logger.error(f"Could not find coordinates for {destination_name}")
            return self._create_empty_result(destination_name, country, destination_info.region)

        lat, lng = city_coords["latitude"], city_coords["longitude"]

        # Step 2: Search for top attractions near the destination
        attractions = await nearby_search(
            latitude=lat,
            longitude=lng,
            place_type="tourist_attraction",
            radius=20000,  # 20km radius
            max_results=10,
        )

        logger.info(f"Found {len(attractions)} attractions for {destination_name}")

        # If we don't have enough attractions, also search by text
        if len(attractions) < 8:
            text_results = await text_search(
                query=f"top attractions in {destination_name}",
                max_results=10,
            )
            # Merge, avoiding duplicates by place_id
            seen_ids = {p.get("place_id") for p in attractions}
            for place in text_results:
                if place.get("place_id") not in seen_ids:
                    attractions.append(place)
                    seen_ids.add(place.get("place_id"))

        # Take top 8-10 places based on rating
        attractions = sorted(
            attractions,
            key=lambda p: (p.get("rating") or 0, p.get("total_ratings") or 0),
            reverse=True,
        )[:10]

        # Step 3: Generate highlights for these places using GPT-4o-mini
        highlights_data = await self._generate_highlights(attractions, destination_name, travel_theme)

        # Step 4: Generate destination summary
        summary_data = await self._generate_destination_summary(destination_name, country, travel_theme)

        # Step 5: Convert to TextHighlightPlace objects
        places = []
        for i, place in enumerate(attractions):
            highlight = highlights_data.get(place.get("place_id", ""), {})

            # Get photo URL
            photo_url = None
            if place.get("photo_reference"):
                photo_url = get_photo_url(place["photo_reference"], max_width=800)

            # Parse estimated cost - handle "Free" or text values
            estimated_cost = highlight.get("estimated_cost_usd", 0.0)
            if isinstance(estimated_cost, str):
                # Try to extract number from string
                if estimated_cost.lower() in ["free", "no cost", "none", ""]:
                    estimated_cost = 0.0
                else:
                    try:
                        estimated_cost = float(estimated_cost.replace("$", "").replace(",", "").strip())
                    except (ValueError, AttributeError):
                        estimated_cost = 0.0

            places.append(
                TextHighlightPlace(
                    place_name=place.get("name", ""),
                    place_id=place.get("place_id", ""),
                    photo_url=photo_url,
                    latitude=place.get("latitude", 0.0),
                    longitude=place.get("longitude", 0.0),
                    formatted_address=place.get("formatted_address", ""),
                    rating=place.get("rating"),
                    description=highlight.get("description", ""),
                    vibe_tags=highlight.get("vibe_tags", ["Popular", "Recommended", "Must-Visit"]),
                    signature_experiences=highlight.get("signature_experiences", []),
                    best_time_to_visit=highlight.get("best_time_to_visit", ""),
                    know_more=highlight.get("know_more", ""),
                    estimated_visit_duration=highlight.get("estimated_visit_duration", "2-3 hours"),
                    estimated_cost_usd=estimated_cost,
                    google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}",
                    source="text_generated",
                    category=self._categorize_place(place.get("types", [])),
                )
            )

        return DestinationEnrichmentResult(
            destination_name=destination_name,
            country=country,
            region=destination_info.region,
            city_coordinates=city_coords,
            places=places,
            highlights_summary=summary_data["summary"],
            travel_theme=summary_data["theme"] or travel_theme,
        )

    async def _get_city_coordinates(self, city_name: str, country: str) -> dict | None:
        """Get coordinates for a city using Google Places text search"""
        query = f"{city_name}, {country}" if country else city_name
        results = await text_search(query=query, max_results=1)

        if results:
            place = results[0]
            return {
                "latitude": place.get("latitude", 0.0),
                "longitude": place.get("longitude", 0.0),
            }
        return None

    async def _generate_highlights(
        self,
        places: list[dict],
        destination_name: str,
        theme: str,
    ) -> dict[str, dict]:
        """
        Generate highlight content for all places in batch.
        Returns dict mapping place_id -> highlight data
        """
        if not places:
            return {}

        # Prepare slim place data
        slim_places = []
        for p in places:
            slim_places.append({
                "place_id": p.get("place_id", ""),
                "name": p.get("name", ""),
                "address": p.get("formatted_address", ""),
                "types": p.get("types", [])[:3],
                "rating": p.get("rating"),
                "total_ratings": p.get("total_ratings"),
                "price_level": p.get("price_level"),
            })

        system_prompt = f"""You are a travel writer creating highlights for {destination_name}.

Generate rich, engaging highlight content for each place. Make it feel like a premium travel guide.

RULES:
1. Descriptions: 2-3 vivid sentences specific to each place
2. Vibe tags: Exactly 3 single descriptive words
3. Signature experiences: 2-3 specific must-dos at THAT place
4. Be accurate - use provided Google data (ratings, types)
5. Estimate costs in USD
6. Consider the travel theme: {theme or 'general tourism'}

Respond in JSON: {{"highlights": [array of highlight objects with keys: place_id, description, vibe_tags, signature_experiences, best_time_to_visit, know_more, estimated_visit_duration, estimated_cost_usd]}}
"""

        user_prompt = f"""Generate highlights for these {len(slim_places)} places in {destination_name}:

{json.dumps(slim_places, indent=1)}
"""

        result = await call_openai_json(
            task="fast",  # GPT-4o-mini for cost efficiency
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4096,
            temperature=0.6,
            retries=2,
        )

        if not result or "highlights" not in result:
            logger.warning("Highlight generation failed, using fallbacks")
            return {}

        # Convert list to dict for easy lookup
        highlights_dict = {}
        for h in result.get("highlights", []):
            place_id = h.get("place_id")
            if place_id:
                highlights_dict[place_id] = h

        return highlights_dict

    async def _generate_destination_summary(
        self,
        destination: str,
        country: str,
        theme: str,
    ) -> dict:
        """Generate an exciting 3-4 line summary about the destination"""
        user_prompt = f"""Destination: {destination}, {country}
Travel theme: {theme or 'general tourism'}

Write an exciting 3-4 line paragraph that would make someone want to visit this destination.
"""

        result = await call_openai_json(
            task="fast",
            system_prompt=DESTINATION_SUMMARY_PROMPT,
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.7,
            retries=1,
        )

        if result and "summary" in result:
            return {
                "summary": result["summary"],
                "theme": result.get("theme", theme),
            }

        # Fallback summary
        return {
            "summary": f"Discover the wonders of {destination}, a captivating destination offering unforgettable experiences. From iconic landmarks to local culture, this city has something for every traveler. Plan your perfect trip and create memories that will last a lifetime.",
            "theme": theme or "general",
        }

    def _categorize_place(self, types: list[str]) -> str:
        """Categorize a place based on its Google types"""
        type_mapping = {
            "museum": "cultural",
            "art_gallery": "cultural",
            "church": "cultural",
            "mosque": "cultural",
            "temple": "cultural",
            "park": "nature",
            "natural_feature": "nature",
            "beach": "nature",
            "zoo": "nature",
            "aquarium": "nature",
            "restaurant": "food",
            "cafe": "food",
            "bar": "food",
            "amusement_park": "adventure",
            "tourist_attraction": "landmark",
            "point_of_interest": "landmark",
            "shopping_mall": "shopping",
            "store": "shopping",
        }

        for t in types:
            if t in type_mapping:
                return type_mapping[t]

        return "landmark"

    def _create_empty_result(
        self,
        destination: str,
        country: str,
        region: str,
    ) -> DestinationEnrichmentResult:
        """Create an empty result when enrichment fails"""
        return DestinationEnrichmentResult(
            destination_name=destination,
            country=country,
            region=region,
            city_coordinates={"latitude": 0.0, "longitude": 0.0},
            places=[],
            highlights_summary=f"Explore the beauty of {destination}.",
            travel_theme="general",
        )
