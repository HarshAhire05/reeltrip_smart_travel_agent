"""
Central OpenAI API wrapper. ALL AI calls go through here.
Handles model routing, structured JSON output, retries, and error handling.
"""
from openai import AsyncOpenAI
from config import get_settings
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def get_model(task: str) -> str:
    """
    Route tasks to the cheapest sufficient model.

    RULES:
    - "vision" -> gpt-4o (only model with vision)
    - "reasoning" -> gpt-4o (complex multi-constraint tasks)
    - "fast" -> gpt-4o-mini (simple text tasks, classification, extraction)
    """
    model_map = {
        "vision": settings.VISION_MODEL,
        "reasoning": settings.REASONING_MODEL,
        "fast": settings.FAST_MODEL,
    }
    return model_map.get(task, settings.FAST_MODEL)


def _try_repair_json(raw: str) -> dict | None:
    """
    Attempt to repair truncated JSON by closing open brackets/braces/strings.
    Returns parsed dict on success, None on failure.
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # Track open structures
    stack = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append(ch)
        elif ch == '}':
            if stack and stack[-1] == '{':
                stack.pop()
        elif ch == ']':
            if stack and stack[-1] == '[':
                stack.pop()

    # If nothing to close, the JSON might just be malformed differently
    if not stack and not in_string:
        return None

    # Build closing sequence
    repaired = text
    if in_string:
        repaired += '"'

    # Close open structures in reverse order
    for opener in reversed(stack):
        repaired = repaired.rstrip().rstrip(',')
        repaired += '}' if opener == '{' else ']'

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        # More aggressive: walk backwards to find a natural boundary and close from there
        for cutoff in range(len(text) - 1, max(0, len(text) - 2000), -1):
            candidate = text[:cutoff]
            last_char = candidate.rstrip()[-1:] if candidate.rstrip() else ''
            if last_char in ('}', ']', '"') or last_char.isdigit() or candidate.rstrip().endswith(('null', 'true', 'false')):
                # Re-scan structure for this truncated candidate
                s2 = []
                in_s = False
                esc = False
                for c in candidate:
                    if esc:
                        esc = False
                        continue
                    if c == '\\' and in_s:
                        esc = True
                        continue
                    if c == '"':
                        in_s = not in_s
                        continue
                    if in_s:
                        continue
                    if c in ('{', '['):
                        s2.append(c)
                    elif c == '}' and s2 and s2[-1] == '{':
                        s2.pop()
                    elif c == ']' and s2 and s2[-1] == '[':
                        s2.pop()

                closing = '"' if in_s else ''
                for opener in reversed(s2):
                    closing += '}' if opener == '{' else ']'

                try:
                    return json.loads(candidate + closing)
                except json.JSONDecodeError:
                    continue

        return None


async def call_openai_json(
    task: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retries: int = 2,
) -> dict | None:
    """
    Call OpenAI with JSON response format.

    Args:
        task: "vision" | "reasoning" | "fast" — determines which model to use
        system_prompt: System message (MUST contain the word "JSON")
        user_prompt: User message (text only, no images)
        max_tokens: Max response tokens
        temperature: 0.0-1.0 (lower = more deterministic)
        retries: Number of retries on failure

    Returns:
        Parsed JSON dict, or None on failure
    """
    model = get_model(task)
    content = ""

    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Warn if response was truncated due to token limit
            if finish_reason == "length":
                logger.warning(
                    f"OpenAI response truncated (finish_reason=length, max_tokens={max_tokens}). "
                    f"Response length: {len(content)} chars. Consider increasing max_tokens."
                )

            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error (attempt {attempt + 1}): {e}")
            logger.error(f"Raw response ({len(content)} chars): {content[:500]}")

            # Attempt JSON repair before retrying
            repaired = _try_repair_json(content)
            if repaired:
                logger.info(f"JSON repair succeeded (attempt {attempt + 1}, {len(content)} chars)")
                return repaired

            if attempt < retries:
                await asyncio.sleep(1)
                continue
            return None

        except Exception as e:
            logger.error(f"OpenAI call failed (attempt {attempt + 1}): {e}")
            if attempt < retries:
                wait = 2**attempt
                await asyncio.sleep(wait)
                continue
            return None


async def call_openai_vision(
    system_prompt: str,
    text_prompt: str,
    images_base64: list[str],
    max_tokens: int = 4096,
    temperature: float = 0.3,
    retries: int = 1,
) -> dict | None:
    """
    Call OpenAI with images (vision). Always uses gpt-4o.

    Args:
        system_prompt: System message
        text_prompt: Text part of user message
        images_base64: List of base64-encoded images
        max_tokens: Max response tokens
        temperature: Creativity level
        retries: Retry count (keep low — vision is expensive)

    Returns:
        Parsed JSON dict, or None on failure
    """
    model = get_model("vision")

    # Build content array with text + images
    content = [{"type": "text", "text": text_prompt}]
    for img_b64 in images_base64:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "low",  # 85 tokens per image vs 1105 for "high"
                },
            }
        )

    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )

            raw = response.choices[0].message.content
            return json.loads(raw)

        except Exception as e:
            logger.error(f"Vision call failed (attempt {attempt + 1}): {e}")
            if attempt < retries:
                await asyncio.sleep(2)
                continue
            return None


async def call_openai_text(
    task: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str | None:
    """
    Call OpenAI for free-form text response (not JSON).
    Used for itinerary customization chat and similar conversational tasks.
    """
    model = get_model(task)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI text call failed: {e}")
        return None


async def transcribe_audio(audio_file_path: str) -> dict | None:
    """
    Transcribe audio using Whisper.
    Returns {"text": "...", "language": "en"} or None on failure.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL,
                file=audio_file,
                response_format="verbose_json",
            )
        return {
            "text": response.text,
            "language": response.language if hasattr(response, "language") else "unknown",
        }
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None
