"""The committed frontend fixture equals a fresh regeneration, and its three images differ in shape (alpha mask), not only in colour."""

from __future__ import annotations

from itertools import combinations

from tests.visual_assets.store import runtime_fixture as fx
from visual_assets.store import pixels
from visual_assets.store.contracts import RuntimeManifest, parse_record


def test_the_committed_fixture_is_byte_identical_to_a_fresh_regeneration(tmp_path):
    fresh = tmp_path / "rehearsal"
    fx.export_fixture(fresh)
    assert fx.COMMITTED.is_dir(), "run: python -m tests.visual_assets.store.runtime_fixture --write"
    assert fx.same_tree(fresh, fx.COMMITTED), "the committed fixture is stale: run python -m tests.visual_assets.store.runtime_fixture --write"


def test_the_three_images_differ_in_their_alpha_masks_not_only_their_colours():
    runtime = parse_record(RuntimeManifest, (fx.COMMITTED / "runtime_manifest.json").read_bytes())
    assert len(runtime.entries) == 3
    masks = {}
    for entry in runtime.entries:
        image = pixels.decode_png((fx.COMMITTED / entry.file).read_bytes(), max_dim=16)
        assert (image.width, image.height) == (16, 16)
        masks[entry.visual_key] = bytes(1 if a else 0 for a in image.rgba[3::4])
        assert 0 < sum(masks[entry.visual_key]) < 256  # neither empty nor a full square
    for (_, left), (_, right) in combinations(sorted(masks.items()), 2):
        differing = sum(a != b for a, b in zip(left, right))
        assert differing >= 20, differing  # clearly different shapes, not a one-pixel difference


def test_the_fixture_keys_live_in_the_reserved_fixture_namespace():
    runtime = parse_record(RuntimeManifest, (fx.COMMITTED / "runtime_manifest.json").read_bytes())
    assert all(e.visual_key.startswith("fixture.rehearsal.") for e in runtime.entries)
