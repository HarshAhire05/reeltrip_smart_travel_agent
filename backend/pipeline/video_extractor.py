"""
pipeline/video_extractor.py

yt-dlp wrapper for extracting video metadata and downloading video files.
Uses asyncio.to_thread() since yt-dlp is synchronous.
"""
import yt_dlp
import tempfile
import os
import re
import asyncio
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def extract_video_metadata(url: str, platform: str) -> dict | None:
    """
    Extract metadata + download video for audio/frame processing.

    Returns dict with metadata fields + video_file_path, or None on failure.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "outtmpl": os.path.join(tempfile.gettempdir(), "reeltrip_%(id)s.%(ext)s"),
        "format": "best[height<=720]/bestvideo[height<=720]+bestaudio/best",
        "merge_output_format": "mp4",
    }

    # Add cookies for Instagram if configured
    if platform == "instagram" and settings.INSTAGRAM_COOKIES_PATH:
        if os.path.exists(settings.INSTAGRAM_COOKIES_PATH):
            ydl_opts["cookiefile"] = settings.INSTAGRAM_COOKIES_PATH

    try:
        info, video_path = await asyncio.to_thread(_extract_sync, url, ydl_opts)

        if not info:
            logger.error(f"yt-dlp returned no info for {url}")
            return None

        return {
            "title": info.get("title", ""),
            "description": info.get("description", ""),
            "caption_text": info.get("description", ""),
            "hashtags": _extract_hashtags(info),
            "uploader": info.get("uploader", info.get("channel", "")),
            "duration_seconds": info.get("duration", 0),
            "view_count": info.get("view_count"),
            "thumbnail_url": info.get("thumbnail", ""),
            "platform": platform,
            "video_file_path": video_path,
        }

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp download error: {e}")
        return None
    except Exception as e:
        logger.error(f"Video extraction error: {e}")
        return None


def _extract_sync(url: str, ydl_opts: dict) -> tuple[dict | None, str | None]:
    """Synchronous yt-dlp extraction (runs in thread)."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if not info:
            return None, None

        # Resolve the actual downloaded file path
        video_path = ydl.prepare_filename(info)
        if not os.path.exists(video_path):
            for ext in ["mp4", "webm", "mkv"]:
                alt = video_path.rsplit(".", 1)[0] + f".{ext}"
                if os.path.exists(alt):
                    video_path = alt
                    break

        logger.info(f"Video downloaded to: {video_path} (exists: {os.path.exists(video_path)})")
        return info, video_path


def _extract_hashtags(info: dict) -> list[str]:
    """Extract hashtags from all available fields."""
    hashtags = set()

    # Direct tags field (YouTube)
    if info.get("tags"):
        for tag in info["tags"]:
            hashtags.add(tag.lower().strip())

    # Parse from description (Instagram, TikTok)
    desc = info.get("description", "")
    found = re.findall(r"#(\w+)", desc)
    for h in found:
        hashtags.add(h.lower())

    return list(hashtags)[:20]
