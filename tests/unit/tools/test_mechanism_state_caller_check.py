"""Tests for tools/mechanism_registry/mechanism_state_caller_check.py.

TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION. Claims-as-tests phase 1, scoped as
state-versus-caller-count mismatch detection (not presence/absence) per peer review: every one of
the four real registry state errors found by hand this epic was a wrong state, never a missing
entry, and `orphan` vs `gated` are opposite conclusions a reader could act on backwards.

The load-bearing tests here are the ones built from this tool's OWN validation history: its first
real run against the committed registry produced 4 raw findings, and investigating each one found
two real bugs in the detector itself (comment-text counted as a caller; function-only modules
produced a false "zero callers" reading) before either was fixed. Both bugs are pinned here as
regressions so they can't silently return.
"""
from __future__ import annotations

from pathlib import Path

from tools.mechanism_registry.mechanism_state_caller_check import (
    _is_shim_file,
    _real_callers,
    _symbol_names,
    build_report,
    check_mechanism,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _mechanism(mid, state, implemented_by):
    return {"id": mid, "state": state, "implemented_by": implemented_by}


def test_is_shim_file_identifies_a_real_backward_compat_shim():
    shim = REPO_ROOT / "src" / "systems" / "chest_system.py"
    real_module = REPO_ROOT / "src" / "systems" / "economy_systems" / "chests.py"
    assert _is_shim_file(shim) is True
    assert _is_shim_file(real_module) is False


def test_symbol_names_finds_both_classes_and_module_level_functions():
    """[Load-bearing, real bug] diplomacy's own implementing module
    (src/domains/faction/diplomatic_state_machine.py) is pure free functions -- no class at all.
    A class-only extractor finds nothing to check callers for and silently reports zero callers,
    producing a false 'state_with_zero_callers' finding on a mechanism that is genuinely live."""
    path = REPO_ROOT / "src" / "domains" / "faction" / "diplomatic_state_machine.py"
    symbols = _symbol_names(path)
    assert "compute_transitions" in symbols


def test_real_callers_excludes_comment_only_mentions():
    """[Load-bearing, real bug] strategic_redirection's registered `orphan` state has exactly one
    repo-wide mention of its class name outside its own file, and that mention is a code comment
    ("Hoisted logic from StrategicRedirectionSystem") in intelligence.py. A naive whole-file
    substring search counts that as a real caller and produces a false 'orphan_with_callers'
    finding on a mechanism that really is orphaned."""
    defining_file = REPO_ROOT / "src" / "systems" / "strategic_systems" / "redirection.py"
    hits = _real_callers("StrategicRedirectionSystem", defining_file, [
        REPO_ROOT / "src" / "systems" / "strategic_systems" / "intelligence.py",
    ])
    assert hits == []


def test_real_callers_finds_genuine_code_references():
    """Positive control: CooperationPhase is a real, live, non-comment reference in
    engine/pipeline.py (TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS's own citation)."""
    defining_file = REPO_ROOT / "src" / "domains" / "cooperation" / "phase.py"
    hits = _real_callers("CooperationPhase", defining_file, [REPO_ROOT / "src" / "engine" / "pipeline.py"])
    assert hits == [REPO_ROOT / "src" / "engine" / "pipeline.py"]


def test_check_mechanism_flags_causal_spatial_memory_historical_defect():
    """[Load-bearing] The historical regression: reconstructs causal_spatial_memory's ORIGINAL
    buggy registry entry (state: orphan, before TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING
    corrected it to gated) and confirms this detector would have caught it. MemoryUpdatePhase.apply
    is called live from engine/pipeline.py -- a real, non-comment, non-shim caller -- so `orphan`
    (zero callers) was factually wrong the whole time this defect existed undetected."""
    mechanism = _mechanism(
        "causal_spatial_memory_historical_fixture", "orphan",
        ["src/domains/memory/phase.py"],
    )
    findings = check_mechanism(mechanism, list((REPO_ROOT / "src").rglob("*.py")))
    assert any(f.check == "orphan_with_callers" for f in findings), (
        "detector failed to catch the exact historical causal_spatial_memory defect"
    )


def test_check_mechanism_does_not_flag_the_corrected_gated_state():
    """True-negative companion to the above: the CURRENT, corrected registry entry (gated, with
    real ENABLE_MEMORY_UPDATE flag context near its caller) must not be flagged by any check."""
    mechanism = _mechanism("causal_spatial_memory", "gated", ["src/domains/memory/phase.py"])
    findings = check_mechanism(mechanism, list((REPO_ROOT / "src").rglob("*.py")))
    assert findings == []


def test_check_mechanism_flags_done_state_with_zero_callers():
    # check_mechanism resolves implemented_by relative to REPO_ROOT, so the fixture must live at
    # a real repo-relative path rather than an arbitrary tmp_path.
    real_fixture = REPO_ROOT / "tests" / "unit" / "tools" / "_synthetic_zero_caller_fixture.py"
    real_fixture.write_text("class NobodyCallsThisClass:\n    pass\n", encoding="utf-8")
    try:
        mechanism = _mechanism(
            "synthetic_zero_caller", "done",
            ["tests/unit/tools/_synthetic_zero_caller_fixture.py"],
        )
        findings = check_mechanism(mechanism, list((REPO_ROOT / "src").rglob("*.py")) + [real_fixture])
        assert any(f.check == "state_with_zero_callers" for f in findings)
    finally:
        real_fixture.unlink()


def test_check_mechanism_skips_mechanisms_without_implemented_by():
    mechanism = _mechanism("no_binding_yet", "orphan", [])
    assert check_mechanism(mechanism, []) == []


def test_build_report_counts_checked_and_unchecked(registry_data=None):
    import yaml
    with open(REPO_ROOT / "registries" / "mechanisms.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    report = build_report(data)
    total = len(data["mechanisms"])
    assert report.checked + report.unchecked == total
    assert report.checked == sum(1 for m in data["mechanisms"] if m.get("implemented_by"))


def test_makefile_wires_mechanism_state_caller_check_target():
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "mechanism-state-caller-check:" in makefile_text
    assert "tools/mechanism_registry/mechanism_state_caller_check.py" in makefile_text


def test_real_registry_findings_pinned():
    """[Load-bearing] Pins today's known finding set against the real, committed registry so any
    drift is visible in CI. The one remaining finding, `genetics_aptitude`'s own
    `gated_without_flag_context`, is a known, understood low-confidence false positive: the real
    `ENABLE_REPRODUCTION_HUMANOID_PATH` flag check happens several call-frames up
    (`engine/world_dynamics.py`), not within the 5-line text window of the direct
    `GeneticsSystem` reference in `reproduction_humanoid.py` -- the check's own textual-proximity
    heuristic has a real, expected blind spot for flag checks made at a different layer than the
    call site. See stored_artifacts/TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION/
    investigation.md for the full disposition of every finding in this batch. Update this test
    only alongside a real investigation of what changed, same discipline as every other
    pinned-count test in this repo."""
    import yaml
    with open(REPO_ROOT / "registries" / "mechanisms.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    report = build_report(data)
    finding_keys = {(f.mechanism_id, f.check) for f in report.findings}
    assert finding_keys == {
        ("genetics_aptitude", "gated_without_flag_context"),
    }
