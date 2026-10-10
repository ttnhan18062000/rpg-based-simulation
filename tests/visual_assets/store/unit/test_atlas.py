"""Opt-in runtime atlases (TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT): deterministic packing, extrude and gutter, pixel equality with the per-file export, no change to the manifest."""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from pathlib import Path

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.store import atlas, cli, config, pixels, runtime_export
from visual_assets.store.contracts import canonical_json, parse_record
from visual_assets.store.contracts.atlas import AtlasManifest
from visual_assets.store.contracts.runtime import RuntimeEntry
from visual_assets.store.errors import BuildError

REAL = config.CATALOG_ROOT


def image(width, height, seed):
    rng = random.Random(seed)
    px = [(rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.choice((0, 255, 128))) for _ in range(width * height)]
    return pixels.decode_png(b.png_encode(width, height, px))


def entry(key, img, detail=None):
    ph = pixels.pixel_hash_of(img)
    return RuntimeEntry(visual_key=key, family="icon", pixel_hash=ph, file=ph.split(":", 1)[1] + ".png", width=img.width, height=img.height, detail=detail)


def make(sizes):
    imgs = {f"icon.k{i:02d}": image(w, h, i) for i, (w, h) in enumerate(sizes)}
    entries = [entry(k, v) for k, v in imgs.items()]
    return entries, {e.pixel_hash: imgs[e.visual_key] for e in entries}


def build(entries, images):
    png, data = atlas.build_atlas("icon", entries, images, catalog_id="pilot", release_id="rc-0001")
    return png, data, parse_record(AtlasManifest, data)


def sheet_of(png):
    return pixels.decode_png(png, max_dim=config.MAX_ATLAS_DIM)


def px(img, x, y):
    return img.rgba[(y * img.width + x) * 4 : (y * img.width + x) * 4 + 4]


def test_every_rectangle_holds_its_artifact_and_is_surrounded_by_its_own_edge():
    entries, images = make([(16, 16), (24, 24), (1, 1), (5, 3), (16, 24)])
    png, _, manifest = build(entries, images)
    sheet = sheet_of(png)
    assert len(manifest.entries) == 5
    for e in manifest.entries:
        src = images[e.pixel_hash]
        for yy in range(-1, e.height + 1):
            for xx in range(-1, e.width + 1):
                assert px(sheet, e.x + xx, e.y + yy) == px(src, min(max(xx, 0), e.width - 1), min(max(yy, 0), e.height - 1)), (e.visual_key, xx, yy)  # extrude, corners included


def test_the_gutter_and_the_sheet_edge_are_transparent_black_and_cells_never_overlap():
    entries, images = make([(16, 16)] * 6 + [(24, 24)] * 3)
    png, _, manifest = build(entries, images)
    sheet = sheet_of(png)
    covered = set()
    for e in manifest.entries:
        cells = {(x, y) for y in range(e.y - 1, e.y + e.height + 1) for x in range(e.x - 1, e.x + e.width + 1)}
        assert not covered & cells
        covered |= cells
    for y in range(sheet.height):
        for x in range(sheet.width):
            if (x, y) not in covered:
                assert px(sheet, x, y) == b"\x00\x00\x00\x00"
    assert min(x for x, _ in covered) >= 1 and min(y for _, y in covered) >= 1  # a gutter around the sheet
    assert max(x for x, _ in covered) <= sheet.width - 2 and max(y for _, y in covered) <= sheet.height - 2
    assert (sheet.width, sheet.height) == (manifest.width, manifest.height)


def test_packing_is_deterministic_and_independent_of_input_order():
    entries, images = make([(16, 16), (24, 24), (7, 9), (16, 16), (3, 3)])
    first = build(entries, images)
    second = build(list(reversed(entries)), images)
    shuffled = list(entries)
    random.Random(1).shuffle(shuffled)
    assert first[0] == second[0] == build(shuffled, images)[0] and first[1] == second[1]
    assert [e.visual_key for e in first[2].entries] == sorted(e.visual_key for e in first[2].entries)  # sorted by key


def test_shelves_wrap_at_the_fixed_width():
    entries, images = make([(100, 10)] * 12)  # 102 + 1 per cell: 9 fit in 1024, so 2 shelves
    _, _, manifest = build(entries, images)
    assert {e.y for e in manifest.entries} == {2, 15}  # shelf 1 at y=1 (+1 extrude), 12 px tall, one gutter, shelf 2 at y=14 (+1)
    assert sum(e.y == 2 for e in manifest.entries) == 9
    assert manifest.width <= atlas.SHELF_WIDTH


def test_the_atlas_png_has_only_ihdr_idat_iend_and_no_time_or_text():
    entries, images = make([(16, 16), (24, 24)])
    png, _, manifest = build(entries, images)
    assert [kind for kind, _ in pixels._chunks(png)] == [b"IHDR", b"IDAT", b"IEND"]
    assert manifest.file_hash == "sha256:" + hashlib.sha256(png).hexdigest()


def test_a_family_that_does_not_fit_is_refused_not_split(monkeypatch):
    entries, images = make([(16, 16)] * 4)
    monkeypatch.setattr(config, "MAX_ATLAS_DIM", 20)
    with pytest.raises(BuildError) as err:
        build(entries, images)
    assert err.value.code == "atlas_too_large"


def test_the_manifest_json_is_canonical_and_round_trips():
    entries, images = make([(16, 16), (24, 24)])
    _, data, manifest = build(entries, images)
    assert canonical_json(manifest) == data and json.loads(data)["record_type"] == "runtime_atlas"


# ---- verification catches every kind of damage ----

def damaged(png, edit):
    sheet = sheet_of(png)
    rgba = bytearray(sheet.rgba)
    edit(rgba, sheet.width)
    return atlas.encode_png(sheet.width, sheet.height, bytes(rgba))


@pytest.mark.parametrize("name, edit", [
    ("rect pixel", lambda rgba, w, m: rgba.__setitem__(slice(((m.y * w) + m.x) * 4, ((m.y * w) + m.x) * 4 + 4), b"\x01\x02\x03\xff")),
    ("extrude pixel", lambda rgba, w, m: rgba.__setitem__(slice(((m.y - 1) * w + m.x) * 4, ((m.y - 1) * w + m.x) * 4 + 4), b"\x09\x09\x09\xff")),
    ("gutter pixel", lambda rgba, w, m: rgba.__setitem__(slice(0, 4), b"\x05\x05\x05\xff")),
])
def test_verify_rejects_a_damaged_sheet(name, edit):
    entries, images = make([(16, 16), (24, 24)])
    png, _, manifest = build(entries, images)
    first = manifest.entries[0]
    bad = damaged(png, lambda rgba, w: edit(rgba, w, first))
    forged = manifest.model_copy(update={"file_hash": "sha256:" + hashlib.sha256(bad).hexdigest()})  # even with a consistent file hash
    with pytest.raises(BuildError) as err:
        atlas.verify_atlas(bad, forged)
    assert err.value.code == "atlas_mismatch"


def test_verify_rejects_a_wrong_file_hash_and_a_wrong_size():
    entries, images = make([(16, 16)])
    png, _, manifest = build(entries, images)
    with pytest.raises(BuildError):
        atlas.verify_atlas(png + b"", manifest.model_copy(update={"file_hash": "sha256:" + "0" * 64}))
    with pytest.raises(BuildError):
        atlas.verify_atlas(png, manifest.model_copy(update={"width": manifest.width + 1}))


# ---- the export: rc-0008, byte equality, nothing else changes ----

@pytest.fixture(scope="module")
def exports(tmp_path_factory):
    base = tmp_path_factory.mktemp("atlas-export")
    runtime_export.export_runtime("pilot", "rc-0008", base / "plain")
    runtime_export.export_runtime("pilot", "rc-0008", base / "one", atlases=True)
    runtime_export.export_runtime("pilot", "rc-0008", base / "two", atlases=True)
    return base


def test_the_atlas_options_leave_the_per_file_export_and_the_manifest_unchanged(exports):
    plain, one = exports / "plain", exports / "one"
    assert sorted(p.name for p in one.iterdir()) == sorted([p.name for p in plain.iterdir()] + [f"atlas-{f}.{x}" for f in ("border", "icon", "terrain") for x in ("png", "json")])
    for p in plain.iterdir():
        assert (one / p.name).read_bytes() == p.read_bytes()  # runtime_manifest.json included


def test_two_atlas_exports_are_byte_identical(exports):
    one, two = exports / "one", exports / "two"
    assert {p.name: p.read_bytes() for p in one.iterdir()} == {p.name: p.read_bytes() for p in two.iterdir()}


def test_every_key_of_rc_0008_reads_back_from_its_atlas_with_the_artifact_pixels(exports):
    one = exports / "one"
    runtime = json.loads((one / "runtime_manifest.json").read_text())
    seen = 0
    for family in ("border", "icon", "terrain"):
        manifest = parse_record(AtlasManifest, (one / f"atlas-{family}.json").read_bytes())
        sheet = sheet_of((one / manifest.file).read_bytes())
        for e in manifest.entries:
            source = pixels.decode_png((one / (e.pixel_hash.split(":", 1)[1] + ".png")).read_bytes())
            rect = pixels.DecodedImage(e.width, e.height, b"".join(sheet.rgba[((e.y + r) * sheet.width + e.x) * 4 : ((e.y + r) * sheet.width + e.x + e.width) * 4] for r in range(e.height)))
            assert rect.rgba == source.rgba and pixels.pixel_hash_of(rect) == e.pixel_hash
            seen += 1
    assert seen == len(runtime["entries"]) == 70


def test_atlas_pngs_pass_the_chunk_allowlist(exports):
    for p in (exports / "one").glob("atlas-*.png"):
        assert {k for k, _ in pixels._chunks(p.read_bytes())} <= {b"IHDR", b"PLTE", b"tRNS", b"sRGB", b"gAMA", b"IDAT", b"IEND"}


def test_the_cli_flag_is_opt_in(tmp_path):
    assert cli.main(["export-runtime", "--catalog-id", "pilot", "--release-id", "rc-0008", "--out", str(tmp_path / "a")]) == 0
    assert not list((tmp_path / "a").glob("atlas-*"))
    assert cli.main(["export-runtime", "--catalog-id", "pilot", "--release-id", "rc-0008", "--out", str(tmp_path / "b"), "--atlas"]) == 0
    assert len(list((tmp_path / "b").glob("atlas-*"))) == 6
    shutil.rmtree(tmp_path / "a")


def test_a_rectangle_that_holds_another_image_than_its_pixel_hash_refuses_at_build():
    entries, images = make([(16, 16), (16, 16)])
    wrong = dict(images)
    wrong[entries[0].pixel_hash] = image(16, 16, 999)  # consistent sheet (extrude and gutter fine) but the wrong picture for that key
    with pytest.raises(BuildError) as err:
        build(entries, wrong)
    assert err.value.code == "atlas_mismatch" and entries[0].visual_key in str(err.value)
