"""stdio MCP server for the drawing tools. Run: python -m visual_assets.drawing.server (from the repo root)."""

from __future__ import annotations

from visual_assets.drawing.server import (  # noqa: F401  (registers tools)
    handoff_tools,
    highlevel_tools,
    lowlevel_tools,
    store_readonly_tools,
)
from visual_assets.drawing.server.app import mcp

highlevel_tools.register(mcp)

__all__ = ["mcp"]
