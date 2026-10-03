"""The store's own render of a source, compared with the producer's preview. One comparison, used by `review` AND `adopt`.

The renderer is an injected `RenderTool` (the real one is the sandboxed Aseprite exporter in `store/build`), so everything here is unit-tested in CI
without Aseprite. The comparison is by decoded pixels at the preview's own scale: it does not depend on how either PNG was encoded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from visual_assets.store import config, pixels
from visual_assets.store.contracts import ReviewRenderCheck
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.errors import PngDecodeError, RenderError
from visual_assets.store.intake import aseprite
from visual_assets.store.intake.validator import file_hash

MAX_RENDER_SCALE = 16  # provisional (U-05): the drawing tools' own maximum preview scale


class RenderTool(Protocol):
    """Renders the first frame of an Aseprite source (all visible layers) at an integer scale and returns PNG bytes."""

    tool_name: str
    tool_version: str

    def render(self, source: bytes, *, scale: int) -> bytes: ...


@dataclass(frozen=True)
class RenderComparison:
    check: ReviewRenderCheck
    rendered_png: bytes


def preview_scale(preview: bytes, source: bytes) -> int:
    """The whole-number scale at which `preview` shows `source` (the source's width divides the preview's width)."""
    facts, _ = aseprite.read_facts(source)
    try:
        width = pixels.decode_png(preview, max_dim=config.MAX_PREVIEW_DIM).width
    except PngDecodeError as exc:
        raise RenderError("preview_undecodable", f"the producer preview cannot be decoded ({exc.code})") from None
    if facts is None or facts.width < 1 or width % facts.width:
        raise RenderError("scale_unsupported", "the preview is not a whole-number scale of the source")
    scale = width // facts.width
    if not 1 <= scale <= MAX_RENDER_SCALE:
        raise RenderError("scale_unsupported", f"the preview scale {scale} is outside 1..{MAX_RENDER_SCALE}")
    return scale


def compare_preview(*, intake_id: str, source: bytes, preview: bytes, tool: RenderTool, created_at: str) -> RenderComparison:
    """Render `source` with `tool` at the preview's scale and compare decoded pixels with the producer's `preview`."""
    scale = preview_scale(preview, source)
    try:
        rendered = tool.render(source, scale=scale)
    except RenderError:
        raise
    except Exception as exc:  # a renderer must never leak anything but a coded error
        raise RenderError("render_failed", f"the renderer failed ({type(exc).__name__})") from None
    try:
        rendered_px = pixels.pixel_hash(rendered, max_dim=config.MAX_PREVIEW_DIM)
        producer_px = pixels.pixel_hash(preview, max_dim=config.MAX_PREVIEW_DIM)
    except PngDecodeError as exc:
        raise RenderError("render_undecodable", f"a rendered or preview PNG cannot be decoded ({exc.code})") from None
    check = ReviewRenderCheck(
        record_type="review_render_check", schema_version=1, intake_id=intake_id, source_hash=file_hash(source),
        producer_preview_hash=file_hash(preview), rendered_png_hash=file_hash(rendered), producer_pixel_hash=producer_px,
        rendered_pixel_hash=rendered_px, scale=scale,
        verdict=RenderVerdict.MATCH if producer_px == rendered_px else RenderVerdict.MISMATCH,
        tool_name=tool.tool_name, tool_version=tool.tool_version, created_at=created_at,
    )
    return RenderComparison(check, rendered)
