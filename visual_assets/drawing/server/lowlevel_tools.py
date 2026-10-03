"""MCP tools for the low-level drawing API. Importing this module registers them on the shared server."""

from __future__ import annotations

from mcp.server.fastmcp.utilities.types import Image

from visual_assets.drawing import api
from visual_assets.drawing.server.app import call, mcp

OPS_HELP = """Operations (each a dict with "op"; targeted ops accept optional "layer" name, default the
bottom layer, and "frame", 1-based, default 1):
  pixels {pixels:[{x,y,color}]}        line {x0,y0,x1,y1,color}
  rect {x,y,width,height,color,filled=true}   ellipse {x,y,width,height,color,filled=true}
  flood_fill {x,y,color}               replace_color {from_color,to_color}
  outline {color}   (1px 4-neighbour ring around opaque pixels)   silhouette {color}
  flip {axis:"h"|"v"}   clear {}   grayscale {}
  stamp {source, source_revision?, source_frame?, x, y}   (composite another sprite, flattened)
  add_layer {name}   rename_layer {layer,name}   set_visible {layer,visible}
  add_frame {copy_from?}  (copy is inserted right after its source; no copy_from = empty, appended)
  set_duration {frame,ms}   add_tag {name,from_frame,to_frame}   set_palette {colors:[...]}
  delete_layer {layer}   (layer required; the last layer cannot be deleted)
  delete_frame {frame}   (frame required, later frames renumber; the last frame cannot be deleted;
                          tags spanning it shrink, a tag wholly inside it is removed)
  resize_canvas {width,height}   (1..128, top-left anchored: crops or pads with transparency on every
                                  layer/frame; not a scale)
Colors: #rrggbb or #rrggbbaa. Coordinates are 0-based from the top-left."""


@mcp.tool()
def new_sprite(name: str, width: int, height: int, background: str | None = None) -> dict:
    """Create a new sprite (revision r0001) with one layer named "base". background is an optional fill."""
    return call(api.new_sprite, name, width, height, background)


@mcp.tool(description="Apply a batch of operations as ONE new immutable revision (all-or-nothing). " + OPS_HELP)
def apply_ops(name: str, base_revision: str, ops: list[dict]) -> dict:
    return call(api.apply_ops, name, base_revision, ops)


@mcp.tool()
def branch_sprite(name: str, new_name: str, revision: str | None = None) -> dict:
    """Start a new sprite whose r0001 is a copy of an existing revision (for variants such as grayscale)."""
    return call(api.branch_sprite, name, new_name, revision)


@mcp.tool()
def inspect(
    name: str, revision: str | None = None, region: dict | None = None, frame: int = 1
) -> dict:
    """Layers, frames (duration, pixel count, checksum), tags, palette, colors in use; optionally a
    region {x,y,w,h} (max 32x32) of the flattened frame as hex pixels."""
    return call(api.inspect_sprite, name, revision, region, frame)


@mcp.tool()
def preview(
    name: str, revision: str | None = None, scale: int = 8, frame: int = 1, layer: str | None = None
) -> Image:
    """PNG of one frame (visible layers, or just `layer`), nearest-neighbour upscaled 1-16x."""
    return Image(data=call(api.render_preview, name, revision, scale, frame, layer), format="png")


@mcp.tool()
def filmstrip(name: str, revision: str | None = None, scale: int = 4) -> Image:
    """PNG with every frame side by side."""
    return Image(data=call(api.render_filmstrip, name, revision, scale), format="png")


@mcp.tool()
def list_sprites() -> list[dict]:
    """List sprites with their latest revision."""
    return api.list_sprites()
