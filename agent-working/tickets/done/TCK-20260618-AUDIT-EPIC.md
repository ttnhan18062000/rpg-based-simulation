---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-EPIC
phase: done
date: 2026-06-18
tags: [audit, epic, planning, simulation-quality, codebase-health, developer-tooling]
---

# TCK-20260618-AUDIT-EPIC

## Title
Engine Audit — 18-Dimension Simulation & Codebase Audit

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
Comprehensive audit of the engine across 18 dimensions covering simulation quality,
codebase and architecture health, and developer tooling. Goal is to produce a
prioritized, factual picture of what the engine has, what it needs, and what it wants
— grounded in observed behavior and code reading, not assumption.

## Scope

- Define and maintain the 18-dimension audit framework (`docs/audits/audit_dimensions.md`)
- Produce a detail file for each dimension with findings, feature lists, and ratings
- Score each dimension on Impact (1–5) and Interest (1–5) for prioritization
- Audit dimensions in priority order (highest Impact + Interest first)
- Capture every gap, partial, and missing feature in a form that feeds planning

## Out of Scope

- Implementing fixes or new features discovered during the audit
- Creating implementation tickets (those belong to the relevant feature epics)
- Performance benchmarking beyond what supports the audit findings
- Auditing external dependencies or infrastructure outside the engine

## Acceptance Criteria

- [x] `docs/audits/audit_dimensions.md` is complete with all 18 dimensions, ratings, and method
- [x] All 18 detail files exist with findings, feature lists, and ratings
- [x] All `run-sim` dimensions have been run against actual simulation output, not code inference
- [x] D09 (System Wiring) verifies every `[E]` feature in D02 is live in the pipeline
- [x] Audit findings are reflected in `docs/plans/engine_future_epics_roadmap.md` where they update it
- [x] Epic ticket closed and moved to `tickets/done/`

## Child Tickets

| ID | Dimension | Priority | State | Child Ticket |
|---|---|---|---|---|
| D01 | RPG Feature Impact | 10 | `done` | — (captured in D01 detail file) |
| D02 | Foundation Feature Inventory | 9 | `done` | — (captured in D02 detail file) |
| D03 | Behavioral Emergence Quality | 10 | `done` | TCK-20260618-AUDIT-D03-BEHAVIOR |
| D04 | Balance & Tuning | 7 | `partial` | TCK-20260618-AUDIT-D04-BALANCE (blocked by D06 F1) |
| D05 | Entity Differentiation | 8 | `done` | TCK-20260619-AUDIT-D05-ENTITY-DIFF |
| D06 | Long-Run Simulation Health | 9 | `done` | TCK-20260619-AUDIT-D06-LONGRUN |
| D07 | Content Depth & Variety | 7 | `done` | TCK-20260618-AUDIT-D07-CONTENT |
| D08 | Multi-Scenario Consistency | 5 | `done` | TCK-20260619-AUDIT-D08-MULTI-SCENARIO |
| D09 | System Wiring & Integration | 9 | `done` | TCK-20260618-AUDIT-D09-WIRING |
| D10 | Test Coverage & Regression Risk | 7 | `done` | TCK-20260618-AUDIT-D10-TEST-COVERAGE |
| D11 | Dead Code & Orphaned Modules | 4 | `done` | TCK-20260618-AUDIT-D11-DEAD-CODE |
| D12 | Pattern Consistency | 6 | `done` | TCK-20260618-AUDIT-D12-PATTERNS |
| D13 | Type Safety & Validation Boundary | 5 | `done` | TCK-20260618-AUDIT-D13-TYPE-SAFETY |
| D14 | Coupling Depth | 7 | `done` | TCK-20260618-AUDIT-D14-COUPLING |
| D15 | Entity Decision Inspection Tooling | 9 | `done` | TCK-20260618-AUDIT-D15-DECISION-INSPECT |
| D16 | Scenario & Content Authoring DX | 7 | `done` | TCK-20260618-AUDIT-D16-AUTHORING-DX |
| D17 | Documentation Currency | 7 | `done` | TCK-20260618-AUDIT-D17-DOC-CURRENCY |
| D18 | CI / Release Pipeline Completeness | 5 | `done` | TCK-20260618-AUDIT-D18-CI-PIPELINE |

**Note on D04:** The balance & tuning audit is `partial` — combat and hunger balance were observed and documented, but economic/crafting balance measurement is blocked by D06 F1 (hunger urgency permanently outscores economic goals). D04 detail file exists at `docs/audits/D04_balance_tuning.md` with all observable findings. Full balance measurement requires the hunger satiation gap to be resolved in a future ticket.

## Related Tickets
- `docs/plans/engine_future_epics_roadmap.md` — updated with audit findings 2026-06-19
- `tickets/todos/TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING.md` — RC1 fix (created as output of D03)
- `tickets/todos/TCK-20260619-FIX-NEAR-SERVICE-REGION.md` — RC2 fix (created as output of D03)
- `tickets/todos/TCK-20260619-FIX-PERF-BUDGETS-RESET.md` — RC3 fix (created as output of D03)

## Related Docs
- `docs/audits/audit_dimensions.md` — master dimension index (primary artifact of this epic)
- `docs/audits/D01_rpg_feature_impact.md` — D01 detail file
- `docs/audits/D02_foundation_features.md` — D02 detail file
- `docs/audits/D03_behavioral_emergence.md` — D03 detail file
- `docs/audits/D04_balance_tuning.md` — D04 detail file (partial)
- `docs/audits/D05_entity_differentiation.md` — D05 detail file
- `docs/audits/D06_longrun_health.md` — D06 detail file
- `docs/audits/D07_content_depth.md` — D07 detail file
- `docs/audits/D08_multi_scenario.md` — D08 detail file
- `docs/audits/D09_system_wiring.md` — D09 detail file
- `docs/audits/D10_test_coverage.md` — D10 detail file
- `docs/audits/D11_dead_code.md` — D11 detail file
- `docs/audits/D12_pattern_consistency.md` — D12 detail file
- `docs/audits/D13_type_safety.md` — D13 detail file
- `docs/audits/D14_coupling_depth.md` — D14 detail file
- `docs/audits/D15_entity_decision_inspection.md` — D15 detail file
- `docs/audits/D16_scenario_authoring_dx.md` — D16 detail file
- `docs/audits/D17_documentation_currency.md` — D17 detail file
- `docs/audits/D18_ci_release_pipeline.md` — D18 detail file
- `docs/plans/engine_future_epics_roadmap.md` — updated with audit findings

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/plan.md`
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/investigation.md`
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/test_plan.md`

## Related Code Areas
None — this is an audit epic; no src/ changes.

## Assumptions / Open Questions

All open questions from scope have been resolved:
- D03/D06 confirmed the codebase runs cleanly (after RC1/RC2/RC3 fixes).
- D09 found all 61 `[E]` features in D02 are live — no orphaned `[E]` features.
- Interest ratings held throughout the audit — no project direction shift.

## Implementation Notes
See `stored_artifacts/TCK-20260618-AUDIT-EPIC/plan.md` for dimension sequencing rationale.

## Test Summary
N/A — audit epic produces documentation, not code.

## Files Changed

### Audit Dimension Index
- `docs/audits/audit_dimensions.md` — created; updated throughout the programme

### Detail Files (18 total; 17 `done`, 1 `partial`)
- `docs/audits/D01_rpg_feature_impact.md`
- `docs/audits/D02_foundation_features.md`
- `docs/audits/D03_behavioral_emergence.md`
- `docs/audits/D04_balance_tuning.md` *(partial — blocked by D06 F1)*
- `docs/audits/D05_entity_differentiation.md`
- `docs/audits/D06_longrun_health.md`
- `docs/audits/D07_content_depth.md`
- `docs/audits/D08_multi_scenario.md`
- `docs/audits/D09_system_wiring.md`
- `docs/audits/D10_test_coverage.md`
- `docs/audits/D11_dead_code.md`
- `docs/audits/D12_pattern_consistency.md`
- `docs/audits/D13_type_safety.md`
- `docs/audits/D14_coupling_depth.md`
- `docs/audits/D15_entity_decision_inspection.md`
- `docs/audits/D16_scenario_authoring_dx.md`
- `docs/audits/D17_documentation_currency.md`
- `docs/audits/D18_ci_release_pipeline.md`

### Roadmap Update
- `docs/plans/engine_future_epics_roadmap.md` — "Engine Audit Update 2026-06-19" section added

### Fix Tickets (created as audit output, not implemented here)
- `tickets/todos/TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING.md`
- `tickets/todos/TCK-20260619-FIX-NEAR-SERVICE-REGION.md`
- `tickets/todos/TCK-20260619-FIX-PERF-BUDGETS-RESET.md`
- `tickets/todos/SEQUENCE.md`

## Completion Summary

The 18-dimension audit programme ran from 2026-06-18 to 2026-06-19. All 18 dimensions have been investigated and documented. 17 of 18 dimensions are fully closed; D04 (Balance & Tuning) is `partial` due to a blocker (D06 F1) that requires a future fix before economic balance can be measured.

### Headline Findings by Group

**Group A — Simulation Quality:**
- **Three critical wiring bugs (RC1/RC2/RC3)** caused total behavioral stasis before any audit data could be collected. These were diagnosed in D03, documented as P0/P1 fix tickets, and fixed by a separate agent session before D05/D06/D08 ran.
- **After RC fixes**, behavioral activity restored from tick ~201. The simulation runs, entities pursue goals, and events fire — but at a reduced quality level due to two remaining systemic blockers.
- **Hunger satiation gap (D06 F1):** Hunger urgency permanently outscores all economic goals because no food-kind resource node exists in any world. Entities cycle hunger projects indefinitely; economic/crafting systems are never reached.
- **Personality initialization absent (D05 F1):** `WorldCompiler` never seeds `PersonalityComponent` — all traits are 0.0 for every entity. The OCEAN scoring formula is correct but all inputs are identical; all entities are behaviorally indistinguishable.
- **world differentiation confirmed (D08):** `urban_political` (7 buildings) is the only world producing non-survival behavioral output (`town_return`, `harvesting`). `dungeon_crawl` (1 building, 32 entities) produces 94% attrition. `wilderness_survival` (0 buildings) collapses to near-extinction.
- **D04 partial:** Combat balance observable (attrition range 5–75% across worlds, driven by world content not engine constants). Economic/crafting balance blocked until hunger satiation is fixed.

**Group B — Codebase / Architecture:**
- **Architecture is clean.** Only 1 prohibited cross-domain import found (D14); 61 `[E]` features all live in the pipeline (D09); domain phase pattern applied uniformly (D12).
- **Three high-risk items:** (1) `core/state.py` constructs `MovementPlanCache` — upward lazy import through the most-imported file (D14). (2) Teardown contamination in tests leaks across unrelated cognition tests (D10). (3) Bare `random.` calls outside `rng.py` silently break replay determinism (D10 F3, P0 engine contract violation).
- **9 orphaned src/ directories** contain 36 files of unreachable V1 code (D11). `src/ai/` carries parity compliance IDs requiring ledger audit before deletion.

**Group C — Developer Tooling:**
- **Decision inspection answers "what", not "why"** (D15). Goal scoring computed in `execute_brain()` and discarded at tick boundary; route trace not stored. Promoting existing data to a queryable API closes the gap without new simulation logic.
- **Zero CI test automation** (D18). Only `deploy-docs.yml` exists — tests, architecture guards, and certification harness all require local invocation. Fix is a single `test.yml`.
- **Documentation has two P0 stale docs** (D17): `authoritative_pipeline.md` (17-phase table vs. 30+ current phases) and `kernel.md` (two conflicting phase tables). Biological thresholds in mechanics/01 are numerically wrong.
- **No type checker configured** (D13). 455 `Any` usages and 186 missing return annotations produce zero automated enforcement.

### Top-Priority Follow-Up Tickets (immediate, pre-epic)

| Priority | Item | Detail file |
|---|---|---|
| P0 | Add `test.yml` CI workflow | D18 |
| P0 | Fix bare `random.` calls (determinism breach) | D10 F3 |
| P0 | Fix `authoritative_pipeline.md` (17→30 phases) | D17 |
| P0 | Fix hunger satiation gap (food resource node or urgency calibration) | D06 F1 |
| P1 | Seed `PersonalityComponent` in `WorldCompiler` | D05 F1 |
| P1 | Add HERO role entities to sandbox_world | D05 F3 |
| P1 | Delete 9 orphaned src/ directories (after `src/ai/` ledger audit) | D11 |
| P1 | Fix `core/state.py` upward `MovementPlanCache` import | D14 |

### Next Epics (from roadmap, now confirmed by audit)

The audit confirms the roadmap's recommended sequencing anchors:
1. **Resource Ecology Regeneration** (C) — now also prerequisite for economic balance (D04) and hunger satiation (D06)
2. **Personality → Long-Run Behavior Calibration** (B) — confirmed not calibration but initialization; quick fix unblocks D05
3. **Persistent Campaign Runtime** (D) — unblocks Social Memory; largest "lab → product" gap
4. **Faction & Diplomacy System** (A) — largest single missing system; deliberate scheduling required
