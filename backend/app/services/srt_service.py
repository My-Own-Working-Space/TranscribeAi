"""SRT subtitle generation service."""


def segments_to_srt(segments: list[dict]) -> str:
    """Convert transcript segments to SRT subtitle format.

    Args:
        segments: List of dicts with 'start', 'end', 'text' keys.

    Returns:
        SRT-formatted string.
    """
    lines: list[str] = []

    for idx, seg in enumerate(segments, start=1):
        start_ts = _format_timestamp(seg["start"])
        end_ts = _format_timestamp(seg["end"])
        text = seg.get("text", "").strip()
        lines.append(f"{idx}")
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")  # blank line separator

    return "\n".join(lines)


def _format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
