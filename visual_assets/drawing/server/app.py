"""The FastMCP instance and the error translation shared by every tool module."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from visual_assets.drawing.errors import AdapterError

mcp = FastMCP(
    "aseprite-pixel-art",
    instructions=(
        "Draw small RGB pixel-art sprites (max 128x128). Every edit takes the sprite's current "
        "revision as base_revision and creates a NEW immutable revision; a stale base_revision is "
        "rejected, so re-inspect and retry. Colors are #rrggbb or #rrggbbaa. Coordinates are "
        "0-based from the top-left. Use preview to look at the result and inspect to read pixels back. "
        "Gates: an agent may draw, hand off (export_handoff), submit a handoff for intake and read the store, but adopting, revoking, "
        "building, releasing and deleting are human decisions with no tool on this server."
    ),
)


def call(fn, *args, **kwargs):
    """Run an API function, turning a rejected request into a tool error carrying its message."""
    try:
        return fn(*args, **kwargs)
    except AdapterError as exc:
        raise ValueError(str(exc)) from None
