"""The op schema: one validator per operation, and `validate_ops` for a whole batch."""

from __future__ import annotations

from visual_assets.drawing import config
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.schema.primitives import (
    check_color,
    check_coord,
    check_dict,
    check_int,
    check_layer_name,
    check_name,
    check_no_extra,
)

def _v_pixels(op, ctx):
    check_no_extra(op, {"pixels"})
    px = op.get("pixels")
    if not isinstance(px, list) or not 1 <= len(px) <= config.MAX_PIXELS_PER_OP:
        raise AdapterError(f"pixels must hold 1..{config.MAX_PIXELS_PER_OP} entries")
    ctx["pixels"] += len(px)
    return {
        "pixels": [
            {"x": check_coord(check_dict(p, "pixel").get("x"), "x"), "y": check_coord(p.get("y"), "y"),
             "c": check_color(p.get("color"))}
            for p in px
        ]
    }


def _v_line(op, ctx):
    check_no_extra(op, {"x0", "y0", "x1", "y1", "color"})
    return {
        "x0": check_coord(op.get("x0"), "x0"), "y0": check_coord(op.get("y0"), "y0"),
        "x1": check_coord(op.get("x1"), "x1"), "y1": check_coord(op.get("y1"), "y1"),
        "c": check_color(op.get("color")),
    }


def _box(op, extra: set[str] = frozenset()):
    check_no_extra(op, {"x", "y", "width", "height", "color", "filled"} | set(extra))
    x, y = check_coord(op.get("x"), "x"), check_coord(op.get("y"), "y")
    w, h = check_int(op.get("width"), "width", 1, config.MAX_DIM), check_int(op.get("height"), "height", 1, config.MAX_DIM)
    filled = op.get("filled", True)
    if not isinstance(filled, bool):
        raise AdapterError("filled must be a boolean")
    return {"x": x, "y": y, "w": w, "h": h, "c": check_color(op.get("color")), "fill": filled}


def _v_flood_fill(op, ctx):
    check_no_extra(op, {"x", "y", "color"})
    return {"x": check_coord(op.get("x"), "x"), "y": check_coord(op.get("y"), "y"),
            "c": check_color(op.get("color"))}


def _v_replace_color(op, ctx):
    check_no_extra(op, {"from_color", "to_color"})
    return {"from": check_color(op.get("from_color")), "to": check_color(op.get("to_color"))}


def _v_outline(op, ctx):
    check_no_extra(op, {"color"})
    return {"c": check_color(op.get("color"))}


def _v_flip(op, ctx):
    check_no_extra(op, {"axis"})
    if op.get("axis") not in ("h", "v"):
        raise AdapterError("axis must be 'h' or 'v'")
    return {"axis": op["axis"]}


def _v_none(op, ctx):
    check_no_extra(op, set())
    return {}


def _v_stamp(op, ctx):
    check_no_extra(op, {"source", "source_revision", "source_frame", "x", "y"})
    src = check_name(op.get("source"))
    rev = op.get("source_revision")
    key = (src, rev)
    if key not in ctx["refs"]:
        if len(ctx["refs"]) >= config.MAX_REFS:
            raise AdapterError(f"at most {config.MAX_REFS} distinct stamp sources per batch")
        ctx["refs"][key] = len(ctx["refs"]) + 1
    out = {"ref": ctx["refs"][key], "x": check_coord(op.get("x"), "x"), "y": check_coord(op.get("y"), "y")}
    if op.get("source_frame") is not None:
        out["src_frame"] = check_int(op["source_frame"], "source_frame", 1, config.MAX_FRAMES)
    return out


def _v_add_layer(op, ctx):
    check_no_extra(op, {"name"})
    return {"name": check_layer_name(op.get("name"), "name")}


def _v_rename_layer(op, ctx):
    check_no_extra(op, {"name"})
    return {"name": check_layer_name(op.get("name"), "name")}


def _v_set_visible(op, ctx):
    check_no_extra(op, {"visible"})
    if not isinstance(op.get("visible"), bool):
        raise AdapterError("visible must be a boolean")
    return {"visible": op["visible"]}


def _v_add_frame(op, ctx):
    check_no_extra(op, {"copy_from"})
    out = {}
    if op.get("copy_from") is not None:
        out["copy_from"] = check_int(op["copy_from"], "copy_from", 1, config.MAX_FRAMES)
    return out


def _v_set_duration(op, ctx):
    check_no_extra(op, {"ms"})
    return {"ms": check_int(op.get("ms"), "ms", 1, config.MAX_DURATION_MS)}


def _v_add_tag(op, ctx):
    check_no_extra(op, {"name", "from_frame", "to_frame"})
    return {
        "name": check_layer_name(op.get("name"), "name"),
        "from": check_int(op.get("from_frame"), "from_frame", 1, config.MAX_FRAMES),
        "to": check_int(op.get("to_frame"), "to_frame", 1, config.MAX_FRAMES),
    }


def _v_set_palette(op, ctx):
    check_no_extra(op, {"colors"})
    colors = op.get("colors")
    if not isinstance(colors, list) or not 1 <= len(colors) <= config.MAX_PALETTE:
        raise AdapterError(f"colors must hold 1..{config.MAX_PALETTE} entries")
    return {"colors": [check_color(c) for c in colors]}


def _v_resize_canvas(op, ctx):
    check_no_extra(op, {"width", "height"})
    return {"width": check_int(op.get("width"), "width", 1, config.MAX_DIM),
            "height": check_int(op.get("height"), "height", 1, config.MAX_DIM)}


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


_TARGETED = {"pixels", "line", "rect", "ellipse", "flood_fill", "replace_color", "outline",
             "silhouette", "flip", "clear", "grayscale", "stamp"}


_FRAME_OPS = _TARGETED | {"set_duration", "delete_frame"}


_LAYER_OPS = _TARGETED | {"rename_layer", "set_visible", "delete_layer"}


def validate_ops(ops) -> tuple[list[dict], dict]:
    """Validate a batch. Returns (clean ops for Lua, stamp refs {(name, rev): index})."""
    if not isinstance(ops, list) or not 1 <= len(ops) <= config.MAX_OPS:
        raise AdapterError(f"ops must hold 1..{config.MAX_OPS} entries")
    ctx = {"refs": {}, "pixels": 0}
    clean = []
    for i, raw in enumerate(ops):
        op = check_dict(raw, f"ops[{i}]")
        kind = op.get("op")
        if kind not in OPS:
            raise AdapterError(f"ops[{i}]: unknown op {kind!r}; known: {sorted(OPS)}")
        out = OPS[kind](op, ctx)
        out["op"] = kind
        if "layer" in op and op["layer"] is not None:
            if kind not in _LAYER_OPS:
                raise AdapterError(f"ops[{i}]: op {kind} does not take a layer")
            out["layer"] = check_layer_name(op["layer"])
        if "frame" in op and op["frame"] is not None:
            if kind not in _FRAME_OPS:
                raise AdapterError(f"ops[{i}]: op {kind} does not take a frame")
            out["frame"] = check_int(op["frame"], "frame", 1, config.MAX_FRAMES)
        for needs, field in (("set_duration", "frame"), ("delete_frame", "frame"),
                             ("delete_layer", "layer")):
            if kind == needs and field not in out:
                raise AdapterError(f"ops[{i}]: {needs} needs a {field}")
        clean.append(out)
    if ctx["pixels"] > config.MAX_PIXELS_PER_CALL:
        raise AdapterError(f"at most {config.MAX_PIXELS_PER_CALL} explicit pixels per batch")
    return clean, ctx["refs"]
