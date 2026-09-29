"""Tests for tools/mechanism_registry/mechanism_wiring_map_classdef.py -- derives the wiring map's Entity Operating
Loop diagram's classDef state colouring from the real mechanism registry.

TCK-20260915-MECHANISM-PRIORITY-DERIVATION Scope item 3 (the real part, per peer review: only the
classDef state colouring derives from the registry, not the diagram's own topology).
"""
from __future__ import annotations

from pathlib import Path

from tools.mechanism_registry.mechanism_wiring_map_classdef import (
    OPERATING_LOOP_NODE_TO_MECHANISM_ID,
    STATE_TO_CLASSDEF,
    apply_classdef_fix,
    compute_expected_classdef,
    find_drift,
    render,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_WIRING_MAP_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html"
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"


def _fake_registry(states: dict) -> dict:
    return {"mechanisms": [{"id": mid, "state": state} for mid, state in states.items()]}


def _full_coverage_fixture(overrides: dict) -> tuple:
    """Builds a (registry_yaml_text, wiring_map_text) pair covering EVERY real node in
    OPERATING_LOOP_NODE_TO_MECHANISM_ID -- find_drift()/render() iterate that full real mapping
    regardless of what a minimal fixture registry defines, so a partial fixture reports spurious
    drift (and a naive render() call crashes trying to apply a fix for a node whose bracket text
    was never provided) for every node the caller didn't think to include. Every node defaults to
    state "done" (-> classdef "live") with a matching inline `:::live` override, i.e. genuinely no
    drift, except `overrides` (node -> (registry_state, wiring_map_line)), which sets that node's
    real state and its own wiring map source line."""
    import yaml as _yaml

    registry_entries = []
    text_lines = []
    for node, mech_id in OPERATING_LOOP_NODE_TO_MECHANISM_ID.items():
        if node in overrides:
            state, line = overrides[node]
            registry_entries.append({"id": mech_id, "state": state})
            text_lines.append(line)
        else:
            registry_entries.append({"id": mech_id, "state": "done"})
            text_lines.append(f'{node}["{node} label"]:::live')
    registry_yaml = _yaml.safe_dump({"mechanisms": registry_entries})
    return registry_yaml, "\n".join(text_lines) + "\n"


def test_compute_expected_classdef_maps_states_correctly():
    registry = _fake_registry({
        "combat_resolution": "done",
        "self_model": "gated",
        "conversation": "gap",
        "causal_spatial_memory": "orphan",
    })
    expected = compute_expected_classdef(registry)
    assert expected["CMB"] == "live"    # combat_resolution -> done -> live
    assert expected["SELF"] == "gated"  # self_model -> gated -> gated
    assert expected["CNV"] == "bug"     # conversation -> gap -> bug
    assert expected["MEM"] == "bug"     # causal_spatial_memory -> orphan -> bug


def test_find_drift_detects_a_real_mismatch():
    # Fixture wiring map text: SELF has no inline class and isn't in the "live" list either
    # (simulating a node the diagram simply never colored), while the registry says it's gated.
    registry = _fake_registry({"self_model": "gated"})
    text = 'SELF["Self-Model"]\nclass PER live\n'
    drift = find_drift(registry, text)
    assert "SELF" in drift
    assert drift["SELF"]["expected"] == "gated"


def test_find_drift_reports_nothing_when_diagram_agrees_with_registry():
    registry = _fake_registry({"self_model": "gated"})
    text = 'SELF["Self-Model"]:::gated\n'
    drift = find_drift(registry, text)
    assert "SELF" not in drift


def test_dec_has_no_registry_mapping():
    # Decide Route has no corresponding registry mechanism id -- deliberately excluded, not
    # silently guessed.
    assert "DEC" not in OPERATING_LOOP_NODE_TO_MECHANISM_ID


# ---------------------------------------------------------------------------
# TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP -- write mode
# ---------------------------------------------------------------------------


def test_apply_classdef_fix_inserts_inline_override_when_node_never_colored():
    text = 'SELF["Self-Model"]\nclass PER live\n'
    fixed = apply_classdef_fix(text, "SELF", "gated")
    assert 'SELF["Self-Model"]:::gated\n' in fixed
    assert "class PER live" in fixed  # untouched -- SELF was never a member of it


def test_apply_classdef_fix_replaces_existing_inline_override():
    text = 'SELF["Self-Model"]:::gated\n'
    fixed = apply_classdef_fix(text, "SELF", "bug")
    assert fixed == 'SELF["Self-Model"]:::bug\n'


def test_apply_classdef_fix_removes_node_from_class_live_line_and_adds_inline_override():
    text = 'TRM["Trauma"]\nclass BEL,TRM,EMO live\n'
    fixed = apply_classdef_fix(text, "TRM", "bug")
    assert 'TRM["Trauma"]:::bug' in fixed
    assert "class BEL,EMO live" in fixed
    # not left in the class-line AND inline-overridden at once (mermaid would apply the class-line
    # assignment last, silently shadowing the inline override)
    assert "class BEL,TRM,EMO live" not in fixed


def test_apply_classdef_fix_drops_class_live_line_entirely_when_it_becomes_empty():
    text = 'SELF["Self-Model"]\nclass SELF live\n'
    fixed = apply_classdef_fix(text, "SELF", "gated")
    assert "class SELF live" not in fixed
    assert "class  live" not in fixed  # no dangling empty-list line either
    assert 'SELF["Self-Model"]:::gated\n' in fixed


def test_apply_classdef_fix_leaves_other_nodes_and_lines_byte_identical():
    text = 'PER["Perceive"]:::bug\nSELF["Self-Model"]\nclass PER,SELF live\n'
    fixed = apply_classdef_fix(text, "SELF", "gated")
    assert 'PER["Perceive"]:::bug' in fixed  # untouched
    assert 'SELF["Self-Model"]:::gated' in fixed
    assert "class PER live" in fixed


def test_render_default_write_mode_fixes_real_drift_in_a_tmp_copy(tmp_path):
    """AC1/AC2: running with no flags writes the file when drift exists -- a real state
    correction needs zero manual Edit calls. Fails on the pre-fix code's own render() (which
    doesn't exist pre-fix) -- this test IS the new capability, not a regression re-check of an
    existing one."""
    registry_yaml, wiring_map_text = _full_coverage_fixture(
        {"TRM": ("gap", 'TRM["Trauma"]\nclass BEL,TRM,EMO live')}
    )
    wiring_map = tmp_path / "wiring_map.html"
    wiring_map.write_text(wiring_map_text, encoding="utf-8")
    registry = tmp_path / "mechanisms.yaml"
    registry.write_text(registry_yaml, encoding="utf-8")

    exit_code = render(check=False, wiring_map_path=wiring_map, registry_path=registry)
    assert exit_code == 0
    fixed_text = wiring_map.read_text(encoding="utf-8")
    assert 'TRM["Trauma"]:::bug' in fixed_text
    assert "class BEL,EMO live" in fixed_text
    assert "TRM,EMO live" not in fixed_text  # TRM genuinely removed, not left behind too


def test_render_check_mode_reports_drift_and_writes_nothing(tmp_path):
    """AC3: --check mode's existing report-only/exit-1-on-drift behavior is preserved."""
    registry_yaml, wiring_map_text = _full_coverage_fixture(
        {"TRM": ("gap", 'TRM["Trauma"]\nclass BEL,TRM,EMO live')}
    )
    wiring_map = tmp_path / "wiring_map.html"
    wiring_map.write_text(wiring_map_text, encoding="utf-8")
    registry = tmp_path / "mechanisms.yaml"
    registry.write_text(registry_yaml, encoding="utf-8")

    exit_code = render(check=True, wiring_map_path=wiring_map, registry_path=registry)
    assert exit_code == 1
    assert wiring_map.read_text(encoding="utf-8") == wiring_map_text  # nothing written


def test_render_no_drift_writes_nothing_and_exits_zero(tmp_path):
    registry_yaml, wiring_map_text = _full_coverage_fixture({})
    wiring_map = tmp_path / "wiring_map.html"
    wiring_map.write_text(wiring_map_text, encoding="utf-8")
    registry = tmp_path / "mechanisms.yaml"
    registry.write_text(registry_yaml, encoding="utf-8")

    exit_code = render(check=False, wiring_map_path=wiring_map, registry_path=registry)
    assert exit_code == 0
    assert wiring_map.read_text(encoding="utf-8") == wiring_map_text


def test_all_state_classes_have_a_classdef_mapping():
    from tools.mechanism_registry import VALID_STATES
    for state in VALID_STATES:
        assert state in STATE_TO_CLASSDEF, f"no classDef mapping for state '{state}'"


def test_real_wiring_map_has_no_drift_against_the_real_registry():
    # The load-bearing regression test: the real committed file must stay in sync with the real
    # registry going forward, not just at the moment of the one-time fix. Re-derives on every run.
    import yaml
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    text = _WIRING_MAP_PATH.read_text(encoding="utf-8")
    drift = find_drift(registry, text)
    assert drift == {}, (
        f"Entity Operating Loop diagram has drifted from the registry: {drift}. "
        f"Run `python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py` for a readable report."
    )


def test_every_mapped_mechanism_id_exists_in_the_real_registry():
    import yaml
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    real_ids = {m["id"] for m in registry["mechanisms"]}
    for node, mech_id in OPERATING_LOOP_NODE_TO_MECHANISM_ID.items():
        assert mech_id in real_ids, f"node '{node}' maps to unknown mechanism id '{mech_id}'"
