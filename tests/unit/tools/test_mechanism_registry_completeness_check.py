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
    same divergence as every prior batch."""
    data = _real_registry_data()
    report = build_report(data)
    assert report.total_targets == 64
    assert len(report.bound) == 33
    assert len(report.excluded) == 3
    assert len(report.unbound) == 28
