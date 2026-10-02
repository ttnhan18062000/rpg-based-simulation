"""Round trip with the fixed Lua template: pin check, req.json in, res.json out."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from visual_assets.drawing import config
from visual_assets.drawing.backend import sandbox
from visual_assets.drawing.errors import AdapterError


def check_lua_template() -> None:
    if hashlib.sha256(config.LUA_PATH.read_bytes()).hexdigest() != config.LUA_SHA256:
        raise AdapterError("lua/ops.lua does not match its pinned hash; refusing to run")


def _aslist(value) -> list:
    """Lua serialises an empty table as {}; normalise to a list."""
    return value if isinstance(value, list) else []


def run_lua(job: Path, req: dict) -> dict:
    check_lua_template()
    (job / "req.json").write_text(json.dumps(req))
    proc = sandbox.bwrap(job, ["--script", "/lua/ops.lua"])
    res_path = job / "res.json"
    if not res_path.exists():
        tail = proc.stderr.decode("utf-8", "replace")[-300:]
        raise AdapterError(f"aseprite produced no result (exit {proc.returncode}): {tail}")
    res = json.loads(res_path.read_text())
    if not res.get("ok"):
        raise AdapterError(f"operation failed: {res.get('error', 'unknown error')}")
    for key in ("frames", "layers", "tags", "palette", "colors"):
        res[key] = _aslist(res.get(key))
    for layer in res["layers"]:
        layer["nonempty_by_frame"] = _aslist(layer.get("nonempty_by_frame"))
    return res
