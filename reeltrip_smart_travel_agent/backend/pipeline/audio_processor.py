"""
pipeline/audio_processor.py

Extract audio from video via ffmpeg, transcribe with Whisper.
Always cleans up temp audio file in finally block.
"""
import subprocess
import tempfile
import os
import logging
from services.openai_client import transcribe_audio

logger = logging.getLogger(__name__)


async def extract_and_transcribe(video_path: str) -> dict:
    """
    Extract audio from video, transcribe with Whisper.

    Returns:
        {"text": "transcript...", "language": "en", "has_speech": True}
        OR
        {"text": "", "language": "", "has_speech": False}
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return {"text": "", "language": "", "has_speech": False}

    audio_path = tempfile.mktemp(suffix=".wav")

    try:
        # Extract audio: 16kHz mono WAV (optimal for Whisper)
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0:
            logger.warning(f"ffmpeg audio extraction failed: {result.stderr.decode()[:200]}")
            return {"text": "", "language": "", "has_speech": False}

        # Check if audio file is too small (likely no audio track)
        if os.path.getsize(audio_path) < 1024:
            logger.info("Audio file too small, likely no audio track")
            return {"text": "", "language": "", "has_speech": False}

        # Transcribe with Whisper
        whisper_result = await transcribe_audio(audio_path)

        if not whisper_result or not whisper_result.get("text", "").strip():
            return {"text": "", "language": "", "has_speech": False}

        # Detect if it's actual speech or just music
        transcript_text = whisper_result["text"].strip()
        word_count = len(transcript_text.split())

        # Heuristic: fewer than 5 words is likely not meaningful speech
        has_speech = word_count >= 5

        return {
            "text": transcript_text if has_speech else "",
            "language": whisper_result.get("language", ""),
            "has_speech": has_speech,
        }

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
