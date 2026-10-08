"""Tests for tools/mechanism_registry/mechanism_registry_completeness_check.py.

TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING. This tool is the recurring, standing version of
the manual completeness pass (TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS) that found 11
real, unregistered mechanisms. It reads the registry's own `implemented_by` field (structured),
never regex-searches prose -- an earlier draft did, and produced 47 false "unmapped" results on
its first real run, because the original 75 mechanisms have zero source-path citations anywhere in
mechanisms.yaml (their evidence cites atlas cards / wiring-map nodes only).

The load-bearing test here is `test_real_registry_enumeration_and_binding_counts_pinned`: it pins
today's known enumeration count, bound/excluded/unbound sets so that a new file appearing under
src/domains/ or src/systems/ -- or an implemented_by binding disappearing -- fails CI, forcing a
human decision (bind it, exclude it with a reason, or register a new mechanism) instead of a
silent skip. Mirrors tests/unit/tools/test_mechanism_atlas_regenerate.py's own
test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms convention.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tools.mechanism_registry.mechanism_registry_completeness_check import (
    EXCLUSIONS,
    WIDER_EXCLUSIONS,
    WIDER_PENDING,
    build_report,
    enumerate_targets,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"


def _real_registry_data() -> dict:
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_enumerate_targets_resolves_shims_not_top_level_filenames():
    """[Load-bearing] domains/systems targets must come from real subpackage files, never from a
    top-level src/systems/*.py shim's own bare filename -- checking `chest_system` (the shim) would
    be checking the wrong identity entirely."""
    targets = enumerate_targets()
    ids = {t.id for t in targets}
    assert "systems/economy_systems/chests" in ids
    assert "systems/chest_system" not in ids  # the shim itself is never a target


def test_exclusions_all_point_to_real_paths():
    """Every EXCLUSIONS key must correspond to a real enumerated target -- an exclusion for a
    target that no longer exists (renamed/removed directory) should be caught, not silently kept
    around forever."""
    targets = {t.id for t in enumerate_targets()}
    for excluded_id in EXCLUSIONS:
        assert excluded_id in targets, (
            f"EXCLUSIONS references {excluded_id!r}, which is no longer a real enumerated target"
        )


def test_exclusions_each_have_a_real_reason():
    """Per peer review: 'the checker needs a recorded-exclusions list with a reason per entry, not
    a silent skip.'"""
    for excluded_id, reason in EXCLUSIONS.items():
        assert isinstance(reason, str) and len(reason) > 20, (
            f"EXCLUSIONS[{excluded_id!r}] must have a real, non-trivial reason"
        )


def test_build_report_bound_targets_cite_a_real_mechanism_id(registry_data=None):
    data = _real_registry_data()
    report = build_report(data)
    real_ids = {m["id"] for m in data["mechanisms"]}
    for target_id, mech_id in report.bound.items():
        assert mech_id in real_ids, f"{target_id!r} bound to unknown mechanism id {mech_id!r}"


def test_build_report_never_double_counts_a_target():
    data = _real_registry_data()
    report = build_report(data)
    bound_ids = set(report.bound.keys())
    excluded_ids = set(report.excluded.keys())
    unbound_ids = set(report.unbound)
    assert not (bound_ids & excluded_ids)
    assert not (bound_ids & unbound_ids)
    assert not (excluded_ids & unbound_ids)
    assert len(bound_ids) + len(excluded_ids) + len(unbound_ids) == report.total_targets


def test_mechanisms_with_binding_matches_real_implemented_by_count():
    data = _real_registry_data()
    report = build_report(data)
    expected = sum(1 for m in data["mechanisms"] if m.get("implemented_by"))
    assert report.mechanisms_with_binding == expected


def test_real_registry_enumeration_and_binding_counts_pinned():
    """[Load-bearing] Pins today's known state so any drift -- a new domain/systems file, a
    removed implemented_by binding -- is visible in CI rather than silently absorbed. Update this
    test's expected numbers only alongside a real investigation of what changed, the same
    discipline test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms already uses.

    2026-09-19 (TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION, combat-first batch):
    `combat_engagement` bound to `src/domains/combat_engagement/service.py::CombatEngagementDecisionService`,
    moving `domains/combat_engagement` from unbound to bound (24 -> 25, 37 -> 36). `total_targets`
    unchanged at 64 -- the batch's other 4 bindings (combat_resolution/tactical_decision/movement/
    status_effects) all resolve to `src/engine/`/`src/core/` targets, outside this checker's own
    `src/domains/`/`src/systems/` scope entirely (same divergence the ticket's own Request Summary
    already documents for `declared_cognition_schema`/`committed_intentions` -> `core/cognition.py`),
    so they don't move this metric even though they do move `mechanisms_with_binding`.

    2026-09-20 (TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION, 24-mechanism entity-
    layer batch): `bound` 25 -> 29, `unbound` 36 -> 32. New `src/domains/`/`src/systems/` targets
    entering `bound` from this batch's new class-level bindings: `domains/perception` (`perception`),
    `systems/lifecycle_systems/lifecycle` (`aging_death`), `systems/strategic_systems/belief`
    (`belief_cycle`), `systems/strategic_systems/intelligence` (`goal_hierarchy`/
    `strategic_intelligence_core`, both method-level bindings on the same file),
    `systems/world_systems/quests` (`quest_generation_sourcing`) -- 5 newly-bound mechanisms' targets
    map to only 4 new distinct target keys since two mechanisms share the `intelligence` target.
    Most of this batch's other ~15 new bindings resolve to `src/engine/`/`src/core/`/`src/content/`/
    `src/progression/`/`src/cognition/` targets, outside this checker's own narrower scope, same
    divergence as every prior batch -- `mechanisms_with_binding` (55) moved by more than `bound`
    did, for the same reason.

    2026-09-20 (TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION,
    23-mechanism world/faction/region/group batch): `bound` 29 -> 33, `unbound` 32 -> 28. New
    targets: `domains/campaigns` (`campaigns`/`cross_episode_grief_nemesis` share it),
    `domains/chronicle` (`chronicle`), `domains/world_emergence` (`opportunity_rumor_seeds`),
    `systems/social_systems/reputation` (`reputation`). `calamity_intensity`'s attempted binding was
    reverted after this checker's own `state_with_zero_callers` finding held up under direct
    re-check (a real finding, not a false positive -- see
    `test_mechanism_state_caller_check.py::test_real_registry_findings_pinned`'s own note), so it
    contributes no target here. `mechanisms_with_binding` (76) again moved by more than `bound` did,
    same divergence as every prior batch.

    2026-09-30 (TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION): `bound` 33 -> 36,
    `unbound` 28 -> 25. New targets: `domains/information` (`information_trust_deception` bound to
    `SourceTrustUpdateService`), `systems/social_systems/memory` (`social_memory`),
    `systems/social_systems/relationships` (`affection_relationship_bonds`).

    2026-10-05 (TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES):
    `total_targets` 64 -> 65 and `unbound` 25 -> 26. The new target is
    `systems/strategic_systems/entity_target_objective` (a pure predicate module with no class, shared by
    `intelligence.py` and `work_queue.py`). It is a lifecycle rule of the existing `goal_hierarchy` /
    `strategic_intelligence_core` mechanisms, not a mechanism of its own, so it was first left unbound rather than
    given a registry entry (registry ownership is `rpg-feature-planning`'s).

    2026-10-06 (TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION, at
    the planner's request): `bound` 36 -> 37 and `unbound` 26 -> 25, `total_targets` unchanged at 65. The module
    is now cited under `goal_hierarchy`'s `implemented_by` (`entity_target_outcome`,
    `close_entity_target_project`), directly after `evaluate_strategic_intent`, whose docstring names it. The
    counts were taken by running the check, not by subtracting one.

    2026-10-07 (row 7 (b) pass, rpg-feature-planning): `bound` 37 -> 53, `excluded` 3 -> 4, `unbound` 25 -> 8.
    16 modules bound by real call sites (not name matches or comments), one helper excluded
    (`strategic_systems/town_targeting`). The 8 left are `domains/motivation` (Child B) and seven modules with no
    caller in `src/`, filed for deletion as
    TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE. Taken by running the
    check."""
    data = _real_registry_data()
    report = build_report(data)
    assert report.total_targets == 65
    assert len(report.bound) == 53
    assert len(report.excluded) == 4
    assert len(report.unbound) == 8


# --- state: gap is not a coverage hole (TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION) ---


def test_gap_mechanisms_are_reported_separately_and_never_counted_as_unbound():
    data = _real_registry_data()
    report = build_report(data)
    gap_ids = sorted(m["id"] for m in data["mechanisms"] if m.get("state") == "gap")
    assert report.gap_mechanisms == gap_ids
    assert not set(report.gap_mechanisms) & set(report.unbound_real_state)
    assert set(report.unbound_real_state) == {
        m["id"] for m in data["mechanisms"] if m.get("state") != "gap" and not m.get("implemented_by")
    }


def test_real_registry_has_no_non_gap_mechanism_without_implemented_by():
    """[Load-bearing] After the residue resolution every mechanism with a real state has a code
    binding; a new non-gap mechanism registered without one shows up here."""
    assert build_report(_real_registry_data()).unbound_real_state == []


def test_gap_rule_on_a_synthetic_registry():
    data = {"mechanisms": [
        {"id": "g", "state": "gap"},
        {"id": "done_bound", "state": "done", "implemented_by": ["src/engine/evolution.py::EvolutionSystem"]},
        {"id": "done_unbound", "state": "done"},
    ]}
    report = build_report(data)
    assert report.gap_mechanisms == ["g"]
    assert report.unbound_real_state == ["done_unbound"]


# --- wider-scope tier (TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP) ---


def test_wider_scope_every_wired_candidate_has_a_recorded_disposition():
    """[Load-bearing] A new wired, unbound, mechanism-shaped class outside domains/systems fails
    here until it is bound, excluded with a reason, or recorded as pending an identity decision."""
    report = build_report(_real_registry_data())
    assert report.wider_unresolved == []


def test_wider_scope_numbers_pinned():
    wider = build_report(_real_registry_data()).wider
    # 296 + src/worldassembly/resolve_io.py + src/systems/strategic_systems/entity_target_objective.py (two new modules)
    # 298 -> 299 on 2026-10-05: +src/core/violent_cause.py (rule ENV-07's one set of violent death causes;
    # constants and two predicates, no class, so it adds no unbound candidate).
    # 299 -> 301 on 2026-10-05: +src/worldassembly/region_precedence.py (LOC-08, bound under world_composition_assembly)
    # and +src/core/region_resolution.py (the one position-to-region lookup rule).
    # 301 -> 302 on 2026-10-07: +src/engine/tactical_threat.py (AGENCY-07's present-threat gate, bound under
    # `tactical_decision`; two public functions, no class, so it adds no unbound file and no unbound candidate).
    # 302 -> 305 on 2026-10-07: +src/engine/biological_needs.py (need_rates, bound under `attributes_biology`),
    # +src/engine/service_reach.py (a lookup helper, unbound) and +src/engine/need_paths.py (advisory report, unbound);
    # all three are functions only, so they add no unbound mechanism-shaped class.
    # 305 -> 309 on 2026-10-07 (SURV-07): +src/engine/need_pull.py (the pull curve), +src/ai/goals/present_threat.py and
    # +src/ai/goals/scorers_support.py (the present-threat gate and its hostile lookup) and +src/engine/tactical_rest.py
    # (rest in place); all four are functions only, so they add no unbound mechanism-shaped class.
    # 309 -> 310 on 2026-10-07 (KNOW-04, rebased after SURV-07): +src/cognition/common_knowledge.py (seeding and the combat-belief
    # lookup; functions only, bound under `knowledge_model`, so it adds no unbound file or mechanism-shaped class).
    # 310 -> 311 on 2026-10-08 (layer-order fix): +src/content/common_knowledge_seed.py (KNOW-04's seeding, moved out of
    # src/cognition/common_knowledge.py so the compiler and spawner need not import cognition; bound under `knowledge_model`).
    # 311 -> 312 on 2026-10-08 (CONFLICT-04): +src/engine/tactical_hold.py (the held swing and the stalemate-break emission;
    # functions only, bound under `tactical_decision`, so it adds no unbound file or mechanism-shaped class).
    # 312 -> 313 on 2026-10-08 (movement-layer rule): +src/engine/hostility.py (the shared perceived-hostile test; functions only,
    # bound under `tactical_decision`, so it adds no unbound file or mechanism-shaped class).
    assert wider["scope_files"] == 313
    # 233 -> 227 on 2026-10-05: the world-building split names six more files (worldmodules/normalizer,
    # worldassembly/resolve_io, worldbuilding/repository and validator, worldgeneration/generator and scorer).
    # Then +1 for the unbound entity_target_objective.py module (TCK-20261002-COMBAT-OBJECTIVE-TARGETS-...).
    # 228 -> 226 on 2026-10-07 (row 7 (b) pass): src/quests/generator.py (QuestGenerator, bound under `guilds`) and
    # src/engine/pipeline_phases/clan_lifecycle.py (ClanLifecyclePhase, bound under `clan`) are now cited.
    # 226 -> 228 on 2026-10-07 (biology child): src/engine/service_reach.py and src/engine/need_paths.py are unbound helpers
    # (a lookup and an advisory report, no mechanism of their own); biological_needs.py is bound under `attributes_biology`.
    # 228 -> 232 on 2026-10-07 (SURV-07): the four new modules above are unbound helpers (pure functions, no mechanism of their own).
    # KNOW-04 (2026-10-07): src/cognition/common_knowledge.py is bound under `knowledge_model`, so unbound_files stays 232.
    # CONFLICT-04: tactical_hold.py is bound under `tactical_decision`, so unbound_files stays 232.
    assert wider["unbound_files"] == 232
    # 73 -> 72 on 2026-10-07 (row 7 (b) pass): src/quests/generator.py::QuestGenerator is now bound under `guilds`.
    assert wider["candidates"] == 72  # unbound mechanism-shaped classes, wired or not
    assert len(wider["wired"]) == 21  # ... of which referenced from another top-level package
    assert len(WIDER_EXCLUSIONS) == 18 and len(WIDER_PENDING) == 3


def test_wider_exclusions_and_pending_all_point_to_real_wired_candidates():
    report = build_report(_real_registry_data())
    wired = {c.id for c in report.wider["wired"]}
    for cid in list(WIDER_EXCLUSIONS) + list(WIDER_PENDING):
        assert cid in wired, f"{cid!r} is recorded but is no longer a wired, unbound candidate"
    assert not set(WIDER_EXCLUSIONS) & set(WIDER_PENDING)


def test_wider_exclusions_and_pending_each_have_a_real_reason():
    for cid, reason in {**WIDER_EXCLUSIONS, **WIDER_PENDING}.items():
        assert isinstance(reason, str) and len(reason) > 30, cid
