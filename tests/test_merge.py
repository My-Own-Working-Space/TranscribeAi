"""Tests for transcript merging functionality."""

import pytest

from app.schemas import FinalTranscript, TranscriptResult, TranscriptSegment
from app.mcp.tools.merge_transcript import merge_transcripts


class TestTranscriptSegment:
    """Tests for TranscriptSegment model."""

    def test_valid_segment(self) -> None:
        """Test creating a valid transcript segment."""
        segment = TranscriptSegment(
            start=0.0,
            end=1.5,
            text="Hello world",
            confidence=0.95,
            speaker="speaker_1",
        )
        assert segment.start == 0.0
        assert segment.end == 1.5
        assert segment.text == "Hello world"
        assert segment.confidence == 0.95
        assert segment.speaker == "speaker_1"

    def test_segment_without_speaker(self) -> None:
        """Test segment with optional speaker field."""
        segment = TranscriptSegment(
            start=0.0,
            end=1.0,
            text="Test",
            confidence=0.9,
        )
        assert segment.speaker is None

    def test_confidence_bounds(self) -> None:
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            TranscriptSegment(
                start=0.0,
                end=1.0,
                text="Test",
                confidence=1.5,  # Invalid: > 1
            )

        with pytest.raises(ValueError):
            TranscriptSegment(
                start=0.0,
                end=1.0,
                text="Test",
                confidence=-0.1,  # Invalid: < 0
            )


class TestTranscriptResult:
    """Tests for TranscriptResult model."""

    def test_valid_result(self) -> None:
        """Test creating a valid transcript result."""
        segments = [
            TranscriptSegment(start=0.0, end=1.0, text="Hello", confidence=0.9),
            TranscriptSegment(start=1.0, end=2.0, text="world", confidence=0.85),
        ]
        result = TranscriptResult(
            agent_name="raw_agent",
            language="en",
            segments=segments,
            avg_confidence=0.875,
            meta={"model": "whisper-large"},
        )
        assert result.agent_name == "raw_agent"
        assert len(result.segments) == 2
        assert result.meta["model"] == "whisper-large"

    def test_empty_segments(self) -> None:
        """Test result with no segments."""
        result = TranscriptResult(
            agent_name="test_agent",
            language="en",
            segments=[],
            avg_confidence=0.0,
            meta={},
        )
        assert len(result.segments) == 0


class TestFinalTranscript:
    """Tests for FinalTranscript model."""

    def test_valid_final_transcript(self) -> None:
        """Test creating a valid final transcript."""
        segments = [
            TranscriptSegment(start=0.0, end=2.0, text="Hello world", confidence=0.92),
        ]
        transcript = FinalTranscript(
            segments=segments,
            overall_confidence=0.92,
            notes="Merged from 3 agents",
        )
        assert len(transcript.segments) == 1
        assert transcript.overall_confidence == 0.92
        assert transcript.notes == "Merged from 3 agents"

    def test_transcript_without_notes(self) -> None:
        """Test final transcript with optional notes."""
        transcript = FinalTranscript(
            segments=[],
            overall_confidence=0.0,
        )
        assert transcript.notes is None


class TestMergeTranscript:
    """Tests for merge_transcripts function."""

    @pytest.fixture
    def sample_results(self) -> list[TranscriptResult]:
        """Create sample transcription results for testing."""
        return [
            TranscriptResult(
                agent_name="agent_1",
                language="en",
                segments=[
                    TranscriptSegment(start=0.0, end=1.0, text="Hello", confidence=0.9),
                    TranscriptSegment(start=1.0, end=2.0, text="world", confidence=0.85),
                ],
                avg_confidence=0.875,
                meta={},
            ),
            TranscriptResult(
                agent_name="agent_2",
                language="en",
                segments=[
                    TranscriptSegment(start=0.0, end=1.0, text="Hello", confidence=0.95),
                    TranscriptSegment(start=1.0, end=2.0, text="World", confidence=0.9),
                ],
                avg_confidence=0.925,
                meta={},
            ),
        ]

    @pytest.mark.asyncio
    async def test_merge_empty_results(self) -> None:
        """Test merging empty results list."""
        final = await merge_transcripts([])
        assert len(final.segments) == 0
        assert final.overall_confidence == 0.0

    @pytest.mark.asyncio
    async def test_merge_single_result(self, sample_results: list[TranscriptResult]) -> None:
        """Test merging a single result returns it unchanged."""
        final = await merge_transcripts([sample_results[0]])
        assert len(final.segments) == 2
        assert final.overall_confidence == sample_results[0].avg_confidence
        assert "Single agent" in (final.notes or "")

    @pytest.mark.asyncio
    async def test_merge_confidence_strategy(self, sample_results: list[TranscriptResult]) -> None:
        """Test confidence-weighted merging."""
        final = await merge_transcripts(sample_results, strategy="confidence")
        assert len(final.segments) >= 1
        assert final.overall_confidence > 0
        assert "confidence" in (final.notes or "").lower()

    @pytest.mark.asyncio
    async def test_merge_longest_strategy(self, sample_results: list[TranscriptResult]) -> None:
        """Test longest transcript strategy."""
        final = await merge_transcripts(sample_results, strategy="longest")
        assert len(final.segments) == 2
        assert "longest" in (final.notes or "").lower()

    @pytest.mark.asyncio
    async def test_merge_first_strategy(self, sample_results: list[TranscriptResult]) -> None:
        """Test first result strategy."""
        final = await merge_transcripts(sample_results, strategy="first")
        assert len(final.segments) == 2
        assert final.overall_confidence == sample_results[0].avg_confidence

    @pytest.mark.asyncio
    async def test_merge_filters_empty_results(self) -> None:
        """Test that empty results are filtered out."""
        results = [
            TranscriptResult(
                agent_name="empty",
                language="en",
                segments=[],
                avg_confidence=0.0,
                meta={},
            ),
            TranscriptResult(
                agent_name="valid",
                language="en",
                segments=[
                    TranscriptSegment(start=0.0, end=1.0, text="Hello", confidence=0.9),
                ],
                avg_confidence=0.9,
                meta={},
            ),
        ]
        final = await merge_transcripts(results)
        assert len(final.segments) == 1
        assert final.overall_confidence == 0.9
