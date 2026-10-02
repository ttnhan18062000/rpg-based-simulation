"""stdio MCP server for the drawing tools. Run: python -m visual_assets.drawing.server (from the repo root)."""

from __future__ import annotations

from visual_assets.drawing.server import handoff_tools, highlevel_tools, lowlevel_tools  # noqa: F401  (registers tools)
from visual_assets.drawing.server.app import mcp

highlevel_tools.register(mcp)

__all__ = ["mcp"]
