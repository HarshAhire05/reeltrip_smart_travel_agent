"""
URL validation for supported video platforms.
"""
import re

PLATFORM_PATTERNS = {
    "instagram": [
        r"https?://(?:www\.)?instagram\.com/reel/[\w-]+",
        r"https?://(?:www\.)?instagram\.com/p/[\w-]+",
    ],
    "youtube": [
        r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"https?://youtu\.be/[\w-]+",
    ],
    "tiktok": [
        r"https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+",
        r"https?://vm\.tiktok\.com/[\w]+",
    ],
}


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a video URL against supported platform patterns.

    Returns (is_valid, platform_name).
    If invalid, platform_name will be "unknown".
    """
    url = url.strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url):
                return True, platform
    return False, "unknown"
