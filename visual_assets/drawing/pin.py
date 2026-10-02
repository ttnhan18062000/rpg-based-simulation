"""Re-pin LUA_SHA256 in config.py after a deliberate, reviewed change to backend/lua/ops.lua.

Run: python -m visual_assets.drawing.pin
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pin(config_path: Path = HERE / "config.py", lua_path: Path = HERE / "backend" / "lua" / "ops.lua") -> str:
    digest = hashlib.sha256(lua_path.read_bytes()).hexdigest()
    text = config_path.read_text()
    new, n = re.subn(r'^LUA_SHA256 = .*$', f'LUA_SHA256 = "{digest}"', text, flags=re.M)
    if n != 1:
        raise SystemExit(f"expected exactly one LUA_SHA256 line in {config_path}, found {n}")
    config_path.write_text(new)
    return digest


if __name__ == "__main__":
    print(f"LUA_SHA256 = {pin()}")
    sys.exit(0)
