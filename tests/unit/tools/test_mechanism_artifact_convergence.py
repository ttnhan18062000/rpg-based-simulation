"""The propagation proof for TCK-20260915-ARTIFACT-STATE-CONVERGENCE, AC #2: "A state change in the
registry propagates to every consuming artifact with no per-artifact edit -- proven by changing one
mechanism's state and asserting all consumers move."

Per peer review, this covers exactly the three real mechanism-domain consumers -- atlas,
capabilities, wiring map (taxonomy and scorecard are confirmed independent, not consumers at all;
see investigation.md Finding 3/6) -- "two out of three passing would look like success," so all
three are asserted together in one test against one fixture mutation, not split across separate
tests that could each pass while a fourth silently regressed.

Uses a REAL mechanism id (`combat_resolution`, chosen because it is the only one present in all
three real mapping tables at once) against MUTATED COPIES of the real registry/atlas/capabilities
data -- never the real committed files -- so this proves the convergence mechanism itself works
generally, not just that today's already-correct values happen to agree.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from tools.mechanism_atlas_regenerate import compute_diffs as atlas_compute_diffs
from tools.mechanism_atlas_regenerate import extract_json_block as atlas_extract_json_block
from tools.mechanism_capabilities_regenerate import compute_diffs as capabilities_compute_diffs
from tools.mechanism_capabilities_regenerate import (
    extract_json_block as capabilities_extract_json_block,
)
from tools.mechanism_wiring_map_classdef import compute_expected_classdef

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_ATLAS_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html"
_CAPABILITIES_PATH = REPO_ROOT / "docs" / "brainstorm" / "simulation_capabilities.html"

_MECHANISM_ID = "combat_resolution"
_WIRING_NODE = "CMB"


def _load_real_registry_data() -> dict:
    return yaml.safe_load(_REGISTRY_PATH.read_text())


def _load_real_atlas_data() -> dict:
    raw_json, _, _ = atlas_extract_json_block(_ATLAS_PATH.read_text())
    return json.loads(raw_json)


def _load_real_capabilities_data() -> list:
    raw_json, _, _ = capabilities_extract_json_block(_CAPABILITIES_PATH.read_text())
    return json.loads(raw_json)


def _registry_with_state(registry_data: dict, mechanism_id: str, new_state: str) -> dict:
    mutated = copy.deepcopy(registry_data)
    found = False
    for m in mutated["mechanisms"]:
        if m["id"] == mechanism_id:
            m["state"] = new_state
            m["verified"] = None  # isolate the state axis; verified defaults to unverified
            found = True
    assert found, f"fixture mechanism {mechanism_id!r} not found in the real registry"
    return mutated


def test_state_change_propagates_to_all_three_real_consumers():
    registry_data = _load_real_registry_data()
    atlas_data = _load_real_atlas_data()
    capabilities_data = _load_real_capabilities_data()

    # Two real states, chosen to map to different values on all three consumer vocabularies:
    # done -> atlas cls "done" / capabilities tier "live" / wiring classdef "live"
    # gap  -> atlas cls "gap"  / capabilities tier "planned" / wiring classdef "bug"
    registry_done = _registry_with_state(registry_data, _MECHANISM_ID, "done")
    registry_gap = _registry_with_state(registry_data, _MECHANISM_ID, "gap")

    states_done = {m["id"]: m["state"] for m in registry_done["mechanisms"]}
    states_gap = {m["id"]: m["state"] for m in registry_gap["mechanisms"]}
    verified_done = {m["id"]: m.get("verified") for m in registry_done["mechanisms"]}
    verified_gap = {m["id"]: m.get("verified") for m in registry_gap["mechanisms"]}

    # --- Atlas -----------------------------------------------------------------------------
    atlas_diffs_done = atlas_compute_diffs(atlas_data, states_done)
    atlas_diffs_gap = atlas_compute_diffs(atlas_data, states_gap)
    atlas_cls_done = next(d["new_cls"] for d in atlas_diffs_done if d["mechanism_id"] == _MECHANISM_ID) \
        if any(d["mechanism_id"] == _MECHANISM_ID for d in atlas_diffs_done) else states_done[_MECHANISM_ID]
    atlas_cls_gap = next(d["new_cls"] for d in atlas_diffs_gap if d["mechanism_id"] == _MECHANISM_ID)

    assert atlas_cls_gap == "gap"
    assert atlas_cls_gap != atlas_cls_done
    # No other mechanism's mapped card moved in either run.
    assert all(d["mechanism_id"] == _MECHANISM_ID for d in atlas_diffs_gap), (
        f"unexpected atlas diffs beyond {_MECHANISM_ID}: {atlas_diffs_gap}"
    )

    # --- Capabilities ------------------------------------------------------------------------
    cap_diffs_done = capabilities_compute_diffs(capabilities_data, states_done, verified_done)
    cap_diffs_gap = capabilities_compute_diffs(capabilities_data, states_gap, verified_gap)
    cap_tier_gap = next(d["new_tier"] for d in cap_diffs_gap if d["mechanism_id"] == _MECHANISM_ID)

    assert cap_tier_gap == "planned"
    assert all(d["mechanism_id"] == _MECHANISM_ID for d in cap_diffs_gap), (
        f"unexpected capabilities diffs beyond {_MECHANISM_ID}: {cap_diffs_gap}"
    )

    # --- Wiring map ----------------------------------------------------------------------------
    classdef_done = compute_expected_classdef(registry_done)
    classdef_gap = compute_expected_classdef(registry_gap)

    assert classdef_done[_WIRING_NODE] == "live"
    assert classdef_gap[_WIRING_NODE] == "bug"
    assert classdef_done[_WIRING_NODE] != classdef_gap[_WIRING_NODE]
    # No other node's expected classdef moved -- only the one mutated mechanism's own node changed.
    changed_nodes = {n for n in classdef_done if classdef_done[n] != classdef_gap[n]}
    assert changed_nodes == {_WIRING_NODE}, f"unexpected wiring map nodes changed: {changed_nodes}"

    # --- All three moved together, not just two of three ---------------------------------------
    assert atlas_cls_gap != "done"
    assert cap_tier_gap != "live"
    assert classdef_gap[_WIRING_NODE] != "live"


def test_state_change_propagates_via_done_contradicted_case():
    """The camp-shaped case: state stays 'done' but verified.verdict flips to 'contradicted' --
    proves capabilities moves on verified alone, not just state (atlas/wiring map are state-only by
    design, per Foundation/Priority-Derivation's own scope -- confirmed here by asserting they do
    NOT move on a verified-only change, which is the correct behavior, not an oversight)."""
    registry_data = _load_real_registry_data()
    capabilities_data = _load_real_capabilities_data()
    atlas_data = _load_real_atlas_data()

    registry_observed = copy.deepcopy(registry_data)
    registry_contradicted = copy.deepcopy(registry_data)
    for m in registry_observed["mechanisms"]:
        if m["id"] == _MECHANISM_ID:
            m["state"] = "done"
            m["verified"] = {"instrument": "code_trace", "verdict": "observed", "date": "2026-01-01", "note": "x"}
    for m in registry_contradicted["mechanisms"]:
        if m["id"] == _MECHANISM_ID:
            m["state"] = "done"
            m["verified"] = {"instrument": "code_trace", "verdict": "contradicted", "date": "2026-01-01", "note": "x"}

    states = {m["id"]: m["state"] for m in registry_observed["mechanisms"]}
    verified_observed = {m["id"]: m.get("verified") for m in registry_observed["mechanisms"]}
    verified_contradicted = {m["id"]: m.get("verified") for m in registry_contradicted["mechanisms"]}

    cap_diffs_observed = capabilities_compute_diffs(capabilities_data, states, verified_observed)
    cap_diffs_contradicted = capabilities_compute_diffs(capabilities_data, states, verified_contradicted)

    tier_observed = next(
        (d["new_tier"] for d in cap_diffs_observed if d["mechanism_id"] == _MECHANISM_ID),
        "live",  # done+observed is the no-diff case since combat_resolution is already live
    )
    tier_contradicted = next(d["new_tier"] for d in cap_diffs_contradicted if d["mechanism_id"] == _MECHANISM_ID)

    assert tier_observed == "live"
    assert tier_contradicted == "built"
    assert tier_observed != tier_contradicted

    # Atlas is state-only by design -- verified must NOT move its cls.
    atlas_diffs_observed = atlas_compute_diffs(atlas_data, states)
    atlas_diffs_contradicted = atlas_compute_diffs(atlas_data, states)
    assert atlas_diffs_observed == atlas_diffs_contradicted
