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
LUA_SHA256 = "ad42d215cea94f6b016f36abeaa344cdb912124e0c7881c2e9616e356883d9d0"

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
MAX_PALETTE = 64
MAX_REGION = 32
MAX_SCALE = 16
MAX_DURATION_MS = 10_000
JOB_TIMEOUT_S = 30
MAX_REVISIONS = 9999
MAX_FILE_BYTES = 8 * 1024 * 1024
