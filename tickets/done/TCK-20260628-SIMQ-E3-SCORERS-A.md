---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E3-SCORERS-A
phase: done
date: 2026-06-28
tags: [simulation-quality, scoring, cognition, faction, economy, progression]
---

# TCK-20260628-SIMQ-E3-SCORERS-A

## Title
Simulation Quality Scoring — Scorers Batch A (Cognition, Faction, Economy, Progression)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement four pillar scorers: Cognition, Faction & Military, Economy, and Progression.
These four cover the Tier-1 RPG systems (resource ecology, adventure routing) and the
most commonly asked balance questions about factions and character growth.

## Scope
- `src/simulation_quality/scorers/cognition.py` — `CognitionScorer`
  All scoring rules from contract §5 COGNITION
  Scenarios covered: SQ-21 (primary), SQ-01/SQ-02 (secondary via goal-lock signals)
- `src/simulation_quality/scorers/faction.py` — `FactionScorer`
  All scoring rules from contract §5 FACTION & MILITARY
  Scenarios covered: SQ-05, SQ-06 (primary)
- `src/simulation_quality/scorers/economy.py` — `EconomyScorer`
  All scoring rules from contract §5 ECONOMY
  Scenarios covered: SQ-07, SQ-09 (primary), SQ-16 (secondary)
- `src/simulation_quality/scorers/progression.py` — `ProgressionScorer`
  All scoring rules from contract §5 PROGRESSION
  Scenarios covered: SQ-10, SQ-11 (primary), SQ-04 (secondary)

## Out of Scope
- Social, Information, World Dynamics, Narrative scorers (E4)

## Acceptance Criteria
- [ ] All four scorers cover every rule in their respective §5 table
- [ ] Each scorer declares its `EVENT_TYPES` class attribute for `SCORER_REGISTRY` registration
- [ ] No scorer imports from `src/engine/`, `src/domains/`, or `src/systems/`
- [ ] Time-gated rules use `context.current_tick` (e.g., economy zero-harvest penalty only after tick 100)
- [ ] `EconomyScorer` does NOT score ecology events (`ecology_cycle_completed`) — that is `WorldDynamicsScorer` (E4). Verify against SQ-07/SQ-08 in §6 conflict notes
- [ ] `CognitionScorer` does NOT score `paid_information_transaction` — that is `InformationScorer` (E4)
- [ ] `FactionScorer` does NOT score entity-level combat events — that is `CombatScorer` (E2)
- [ ] Unit tests: all rules (positive, negative, null, time-gated, tag, conflict scenarios)
- [ ] Scenario coverage test entries added for SQ-05, SQ-06, SQ-07, SQ-09, SQ-10, SQ-11, SQ-21

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Requires: TCK-20260628-SIMQ-E2-HUB-CORE
- Parallel: TCK-20260628-SIMQ-E4-SCORERS-B (no shared files)
- Next: TCK-20260628-SIMQ-E5-API (requires E3 + E4 both done)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 — COGNITION, FACTION, ECONOMY, PROGRESSION
- `docs/simulation_quality/quality_scoring_contract.md` §6 — SQ-05 to SQ-11, SQ-21 (conflict notes)
- `docs/simulation_quality/quality_scoring_contract.md` §7.2/7.3 — extensibility & conflict detection
- `docs/audits/D04_balance_tuning.md` §6.2 — known root causes for zero Economy score (reference for Economy scorer traceability path)

## Implementation Notes
**Economy scorer cross-check:** D04 §6.2 identifies three confirmed root causes of
zero economic output: `ENABLE_ADVENTURE_ROUTING` defaults to OFF, urban_political has
0 resource nodes, entity `navigation.region_id` is None. The Economy scorer's
`zero_harvest` tag and traceability path in §5 are specifically designed for these.
The scorer itself cannot detect these root causes (it only sees events), but the
traceability documentation in §5 must be accurate — verify it against D04 before
finalizing the scorer.

**Faction scorer:** PP-08 is a direct-call phase (not via `run_phase()`). Verify that
`faction_decision` and `faction_awareness` events are actually emitted to the event bus
from `FactionDecisionPhase.execute()` and `FactionAwarenessService` before registering
event_types. If these events are not currently emitted, the scorer must document this as
a prerequisite (event emission, not scoring logic, is the gap).

## Implementation Notes
Implemented CognitionScorer (belief updates, divergence detection, dormancy, omniscience collapse), FactionScorer (diplomacy, alliances, territory, faction extinction), EconomyScorer (all economy events; ecology_cycle_completed intentionally excluded per SQ-08 conflict note), ProgressionScorer (XP scaling, level milestones, all plateau types). All scorers follow no-numeric-literals rule.

## Test Summary
60 new tests passing. Tests cover all positive, negative, time-gated, null-return, and tag cases for all four scorers. Ecology exclusion test explicitly verifies event_type not in EconomyScorer.EVENT_TYPES.

## Files Changed
- `src/simulation_quality/scorers/cognition.py` (new)
- `src/simulation_quality/scorers/faction.py` (new)
- `src/simulation_quality/scorers/economy.py` (new)
- `src/simulation_quality/scorers/progression.py` (new)
- `tests/simulation_quality/test_cognition_scorer.py` (new)
- `tests/simulation_quality/test_faction_scorer.py` (new)
- `tests/simulation_quality/test_economy_scorer.py` (new)
- `tests/simulation_quality/test_progression_scorer.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-240 through INFRA-243)

## Completion Summary
Four pillar scorers implemented covering all §5 contract rules for COGNITION, FACTION, ECONOMY (ecology excluded per SQ-08), and PROGRESSION. All 60 tests pass. No imports from engine/domains/systems.
