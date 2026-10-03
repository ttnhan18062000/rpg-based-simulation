"""Bounded Aseprite drawing tools: typed ops, hash-pinned Lua, bwrap sandbox, immutable revisions.

Public API re-exported here; the MCP server lives in `visual_assets.drawing.server` (needs the `mcp` package).
"""

from __future__ import annotations

from visual_assets.drawing.api import (
    apply_ops,
    branch_sprite,
    inspect_sprite,
    list_sprites,
    new_sprite,
    render_filmstrip,
    render_preview,
)
from visual_assets.drawing.errors import AdapterError

__version__ = "0.1.0"

__all__ = [
    "AdapterError",
    "apply_ops",
    "branch_sprite",
    "inspect_sprite",
    "list_sprites",
    "new_sprite",
    "render_filmstrip",
    "render_preview",
]
