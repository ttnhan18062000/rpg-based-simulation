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
    drift is visible in CI. `genetics_aptitude`'s own `gated_without_flag_context` is a known,
    understood low-confidence false positive: the real `ENABLE_REPRODUCTION_HUMANOID_PATH` flag
    check happens several call-frames up (`engine/world_dynamics.py`), not within the 5-line text
    window of the direct `GeneticsSystem` reference in `reproduction_humanoid.py` -- the check's
    own textual-proximity heuristic has a real, expected blind spot for flag checks made at a
    different layer than the call site. See stored_artifacts/TCK-20260916-MECHANISM-ORPHAN-STATE-
    BATCH-VERIFICATION/investigation.md for the full disposition of every finding in that batch.

    2026-09-19: `trauma` briefly carried a same-day, same-session `orphan_with_callers` finding
    after a real misattribution error (this entry was incorrectly bound to
    `RecoveryReadinessService`, an unrelated orphan class, instead of its own real implementation,
    `WoundService`, `src/engine/rpg_depth.py` -- see the mechanism's own `verified` block in
    `registries/mechanisms.yaml` for the full self-correction). Reverted the same day once the
    error was caught; `trauma` is correctly `done`/bound to `WoundService` again, which has real
    confirmed callers, so no finding fires for it here.

    2026-09-20 (TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION): a large binding
    batch (24 entity-layer mechanisms) surfaced 5 new findings, each independently re-checked
    directly against source rather than trusted from the tool's own report. (`breakthrough_bonuses`
    briefly also fired `orphan_with_callers` mid-batch when first bound as `orphan`; self-corrected
    to `partial` within the same batch once this exact tool caught it -- `orphan` specifically means
    zero real callers, and `BreakthroughService.apply_bonuses()` has one; see that entry's own
    verified note for the full self-correction. No finding fires for it here.)
    - `knowledge_model` (`gated_without_flag_context`, low): same shape as `genetics_aptitude`
      above -- the real `ENABLE_SELF_MODEL_COGNITION` check is at the call site
      (`engine/pipeline.py:192`), several frames from the direct
      `KnowledgeModelService.assimilate()` reference inside `self_model_phase.py`.
    - `attributes_biology`, `class_assignment`, `goal_hierarchy` (`state_with_zero_callers`, high
      confidence per the tool, false per direct re-check): all three are method-level bindings
      whose real callers are exclusively *within the same defining file* as the binding itself
      (`ApplyPath._compute_entity_changes` is invoked via a same-file callback registration
      consumed by `ApplyPlanBuilder.build_plan()`; `SocialDefaultsResolver.resolve_role_defaults()`
      is called only from two other sites inside `resolver.py` itself;
      `StrategicIntelligenceSystem`'s 5 goal_hierarchy methods are all called only from sibling
      methods on the same class within `intelligence.py` itself). `_real_callers()` deliberately
      excludes the defining file (to avoid a method counting itself/its own recursion as a caller,
      the correct general rule) -- a real, understood blind spot for a large multi-method
      orchestrator class whose own methods call each other internally, not evidence the bindings
      are wrong. Independently re-verified via direct grep for each case before concluding this.
    - `commitment_betrayal` (`orphan_with_callers`, high confidence per the tool, expected given
      this registry's own established `orphan` meaning): `BetrayalRecord` is type-referenced in
      `core/state.py`/`core/updates.py`/`core/builder.py` (which the tool counts as "callers") but
      never actually constructed anywhere (`BetrayalRecord(` grepped repo-wide, zero hits) --
      genuinely `orphan` (dead code, not a live producer), the tool just can't distinguish a type
      reference from a real instantiation. Same established shape as `status_effects`'s own prior
      `orphan` finding this same epic: present, referenced code whose actual claimed behavior never
      fires in real play. The checker's binary "any caller = not orphan" heuristic can't represent
      this nuance; not a registry error.

    2026-09-20 (TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION): the
    23-mechanism world/faction/region/group batch surfaced 4 more findings, 3 understood/false and
    1 that changed the registry (not a pin-only fix):
    - `opportunity_rumor_seeds` (`gated_without_flag_context`, low): same shape as
      `genetics_aptitude`/`knowledge_model` above -- `ENABLE_WORLD_EMERGENCE` is checked at the call
      site (`engine/pipeline.py:355`), not within 5 lines of the direct service references inside
      `world_emergence/phase.py`.
    - `campaigns` (`state_with_zero_callers`, high confidence per the tool, false per direct
      re-check): `CampaignOrchestrator`'s only real, non-docstring, non-test instantiation is in
      `tools/calibrate_simq.py` -- outside `_SRC_DIR` (`src/` only), which this checker's own
      `_real_source_files()` never scans. A real caller, invisible to this checker by design scope,
      not a registry error.
    - `chronicle` (`orphan_with_callers`, high confidence per the tool, false per direct re-check):
      the "real callers" are `src/domains/chronicle/__init__.py`'s own package re-export (11 `from
      ... import` lines, one per class) plus comments -- `_is_shim_file()`'s own `len(lines) > 4`
      threshold doesn't recognize a multi-symbol `__init__.py` re-export as a shim the way it
      recognizes the single-line shims elsewhere in this repo (`systems/quests.py` etc.), even
      though it is semantically identical (no real logic, only re-exporting). Direct re-check
      (`grep -rn "ChronicleCompiler(" src/` outside tests) still finds only a class-docstring usage
      example, corroborated by the already-filed
      `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION`. `orphan` stands.
    - `calamity_intensity` (no longer bound, not a checker false positive -- a real, registry-
      changing finding): this one was real. Attempted to bind
      `CalamityService.apply_calamity_consequences()` on the strength of its own pre-existing
      (2026-09-17) verified note's confident claim ("the sole real producer of
      region.calamity_intensity"); this checker immediately flagged zero real callers. Re-checked
      directly rather than trusted, and confirmed the checker was right: `apply_calamity_
      consequences()` has no real callers anywhere, not even the one already-called sibling method
      on its own class (`process_world_dynamics()`, which only *reads* `calamity_intensity`, never
      writes it). Reverted the binding; left unbound with the contradiction flagged on the entry
      itself for the roadmap session, since the mechanism's own 2026-09-17 `verified` block predates
      this batch and this batch's rule is not to silently overwrite an already-verified conclusion.
      This mechanism carries no finding here because it has no `implemented_by` to check.

    2026-09-20 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION): `perception`
    now fires `orphan_with_callers` (high confidence per the tool, expected and NOT a checker false
    positive here -- this is the exact one-level-deep blind spot the entry's own registry note
    names). The tool counts `src/domains/perception/phase.py` as a real caller of
    `PerceptionFilterService` because `phase.py` does contain a real call to `.filter()` -- but
    `phase.py`'s own `PerceptionUpdatePhase` class is itself never instantiated anywhere else in
    `src/`, confirmed both by direct grep and by a real differential runtime scenario
    (`tests/mechanic_scenarios/test_perception_pipeline_wiring.py`: zero real `.filter()` calls and
    an empty `perceived_entities` across 5 real ticks against a world with an adjacent, perceivable
    entity, plus a positive control proving the code itself works when called directly). Same
    "type/class reference counted as a caller without checking reachability" shape as
    `commitment_betrayal` above, one level removed -- there it was a type reference; here it's a
    real call inside a dead chain. `orphan` stands, now runtime-confirmed rather than asserted from
    a static read alone.

    2026-09-20 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION, batch 2):
    `temporal_pressure` now fires `gated_without_flag_context` (low confidence per the tool) after
    its own `state` correction `skeleton` -> `gated` -- same shape as `genetics_aptitude`/
    `knowledge_model`/`opportunity_rumor_seeds` below: the real `ENABLE_MEMORY_UPDATE` flag check is
    several frames away from `TemporalPressureService.calculate_urgencies()`'s own direct reference
    (it gates `MemoryUpdatePhase.apply()`, the containing phase, not `calculate_urgencies()`
    itself). A real differential scenario
    (`tests/mechanic_scenarios/test_temporal_pressure_gated_dormancy.py`) independently confirms the
    gating is real: flag ON computes urgency, flag OFF (the real default) does not.

    Update this test only alongside a real investigation of what changed, same discipline as every
    other pinned-count test in this repo."""
    import yaml
    with open(REPO_ROOT / "registries" / "mechanisms.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    report = build_report(data)
    finding_keys = {(f.mechanism_id, f.check) for f in report.findings}
    assert finding_keys == {
        ("genetics_aptitude", "gated_without_flag_context"),
        ("knowledge_model", "gated_without_flag_context"),
        ("opportunity_rumor_seeds", "gated_without_flag_context"),
        ("temporal_pressure", "gated_without_flag_context"),
        ("attributes_biology", "state_with_zero_callers"),
        ("class_assignment", "state_with_zero_callers"),
        ("campaigns", "state_with_zero_callers"),
        ("chronicle", "orphan_with_callers"),
        ("goal_hierarchy", "state_with_zero_callers"),
        ("commitment_betrayal", "orphan_with_callers"),
        ("perception", "orphan_with_callers"),
    }
