---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-BATCH-OBS-TEST-COMBAT
phase: open
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, observability, testing, combat, systems]
---

# TCK-20260616-DOCS-BATCH-OBS-TEST-COMBAT

## Title
Readability Batch: docs/observability/, docs/testing/, docs/combat/, docs/systems/

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
Apply the approved readability rewrite rule (TCK-20260616-DOCS-READABILITY-PILOT) to the observability, testing, combat, and systems doc groups.

## Scope
`docs/observability/*.md` (11 files: simulation_mining, single_run_pipeline, multi_run_baseline, live_observatory, semantic_observability, production_platform, foundation, advanced_understanding, externalization_scale, simulation_mining_usage, agentic_lab), `docs/testing/*.md` (10 files), `docs/combat/*.md` (9 files), `docs/systems/*.md` (5 files: world_evolution_and_resilience, combat_and_progression, world, buildings_and_economy, ai_system).

Special attention: `docs/systems/world_evolution_and_resilience.md` §3.5 "The Legend's Legacy: Succession and Inheritance [PHASE 4]" — this is a section title with a bracketed phase tag; convert to a plain thematic title.

## Out of Scope
Everything else (separate batch tickets). Note `docs/systems/strategic_cognition.md` already done in the pilot — skip.

## Acceptance Criteria
- Zero numbered phase/milestone matches remain
- No broken incoming links

## Related Tickets
TCK-20260616-DOCS-READABILITY-EPIC (parent), TCK-20260616-DOCS-READABILITY-PILOT (style source)

## Implementation Notes
Judgment call beyond original ticket scope: triaged the full 34-file flagged set by frontmatter `status` before rewriting (same signal used in TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER/SPECS-PERF-PLANS). 21 of 34 files were already self-declared `status: historical` (all of `docs/observability/`'s phase-titled reports, 6 `docs/combat/` rulebooks/matrices, 6 `docs/testing/` coverage audits) — relocated these to `docs/archive/{observability,combat,testing}/` rather than rewriting in place, consistent with the established archival pattern. Only the 12 `status: active` files were rewritten in place.

Also distinguished bare (non-numbered) "phase"/"milestone" word usage during a second sweep, since the numbered-only regex missed some: kept all genuine kernel/pipeline architecture usage (`PACKETIZATION` phase, `resolution` phase, "6-phase deterministic loop", "17-phase" pipeline, "per-phase budget") and the RPG game-design term "Milestone Levels" (level thresholds 5/10/15/20/25/30 that trigger stat spikes — a gameplay vocabulary term, not implementation tracking). Stripped genuine dev-tracking instances: "Milestone-specific TDD tests", "(epic-18 Phase A/B/C)" tags.

One literal code-path reference was deliberately left untouched: `docs/testing/regression_policy.md`'s "(phase20–28, ...)" cites real test files (`tests/integration/observability/test_phase20_*.py` through `test_phase28_*.py`, confirmed via `find`) — renaming the doc text would misdescribe real file names.

Fixed 4 cross-references broken by the archival moves: `docs/combat/rollout_hardening_rulebook.md` (link to moved `arena_regression_test_matrix.md`), `docs/plans/missing-docs-contracts.md` and `docs/simulation/lab_contract.md` (inline-code path mentions of moved `agentic_lab.md`), `docs/engine/contracts/infrastructure_overview.md` (markdown links to moved `simulation_mining.md`/`simulation_mining_usage.md`).

## Test Summary
Grep sweep (`\bphase[ _-]?[0-9]+|\bmilestone[ _-]?[0-9]+`, case-insensitive) on all 12 rewritten active files: zero matches except the intentionally-preserved literal test-path citation. Cross-reference check (`grep -rl` for each moved filename, excluding `docs/archive/`) confirmed no remaining broken links after fixes. No internal relative links existed among the 21 archived files, so no internal link repair was needed for those.

## Files Changed
**Archived** (moved to `docs/archive/observability|combat|testing/`, content untouched): `advanced_understanding.md`, `agentic_lab.md`, `externalization_scale.md`, `foundation.md`, `live_observatory.md`, `multi_run_baseline.md`, `production_platform.md`, `semantic_observability.md`, `simulation_mining.md`, `simulation_mining_usage.md`, `single_run_pipeline.md` (observability); `arena_harness_rulebook.md`, `arena_regression_test_matrix.md`, `arena_scenario_matrix.md`, `combat_movement_rulebook.md`, `combat_movement_test_matrix.md`, `tactical_behavior_rulebook.md` (combat); `life_arc_campaign_coverage.md`, `optimization_scaling_coverage.md`, `party_social_cooperation_coverage.md`, `progression_reward_conversion_coverage.md`, `self_model_coverage.md`, `world_emergence_coverage.md` (testing).

**Rewritten in place**: `docs/combat/combat_movement_overhaul_spec.md`, `docs/combat/observability_rulebook.md`, `docs/combat/rollout_hardening_rulebook.md`, `docs/systems/ai_system.md`, `docs/systems/buildings_and_economy.md`, `docs/systems/combat_and_progression.md`, `docs/systems/world.md`, `docs/systems/world_evolution_and_resilience.md`, `docs/testing/content_migration_test_ownership.md`, `docs/testing/no_duplication_test_policy.md`, `docs/testing/v2_test_taxonomy.md`. (`docs/testing/regression_policy.md` had its one match deliberately left as-is.)

**Reference fixes**: `docs/plans/missing-docs-contracts.md`, `docs/simulation/lab_contract.md`, `docs/engine/contracts/infrastructure_overview.md`.

## Completion Summary
Batch complete. 21 self-declared-historical files archived, 12 active files rewritten per the approved rule, all cross-references fixed. Coordinator still needs to run `make docs-registry` and `make knowledge-index-update` once after all parallel batches finish (not run here per instruction, to avoid races with concurrent batches).
