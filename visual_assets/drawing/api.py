"""The drawing API: create, edit (one batch = one immutable revision), inspect, render, list.

Everything below `new_sprite` is what callers (the MCP server, the high-level composers, tests) use.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from visual_assets.drawing import config
from visual_assets.drawing.backend import lua_runner, sandbox
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.schema.ops import validate_ops
from visual_assets.drawing.schema.primitives import (
    NAME_RE,
    check_color,
    check_coord,
    check_dict,
    check_int,
    check_layer_name,
    check_name,
)
from visual_assets.drawing.workspace import jobs, locks, revisions

def summary(name: str, rev: str, digest: str, res: dict) -> dict:
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
        "cels": res["cels"],
        "aseprite_version": res["aseprite_version"],
    }


def stage_refs(job: Path, refs: dict) -> None:
    for (src, rev), idx in refs.items():
        _, path, _ = revisions.resolve_revision(src, rev)
        shutil.copyfile(path, job / f"ref{idx}.aseprite")


def new_sprite(name: str, width: int, height: int, background: str | None = None) -> dict:
    check_name(name)
    req = {
        "mode": "new",
        "width": check_int(width, "width", 1, config.MAX_DIM),
        "height": check_int(height, "height", 1, config.MAX_DIM),
        "ops": [],
    }
    if background is not None:
        req["bg"] = check_color(background)
    with locks.SpriteLock(name):
        if revisions.rev_files(name):
            raise AdapterError(f"sprite already exists: {name} (edits create new revisions)")
        with jobs.Job() as job:
            res = lua_runner.run_lua(job, req)
            rev, digest = revisions.publish(name, job)
    return summary(name, rev, digest, res)


def apply_ops(name: str, base_revision: str, ops: list[dict]) -> dict:
    """One batch -> exactly one new immutable revision, or nothing."""
    check_name(name)
    clean, refs = validate_ops(ops)
    with locks.SpriteLock(name):
        latest, src, _ = revisions.resolve_revision(name, None)
        if base_revision != latest:
            raise AdapterError(
                f"stale base_revision {base_revision}; latest is {latest}. Re-inspect and retry."
            )
        with jobs.Job() as job:
            shutil.copyfile(src, job / "in.aseprite")
            stage_refs(job, refs)
            res = lua_runner.run_lua(job, {"mode": "edit", "ops": clean, "refs": len(refs)})
            rev, digest = revisions.publish(name, job)
    return summary(name, rev, digest, res)


def branch_sprite(name: str, new_name: str, revision: str | None = None) -> dict:
    """Start a new sprite whose r0001 is a verified copy of an existing revision."""
    check_name(name)
    check_name(new_name)
    _, src, digest = revisions.resolve_revision(name, revision)
    with locks.SpriteLock(new_name):
        if revisions.rev_files(new_name):
            raise AdapterError(f"sprite already exists: {new_name}")
        with jobs.Job() as job:
            shutil.copyfile(src, job / "in.aseprite")
            res = lua_runner.run_lua(job, {"mode": "inspect", "ops": []})
            shutil.copyfile(src, job / "out.aseprite")
            rev, digest = revisions.publish(new_name, job)
    return summary(new_name, rev, digest, res)


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
    check_name(name)
    req: dict = {"mode": "inspect", "ops": [], "frame": check_int(frame, "frame", 1, config.MAX_FRAMES)}
    if region is not None:
        check_dict(region, "region")
        req["region"] = {
            "x": check_coord(region.get("x"), "region.x"),
            "y": check_coord(region.get("y"), "region.y"),
            "w": check_int(region.get("w"), "region.w", 1, config.MAX_REGION),
            "h": check_int(region.get("h"), "region.h", 1, config.MAX_REGION),
        }
    rev, src, digest = revisions.resolve_revision(name, revision)
    with jobs.Job() as job:
        shutil.copyfile(src, job / "in.aseprite")
        res = lua_runner.run_lua(job, req)
    out = summary(name, rev, digest, res)
    out["palette"] = res["palette"]
    if "region" in res:
        out["region"] = res["region"]
    return out


def export_png(
    name: str, revision: str | None, pre: list[str], post: list[str], scale: int,
    check: tuple[int, str | None] | None = None,
) -> bytes:
    s = check_int(scale, "scale", 1, config.MAX_SCALE)
    _, src, _ = revisions.resolve_revision(name, revision)
    if check is not None:  # Aseprite silently exports *something* for a missing frame/layer
        info = inspect_sprite(name, revision)
        frame, layer = check
        if frame > len(info["frames"]):
            raise AdapterError(f"no such frame: {frame}")
        if layer is not None and layer not in {l["name"] for l in info["layers"]}:
            raise AdapterError(f"no such layer: {layer}")
    with jobs.Job() as job:
        shutil.copyfile(src, job / "in.aseprite")
        proc = sandbox.bwrap(job, ["/job/in.aseprite", *pre, "--scale", str(s), *post])
        png = job / "out.png"
        if not png.is_file() or png.stat().st_size > config.MAX_FILE_BYTES:
            tail = proc.stderr.decode("utf-8", "replace")[-300:]
            raise AdapterError(f"export failed (exit {proc.returncode}): {tail}")
        return png.read_bytes()


def render_preview(
    name: str, revision: str | None = None, scale: int = 8, frame: int = 1,
    layer: str | None = None,
) -> bytes:
    """One frame, all visible layers (or just `layer`), nearest-neighbour upscaled."""
    check_name(name)
    f = check_int(frame, "frame", 1, config.MAX_FRAMES)
    pre = ["--frame-range", f"{f - 1},{f - 1}"]
    if layer is not None:
        pre += ["--layer", check_layer_name(layer)]
    return export_png(name, revision, pre, ["--save-as", "/job/out.png"], scale, (f, layer))


def render_filmstrip(name: str, revision: str | None = None, scale: int = 4) -> bytes:
    """All frames side by side in one PNG."""
    check_name(name)
    return export_png(
        name, revision, [], ["--sheet", "/job/out.png", "--sheet-type", "horizontal"], scale
    )


def read_revision(name: str, revision: str) -> tuple[str, bytes, str]:
    """The exact bytes of one named revision (no default), re-checked against its content-hash sidecar."""
    check_name(name)
    if revision is None:
        raise AdapterError("a revision is required (r0001 style)")
    rev, path, digest = revisions.resolve_revision(name, revision)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise AdapterError(f"{name}/{rev} changed while being read; refusing to use it")
    return rev, data, digest


def list_sprites() -> list[dict]:
    root = config.WORKSPACE / "sprites"
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and not d.is_symlink() and NAME_RE.fullmatch(d.name):
            revs = revisions.rev_files(d.name)
            if revs:
                out.append({"name": d.name, "latest": f"r{revs[-1][0]:04d}", "revisions": len(revs)})
    return out
