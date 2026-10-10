"""The committed evidence of the rehearsal captured from the BUILT bundle (`TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`; local-only `make visual-assets-bundle-capture`).

CI never runs the capture. What CI can check is that the committed record (`docs/assets/surface_rehearsal_bundle_evidence.json.txt`) says what a real run established and nothing more:
every page loaded only hashed images of committed fixtures, `rehearsal.html` carries exactly three identical pixel verdicts equal to the committed manifest's own hashes, the OTHER pages say in
plain words that they have no pixel verdict, and the planted wrong asset (one pixel changed) was caught. Pure functions over the record; the rules are proven on planted violations.
"""

from __future__ import annotations

import copy
import json

import pytest

from tools import visual_assets_bundle_capture as bundle
from visual_assets.store import pixels

MANIFEST = json.loads((bundle.FIXTURES / "rehearsal" / "runtime_manifest.json").read_text())
ENTRIES = {e["visual_key"]: e for e in MANIFEST["entries"]}
FILES = bundle.fixture_files()
OTHER_FILES = sorted(FILES - {e["file"] for e in MANIFEST["entries"]})[:2]


def url_of(file: str) -> str:
    return f"/assets/{file[:-4]}-AbCd1234.png"


def run_evidence(*, planted: bool = False) -> dict:
    """What the spec writes for a run (the real one when `planted` is False)."""
    pages = []
    for name in bundle.PAGE_NAMES:
        files = [e["file"] for e in MANIFEST["entries"]] if name == bundle.PIXEL_PAGE else OTHER_FILES
        page = {"page": name, "settled": f"data-settled=true on [data-testid={name}]", "image_urls": [url_of(f) for f in files], "all_images_hashed": True,
                "unknown_fixture_files": [], "dev_server_requests": [], "failed_requests": [], "data_url_images": 0, "pixel_verified": False, "pixel_verdicts": None}
        if name == bundle.PIXEL_PAGE:
            verdicts = {k: {"expected": ENTRIES[k]["pixel_hash"], "drawn": ENTRIES[k]["pixel_hash"], "identical": True, "scale": 1} for k in bundle.PIXEL_KEYS}
            if planted:
                verdicts[bundle.PIXEL_KEYS[0]].update(drawn="pixels-v1:" + "0" * 64, identical=False)
            page["pixel_verdicts"], page["pixel_verified"] = verdicts, not planted
        pages.append(page)
    return {"browser": "chromium", "browser_version": "151.0.0.0", "device_pixel_ratio": 1, "pages": pages}


def good_record() -> dict:
    return bundle.compose_record(
        run_evidence(), run_evidence(planted=True), 1, changed_file=ENTRIES[bundle.PIXEL_KEYS[0]]["file"], commit="a" * 40, run_at="2026-10-10T12:00:00Z", vite_version="vite/7.3.1",
    )


def problems(record: dict) -> list[str]:
    return bundle.record_problems(record, MANIFEST, FILES)


# ---- the planted image ----

def test_the_planted_png_decodes_to_the_same_size_with_exactly_one_pixel_one_byte_different():
    for entry in MANIFEST["entries"]:
        original = (bundle.FIXTURES / "rehearsal" / entry["file"]).read_bytes()
        planted = bundle.plant_one_pixel(original)
        before, after = pixels.decode_png(original, max_dim=128), pixels.decode_png(planted, max_dim=128)
        assert (before.width, before.height) == (after.width, after.height) and planted != original
        differing = [i for i in range(len(before.rgba)) if before.rgba[i] != after.rgba[i]]
        assert len(differing) == 1 and differing[0] % 4 == 0 and abs(before.rgba[differing[0]] - after.rgba[differing[0]]) == 1, entry["file"]
        assert pixels.pixel_hash_of(after) != pixels.pixel_hash_of(before) == entry["pixel_hash"]


def test_an_image_with_no_opaque_pixel_cannot_be_planted():
    from visual_assets.store import atlas

    with pytest.raises(ValueError):
        bundle.plant_one_pixel(atlas.encode_png(2, 2, bytes(16)))


def test_the_hashed_url_pattern_accepts_a_built_asset_and_refuses_dev_server_and_inlined_urls():
    stem = "a" * 64
    assert bundle.HASHED_URL.match(f"/assets/{stem}-DVm3K1xP.png").group(1) == stem
    for bad in (f"/src/visualAssets/__fixtures__/rehearsal/{stem}.png", f"/assets/{stem}.png", f"/assets/{stem}-short.png", f"/assets/x-DVm3K1xP.png", "data:image/png;base64,AAAA", f"/assets/{stem}-DVm3K1xP.jpg"):
        assert not bundle.HASHED_URL.match(bad), bad


# ---- the record's rules, on planted violations ----

def test_a_record_composed_from_a_good_run_and_a_caught_planted_run_has_no_problems():
    assert problems(good_record()) == []


def test_the_record_says_per_page_which_pages_have_pixel_verdicts_and_which_do_not():
    record = good_record()
    by_page = {p["page"]: p for p in record["pages"]}
    assert by_page["rehearsal"]["pixel_verification"] == bundle.VERIFIED and sorted(by_page["rehearsal"]["pixel_verdicts"]) == sorted(bundle.PIXEL_KEYS)
    for name in ("pilot", "map", "icons", "draft"):
        assert by_page[name]["pixel_verification"] == bundle.NOT_TAKEN and by_page[name]["pixel_verdicts"] is None, name
    assert "asset-loading evidence only" in bundle.NOT_TAKEN and record["gate_result_moved"] is False


def mutate(path, change):
    record = good_record()
    before = json.dumps(record, sort_keys=True)
    change(record)
    assert json.dumps(record, sort_keys=True) != before, "the mutant must change the record"
    return problems(record)


@pytest.mark.parametrize("name, change", [
    ("an unhashed image", lambda r: r["pages"][1]["images"][0].update(url="/src/visualAssets/__fixtures__/pilot/x.png")),
    ("an image that is not a committed fixture", lambda r: r["pages"][2]["images"][0].update(url=url_of("f" * 64 + ".png"), fixture_file="f" * 64 + ".png")),
    ("all_images_hashed false", lambda r: r["pages"][3].update(all_images_hashed=False)),
    ("an inlined data image", lambda r: r["pages"][0].update(data_url_images=1)),
    ("a dev-server request", lambda r: r["pages"][4].update(dev_server_requests=["/src/main.tsx"])),
    ("a failed request", lambda r: r["pages"][1].update(failed_requests=["404 /assets/x.png"])),
    ("no images on a page", lambda r: r["pages"][2].update(images=[])),
    ("a pixel verdict that is not identical", lambda r: r["pages"][0]["pixel_verdicts"][bundle.PIXEL_KEYS[1]].update(identical=False)),
    ("a drawn hash that differs from the manifest", lambda r: r["pages"][0]["pixel_verdicts"][bundle.PIXEL_KEYS[2]].update(drawn="pixels-v1:" + "1" * 64, expected="pixels-v1:" + "1" * 64)),
    ("a missing pixel verdict", lambda r: r["pages"][0]["pixel_verdicts"].pop(bundle.PIXEL_KEYS[0])),
    ("a pixel verdict at a non-native scale", lambda r: r["pages"][0]["pixel_verdicts"][bundle.PIXEL_KEYS[0]].update(scale=2)),
    ("a pixel verdict claimed for a page without one", lambda r: r["pages"][1].update(pixel_verification=bundle.VERIFIED, pixel_verdicts={"x": {}})),
    ("a page that does not say it has no pixel verdict", lambda r: r["pages"][3].update(pixel_verification="verified")),
    ("a planted proof that was not caught", lambda r: r["planted"].update(capture_failed=False)),
    ("a planted proof that failed on the wrong image", lambda r: r["planted"].update(failing_verdicts=[bundle.PIXEL_KEYS[1]])),
    ("a planted proof of a different file", lambda r: r["planted"].update(changed_fixture_file=ENTRIES[bundle.PIXEL_KEYS[1]]["file"])),
    ("a moved gate result", lambda r: r.update(gate_result_moved=True)),
    ("a HiDPI run", lambda r: r.update(device_pixel_ratio=2)),
    ("a blank browser version", lambda r: r.update(browser_version=" ")),
    ("a wrong make target", lambda r: r.update(make_target="other")),
    ("an extra key", lambda r: r.update(extra=1)),
    ("a page missing", lambda r: r["pages"].pop()),
    ("pages out of order", lambda r: r["pages"].reverse()),
])
def test_each_planted_violation_is_reported(name, change):
    assert mutate(None, change), name


def test_a_planted_run_that_the_capture_did_not_fail_is_reported_not_recorded():
    record = bundle.compose_record(run_evidence(), run_evidence(planted=True), 0, changed_file=ENTRIES[bundle.PIXEL_KEYS[0]]["file"], commit="a" * 40, run_at="x", vite_version="v")
    assert record["planted"]["capture_failed"] is False and problems(record)


def test_a_record_that_is_not_an_object_is_reported():
    assert bundle.record_problems([], MANIFEST, FILES) and bundle.record_problems(None, MANIFEST, FILES)
