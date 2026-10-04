"""The synthetic rehearsal catalog and its runtime export, built without Aseprite.

Three `fixture.rehearsal.*` assets of 16 x 16 pixels in clearly different SHAPES (a diamond, a disc, a hollow frame), not only
different hues: the surface rehearsal (ticket 4) checks that its three images differ in their alpha masks. Everything is deterministic
(fixed timestamps and ids, a renderer that draws the shape registered for a source's hash), so the same code always produces
byte-identical output. The committed copy lives at `frontend/src/visualAssets/__fixtures__/rehearsal/`; this is the only link between
`visual_assets` and `frontend/`, at test time and file level (no import either way).

    python -m tests.visual_assets.store.runtime_fixture --write    # refresh the committed copy
    python -m tests.visual_assets.store.runtime_fixture --check    # exit 1 if it differs from a fresh regeneration
"""

from __future__ import annotations

import argparse
import contextlib
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import builders as b
from visual_assets.store import config
from visual_assets.store import review as review_api
from visual_assets.store.build import exporter
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.intake import aseprite, intake
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.release import assemble_release
from visual_assets.store.runtime_export import export_runtime

REPO = Path(__file__).resolve().parents[3]
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "rehearsal"
CATALOG_ID, RELEASE_ID = "rehearsal", "rc-0001"
SIZE = 16

# (source asset id, visual key, registry family, shape, colour, source layers): the layer count only makes the source bytes differ
ASSETS = (
    ("gem", "fixture.rehearsal.gem", "item", "diamond", (40, 200, 220), 1),
    ("rock", "fixture.rehearsal.rock", "terrain", "disc", (130, 130, 140), 2),
    ("frame", "fixture.rehearsal.frame", "ui", "frame", (230, 190, 60), 3),
)
CLEAR = (0, 0, 0, 0)


def shape_pixels(shape: str, colour: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    """16 x 16 RGBA, row-major. Pixel centres are tested against the shape, so the masks are symmetric and clearly different."""
    solid = (*colour, 255)
    out = []
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x - 7.5, y - 7.5
            if shape == "diamond":
                inside = abs(dx) + abs(dy) <= 7
            elif shape == "disc":
                inside = dx * dx + dy * dy <= 7.5 * 7.5
            else:  # frame: a hollow square, two pixels thick
                inside = max(abs(dx), abs(dy)) <= 7.5 and max(abs(dx), abs(dy)) >= 5.5
            out.append(solid if inside else CLEAR)
    return out


def shape_png(shape: str, colour: tuple[int, int, int], scale: int = 1) -> bytes:
    pixels = shape_pixels(shape, colour)
    if scale > 1:
        pixels = [pixels[(y // scale) * SIZE + (x // scale)] for y in range(SIZE * scale) for x in range(SIZE * scale)]
    # level 0 (stored blocks): the bytes do not depend on which zlib implementation compresses them, so the committed copy is portable
    return b.png_encode(SIZE * scale, SIZE * scale, pixels, level=0)


class ShapeRenderer:
    """A deterministic stand-in for the sandboxed Aseprite: it draws the shape registered for a source's file hash."""

    tool_name = "Aseprite"
    tool_version = "1.3.test"

    def __init__(self, by_source_hash: dict[str, tuple[str, tuple[int, int, int]]]) -> None:
        self._by_hash = by_source_hash

    def render(self, source: bytes, *, scale: int) -> bytes:
        facts, _ = aseprite.read_facts(source)
        assert (facts.width, facts.height) == (SIZE, SIZE)
        shape, colour = self._by_hash[file_hash(source)]
        return shape_png(shape, colour, scale)


@contextlib.contextmanager
def isolated_roots(base: Path):
    """Point the store at `base/catalog` etc. for the duration (every store module reads `config.NAME` at call time)."""
    saved = (config.CATALOG_ROOT, config.QUARANTINE_ROOT, config.REVIEW_ROOT)
    config.CATALOG_ROOT, config.QUARANTINE_ROOT, config.REVIEW_ROOT = base / "catalog", base / "quarantine", base / "review"
    config.CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        config.CATALOG_ROOT, config.QUARANTINE_ROOT, config.REVIEW_ROOT = saved


def build_catalog(work: Path) -> None:
    """Adopt, build and release the three assets in the CURRENT store roots (patched by the caller). Returns nothing; `rc-0001` exists after."""
    catalog = config.CATALOG_ROOT
    s.write_export_config(catalog)
    s.write_store_format(catalog)
    lines = ["record_type: visual_key_registry", "schema_version: 1", "keys:"]
    lines += [f"  - {{key: {key}, family: {family}, description: synthetic rehearsal image, variant_axes: [], optional: false}}" for _, key, family, *_ in ASSETS]
    lines.append("aliases: []")
    registry_path = catalog / "definitions" / "visual_keys.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text("\n".join(lines) + "\n")
    registry = load_registry(registry_path, allow_fixture_namespace=True)

    sources = {sid: b.aseprite(width=SIZE, height=SIZE, layers=layers) for sid, _, _, _, _, layers in ASSETS}
    renderer = ShapeRenderer({file_hash(sources[sid]): (shape, colour) for sid, _, _, shape, colour, _ in ASSETS})
    for number, (sid, key, _, shape, colour, _) in enumerate(ASSETS, 1):
        preview = shape_png(shape, colour)
        package = b.package_bytes(sources[sid], preview, candidate_id=f"cand-{number:016x}")
        directory = b.write_dir(work / f"package-{sid}", package, sources[sid], preview)
        result = intake(directory, created_at="2026-01-01T00:00:00Z")
        assert result.verdict.value == "PASSED", result.findings
        review_api.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer)
        s.do_adopt(result.intake_id, source_asset_id=sid, visual_key=key, registry=registry, renderer=renderer)
    exporter.build(renderer=renderer)
    assemble_release(CATALOG_ID, release_id=RELEASE_ID, allow_fixture_namespace=True)


def export_fixture(out_dir: Path) -> None:
    """Build the whole synthetic catalog in a scratch area and export release `rc-0001` to `out_dir` (which must not exist)."""
    with tempfile.TemporaryDirectory(prefix="rehearsal-") as scratch:
        base = Path(scratch)
        with isolated_roots(base):
            build_catalog(base)
            export_runtime(CATALOG_ID, RELEASE_ID, out_dir, allow_fixture_namespace=True)


def same_tree(left: Path, right: Path) -> bool:
    """True when both directories hold the same file names with byte-identical contents."""
    names = lambda root: sorted(p.name for p in root.iterdir())  # noqa: E731
    if names(left) != names(right):
        return False
    return all(filecmp.cmp(left / name, right / name, shallow=False) for name in names(left))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="replace the committed copy with a fresh export")
    mode.add_argument("--check", action="store_true", help="exit 1 when the committed copy differs from a fresh export")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="rehearsal-out-") as scratch:
        fresh = Path(scratch) / "rehearsal"
        export_fixture(fresh)
        if args.check:
            ok = COMMITTED.is_dir() and same_tree(fresh, COMMITTED)
            print("fixture is current" if ok else f"{COMMITTED} differs from a fresh export; run with --write")
            return 0 if ok else 1
        assert COMMITTED.name == "rehearsal" and COMMITTED.parent.name == "__fixtures__", COMMITTED  # the only directory this ever replaces
        if COMMITTED.exists():
            shutil.rmtree(COMMITTED)
        COMMITTED.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(fresh, COMMITTED)
        print(f"wrote {COMMITTED}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
