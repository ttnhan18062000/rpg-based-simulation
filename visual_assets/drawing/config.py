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
LUA_SHA256 = "5a9b265f167a0ca9c436bc370d186d7c7702a31abc81355536b4aa9627ac6b54"

WORKSPACE = Path(
    os.environ.get("ASEPRITE_MCP_WORKSPACE", Path.home() / ".cache" / "rpg-aseprite-mcp")
)
ASEPRITE = os.environ.get("ASEPRITE_MCP_BINARY", "/usr/bin/aseprite")
# The editor build the real-Aseprite tests are run against (ADR D10); strict mode fails on any other version.
ASEPRITE_VERSION = "1.3.18.6"

MAX_DIM = 128
MAX_PIXELS_PER_OP = 4096
MAX_PIXELS_PER_CALL = 8192
MAX_OPS = 256
MAX_REFS = 8
MAX_FRAMES = 16
MAX_SLICES = 16  # equal to the store's MAX_SOURCE_SLICES (a parity test), so no tool-made source carries more slices than the store accepts
MAX_PALETTE = 64
MAX_REGION = 32
MAX_SCALE = 16
MAX_DURATION_MS = 10_000
JOB_TIMEOUT_S = 30
MAX_REVISIONS = 9999
MAX_FILE_BYTES = 8 * 1024 * 1024
