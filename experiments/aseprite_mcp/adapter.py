"""Bounded Aseprite adapter (spike, not production code).

Design rules from docs/plans/aseprite-mcp-pixel-art/ (M1):
- typed, bounded operations only; no caller-supplied code, paths, or URLs
- a fixed, hash-pinned Lua template; caller data reaches Lua only as parsed JSON
- Aseprite runs in a bwrap sandbox: no network, read-only system, one job dir
- immutable revisions: every mutation publishes a NEW file, never edits in place
- stale-revision and content-hash checks before every mutation
- one batch of operations produces exactly one new revision (all-or-nothing)
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
log = logging.getLogger("aseprite_mcp")
LUA_PATH = HERE / "lua" / "ops.lua"
# Pinned hash of lua/ops.lua; bump deliberately when the template is reviewed.
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

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
_LAYER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$")
_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")
_REV_RE = re.compile(r"^r(\d{4})$")


class AdapterError(Exception):
    """A rejected or failed request. Message is safe to show the agent."""


# --------------------------------------------------------------------------- validation


def _name(name) -> str:
    if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
        raise AdapterError("name must match [a-z0-9][a-z0-9_-]{0,31}")
    return name


def _layer_name(value, label="layer") -> str:
    if not isinstance(value, str) or not _LAYER_RE.fullmatch(value):
        raise AdapterError(f"{label} must match [A-Za-z0-9][A-Za-z0-9 _-]{{0,31}}")
    return value


def _color(value) -> list[int]:
    m = _COLOR_RE.fullmatch(value) if isinstance(value, str) else None
    if not m:
        raise AdapterError("color must be #rrggbb or #rrggbbaa")
    rgb, a = m.group(1), m.group(2) or "ff"
    return [int(rgb[i : i + 2], 16) for i in (0, 2, 4)] + [int(a, 16)]


def _int(value, label: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise AdapterError(f"{label} must be an integer in [{lo}, {hi}]")
    return value


def _coord(value, label: str) -> int:
    return _int(value, label, 0, MAX_DIM - 1)


def _dict(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be an object")
    return value


def _no_extra(op: dict, allowed: set[str]) -> None:
    extra = set(op) - allowed - {"op", "layer", "frame"}
    if extra:
        raise AdapterError(f"op {op['op']}: unexpected field(s) {sorted(extra)}")


# --------------------------------------------------------------------------- op schema
# Each validator returns the cleaned op for Lua. `ctx` collects stamp sources.


def _v_pixels(op, ctx):
    _no_extra(op, {"pixels"})
    px = op.get("pixels")
    if not isinstance(px, list) or not 1 <= len(px) <= MAX_PIXELS_PER_OP:
        raise AdapterError(f"pixels must hold 1..{MAX_PIXELS_PER_OP} entries")
    ctx["pixels"] += len(px)
    return {
        "pixels": [
            {"x": _coord(_dict(p, "pixel").get("x"), "x"), "y": _coord(p.get("y"), "y"),
             "c": _color(p.get("color"))}
            for p in px
        ]
    }


def _v_line(op, ctx):
    _no_extra(op, {"x0", "y0", "x1", "y1", "color"})
    return {
        "x0": _coord(op.get("x0"), "x0"), "y0": _coord(op.get("y0"), "y0"),
        "x1": _coord(op.get("x1"), "x1"), "y1": _coord(op.get("y1"), "y1"),
        "c": _color(op.get("color")),
    }


def _box(op, extra: set[str] = frozenset()):
    _no_extra(op, {"x", "y", "width", "height", "color", "filled"} | set(extra))
    x, y = _coord(op.get("x"), "x"), _coord(op.get("y"), "y")
    w, h = _int(op.get("width"), "width", 1, MAX_DIM), _int(op.get("height"), "height", 1, MAX_DIM)
    filled = op.get("filled", True)
    if not isinstance(filled, bool):
        raise AdapterError("filled must be a boolean")
    return {"x": x, "y": y, "w": w, "h": h, "c": _color(op.get("color")), "fill": filled}


def _v_flood_fill(op, ctx):
    _no_extra(op, {"x", "y", "color"})
    return {"x": _coord(op.get("x"), "x"), "y": _coord(op.get("y"), "y"),
            "c": _color(op.get("color"))}


def _v_replace_color(op, ctx):
    _no_extra(op, {"from_color", "to_color"})
    return {"from": _color(op.get("from_color")), "to": _color(op.get("to_color"))}


def _v_outline(op, ctx):
    _no_extra(op, {"color"})
    return {"c": _color(op.get("color"))}


def _v_flip(op, ctx):
    _no_extra(op, {"axis"})
    if op.get("axis") not in ("h", "v"):
        raise AdapterError("axis must be 'h' or 'v'")
    return {"axis": op["axis"]}


def _v_none(op, ctx):
    _no_extra(op, set())
    return {}


def _v_stamp(op, ctx):
    _no_extra(op, {"source", "source_revision", "source_frame", "x", "y"})
    src = _name(op.get("source"))
    rev = op.get("source_revision")
    key = (src, rev)
    if key not in ctx["refs"]:
        if len(ctx["refs"]) >= MAX_REFS:
            raise AdapterError(f"at most {MAX_REFS} distinct stamp sources per batch")
        ctx["refs"][key] = len(ctx["refs"]) + 1
    out = {"ref": ctx["refs"][key], "x": _coord(op.get("x"), "x"), "y": _coord(op.get("y"), "y")}
    if op.get("source_frame") is not None:
        out["src_frame"] = _int(op["source_frame"], "source_frame", 1, MAX_FRAMES)
    return out


def _v_add_layer(op, ctx):
    _no_extra(op, {"name"})
    return {"name": _layer_name(op.get("name"), "name")}


def _v_rename_layer(op, ctx):
    _no_extra(op, {"name"})
    return {"name": _layer_name(op.get("name"), "name")}


def _v_set_visible(op, ctx):
    _no_extra(op, {"visible"})
    if not isinstance(op.get("visible"), bool):
        raise AdapterError("visible must be a boolean")
    return {"visible": op["visible"]}


def _v_add_frame(op, ctx):
    _no_extra(op, {"copy_from"})
    out = {}
    if op.get("copy_from") is not None:
        out["copy_from"] = _int(op["copy_from"], "copy_from", 1, MAX_FRAMES)
    return out


def _v_set_duration(op, ctx):
    _no_extra(op, {"ms"})
    return {"ms": _int(op.get("ms"), "ms", 1, MAX_DURATION_MS)}


def _v_add_tag(op, ctx):
    _no_extra(op, {"name", "from_frame", "to_frame"})
    return {
        "name": _layer_name(op.get("name"), "name"),
        "from": _int(op.get("from_frame"), "from_frame", 1, MAX_FRAMES),
        "to": _int(op.get("to_frame"), "to_frame", 1, MAX_FRAMES),
    }


def _v_set_palette(op, ctx):
    _no_extra(op, {"colors"})
    colors = op.get("colors")
    if not isinstance(colors, list) or not 1 <= len(colors) <= MAX_PALETTE:
        raise AdapterError(f"colors must hold 1..{MAX_PALETTE} entries")
    return {"colors": [_color(c) for c in colors]}


def _v_resize_canvas(op, ctx):
    _no_extra(op, {"width", "height"})
    return {"width": _int(op.get("width"), "width", 1, MAX_DIM),
            "height": _int(op.get("height"), "height", 1, MAX_DIM)}


OPS = {
    "pixels": _v_pixels,
    "line": _v_line,
    "rect": lambda op, ctx: _box(op),
    "ellipse": lambda op, ctx: _box(op),
    "flood_fill": _v_flood_fill,
    "replace_color": _v_replace_color,
    "outline": _v_outline,
    "silhouette": _v_outline,
    "flip": _v_flip,
    "clear": _v_none,
    "grayscale": _v_none,
    "stamp": _v_stamp,
    "add_layer": _v_add_layer,
    "rename_layer": _v_rename_layer,
    "set_visible": _v_set_visible,
    "add_frame": _v_add_frame,
    "set_duration": _v_set_duration,
    "add_tag": _v_add_tag,
    "set_palette": _v_set_palette,
    "delete_layer": _v_none,
    "delete_frame": _v_none,
    "resize_canvas": _v_resize_canvas,
}
# Ops that address a pixel layer/frame; the rest are document-level.
_TARGETED = {"pixels", "line", "rect", "ellipse", "flood_fill", "replace_color", "outline",
             "silhouette", "flip", "clear", "grayscale", "stamp"}
_FRAME_OPS = _TARGETED | {"set_duration", "delete_frame"}
_LAYER_OPS = _TARGETED | {"rename_layer", "set_visible", "delete_layer"}


def validate_ops(ops) -> tuple[list[dict], dict]:
    """Validate a batch. Returns (clean ops for Lua, stamp refs {(name, rev): index})."""
    if not isinstance(ops, list) or not 1 <= len(ops) <= MAX_OPS:
        raise AdapterError(f"ops must hold 1..{MAX_OPS} entries")
    ctx = {"refs": {}, "pixels": 0}
    clean = []
    for i, raw in enumerate(ops):
        op = _dict(raw, f"ops[{i}]")
        kind = op.get("op")
        if kind not in OPS:
            raise AdapterError(f"ops[{i}]: unknown op {kind!r}; known: {sorted(OPS)}")
        out = OPS[kind](op, ctx)
        out["op"] = kind
        if "layer" in op and op["layer"] is not None:
            if kind not in _LAYER_OPS:
                raise AdapterError(f"ops[{i}]: op {kind} does not take a layer")
            out["layer"] = _layer_name(op["layer"])
        if "frame" in op and op["frame"] is not None:
            if kind not in _FRAME_OPS:
                raise AdapterError(f"ops[{i}]: op {kind} does not take a frame")
            out["frame"] = _int(op["frame"], "frame", 1, MAX_FRAMES)
        for needs, field in (("set_duration", "frame"), ("delete_frame", "frame"),
                             ("delete_layer", "layer")):
            if kind == needs and field not in out:
                raise AdapterError(f"ops[{i}]: {needs} needs a {field}")
        clean.append(out)
    if ctx["pixels"] > MAX_PIXELS_PER_CALL:
        raise AdapterError(f"at most {MAX_PIXELS_PER_CALL} explicit pixels per batch")
    return clean, ctx["refs"]


# --------------------------------------------------------------------------- storage


def _sprite_dir(name: str) -> Path:
    d = WORKSPACE / "sprites" / name
    if d.is_symlink():
        raise AdapterError(f"sprite directory for {name} is a symlink; refusing to use it")
    return d


def _rev_files(name: str) -> list[tuple[int, Path]]:
    d = _sprite_dir(name)
    if not d.is_dir():
        return []
    out = []
    for p in d.glob("r????.aseprite"):
        m = _REV_RE.fullmatch(p.stem)
        if m and not p.is_symlink() and p.is_file():
            out.append((int(m.group(1)), p))
    return sorted(out)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_revision(name: str, revision: str | None) -> tuple[str, Path, str]:
    revs = _rev_files(name)
    if not revs:
        raise AdapterError(f"no such sprite: {name}")
    if revision is None:
        num, path = revs[-1]
    else:
        m = _REV_RE.fullmatch(revision) if isinstance(revision, str) else None
        if not m:
            raise AdapterError("revision must look like r0001")
        found = dict(revs).get(int(m.group(1)))
        if found is None:
            raise AdapterError(f"no such revision: {revision}")
        num, path = int(m.group(1)), found
    expected = path.with_suffix(".sha256").read_text().strip()
    if _sha256(path) != expected:
        raise AdapterError(f"{name}/r{num:04d} failed its content-hash check; refusing to use it")
    return f"r{num:04d}", path, expected


# --------------------------------------------------------------------------- sandbox


def _check_lua_template() -> None:
    if _sha256(LUA_PATH) != LUA_SHA256:
        raise AdapterError("lua/ops.lua does not match its pinned hash; refusing to run")


def _bwrap(job: Path, argv: list[str]) -> subprocess.CompletedProcess:
    home = "/home/sandbox"
    cmd = [
        "bwrap",
        "--unshare-all",  # includes network
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--setenv", "HOME", home,
        "--setenv", "PATH", "/usr/bin",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--tmpfs", home,
        "--ro-bind", str(LUA_PATH.parent), "/lua",
        "--bind", str(job), "/job",
        "--chdir", "/job",
        ASEPRITE, "-b", *argv,
    ]
    try:
        return subprocess.run(
            cmd, capture_output=True, timeout=JOB_TIMEOUT_S, stdin=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError(f"aseprite timed out after {JOB_TIMEOUT_S}s") from exc


def _aslist(value) -> list:
    """Lua serialises an empty table as {}; normalise to a list."""
    return value if isinstance(value, list) else []


def _run_lua(job: Path, req: dict) -> dict:
    _check_lua_template()
    (job / "req.json").write_text(json.dumps(req))
    proc = _bwrap(job, ["--script", "/lua/ops.lua"])
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


class _Job:
    def __enter__(self) -> Path:
        jobs = WORKSPACE / ".jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(dir=jobs))
        return self.path

    def __exit__(self, *exc) -> None:
        try:
            shutil.rmtree(self.path)
        except OSError as err:
            # never mask the real outcome, but never be silent about a leaked job dir either
            log.warning("could not remove job dir %s: %s", self.path.name, err)


def _publish(name: str, job: Path) -> tuple[str, str]:
    """Hard-link the job output as the next revision. Never overwrites."""
    out = job / "out.aseprite"
    if not out.is_file() or out.stat().st_size == 0 or out.stat().st_size > MAX_FILE_BYTES:
        raise AdapterError("aseprite did not produce a valid output file")
    revs = _rev_files(name)
    num = (revs[-1][0] if revs else 0) + 1
    if num > MAX_REVISIONS:
        raise AdapterError("revision limit reached")
    d = _sprite_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"r{num:04d}.aseprite"
    sidecar = target.with_suffix(".sha256")
    digest = _sha256(out)
    if target.exists() or target.is_symlink():
        raise AdapterError("revision collision; retry")
    # Sidecar first, created exclusively: a visible revision file must never lack its hash (that
    # would brick the sprite), and a sidecar that already exists is never overwritten (it may belong
    # to a competing writer's revision). A sidecar with no revision file next to it is an orphan from
    # an interrupted publish: remove it once and retry. Writers that hold the sprite flock cannot
    # race here; this guards the case where one does not.
    created = False
    try:
        for attempt in (1, 2):
            try:
                fh = open(sidecar, "x")
            except FileExistsError:
                if attempt == 2 or target.exists() or target.is_symlink():
                    raise
                sidecar.unlink(missing_ok=True)
                continue
            created = True
            with fh:
                fh.write(digest + "\n")
            break
        os.link(out, target)  # same filesystem as the job dir; fails if target exists
    except FileExistsError as exc:
        if created:
            sidecar.unlink(missing_ok=True)  # only ever our own sidecar; theirs was never touched
        raise AdapterError("revision collision; retry") from exc
    except OSError as exc:
        if created:
            sidecar.unlink(missing_ok=True)
        log.warning("publish of %s/r%04d failed: %s", name, num, exc)
        raise AdapterError("could not publish revision (storage error); nothing was saved") from exc
    return f"r{num:04d}", digest


class _SpriteLock:
    def __init__(self, name: str):
        d = _sprite_dir(name)
        d.mkdir(parents=True, exist_ok=True)
        self._fh = open(d / ".lock", "w")

    def __enter__(self):
        fcntl.flock(self._fh, fcntl.LOCK_EX)

    def __exit__(self, *exc):
        fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()


def _summary(name: str, rev: str, digest: str, res: dict) -> dict:
    return {
        "name": name,
        "revision": rev,
        "sha256": digest,
        "width": res["width"],
        "height": res["height"],
        "nonempty_pixels": res["nonempty_pixels"],
        "colors": res["colors"],
        "n_colors": res["n_colors"],
        "frames": res["frames"],
        "layers": res["layers"],
        "tags": res["tags"],
        "palette_size": res["palette_size"],
    }


def _stage_refs(job: Path, refs: dict) -> None:
    for (src, rev), idx in refs.items():
        _, path, _ = _resolve_revision(src, rev)
        shutil.copyfile(path, job / f"ref{idx}.aseprite")


# --------------------------------------------------------------------------- operations


def new_sprite(name: str, width: int, height: int, background: str | None = None) -> dict:
    _name(name)
    req = {
        "mode": "new",
        "width": _int(width, "width", 1, MAX_DIM),
        "height": _int(height, "height", 1, MAX_DIM),
        "ops": [],
    }
    if background is not None:
        req["bg"] = _color(background)
    with _SpriteLock(name):
        if _rev_files(name):
            raise AdapterError(f"sprite already exists: {name} (edits create new revisions)")
        with _Job() as job:
            res = _run_lua(job, req)
            rev, digest = _publish(name, job)
    return _summary(name, rev, digest, res)


def apply_ops(name: str, base_revision: str, ops: list[dict]) -> dict:
    """One batch -> exactly one new immutable revision, or nothing."""
    _name(name)
    clean, refs = validate_ops(ops)
    with _SpriteLock(name):
        latest, src, _ = _resolve_revision(name, None)
        if base_revision != latest:
            raise AdapterError(
                f"stale base_revision {base_revision}; latest is {latest}. Re-inspect and retry."
            )
        with _Job() as job:
            shutil.copyfile(src, job / "in.aseprite")
            _stage_refs(job, refs)
            res = _run_lua(job, {"mode": "edit", "ops": clean, "refs": len(refs)})
            rev, digest = _publish(name, job)
    return _summary(name, rev, digest, res)


def branch_sprite(name: str, new_name: str, revision: str | None = None) -> dict:
    """Start a new sprite whose r0001 is a verified copy of an existing revision."""
    _name(name)
    _name(new_name)
    _, src, digest = _resolve_revision(name, revision)
    with _SpriteLock(new_name):
        if _rev_files(new_name):
            raise AdapterError(f"sprite already exists: {new_name}")
        with _Job() as job:
            shutil.copyfile(src, job / "in.aseprite")
            res = _run_lua(job, {"mode": "inspect", "ops": []})
            shutil.copyfile(src, job / "out.aseprite")
            rev, digest = _publish(new_name, job)
    return _summary(new_name, rev, digest, res)


# Convenience wrappers: single-op batches.
def draw_pixels(name: str, base_revision: str, pixels: list[dict], **target) -> dict:
    return apply_ops(name, base_revision, [{"op": "pixels", "pixels": pixels, **target}])


def draw_line(name, base_revision, x0, y0, x1, y1, color, **target) -> dict:
    op = {"op": "line", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "color": color, **target}
    return apply_ops(name, base_revision, [op])


def fill_rect(name, base_revision, x, y, width, height, color, filled=True, **target) -> dict:
    op = {"op": "rect", "x": x, "y": y, "width": width, "height": height, "color": color,
          "filled": filled, **target}
    return apply_ops(name, base_revision, [op])


def inspect_sprite(
    name: str, revision: str | None = None, region: dict | None = None, frame: int = 1
) -> dict:
    _name(name)
    req: dict = {"mode": "inspect", "ops": [], "frame": _int(frame, "frame", 1, MAX_FRAMES)}
    if region is not None:
        _dict(region, "region")
        req["region"] = {
            "x": _coord(region.get("x"), "region.x"),
            "y": _coord(region.get("y"), "region.y"),
            "w": _int(region.get("w"), "region.w", 1, MAX_REGION),
            "h": _int(region.get("h"), "region.h", 1, MAX_REGION),
        }
    rev, src, digest = _resolve_revision(name, revision)
    with _Job() as job:
        shutil.copyfile(src, job / "in.aseprite")
        res = _run_lua(job, req)
    out = _summary(name, rev, digest, res)
    out["palette"] = res["palette"]
    if "region" in res:
        out["region"] = res["region"]
    return out


def _export_png(
    name: str, revision: str | None, pre: list[str], post: list[str], scale: int,
    check: tuple[int, str | None] | None = None,
) -> bytes:
    s = _int(scale, "scale", 1, MAX_SCALE)
    _, src, _ = _resolve_revision(name, revision)
    if check is not None:  # Aseprite silently exports *something* for a missing frame/layer
        info = inspect_sprite(name, revision)
        frame, layer = check
        if frame > len(info["frames"]):
            raise AdapterError(f"no such frame: {frame}")
        if layer is not None and layer not in {l["name"] for l in info["layers"]}:
            raise AdapterError(f"no such layer: {layer}")
    with _Job() as job:
        shutil.copyfile(src, job / "in.aseprite")
        proc = _bwrap(job, ["/job/in.aseprite", *pre, "--scale", str(s), *post])
        png = job / "out.png"
        if not png.is_file() or png.stat().st_size > MAX_FILE_BYTES:
            tail = proc.stderr.decode("utf-8", "replace")[-300:]
            raise AdapterError(f"export failed (exit {proc.returncode}): {tail}")
        return png.read_bytes()


def render_preview(
    name: str, revision: str | None = None, scale: int = 8, frame: int = 1,
    layer: str | None = None,
) -> bytes:
    """One frame, all visible layers (or just `layer`), nearest-neighbour upscaled."""
    _name(name)
    f = _int(frame, "frame", 1, MAX_FRAMES)
    pre = ["--frame-range", f"{f - 1},{f - 1}"]
    if layer is not None:
        pre += ["--layer", _layer_name(layer)]
    return _export_png(name, revision, pre, ["--save-as", "/job/out.png"], scale, (f, layer))


def render_filmstrip(name: str, revision: str | None = None, scale: int = 4) -> bytes:
    """All frames side by side in one PNG."""
    _name(name)
    return _export_png(
        name, revision, [], ["--sheet", "/job/out.png", "--sheet-type", "horizontal"], scale
    )


def list_sprites() -> list[dict]:
    root = WORKSPACE / "sprites"
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and not d.is_symlink() and _NAME_RE.fullmatch(d.name):
            revs = _rev_files(d.name)
            if revs:
                out.append({"name": d.name, "latest": f"r{revs[-1][0]:04d}", "revisions": len(revs)})
    return out
