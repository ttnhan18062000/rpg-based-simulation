"""A committed fixture draft set and its preview export, built without Aseprite, for the isolated draft preview page.

A set `fixture-terrain` of five terrain keys: `terrain.forest` with its three REAL adopted tiles (plain, bush, tree: read from the committed catalog's artifacts and shown as 8x
previews) and four synthetic tiles (desert, swamp, mountain, grassland). The remaining Live Map terrain codes are deliberately absent, so the page's "missing draft" fallback shows.
Everything is deterministic (fixed ids, timestamps and zlib level 0 so the bytes are portable). The committed copy lives at
`frontend/src/visualAssets/__fixtures__/draft/`; this is the only link between `visual_assets` and `frontend/` (file level, no import either way).

    python -m tests.visual_assets.store.draft_fixture --write    # refresh the committed copy
    python -m tests.visual_assets.store.draft_fixture --check    # exit 1 if it differs from a fresh export
"""

from __future__ import annotations

import argparse
import contextlib
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

from tests.visual_assets.store import builders as b
from tests.visual_assets.store import runtime_fixture as rf
from visual_assets.store import config, draftexport, drafts, pixels, records
from visual_assets.store.catalog.registry import Registry
from visual_assets.store.contracts.definitions import DetailAxis, VisualKeyDefinition
from visual_assets.store.intake import intake

REPO = Path(__file__).resolve().parents[3]
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "draft"
SET_ID = "fixture-terrain"
SIZE = 16
SCALE = 8
Pixel = tuple[int, int, int, int]

# (visual key, detail or None, source asset id of the committed catalog artifact to show, or the synthetic kind to draw)
ENTRIES = (
    ("terrain.forest", None, "terrain_forest"),
    ("terrain.forest", "bush", "terrain_forest_bush"),
    ("terrain.forest", "tree", "terrain_forest_tree"),
    ("terrain.desert", None, "desert"),
    ("terrain.swamp", None, "swamp"),
    ("terrain.mountain", None, "mountain"),
    ("terrain.grassland", None, "grassland"),
)


def _noise(x: int, y: int, k: int = 0) -> int:
    return ((x * 73856093) ^ (y * 19349663) ^ (k * 83492791)) % 100


def synthetic_tile(kind: str) -> list[Pixel]:
    """16 x 16 RGBA, row-major: a flat colour with a simple motif per terrain, distinct at a glance."""
    out: list[Pixel] = []
    for y in range(SIZE):
        for x in range(SIZE):
            if kind == "desert":
                base = (196, 170, 100)
                shade = (168, 140, 78) if (x + 2 * y) % 7 == 0 else None
                spot = (214, 190, 120) if _noise(x, y) < 6 else None
            elif kind == "swamp":
                base = (46, 66, 52)
                shade = (74, 104, 82) if y % 5 == 2 and x % 6 in (1, 2, 3) else None
                spot = (28, 40, 32) if _noise(x, y, 2) < 9 else None
            elif kind == "mountain":
                base = (112, 112, 120)
                peak = (x - 7.5) / 7.5
                shade = (170, 170, 178) if abs(peak) * 7.5 + y * 0.9 < 8 and y > 1 and abs(x - 7.5) < y + 1 else None
                spot = (80, 80, 88) if _noise(x, y, 3) < 8 else None
            else:  # grassland
                base = (92, 142, 62)
                shade = (128, 176, 84) if (x + y * 3) % 8 == 1 else None
                spot = (70, 116, 48) if _noise(x, y, 4) < 10 else None
            out.append((*(shade or spot or base), 255))
    return out


def real_tile(source_asset_id: str) -> list[Pixel]:
    """The adopted 16 x 16 artifact of `source_asset_id` from the committed catalog."""
    directory = records.generated_dir() / f"{source_asset_id}--x1"
    (png_path,) = sorted(directory.glob("*.png"))
    image = pixels.decode_png(png_path.read_bytes(), max_dim=config.MAX_DIM)
    assert (image.width, image.height) == (SIZE, SIZE)
    return [tuple(image.rgba[i : i + 4]) for i in range(0, len(image.rgba), 4)]  # type: ignore[misc]


def preview_png(tile: list[Pixel]) -> bytes:
    scaled = [tile[(y // SCALE) * SIZE + (x // SCALE)] for y in range(SIZE * SCALE) for x in range(SIZE * SCALE)]
    # level 0 (stored blocks): the bytes do not depend on which zlib implementation compresses them, so the committed copy is portable
    return b.png_encode(SIZE * SCALE, SIZE * SCALE, scaled, level=0)


def fixture_registry() -> Registry:
    keys = {}
    for key in ("terrain.forest", "terrain.desert", "terrain.swamp", "terrain.mountain", "terrain.grassland"):
        detail = DetailAxis(values=("plain", "bush", "tree"), default="plain") if key == "terrain.forest" else None
        keys[key] = VisualKeyDefinition(key=key, family="terrain", description="fixture", variant_axes=(), optional=False, detail=detail)
    return Registry(keys, {}, "sha256:" + "0" * 64)


@contextlib.contextmanager
def isolated_drafts(base: Path):
    saved = config.DRAFTS_ROOT
    config.DRAFTS_ROOT = base / "drafts"
    try:
        yield
    finally:
        config.DRAFTS_ROOT = saved


def export_fixture(out_dir: Path) -> None:
    """Keep the fixture drafts in a scratch drafts root and export the set to `out_dir` (which must not exist). Reads the committed catalog's forest artifacts."""
    tiles = {sid: real_tile(sid) if sid.startswith("terrain_forest") else synthetic_tile(sid) for _, _, sid in ENTRIES}  # read before the roots are isolated
    with tempfile.TemporaryDirectory(prefix="draft-fixture-") as scratch:
        base = Path(scratch)
        with rf.isolated_roots(base), isolated_drafts(base):
            registry = fixture_registry()
            for number, (key, detail, sid) in enumerate(ENTRIES, 1):
                source = b.aseprite(width=SIZE, height=SIZE, layers=number)
                preview = preview_png(tiles[sid])
                package = b.package_bytes(source, preview, candidate_id=f"cand-{number:016x}")
                directory = b.write_dir(base / f"package-{number}", package, source, preview)
                result = intake(directory, created_at="2026-01-01T00:00:00Z")
                assert result.verdict.value == "PASSED", result.findings
                drafts.keep(result.intake_id, set_id=SET_ID, visual_key=key, detail=detail, registry=registry,
                            source_asset_id=sid if not sid.startswith("terrain_forest") else f"draft_{sid}")
            draftexport.export_draft_preview(SET_ID, out_dir, registry=registry)


def same_tree(left: Path, right: Path) -> bool:
    names = lambda root: sorted(p.name for p in root.iterdir())  # noqa: E731
    return names(left) == names(right) and all(filecmp.cmp(left / n, right / n, shallow=False) for n in names(left))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="draft-fixture-out-") as scratch:
        fresh = Path(scratch) / "draft"
        export_fixture(fresh)
        if args.check:
            ok = COMMITTED.is_dir() and same_tree(fresh, COMMITTED)
            print("fixture is current" if ok else f"{COMMITTED} differs from a fresh export; run with --write")
            return 0 if ok else 1
        assert COMMITTED.name == "draft" and COMMITTED.parent.name == "__fixtures__", COMMITTED
        if COMMITTED.exists():
            shutil.rmtree(COMMITTED)
        COMMITTED.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(fresh, COMMITTED)
        print(f"wrote {COMMITTED}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
