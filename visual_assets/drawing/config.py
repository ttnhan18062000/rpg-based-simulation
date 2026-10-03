"""Limits, workspace/binary environment and the Lua template pin.

Every other module reads these as `config.NAME` at call time (never `from ...config import NAME`), so a
test that patches this module's attribute is seen everywhere. Do not change that.
"""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUA_PATH = HERE / "backend" / "lua" / "ops.lua"
# Pinned hash of backend/lua/ops.lua; bump deliberately with `python -m visual_assets.drawing.pin`.
LUA_SHA256 = "efa8638607c4686717bb7a41ff0c4e1e7d7f1c543b6d032b3528143534b50a94"

WORKSPACE = Path(
    os.environ.get("ASEPRITE_MCP_WORKSPACE", Path.home() / ".cache" / "rpg-aseprite-mcp")
)
ASEPRITE = os.environ.get("ASEPRITE_MCP_BINARY", "/usr/bin/aseprite")

MAX_DIM = 128
MAX_PIXELS_PER_OP = 4096
MAX_PIXELS_PER_CALL = 8192
MAX_OPS = 256
MAX_REFS = 8
MAX_FRAMES = 16
MAX_PALETTE = 64
MAX_REGION = 32
MAX_SCALE = 16
MAX_DURATION_MS = 10_000
JOB_TIMEOUT_S = 30
MAX_REVISIONS = 9999
MAX_FILE_BYTES = 8 * 1024 * 1024
