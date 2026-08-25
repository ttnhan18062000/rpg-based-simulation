"""Live, repeatable end-to-end check of src/rendering/review_pipeline.py's Tier 0 -> Tier 1 ->
Tier 2 escalation pipeline -- both branches, not just the one a single real-world run happens to
hit.

`tools/calibrate_rendering.py` only exercises the four raw metric modules (connectivity, density,
shape, variants-TVD) -- it never calls `grading.py` or `review_pipeline.py`, so it cannot confirm
the escalation decision or the Tier 2 annotated-render write path actually work. This script fills
that gap: runs the full pipeline twice, once against a real compiled world (exercising the
no-escalation branch, since dungeon_crawl/seed 42 scores a healthy grade), once against a
deliberately disconnected synthetic state (exercising the escalation branch and the annotated PNG
write, exactly the recipe `tests/unit/rendering/test_review_pipeline.py`'s
`test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_escalated` already unit-tests,
but driven live here against the real pipeline entry point rather than only via pytest).

Usage:
    python3 tools/review_pipeline_check.py [--world dungeon_crawl] [--seed 42] [--out-dir DIR]

Exit code 0 and a final "ALL CHECKS PASSED" line on success; non-zero and a clear failure reason
otherwise. Meant to be re-run any time this pipeline's behavior needs live re-confirmation, not a
one-shot investigation script.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.state import AuthoritativeState
from src.rendering.review_pipeline import run_tier0_tier1_pipeline
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository


def _read_png_dimensions(path: str) -> tuple[int, int]:
    """Minimal IHDR read -- src/rendering/png_writer.py is a hand-rolled, dependency-free
    encoder (no Pillow anywhere in this project's rendering stack), so a full-image decode
    isn't available; validating the PNG signature + IHDR chunk is the same level of integrity
    check the existing unit test (`_read_ihdr`) already relies on."""
    with open(path, "rb") as fh:
        data = fh.read(33)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} does not start with a valid PNG signature")
    if data[12:16] != b"IHDR":
        raise ValueError(f"{path} has no IHDR chunk where expected")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _build_disconnected_state() -> AuthoritativeState:
    """Two unreachable 3x3 blobs -- same recipe as the unit test's own fixture, kept in sync
    deliberately so this script and the pytest suite are testing the identical scenario."""
    terrain: dict[tuple[int, int], str] = {}
    for x in range(3):
        for y in range(3):
            terrain[(x, y)] = "PLAIN"
    for x in range(10, 13):
        for y in range(10, 13):
            terrain[(x, y)] = "PLAIN"
    return AuthoritativeState(tick=0, seed=42, entities={}, terrain=terrain)


def check_no_escalation_branch(world_id: str, seed: int, out_dir: str) -> None:
    print(f"[1/2] Real world '{world_id}' seed={seed} -- expecting NO escalation...")
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, _compile_report = WorldCompiler.compile(spec, seed=seed)

    digest = run_tier0_tier1_pipeline(state, world_id=world_id, base_dir=out_dir, run_id="review-check-real")

    print(f"    grade={digest.grade} combined_score={digest.combined_score:.3f} escalate={digest.escalate}")
    if digest.escalate:
        raise AssertionError(
            f"expected no escalation for {world_id}/{seed} but escalate=True "
            f"(grade={digest.grade}) -- either the world's real state changed or the grading "
            f"config drifted; investigate before trusting this check's other branch"
        )
    if digest.annotated_render_path is not None:
        raise AssertionError("escalate=False but annotated_render_path is not None -- bug")
    annotated_dir = os.path.join(out_dir, "review-check-real", "renders")
    if os.path.isdir(annotated_dir):
        leftover_annotated = [f for f in os.listdir(annotated_dir) if "annotated" in f]
        if leftover_annotated:
            raise AssertionError(
                f"escalate=False but found annotated PNG(s) on disk anyway: {leftover_annotated}"
            )
    print("    PASS: no annotated render written, as expected")


def check_escalation_branch(out_dir: str) -> None:
    print("[2/2] Synthetic disconnected world -- expecting escalation + annotated PNG...")
    state = _build_disconnected_state()

    digest = run_tier0_tier1_pipeline(state, world_id="review_check_synthetic", base_dir=out_dir, run_id="review-check-synthetic")

    print(f"    grade={digest.grade} combined_score={digest.combined_score:.3f} escalate={digest.escalate}")
    if not digest.escalate:
        raise AssertionError("expected escalation for a deliberately disconnected state, got escalate=False")
    if digest.annotated_render_path is None:
        raise AssertionError("escalate=True but annotated_render_path is None -- bug")
    if not os.path.isfile(digest.annotated_render_path):
        raise AssertionError(f"annotated_render_path does not exist on disk: {digest.annotated_render_path}")

    width, height = _read_png_dimensions(digest.annotated_render_path)
    size_bytes = os.path.getsize(digest.annotated_render_path)
    if width <= 0 or height <= 0 or size_bytes <= 100:
        raise AssertionError(
            f"annotated PNG looks degenerate: {width}x{height}, {size_bytes} bytes"
        )
    print(f"    PASS: real annotated PNG written -- {width}x{height}, {size_bytes} bytes, "
          f"at {digest.annotated_render_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", default="dungeon_crawl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    out_dir = args.out_dir or tempfile.mkdtemp(prefix="review_pipeline_check_")
    print(f"Output dir: {out_dir}\n")

    try:
        check_no_escalation_branch(args.world, args.seed, out_dir)
        check_escalation_branch(out_dir)
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        return 1

    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
