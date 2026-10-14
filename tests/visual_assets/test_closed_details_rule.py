"""An axis declared after a closed gate does not change what the gate shows (`TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`; planner and lead-planner rulings 2026-10-12, following the rc-0008 ruling (c) for gate-closed sets).

What the owner SAW at a gate stays exact; only an axis the store gained AFTER the gate, on the six pinned terrains, may appear as a fresh `details` row. The mutations each change ONE thing, rewrite the pin
so the "gate evidence was rewritten" check cannot mask the rule under test, and show the closed comparator failing for the right reason. Pure Python, no Aseprite."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil

import pytest

from tests.visual_assets import adopted_facts as af
from tests.visual_assets import closed_draft_fixture as cdf
from tests.visual_assets import derived_runtime
from visual_assets.review import icon_draft_fixture as fx
from visual_assets.review import icon_v2_draft_set
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts import RuntimeManifest, parse_record
from visual_assets.store.errors import ContractError

SET_ID = icon_v2_draft_set.SET_ID
ROW_PROBLEM = "details row"


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    path = tmp_path_factory.mktemp("fresh") / "export"
    fx.export_fresh(path, SET_ID)
    return path


@pytest.fixture
def committed(tmp_path):
    path = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED_V2, path)
    return path


def _manifest(directory):
    return json.loads((directory / fx.MANIFEST).read_text())


def _problems(fresh_dir, committed_dir, manifest=None):
    """The closed comparator's problems, with the pin rewritten to the (mutated) committed manifest so only the rule under test can fail."""
    if manifest is not None:
        (committed_dir / fx.MANIFEST).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    pin = "sha256:" + hashlib.sha256((committed_dir / fx.MANIFEST).read_bytes()).hexdigest()
    return cdf.closed_differences(fresh_dir, committed_dir, fx.recorded_result_text_v2, pinned_manifest_sha256=pin)


def test_the_pinned_keys_are_the_six_terrains_that_gained_an_axis_after_the_gates_and_not_forest():
    registry = load_registry()
    assert cdf.AXES_DECLARED_AFTER_THE_GATES == frozenset(af.TERRAIN_VARIANT_AXES) and len(cdf.AXES_DECLARED_AFTER_THE_GATES) == 6
    assert "terrain.forest" not in cdf.AXES_DECLARED_AFTER_THE_GATES and registry.keys["terrain.forest"].detail is not None
    for key in cdf.AXES_DECLARED_AFTER_THE_GATES:
        assert registry.keys[key].detail is not None


def test_rule_an_axis_declared_after_a_gate_does_not_change_what_the_gate_shows(fresh, committed):
    fresh_rows = {row["visual_key"] for row in _manifest(fresh).get("details", [])}
    committed_rows = {row["visual_key"] for row in _manifest(committed).get("details", [])}
    added = fresh_rows - committed_rows
    assert added and added <= cdf.AXES_DECLARED_AFTER_THE_GATES  # a fresh export DOES carry axes the gate never showed (the premise of the rule)
    assert _problems(fresh, committed) == []  # and the closed gate still passes with its committed manifest untouched
    assert "sha256:" + hashlib.sha256((committed / fx.MANIFEST).read_bytes()).hexdigest() == af.CLOSED_DRAFT_SETS[SET_ID]["fixture_manifest_sha256"]  # no fixture byte changed


def test_the_unmutated_fixture_has_no_details_problem(fresh, committed):
    assert cdf.details_problems(_manifest(fresh), _manifest(committed)) == []


def _forest_row(manifest):
    return next(row for row in manifest["details"] if row["visual_key"] == "terrain.forest")


def test_mutant_a_changed_details_value_for_a_key_the_fixture_shows_with_detail_fails(fresh, committed):
    manifest = _manifest(committed)
    row = _forest_row(manifest)
    assert row["values"] == ["plain", "bush", "tree"]  # the mutant applies at the right site
    row["values"] = ["plain", "tree", "bush"]
    problems = _problems(fresh, committed, manifest)
    assert any("terrain.forest" in p and "differs from a fresh export" in p for p in problems), problems


def test_mutant_a_missing_row_for_a_key_the_fixture_shows_with_detail_fails(fresh, committed):
    manifest = _manifest(committed)
    before = len(manifest["details"])
    manifest["details"] = [row for row in manifest["details"] if row["visual_key"] != "terrain.forest"]
    assert len(manifest["details"]) == before - 1
    problems = _problems(fresh, committed, manifest)
    assert any("terrain.forest" in p for p in problems), problems  # the entry still carries a detail, so the row and the entry disagree


def test_mutant_b_an_added_row_whose_values_are_not_the_registrys_fails(fresh, committed):
    fresh_manifest = _manifest(fresh)
    row = next(r for r in fresh_manifest["details"] if r["visual_key"] == "terrain.swamp")
    assert row["values"] == list(af.TERRAIN_VARIANT_AXES["terrain.swamp"])  # the premise: a fresh export carries swamp's declared axis
    mutated_fresh = copy.deepcopy(fresh_manifest)
    next(r for r in mutated_fresh["details"] if r["visual_key"] == "terrain.swamp")["values"] = ["base", "reeds"]
    other = fresh.parent / "mutated"
    shutil.copytree(fresh, other)
    (other / fx.MANIFEST).write_text(json.dumps(mutated_fresh, sort_keys=True, separators=(",", ":")))
    problems = _problems(other, committed)
    assert any("terrain.swamp" in p and "not an axis declared after the gate" in p for p in problems), problems


def test_mutant_c_a_fixture_entry_that_gains_a_detail_fails(fresh, committed):
    manifest = _manifest(committed)
    entry = next(e for e in manifest["entries"] if e["visual_key"] == "terrain.swamp" and "detail" not in e)  # a reference the owner saw with no detail
    entry["detail"] = "base"
    problems = _problems(fresh, committed, manifest)
    assert any("terrain.swamp" in p and "disagree" in p for p in problems), problems


def test_mutant_c_a_fixture_entry_that_loses_its_detail_fails(fresh, committed):
    manifest = _manifest(committed)
    entry = next(e for e in manifest["entries"] if e["visual_key"] == "terrain.forest" and e.get("detail") is not None)
    del entry["detail"]
    problems = _problems(fresh, committed, manifest)
    assert any("terrain.forest" in p and "shows detail None" in p for p in problems), problems  # other forest entries still carry a detail, so only the per-entry check can see this


def test_mutant_e_a_row_allowed_for_a_key_not_in_the_pinned_list_fails(fresh, committed, monkeypatch):
    """The allowance is the pinned list, not 'any key whose fixture entries have no detail': take swamp out of the list and the same fresh row is refused."""
    monkeypatch.setattr(cdf, "AXES_DECLARED_AFTER_THE_GATES", cdf.AXES_DECLARED_AFTER_THE_GATES - {"terrain.swamp"})
    assert "terrain.swamp" not in cdf.AXES_DECLARED_AFTER_THE_GATES
    problems = _problems(fresh, committed)
    assert any("terrain.swamp" in p and "not an axis declared after the gate" in p for p in problems), problems


def test_mutant_d_a_derived_row_for_a_key_with_no_detail_entries_is_refused_by_the_stores_own_rule(tmp_path):
    out = tmp_path / "derived"
    derived_runtime.write(out, "pilot", "rc-0007")  # an OLD candidate derived with the NEWER registry
    manifest = json.loads((out / "runtime_manifest.json").read_text())
    rows = {row["visual_key"] for row in manifest["details"]}
    detailed = {e["visual_key"] for e in manifest["entries"] if e.get("detail") is not None}
    assert rows == detailed == {"terrain.forest", "border.edge", "border.inner_corner", "border.outer_corner"}  # exactly the keys with detail entries
    assert "terrain.swamp" not in rows and any(e["visual_key"] == "terrain.swamp" for e in manifest["entries"])  # swamp has an entry, no detail, so no row
    swamp = load_registry().keys["terrain.swamp"].detail
    mutated = copy.deepcopy(manifest)
    mutated["details"].append({"visual_key": "terrain.swamp", "values": list(swamp.values), "default": swamp.default})
    with pytest.raises(ContractError):
        parse_record(RuntimeManifest, json.dumps(mutated).encode())  # the mutant: the store's own "detail exactly when listed" rule refuses it
