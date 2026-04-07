"""
Intent Analyzer - Extracts structured destination info from natural language travel intent.
Uses GPT-4o to understand user's travel desires and extract actionable destination data.
"""
import logging
from models.text_input import IntentClassification, DestinationInfo, ClarificationOption
from services.openai_client import call_openai_json

logger = logging.getLogger(__name__)


INTENT_ANALYSIS_SYSTEM_PROMPT = """
You are an intelligent travel planning assistant. Your role is to understand a user's travel intention expressed in natural language and extract structured travel information from it.

The user will provide free-text input describing where they want to go or what kind of travel experience they are seeking. This text may be:
- A simple destination mention (e.g., "I want to visit Dubai")
- A vague interest (e.g., "I want to see historical monuments in Europe")
- An experience-based wish (e.g., "I want a beach vacation somewhere exotic")
- A multi-destination intent (e.g., "I want to travel across Japan and South Korea")

YOUR TASK:

1. INTENT CLASSIFICATION
Classify the user input into one of these intent types:
- SPECIFIC_DESTINATION: User mentions a clear place (city, country, region)
- EXPERIENCE_BASED: User describes an experience without naming a place
- THEME_BASED: User mentions a theme (adventure, culture, food, beach, etc.)
- MULTI_DESTINATION: User mentions two or more places
- NON_TRAVEL: Input is not travel-related at all

2. DESTINATION EXTRACTION
Extract the following:
- primary: The main place the user wants to visit (city name preferred, or country if city unclear)
- country: The country name
- region: Geographic region (e.g., "Middle East", "Southeast Asia", "Western Europe")
- secondary: List of any additional destinations mentioned
- travel_theme: Detected theme (e.g., "luxury", "adventure", "cultural", "beach", "food", "nature")

3. CLARIFICATION LOGIC
If the destination is too vague to proceed (e.g., "I want a beach vacation"), set needs_clarification=true and provide 3 specific destination suggestions in clarification_options with this format:
["Maldives (Luxury tropical paradise)", "Bali, Indonesia (Beach culture blend)", "Phuket, Thailand (Vibrant beach scene)"]

4. NON-TRAVEL HANDLING
If the input is clearly not travel-related (e.g., "What's the weather like?", "How do I cook pasta?"), set intent_type to NON_TRAVEL and provide a polite error message.

RULES:
- Always respond in valid JSON. Do not add any explanation outside the JSON.
- Do not hallucinate destinations. Only suggest real, well-known places.
- For vague input, prioritize popular, tourist-friendly destinations.
- Keep clarification messages friendly and engaging.
- If user mentions a city, always try to determine the country.
- For multi-destination, list all in order of mention.

Return your response as a JSON object with this structure:
{
  "intent_type": "SPECIFIC_DESTINATION | EXPERIENCE_BASED | THEME_BASED | MULTI_DESTINATION | NON_TRAVEL",
  "destination": {
    "primary": "Dubai",
    "country": "United Arab Emirates",
    "region": "Middle East",
    "secondary": []
  },
  "travel_theme": "luxury",
  "confidence": "high | medium | low",
  "needs_clarification": false,
  "clarification_options": [],
  "clarification_message": "",
  "error_message": ""
}
"""


class IntentAnalyzer:
    """Analyzes natural language travel intent and extracts structured destination info"""

    async def analyze(self, user_text: str) -> IntentClassification:
        """
        Analyze user's free-text travel intent.

        Args:
            user_text: User's natural language input (e.g., "I want to visit Dubai")

        Returns:
            IntentClassification with extracted destination info and clarification status
        """
        logger.info(f"Analyzing travel intent: {user_text[:100]}")

        user_prompt = f"User's travel intent: {user_text}"

        result = await call_openai_json(
            task="reasoning",  # Use GPT-4o for better intent understanding
            system_prompt=INTENT_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=0.2,  # Lower temperature for more consistent extraction
            retries=2,
        )

        if not result:
            logger.error("Intent analysis failed - no response from OpenAI")
            return self._create_fallback_classification(
                "I couldn't understand your travel request. Please try describing your destination more clearly."
            )

        # Parse the result into IntentClassification
        try:
            destination_data = result.get("destination", {})
            destination = DestinationInfo(
                primary=destination_data.get("primary", ""),
                country=destination_data.get("country", ""),
                region=destination_data.get("region", ""),
                secondary=destination_data.get("secondary", []),
            )

            intent = IntentClassification(
                intent_type=result.get("intent_type", "SPECIFIC_DESTINATION"),
                destination=destination,
                travel_theme=result.get("travel_theme", ""),
                confidence=result.get("confidence", "medium"),
                needs_clarification=result.get("needs_clarification", False),
                clarification_options=result.get("clarification_options", []),
                clarification_message=result.get("clarification_message", ""),
                error_message=result.get("error_message", ""),
            )

            # Convert string clarification options to structured ClarificationOption objects
            if intent.needs_clarification and intent.clarification_options:
                # For now, keep them as strings - frontend will handle display
                # In future, we can enhance to include images
                pass

            logger.info(
                f"Intent analysis complete: {intent.intent_type}, "
                f"destination={intent.destination.primary}, "
                f"needs_clarification={intent.needs_clarification}"
            )

            return intent

        except Exception as e:
            logger.error(f"Error parsing intent analysis result: {e}")
            return self._create_fallback_classification(
                "I had trouble understanding your request. Please try rephrasing your travel destination."
            )

    def _create_fallback_classification(self, error_msg: str) -> IntentClassification:
        """Create a fallback classification when analysis fails"""
        return IntentClassification(
            intent_type="NON_TRAVEL",
            destination=DestinationInfo(),
            travel_theme="",
            confidence="low",
            needs_clarification=False,
            clarification_options=[],
            clarification_message="",
            error_message=error_msg,
        )
