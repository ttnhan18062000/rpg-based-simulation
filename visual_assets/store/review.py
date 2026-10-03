"""`review`: show a human a PASSED candidate, with the store's OWN render of the source beside the producer's preview.

A human reviews `preview.png` but adopts `source.aseprite`, and intake cannot prove the preview depicts the source. When a renderer is available the store
renders the staged source itself at the preview's scale, compares decoded pixels, writes the typed `ReviewRenderCheck` into the candidate's quarantine
directory and puts `store_render.png` (the image to look at) in the review area; a mismatch is shown prominently at the top of `summary.txt`. Without a
renderer it says plainly that the preview is producer-supplied and unverified, and writes no check (so `adopt` refuses).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.contracts import ReviewRenderCheck, canonical_json, parse_record
from visual_assets.store.contracts.base import ContractError
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.errors import IntakeError, StageError
from visual_assets.store.intake import quarantine, service
from visual_assets.store.rendering import RenderTool, compare_preview

STORE_RENDER_FILE = "store_render.png"

NO_RENDERER_NOTE = (
    "The preview is producer-supplied and UNVERIFIED: this machine cannot render the source (no Aseprite or bwrap), so nothing proves the preview "
    "depicts it. `adopt` will refuse until the review is done where Aseprite is available."
)
MATCH_NOTE = "Store render: MATCH. The store rendered the source itself (store_render.png) and its pixels equal the producer's preview."
MISMATCH_NOTE = (
    "!!! THE PREVIEW DOES NOT MATCH THE SOURCE !!! The store rendered the source itself (store_render.png) and its pixels differ from the producer's "
    "preview. Look at store_render.png, not preview.png. `adopt` will refuse this candidate."
)


@dataclass(frozen=True)
class ReviewOutcome:
    directory: Path
    verdict: RenderVerdict | None  # None: nothing could be checked here
    note: str


def _same_check(a: ReviewRenderCheck, b: ReviewRenderCheck) -> bool:
    """Equal in everything the check proves; the timestamp and tool version of a later re-run may differ."""
    keys = ("intake_id", "source_hash", "producer_preview_hash", "rendered_png_hash", "producer_pixel_hash", "rendered_pixel_hash", "scale", "verdict")
    return all(getattr(a, k) == getattr(b, k) for k in keys)


def review(intake_id: str, *, created_at: str, renderer: RenderTool | None) -> ReviewOutcome:
    """Export the review directory and, when `renderer` is given, record the store's own render check. Raises coded errors."""
    material = service.prepare_review(intake_id)
    if renderer is None:
        return ReviewOutcome(service.export_review(material, notes=(NO_RENDERER_NOTE,)), None, NO_RENDERER_NOTE)

    comparison = compare_preview(
        intake_id=intake_id, source=material.files.source, preview=material.files.preview, tool=renderer, created_at=created_at
    )
    path = config.QUARANTINE_ROOT / intake_id / quarantine.RENDER_CHECK_FILE
    check = comparison.check
    if path.exists() or path.is_symlink():
        try:
            existing = parse_record(ReviewRenderCheck, quarantine.read_one(path.parent, path.name))
        except (StageError, ContractError) as exc:
            raise IntakeError("render_check_corrupt", f"{intake_id}: the stored render check cannot be read ({exc.code})") from None
        if not _same_check(existing, check):
            raise IntakeError("render_check_differs", f"{intake_id}: the render no longer matches the stored check (a non-reproducible render?)")
        check = existing  # idempotent: the first record stands
    else:
        quarantine.write_new(path, canonical_json(check))
    note = MATCH_NOTE if check.verdict is RenderVerdict.MATCH else MISMATCH_NOTE
    directory = service.export_review(material, notes=(note,), extra_files={STORE_RENDER_FILE: comparison.rendered_png})
    return ReviewOutcome(directory, check.verdict, note)
