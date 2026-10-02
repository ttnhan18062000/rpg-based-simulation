"""Helpers to talk to the real drawing MCP server over stdio (shared by the protocol tests)."""

from __future__ import annotations

import asyncio
import base64
import json
import struct
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from visual_assets.drawing import config

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_TOOLS = {
    "new_sprite", "apply_ops", "branch_sprite", "inspect", "preview", "filmstrip", "list_sprites",
    # high-level layer (server/highlevel_tools.register)
    "make_ramp", "shade", "dither", "stroke", "auto_outline", "remap_palette", "lint_sprite",
    "ascii_view",
}


@asynccontextmanager
async def session(workspace: Path):
    """Spawn `python -m visual_assets.drawing.server` from the repo root with an isolated workspace."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "visual_assets.drawing.server"],
        cwd=str(REPO_ROOT),
        env={"ASEPRITE_MCP_WORKSPACE": str(workspace), "ASEPRITE_MCP_BINARY": config.ASEPRITE},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await asyncio.wait_for(s.initialize(), 30)
            yield s


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 120))


def text(result) -> str:
    return "".join(c.text for c in result.content if c.type == "text")


def data(result) -> dict:
    return json.loads(text(result))


def png_size(item):
    assert item.type == "image" and item.mimeType == "image/png"
    raw = base64.b64decode(item.data)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", raw[16:24])
