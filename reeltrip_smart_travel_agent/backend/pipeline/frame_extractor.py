"""
pipeline/frame_extractor.py

Extract evenly-distributed key frames from video via ffmpeg.
Returns frames as base64-encoded JPEG strings.
Always cleans up temp directory in finally block.
"""
import subprocess
import tempfile
import base64
import os
import glob
import shutil
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def extract_frames(video_path: str, duration_seconds: int) -> list[str]:
    """
    Extract key frames from video as base64-encoded JPEGs.

    Strategy: Extract MAX_FRAME_COUNT frames evenly distributed across the video.
    Resize to 768px width to reduce vision API token cost.

    Returns: List of base64 strings (no data URI prefix)
    """
    if not os.path.exists(video_path):
        return []

    max_frames = settings.MAX_FRAME_COUNT

    # Calculate fps filter value
    if duration_seconds and duration_seconds > 0:
        fps_value = max_frames / duration_seconds
    else:
        fps_value = 0.2  # Fallback: 1 frame every 5 seconds

    frame_dir = tempfile.mkdtemp(prefix="reeltrip_frames_")

    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps={fps_value},scale=768:-2",  # -2 ensures even dimensions
            "-frames:v", str(max_frames),
            "-q:v", "3",
            "-y",
            os.path.join(frame_dir, "frame_%03d.jpg"),
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0:
            logger.warning(f"Frame extraction failed: {result.stderr.decode()[:200]}")
            return []

        # Read frames as base64
        frames_b64 = []
        frame_files = sorted(glob.glob(os.path.join(frame_dir, "frame_*.jpg")))

        for fpath in frame_files[:max_frames]:
            with open(fpath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                frames_b64.append(b64)

        logger.info(f"Extracted {len(frames_b64)} frames")
        return frames_b64

    finally:
        shutil.rmtree(frame_dir, ignore_errors=True)
