"""MCP (Model Context Protocol) components for multi-agent orchestration.

This package provides:
- BaseTranscriptionAgent: Interface for all transcription agents
- MCPOrchestrator: Coordinates multiple agents
- Tools: Individual transcription and merging tools
"""

from app.mcp.base_agent import BaseTranscriptionAgent
from app.mcp.orchestrator import MCPOrchestrator, get_orchestrator

__all__ = [
    "BaseTranscriptionAgent",
    "MCPOrchestrator",
    "get_orchestrator",
]
