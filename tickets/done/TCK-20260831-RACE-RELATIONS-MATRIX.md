---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-RACE-RELATIONS-MATRIX
phase: done
date: 2026-08-31
tags: [faction, content, combat]
---

# TCK-20260831-RACE-RELATIONS-MATRIX

## Title
Author race-relations hostility matrix and wire it into legality/tactical scoring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Race-relations hostility matrix — the highest content risk in the whole roadmap. Investigation found the gap is worse than "lookup table missing": RelationContext.target_race is set at 2 real live call sites (attack-legality and tactical scoring) but read by ZERO consuming logic in RelationProjectionService.project_relation() — both the content table and the consuming logic must be built. This ticket must not be started (not just not merged) until the metamorphic-lab pilot ticket is done, per both the concern text and an independently corroborating decision record.

## Scope
- Do not start this ticket until TCK-20260831-METAMORPHIC-LAB-PILOT has landed and passed — hard blocking dependency, stated explicitly here.
- Load a new race_relations content family via a new ContentFamilySpec + Pydantic model (extra="forbid") in src/content/repository.py, matching faction_relationships.yaml's convention — using the corrected schema shape, a flat List[RaceRelationRecord] (source_race/target_race/relationship_model/axes qualitative labels), not the roadmap concern text's stale Dict[Tuple[str,str], float].
- Wire RelationContext.target_race to actually be consumed by RelationProjectionService.project_relation(), resolving a race_relations entry and factoring axes.hostility into the returned label.
- Author a disclosed defensible subset of the 156 directed race pairs (13x12, excluding self-pairs) with explicit rationale for any pair left at a neutral default, following TCK-20260627-P2D-FACTION-RELS's coverage precedent — not all 156 uniformly.
- **Updated 2026-09-01 (user-approved during Plan phase, per a confirmed structural gap):** `MutationLabOrchestrator.run_mutation_lab()`/`MutationEngine.apply_mutations` structurally cannot target content-catalog files — `target.split(".")[0]` must resolve against `WorldSpec`/`ScenarioSpec` model fields, and `race_relations.yaml` lives entirely outside both. AC #3 is satisfied instead via a hand-orchestrated validation that bypasses `MutationEngine`'s pipeline: physically swap the on-disk `race_relations.yaml` wolf↔human entries between a no-entry baseline and a `hostility: "high"` variant, run a real corpus world (`unit_faction_tension`) via `ScenarioLabOrchestrator.run_lab()` directly for each variant, compute real `combat_engagement_rate` from each run's `simulation_events.jsonl`, and call the real `MetamorphicRuleEngine.evaluate_rules()` directly against the resulting `variant_metrics`. This does not extend `MutationEngine` — it stays self-contained to this ticket's own validation script/test, not shared lab infrastructure.
- Update all 3 touched parity ledgers: docs/parity_ledger/combat_movement.yaml, docs/parity_ledger/social_narrative.yaml, docs/parity_ledger/strategic_cognition.yaml.

## Out of Scope
- Any change to faction_relationships.yaml's own content or FactionState relations — race relations is a separate content family, reusing only its schema convention.
- Starting implementation on this ticket before TCK-20260831-METAMORPHIC-LAB-PILOT is done — hard blocking dependency.

## Acceptance Criteria
- [x] race_relations content family loads via a new ContentFamilySpec + Pydantic model (extra="forbid") in src/content/repository.py, matching faction_relationships.yaml's convention.
- [x] RelationContext.target_race is actually consumed by RelationProjectionService.project_relation() to resolve a race_relations entry and factor axes.hostility into the returned label — verified by a test showing two race pairs with different authored hostility produce different projected labels.
- [x] A real, hand-orchestrated metamorphic validation (per the updated Scope note above — direct `MetamorphicRuleEngine.evaluate_rules()` call against real two-variant combat-engagement-rate data, not `MutationLabOrchestrator.run_mutation_lab()`) confirms increasing hostility does not decrease combat-engagement rate for the wolf/human pair, on the real `unit_faction_tension` corpus world.
- [x] Authored pair coverage is a disclosed defensible subset with explicit rationale for any neutral-default pair, not all 156 uniformly.
- [x] This ticket must not be started until TCK-20260831-METAMORPHIC-LAB-PILOT is done, stated explicitly in Scope/Assumptions.

## Related Tickets
- TCK-20260627-P2D-FACTION-RELS
- TCK-20260523-METAMORPHIC-VALIDATION
- TCK-20260612-LAB-CONTRACT
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
- TCK-20260831-METAMORPHIC-LAB-PILOT (hard prerequisite — must land first)

## Related Docs
- docs/content/content_semantics_contract.md (RelationProjectionService, WORLD-SEM-003/004 — new race-hostility escalation paragraph)
- docs/mechanics/content_usage_matrix.md (new social/race_relations row)
- docs/mechanics/02_combat_laws.md (Friendly Fire law section — new "Race-hostility escalation preserves the law" bullet, added by Document-Update after confirming this doc covers the exact `is_hostile_compat` function this ticket extends)

## Related Stored Artifacts
None.

## Related Code Areas
- src/content_semantics/relation.py
- src/engine/legality.py
- src/engine/tactical.py
- src/lab/metamorphic.py
- src/lab/mutation_orchestrator.py
- src/content/repository.py

## Assumptions / Open Questions
- This ticket is HARD BLOCKED from starting (not just merging) until TCK-20260831-METAMORPHIC-LAB-PILOT is done — per both the concern text and TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY's independently-corroborating decision record.
- Coverage must be a disclosed defensible subset of the 156 pairs, not uniform, following the faction-relations precedent's own rationale approach.
- This idea touches 3 parity ledgers — the widest single-idea cross-ledger footprint alongside idea 39.

## Implementation Notes

Implemented all 14 steps of `staging_artifacts/TCK-20260831-RACE-RELATIONS-MATRIX/plan.md`
exactly, with 4 minor deviations documented in that file's own new "Deviations" section (all
discovered live during implementation/test execution; none change the plan's design intent):

1. **Schema (Step 1)**: `RaceRelationRecord(CatalogBaseDefinition)` added to `src/content/schema.py`
   directly after `FactionRelationshipDefinition`, mirroring its shape exactly
   (`source_race`, `target_race`, `relationship_model`, `axes: Dict[str,str]`), inheriting
   `extra="forbid"` from `CatalogBaseDefinition`.
2. **Catalog registration (Step 2)**: `src/content/repository.py` — imported `RaceRelationRecord`,
   added `self.race_relations: Dict[str, RaceRelationRecord] = {}`, registered
   `ContentFamilySpec("social.race_relations", "social/race_relations.yaml", RaceRelationRecord,
   "race_relations")` in `CANONICAL_FAMILIES`, and added `get_race_relationship()` for API
   consistency with `get_faction_relationship()`.
3. **Matrix registration (Step 3)**: `src/content/matrix.py` — added `"social/race_relations"` to
   `CONTENT_USAGE_MATRIX`. Deviated from the plan's literal `validator_coverage=None`/
   `resolver_component=None` to the string `"None"` (see plan's Deviations section — required by
   `test_content_usage_matrix.py`'s non-null constraint on those two fields, matching the
   established convention used by every other "no validator/resolver" entry in the file).
4. **Docs row (Step 4)**: `docs/mechanics/content_usage_matrix.md` — added the `social/race_relations`
   row, placed alphabetically (matching the table's real sort order and
   `generate_matrix_report()`'s own `sorted()` iteration) rather than the plan's literal
   "after faction_relationships" instruction.
5. **`RelationContext.source_race` (Step 5)** and **race-hostility escalation (Step 6)**:
   `src/content_semantics/relation.py` — added `source_race: Optional[str] = None` to
   `RelationContext`, and a new "3.5 Race-hostility escalation" block in `project_relation()`,
   inserted after perspective/relationship-axis label resolution and before the legacy fallback.
   Fail-closed ladder guard implemented exactly as specified:
   `_RACE_LABEL_LADDER_RANK = {None: 0, "neutral": 0, "threat": 1, "intruder": 1, "enemy": 2}`,
   gated on `label in _RACE_LABEL_LADDER_RANK` (never a `.get(label, 0)` default), plus
   `source_faction_id != target_faction_id` (Friendly Fire guard) and both `context.source_race`/
   `context.target_race` being set. Only ever assigns `label = "enemy"` or `label = "threat"`
   (upgrade-only, no downgrade branch exists).
6. **Legality wiring (Step 7)**: `src/engine/legality.py` — `RelationContext(...)` in
   `verify_attack_legality` now also passes `source_race=get_race_id_str(attacker)`.
7. **Tactical wiring (Step 8)**: `src/engine/tactical.py` — `RelationContext(...)` in
   `evaluate_entity_intent`'s hostile-scan loop now also passes `source_race=get_race_id_str(entity)`.
   `target_score()`'s existing 6-element sort tuple (`tactical.py`) was not touched — confirmed
   unmodified and confirmed passing via `tests/unit/combat/test_capability_driven_targeting.py`.
8. **`RegionThreatClassifier` (Step 9)**: no code change, confirmed dead code (zero live callers),
   per plan.
9. **Content (Step 10)**: authored `data/content/social/race_relations.yaml` — 24 directed entries
   (12 undirected pairs, bidirectional) covering hero-race-vs-monster-race and predator/prey pairs
   across the 12 populated races (all races in `living/races.yaml` except `slime`, which has zero
   `entity_archetypes.yaml` entries). Disclosed ~18% coverage (12/66 populated undirected pairs),
   with the gap rationale recorded in the file's own header comment.
10. **Coverage guard (Step 11)**: `tests/unit/content/test_race_relations_coverage.py` — mirrors
    `test_faction_relationships_coverage.py`'s `POPULATED_FACTIONS` pattern.
11. **AC #3 hand-orchestrated validation (Step 12)**:
    `tests/integration/lab/test_race_relations_metamorphic_validation.py` — physically swaps
    `data/content/social/race_relations.yaml`'s wolf<->human entries between a no-entry baseline
    and a `hostility: "high"` variant, runs the real `unit_faction_tension` corpus world (3 seeds,
    200 ticks each) via `ScenarioLabOrchestrator.run_lab()` directly for each variant, computes
    real `combat_engagement_rate` from each run's `simulation_events.jsonl`'s
    `combat_engagement_started` events, and calls `MetamorphicRuleEngine.evaluate_rules()`
    directly. Result: **PASSED** (baseline_value≈0.0217, compared_value≈0.0317 — a genuine,
    non-degenerate increase, not a 0/0 or equal/equal hollow result). Does not touch
    `MutationEngine`/`MutationLabOrchestrator`. Needed `@pytest.mark.resource_budget_large`
    (not anticipated by the plan — see Deviations) since the real ~69s two-variant run exceeds
    `tests/conftest.py`'s default 60s per-test SIGALRM budget. Cleanup extended one level beyond
    the plan's four named directories to also remove the `scenario_index.json`/
    `experiment_index.json`/`lab_runs_index.json` index files `ScenarioRepository`/
    `ExperimentRepository`/`LabRunRepository` write at the `data/scenarios/`/`data/experiments/`/
    `data/lab_runs/` parent level (also see Deviations) — confirmed via a clean `git status`
    after two full test runs.
12. **Parity ledger (Step 13)**: `COMB-317` (`combat_movement.yaml`, P0), `STRAT-263`
    (`strategic_cognition.yaml`, P1), `SOC-257` (`social_narrative.yaml`, P1) — all written via
    `tools/parity_ledger_writer.py` (schema-validating, not raw YAML edit), confirmed the writer's
    `_ID_PATTERN = ^[A-Z]+-[0-9]{3}$` accepts single-segment IDs like these fine (the
    `WORLD-DEMO-*` regex bug only affects multi-segment IDs). `python3 tools/parity_index.py build`
    run afterward as the separate, retro-metric-visible rebuild call.
13. **Docs (Step 14)**: `docs/content/content_semantics_contract.md` — added `source_race` to the
    `RelationContext fields` list and one sentence describing the new race-hostility resolution
    step, in the `RelationProjectionService` section (`WORLD-SEM-003`/`WORLD-SEM-004`).
    `make knowledge-index-update` run afterward (2 changed doc files picked up, incremental).

Separately: `graphify update .` was run per CLAUDE.md convention but declined to write
(`new graph has 34645 nodes but existing graph.json has 34656 — refusing to overwrite`), a
stale/concurrent-session graph-state mismatch unrelated to this ticket's own correctness; not
forced.

## Test Summary

All new tests pass; full regression sweep across every touched subsystem passes unmodified.

- New tests (19 fast + 1 slow), all passing:
  - `tests/unit/content/test_race_relations_catalog.py` (4 tests) — AC #1.
  - `tests/unit/content/test_race_relations_coverage.py` (4 tests) — AC #4.
  - `tests/unit/content_semantics/test_relation_race_projection.py` (8 tests) — AC #2, upgrade-only
    guard, same-faction guard, and `test_race_relations_never_overrides_ally_label` /
    `test_race_relations_never_overrides_ally_label_dwarf_variant` (the ally-inversion regression
    guard, using the real `hero_guild_perspective` / `forest_wardens` (elf) and
    `dwarven_mine_clan` (dwarf) ally pairings).
  - `tests/unit/combat/test_race_relations_legality_wiring.py` (2 tests) — Step 7 wiring.
  - `tests/unit/combat/test_race_relations_tactical_wiring.py` (2 tests) — Step 8 wiring.
  - `tests/integration/lab/test_race_relations_metamorphic_validation.py` (1 slow test,
    `@pytest.mark.resource_budget_large`) — AC #3, run twice locally, both **PASSED**
    (baseline≈0.0217, high_hostility≈0.0317; second run confirmed reproducibility and clean
    teardown via `git status`).
- Explicitly requested regression checks, all passing unmodified:
  - `tests/unit/combat/test_capability_driven_targeting.py` — 7/7 passed, confirming
    `target_score()`'s 6-element sort tuple is genuinely untouched.
  - `tests/unit/content/test_faction_relationships_coverage.py`,
    `tests/unit/content/test_content_usage_matrix.py`,
    `tests/unit/engine/test_combat_relation_projection.py`,
    `tests/unit/quest/test_quest_relation_projection.py`,
    `tests/unit/social/test_relationships.py` — all passing unmodified.
  - `tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_index.py`,
    `tests/tools/test_parity_index_baseline.py` — all passing (56/56), confirming the 3 new
    parity ledger entries validate and don't drift the baseline metrics.
- Full scoped regression sweep:
  `pytest tests/unit/content/ tests/unit/content_semantics/ tests/unit/engine/ tests/unit/combat/
  tests/unit/quest/test_quest_relation_projection.py tests/unit/social/test_relationships.py
  tests/unit/lab/ tests/integration/combat/ tests/integration/lab/
  tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_writer.py -m "not slow"`
  → **754 passed, 1 skipped, 4 deselected**.

## Files Changed

- `src/content/schema.py` — `RaceRelationRecord` schema.
- `src/content/repository.py` — content family registration, `get_race_relationship()`.
- `src/content/matrix.py` — `CONTENT_USAGE_MATRIX` entry.
- `src/content_semantics/relation.py` — `RelationContext.source_race`, race-hostility escalation
  block in `project_relation()`.
- `src/engine/legality.py` — `RelationContext(source_race=...)` wiring.
- `src/engine/tactical.py` — `RelationContext(source_race=...)` wiring.
- `data/content/social/race_relations.yaml` — new content file (24 directed entries).
- `docs/mechanics/content_usage_matrix.md` — new table row.
- `docs/content/content_semantics_contract.md` — `RelationProjectionService` section updated.
- `docs/mechanics/02_combat_laws.md` — new "Race-hostility escalation preserves the law" bullet under
  the Friendly Fire section, added by Document-Update after confirming this doc covers the exact
  `is_hostile_compat` function this ticket extends but was not updated by the original Implement pass.
- `docs/parity_ledger/combat_movement.yaml` — new `COMB-317` entry.
- `docs/parity_ledger/strategic_cognition.yaml` — new `STRAT-263` entry.
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-257` entry.
- `tests/unit/content/test_race_relations_catalog.py` — new.
- `tests/unit/content/test_race_relations_coverage.py` — new.
- `tests/unit/content_semantics/test_relation_race_projection.py` — new.
- `tests/unit/combat/test_race_relations_legality_wiring.py` — new.
- `tests/unit/combat/test_race_relations_tactical_wiring.py` — new.
- `tests/integration/lab/test_race_relations_metamorphic_validation.py` — new.
- `staging_artifacts/TCK-20260831-RACE-RELATIONS-MATRIX/plan.md` — appended "Deviations" section
  (rewritten this run's Implement phase; `investigation.md`/`test_plan.md` were already present
  from the prior Investigate/Plan phases and not modified further in this run).

## Completion Summary

Implemented the race-relations hostility matrix end-to-end per the fully-approved 14-step plan:
a new `race_relations` content family (schema + catalog + matrix registration), a fail-closed
upgrade-only race-hostility escalation step in `RelationProjectionService.project_relation()`
(gated on same-faction and on an explicit ladder-membership guard that structurally cannot touch
off-ladder labels like `"ally"`), live wiring at both real call sites
(`LegalityServiceV2.verify_attack_legality`, `TacticalDecisionSystem.evaluate_entity_intent`),
24 authored directed content entries (12 undirected pairs, ~18% of the 66 populated-race-pair
basis, disclosed gap), a hand-orchestrated AC #3 metamorphic validation that bypasses
`MutationEngine` entirely and confirms (`PASSED`, real non-degenerate metric delta) that
increasing wolf/human race hostility does not decrease combat-engagement rate on the real
`unit_faction_tension` corpus world, and 3 new parity ledger entries. All 5 acceptance criteria
are satisfied; the full regression sweep (754 tests across every touched subsystem, plus the new
tests) passes with no unmodified-test regressions. Four minor, non-substantive deviations from the
plan's literal text were needed and are documented in `staging_artifacts/.../plan.md`'s new
Deviations section.
