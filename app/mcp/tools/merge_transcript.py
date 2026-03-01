"""Transcript merging tool.

This tool merges transcription results from multiple agents into a single
coherent transcript using various strategies.
"""

import logging
from typing import Any, Literal

from app.schemas import FinalTranscript, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)

MergeStrategy = Literal["confidence", "majority", "first", "longest"]


def _merge_by_confidence(results: list[TranscriptResult]) -> FinalTranscript:
    """Merge by selecting segments from the highest-confidence agent.

    For each time window, pick the segment from the agent with highest confidence.
    """
    if not results:
        return FinalTranscript(segments=[], overall_confidence=0.0)

    if len(results) == 1:
        return FinalTranscript(
            segments=results[0].segments,
            overall_confidence=results[0].avg_confidence,
            notes=f"Single agent: {results[0].agent_name}",
        )

    # Collect all segments with their source confidence
    all_segments: list[tuple[TranscriptSegment, float, str]] = []
    for result in results:
        for seg in result.segments:
            all_segments.append((seg, result.avg_confidence, result.agent_name))

    # Sort by start time
    all_segments.sort(key=lambda x: x[0].start)

    # Merge overlapping segments by choosing higher confidence
    merged: list[TranscriptSegment] = []
    used_agents: set[str] = set()

    for seg, agent_conf, agent_name in all_segments:
        # Check overlap with last merged segment
        if merged and seg.start < merged[-1].end:
            # Overlapping - keep the one with higher confidence
            combined_conf = seg.confidence * agent_conf
            last_conf = merged[-1].confidence
            if combined_conf > last_conf:
                merged[-1] = seg
                used_agents.add(agent_name)
        else:
            merged.append(seg)
            used_agents.add(agent_name)

    overall = sum(s.confidence for s in merged) / len(merged) if merged else 0.0

    return FinalTranscript(
        segments=merged,
        overall_confidence=round(overall, 3),
        notes=f"Merged from {len(results)} agents using confidence strategy. "
        f"Used: {', '.join(used_agents)}",
    )


def _merge_by_longest(results: list[TranscriptResult]) -> FinalTranscript:
    """Use the result with most segments (usually most complete)."""
    if not results:
        return FinalTranscript(segments=[], overall_confidence=0.0)

    best = max(results, key=lambda r: len(r.segments))
    return FinalTranscript(
        segments=best.segments,
        overall_confidence=best.avg_confidence,
        notes=f"Selected longest transcript from {best.agent_name} "
        f"({len(best.segments)} segments)",
    )


def _merge_by_first(results: list[TranscriptResult]) -> FinalTranscript:
    """Use the first result (fastest agent)."""
    if not results:
        return FinalTranscript(segments=[], overall_confidence=0.0)

    first = results[0]
    return FinalTranscript(
        segments=first.segments,
        overall_confidence=first.avg_confidence,
        notes=f"Used first result from {first.agent_name}",
    )


async def merge_transcripts(
    results: list[TranscriptResult],
    strategy: MergeStrategy = "confidence",
) -> FinalTranscript:
    """Merge multiple transcription results into a final transcript.

    Args:
        results: List of transcription results from different agents.
        strategy: Merging strategy:
            - confidence: Weight by segment confidence scores
            - majority: (TODO) Vote on word-level differences
            - first: Use first result (fastest)
            - longest: Use result with most segments

    Returns:
        FinalTranscript: Merged and reconciled transcript.
    """
    logger.info(f"Merging {len(results)} results using '{strategy}' strategy")

    # Filter out empty results
    valid_results = [r for r in results if r.segments]

    if not valid_results:
        logger.warning("No valid results to merge")
        return FinalTranscript(
            segments=[],
            overall_confidence=0.0,
            notes="No transcription results available",
        )

    if strategy == "confidence":
        return _merge_by_confidence(valid_results)
    elif strategy == "longest":
        return _merge_by_longest(valid_results)
    elif strategy == "first":
        return _merge_by_first(valid_results)
    elif strategy == "majority":
        # TODO: Implement word-level majority voting
        logger.warning("Majority voting not implemented, falling back to confidence")
        return _merge_by_confidence(valid_results)
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")


def get_tool_schema() -> dict[str, Any]:
    """Return MCP tool schema for registration."""
    return {
        "name": "merge_transcripts",
        "description": "Merge transcription results from multiple agents",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "description": "List of TranscriptResult objects",
                },
                "strategy": {
                    "type": "string",
                    "enum": ["confidence", "majority", "first", "longest"],
                    "default": "confidence",
                },
            },
            "required": ["results"],
        },
    }
