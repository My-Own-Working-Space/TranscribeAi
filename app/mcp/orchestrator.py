"""MCP Orchestrator for coordinating transcription agents.

This module manages the lifecycle and coordination of multiple transcription
agents, handling task distribution, result aggregation, and error recovery.
"""

import asyncio
import logging
import time
from typing import Any

from app.mcp.base_agent import BaseTranscriptionAgent
from app.mcp.tools.merge_transcript import merge_transcripts, MergeStrategy
from app.schemas import FinalTranscript, TranscriptResult
from app.services.audio_loader import AudioLoader
from app.services.cache import get_cache

logger = logging.getLogger(__name__)


class MCPOrchestrator:
    """Orchestrates multiple transcription agents using MCP-style tools."""

    def __init__(
        self,
        max_concurrent: int = 3,
        timeout_seconds: float = 300.0,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            max_concurrent: Maximum concurrent agent executions.
            timeout_seconds: Timeout for each agent transcription.
        """
        self._agents: dict[str, BaseTranscriptionAgent] = {}
        self._max_concurrent = max_concurrent
        self._timeout = timeout_seconds
        self._audio_loader = AudioLoader()
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def agents(self) -> list[str]:
        """List of registered agent names."""
        return list(self._agents.keys())

    def register_agent(self, agent: BaseTranscriptionAgent) -> None:
        """Register a transcription agent.

        Args:
            agent: The agent instance to register.
        """
        if agent.name in self._agents:
            logger.warning(f"Overwriting existing agent: {agent.name}")
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent by name.

        Args:
            name: Agent name to unregister.

        Returns:
            bool: True if agent was removed.
        """
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Unregistered agent: {name}")
            return True
        return False

    async def _run_agent(
        self,
        agent: BaseTranscriptionAgent,
        audio_data: bytes,
        language: str | None,
        **kwargs: Any,
    ) -> TranscriptResult | None:
        """Run a single agent with timeout and error handling.

        Args:
            agent: The agent to run.
            audio_data: Audio bytes.
            language: Language code.
            **kwargs: Agent-specific options.

        Returns:
            TranscriptResult or None if failed.
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)

        async with self._semaphore:
            try:
                logger.info(f"Starting agent: {agent.name}")
                result = await asyncio.wait_for(
                    agent.transcribe(audio_data, language, **kwargs),
                    timeout=self._timeout,
                )
                logger.info(
                    f"Agent {agent.name} completed: "
                    f"{len(result.segments)} segments, "
                    f"confidence={result.avg_confidence:.2f}"
                )
                return result
            except asyncio.TimeoutError:
                logger.error(f"Agent {agent.name} timed out after {self._timeout}s")
                return None
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                return None

    async def transcribe(
        self,
        audio_path: str | None = None,
        audio_data: bytes | None = None,
        language: str | None = None,
        agents: list[str] | None = None,
        merge_strategy: MergeStrategy = "confidence",
        fast_mode: bool = False,
        use_cache: bool = True,
        **kwargs: Any,
    ) -> FinalTranscript:
        """Run transcription across selected or all agents.

        Args:
            audio_path: Path to audio file (mutually exclusive with audio_data).
            audio_data: Raw audio bytes (mutually exclusive with audio_path).
            language: ISO language code. None for auto-detect.
            agents: List of agent names to use. None for all.
            merge_strategy: Strategy for merging results.
            fast_mode: Use only fastest agent (external_groq or whisper_raw).
            use_cache: Check cache before transcribing.
            **kwargs: Agent-specific options.

        Returns:
            FinalTranscript: Merged transcript from all agents.

        Raises:
            ValueError: If no audio source or no agents available.
        """
        start_time = time.time()

        # Load audio if path provided
        if audio_path:
            audio_data = await self._audio_loader.load_file(audio_path)
        elif audio_data is None:
            raise ValueError("Either audio_path or audio_data must be provided")

        # Check cache first
        if use_cache:
            cache = get_cache()
            cache_key = cache.hash_audio(audio_data, language)
            cached = cache.get(cache_key)
            if cached:
                elapsed = time.time() - start_time
                logger.info(f"Cache hit! Returned in {elapsed:.2f}s")
                return cached

        # Fast mode: use only the fastest agent
        if fast_mode:
            # Prefer external API (faster), fallback to local
            fast_agents = ["external_groq", "external_openai", "whisper_raw"]
            for agent_name in fast_agents:
                if agent_name in self._agents:
                    agents = [agent_name]
                    logger.info(f"Fast mode: using {agent_name}")
                    break

        # Select agents
        if agents:
            selected = {k: v for k, v in self._agents.items() if k in agents}
            if not selected:
                raise ValueError(f"No matching agents found: {agents}")
        else:
            selected = self._agents

        if not selected:
            raise ValueError("No agents registered")

        logger.info(
            f"Running {len(selected)} agents: {list(selected.keys())}, "
            f"strategy={merge_strategy}"
        )

        # Run agents in parallel
        tasks = [
            self._run_agent(agent, audio_data, language, **kwargs)
            for agent in selected.values()
        ]
        results = await asyncio.gather(*tasks)

        # Filter successful results
        valid_results: list[TranscriptResult] = [r for r in results if r is not None]

        if not valid_results:
            logger.error("All agents failed")
            return FinalTranscript(
                segments=[],
                overall_confidence=0.0,
                notes="All transcription agents failed",
            )

        # Merge results
        final = await merge_transcripts(valid_results, strategy=merge_strategy)

        # Cache result
        if use_cache:
            cache.set(cache_key, final)

        elapsed = time.time() - start_time
        logger.info(
            f"Transcription complete: {len(final.segments)} segments, "
            f"confidence={final.overall_confidence:.2f}, time={elapsed:.2f}s"
        )

        return final

    async def health_check(self) -> dict[str, bool]:
        """Check health of all registered agents.

        Returns:
            dict: Agent name to health status mapping.
        """
        results = {}
        for name, agent in self._agents.items():
            try:
                results[name] = await agent.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results


# Singleton orchestrator instance
_orchestrator: MCPOrchestrator | None = None


def get_orchestrator() -> MCPOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MCPOrchestrator()
    return _orchestrator


async def setup_default_agents(orchestrator: MCPOrchestrator) -> None:
    """Register default agents with the orchestrator.

    Args:
        orchestrator: The orchestrator to configure.
    """
    from app.mcp.tools import transcribe_raw, transcribe_external

    # Register local Whisper agent (handles vocabulary via initial_prompt)
    orchestrator.register_agent(transcribe_raw.create_agent())

    # NOTE: whisper_context removed - it duplicated whisper_raw's work
    # and loaded a separate model. whisper_raw now supports initial_prompt.

    # Register external API agent if configured (faster, better accuracy)
    external_agent = transcribe_external.create_agent()
    if await external_agent.health_check():
        orchestrator.register_agent(external_agent)
    else:
        logger.info("External API agent not configured, skipping")
