"""The committed draft-preview fixtures of the CLOSED draft sets are checked against the gate's own record (`tests/visual_assets/closed_draft_fixture.py`; `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`).

Why: a fresh draft export lists a reference for every adopted slot that has a built artifact, so building the 36 icons grew every fresh export (48/56/43 -> 70 entries) while the owner's gates stayed as they
were. The fixtures (and the preview page's tests) are the evidence of what the owner decided on, so they are not regenerated; drafts and references stay byte-checked, and only "must include art built after the
gate" is dropped, only for sets pinned in `adopted_facts.CLOSED_DRAFT_SETS`. An open set keeps the full fresh-export equality. Pure Python, no Aseprite.
"""

from __future__ import annotations

import json
import shutil

import pytest

from tests.visual_assets import adopted_facts as af
from tests.visual_assets import closed_draft_fixture as cdf
from visual_assets.review import icon_draft_fixture as fx
from visual_assets.review import icon_owner_fixes_draft_set, icon_v2_draft_set
from visual_assets.store import config, records

SETS = {
    af.ICON_SET_ID: (fx.COMMITTED, fx.recorded_result_text),
    icon_v2_draft_set.SET_ID: (fx.COMMITTED_V2, fx.recorded_result_text_v2),
    icon_owner_fixes_draft_set.SET_ID: (fx.COMMITTED_FIXES, fx.recorded_result_text_fixes),
}


@pytest.fixture(scope="module")
def fresh_exports(tmp_path_factory):
    out = {}
    for set_id in SETS:
        path = tmp_path_factory.mktemp("fresh") / "export"
        fx.export_fresh(path, set_id)
        out[set_id] = path
    return out


@pytest.fixture(params=sorted(SETS))
def case(request, fresh_exports, tmp_path):
    set_id = request.param
    committed, result_text = SETS[set_id]
    copy = tmp_path / "copy"
    shutil.copytree(committed, copy)
    return set_id, fresh_exports[set_id], copy, result_text


def _write(copy, manifest):
    (copy / fx.MANIFEST).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))


def test_each_closed_set_is_pinned_to_adoption_records_that_exist_and_name_it():
    assert set(SETS) <= set(af.CLOSED_DRAFT_SETS)
    for set_id, pin in af.CLOSED_DRAFT_SETS.items():
        for adoption_id in pin["adoption_ids"]:
            if pin["kind"] == "set_adoption":
                record = json.loads((config.CATALOG_ROOT / "provenance" / "set-adoptions" / f"{adoption_id}.json").read_text())
                assert record["draft_set_hash"] == pin["draft_set_hash"], set_id
            else:
                assert records.load_adoption(adoption_id).source_asset_id.startswith("icon_"), set_id  # the seven revisions; their draft set hash is pinned by test_icon_owner_fixes_adoption


def test_each_fixture_records_the_draft_set_hash_the_owner_adopted_from():
    for set_id, (committed, _) in SETS.items():
        assert json.loads((committed / fx.MANIFEST).read_text())["draft_set_hash"] == af.CLOSED_DRAFT_SETS[set_id]["draft_set_hash"], set_id


def test_a_closed_fixture_matches_its_gate_and_a_full_fresh_export_no_longer_would(case):
    set_id, fresh, copy, result_text = case
    assert cdf.differences(set_id, fresh, copy, result_text) == []
    assert fx.differences(fresh, copy, result_text) != []  # the built icons added references after the gate; this is the drift the closed check ignores
    new = {e["file"] for e in json.loads((fresh / fx.MANIFEST).read_text())["entries"] if e.get("adopted")} - {e["file"] for e in json.loads((copy / fx.MANIFEST).read_text())["entries"]}
    assert new, "the fresh export holds references the gate did not see"


# --- mutation proofs: each mutant is asserted to apply at exactly one site and must be caught ---

def test_mutant_a_flipped_draft_png_byte_is_caught(case):
    set_id, fresh, copy, result_text = case
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    target = next(e["file"] for e in manifest["entries"] if not e.get("adopted"))
    assert sum(e["file"] == target for e in manifest["entries"]) == 1
    data = bytearray((copy / target).read_bytes())
    data[-20] ^= 1
    (copy / target).write_bytes(bytes(data))
    problems = cdf.differences(set_id, fresh, copy, result_text)
    assert any(target in p and "draft PNG" in p for p in problems), problems


def test_mutant_a_flipped_reference_png_byte_is_caught(case):
    set_id, fresh, copy, result_text = case
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    target = next(e["file"] for e in manifest["entries"] if e.get("adopted"))
    assert sum(e["file"] == target for e in manifest["entries"]) == 1
    data = bytearray((copy / target).read_bytes())
    data[-20] ^= 1
    (copy / target).write_bytes(bytes(data))
    problems = cdf.differences(set_id, fresh, copy, result_text)
    assert any(target in p and "not byte-equal" in p for p in problems), problems


def test_mutant_a_reference_naming_an_artifact_that_does_not_exist_is_caught(case):
    set_id, fresh, copy, result_text = case
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    index = next(i for i, e in enumerate(manifest["entries"]) if e.get("adopted"))
    sites = [i for i, e in enumerate(manifest["entries"]) if e.get("adopted") and e["source_asset_id"] == manifest["entries"][index]["source_asset_id"]]
    assert sites == [index]
    manifest["entries"][index]["source_asset_id"] = "terrain_does_not_exist"
    _write(copy, manifest)
    problems = cdf.differences(set_id, fresh, copy, result_text)
    assert any("terrain_does_not_exist" in p for p in problems), problems


def test_mutant_a_stray_entry_is_caught(case):
    set_id, fresh, copy, result_text = case
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    before = len(manifest["entries"])
    stray = dict(next(e for e in manifest["entries"] if not e.get("adopted")), visual_key="icon.stray.key", draft_id="in-0000000000000000")
    manifest["entries"].append(stray)
    assert len(manifest["entries"]) == before + 1
    _write(copy, manifest)
    assert cdf.differences(set_id, fresh, copy, result_text), "a stray entry went unnoticed"


def test_mutant_a_set_removed_from_the_closed_pin_runs_the_full_equality_and_fails_on_todays_store(case):
    set_id, fresh, copy, result_text = case
    pins = dict(af.CLOSED_DRAFT_SETS)
    assert pins.pop(set_id) and set_id not in pins
    assert cdf.differences(set_id, fresh, copy, result_text, closed=pins) != []
    assert cdf.differences(set_id, fresh, copy, result_text, closed=af.CLOSED_DRAFT_SETS) == []
