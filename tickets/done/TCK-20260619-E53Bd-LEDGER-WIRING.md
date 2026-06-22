---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Bd-LEDGER-WIRING
phase: done
date: 2026-06-22
tags: [faction, diplomacy, narrative-ledger, world-event, campaign, phase-5]
---

# TCK-20260619-E53Bd-LEDGER-WIRING

## Title
Epic 5.3Bd · NarrativeLedger Wiring for Diplomatic Events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Wire diplomatic state transitions into the `NarrativeLedger` pipeline. When `DiplomaticStateMachine` or `DiplomaticActionHandler` detects ALLIANCE_FORMED, WAR_DECLARED, or PEACE_TREATY transitions, emit typed `WorldEvent` objects into `AuthoritativeState.recent_world_events`. `CampaignOrchestrator._extract_narrative_entries()` harvests these event types and creates `NarrativeLedgerEntry` records with the correct significance values.

## Scope
- Add `FACTION_WAR_DECLARED`, `FACTION_ALLIANCE_FORMED`, `FACTION_PEACE_TREATY` to `WorldEventCategory` enum
- Add `events_from_transitions()` to `diplomatic_state_machine.py` — builds WorldEvent list from split transition/alliance update batches
- Wire WorldEvent emission in pipeline.py Phase 8d (split `_diplo_updates` into `_diplo_transition_updates` + `_diplo_alliance_updates`; pass both to `events_from_transitions()`)
- Add 3 entries to `_SIGNIFICANCE_MAP` in `orchestrator.py`
- Add 5 new tests to `tests/unit/faction/test_diplomacy.py`

## Out of Scope
- Chronicle Compiler naming alignment (E53Da)
- Changing `NarrativeLedger` or `NarrativeLedgerEntry` model structure
- Altering `CampaignState` serialization

## Acceptance Criteria
- [x] `WorldEvent.FACTION_WAR_DECLARED` emitted on HOSTILE→WAR transition
- [x] `WorldEvent.FACTION_PEACE_TREATY` emitted on WAR→NEUTRAL (exhaustion)
- [x] `WorldEvent.FACTION_ALLIANCE_FORMED` emitted from alliance updates
- [x] `CampaignOrchestrator._extract_narrative_entries()` maps FACTION_WAR_DECLARED → `event_type="war_declared"`, significance=0.95
- [x] Maps FACTION_ALLIANCE_FORMED → `event_type="alliance_formed"`, significance=0.80
- [x] Maps FACTION_PEACE_TREATY → `event_type="peace_treaty"`, significance=0.75
- [x] `test_treaty_flows_through_narrative_ledger` passes
- [x] No regressions in campaigns/ or faction/ tests (69 + 26 all green)

## Related Tickets
- TCK-20260619-E53B-DIPLOMACY (parent epic)
- TCK-20260619-E53Bc-STATE-MACHINE (required — state machine)
- TCK-20260619-E53D-HISTORY (depends on this)

## Related Docs
- `docs/systems/faction_contract.md` (updated — Diplomatic WorldEvent Emission section added)
- `docs/parity_ledger/faction.yaml` (FAC-007 added)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53Bd-LEDGER-WIRING/`

## Related Code Areas
- `src/domains/world_emergence/schema.py`
- `src/domains/faction/diplomatic_state_machine.py`
- `src/engine/pipeline.py`
- `src/domains/campaigns/orchestrator.py`
- `tests/unit/faction/test_diplomacy.py`

## Assumptions / Open Questions
- `WorldEvent.payload: Dict[str, float]` means faction IDs cannot go in payload — use `subject` field instead. Implemented as `":".join(sorted([fid_a, fid_b]))`.
- `_harvest_narrative_entries` was actually named `_extract_narrative_entries` in the current codebase — test was updated accordingly.

## Implementation Notes
- `events_from_transitions()` lives in `diplomatic_state_machine.py` (no src.engine import) — lazy-imports `WorldEvent`/`WorldEventCategory` inside the function body.
- Pipeline.py Phase 8d split into `_diplo_transition_updates` and `_diplo_alliance_updates` to allow separate event detection paths (WAR/PEACE vs ALLIANCE).
- Dedup: `frozenset({fid_a, fid_b})` seen-pairs set emits exactly one WorldEvent per faction pair per call.
- Known deferral: Chronicle `naming.py` uses uppercase keys (`WAR_DECLARED`) while `_SIGNIFICANCE_MAP` emits lowercase (`war_declared`). Tracked in E53Da.

## Test Summary
26 tests in `tests/unit/faction/test_diplomacy.py` — all pass.
69 tests in `tests/unit/campaigns/` — all pass.

5 new E53Bd tests:
- `test_events_from_transitions_war_declared`
- `test_events_from_transitions_peace_treaty`
- `test_events_from_transitions_alliance_formed`
- `test_treaty_flows_through_narrative_ledger`
- `test_war_declared_flows_through_narrative_ledger`

## Files Changed
- `src/domains/world_emergence/schema.py` — added FACTION_WAR_DECLARED, FACTION_ALLIANCE_FORMED, FACTION_PEACE_TREATY to WorldEventCategory
- `src/domains/faction/diplomatic_state_machine.py` — added events_from_transitions()
- `src/engine/pipeline.py` — Phase 8d: split updates, call events_from_transitions, pass world_events_add to StateUpdate
- `src/domains/campaigns/orchestrator.py` — added 3 entries to _SIGNIFICANCE_MAP
- `tests/unit/faction/test_diplomacy.py` — 5 new E53Bd tests
- `docs/parity_ledger/faction.yaml` — FAC-007 added
- `docs/systems/faction_contract.md` — Pipeline Position + Diplomatic WorldEvent Emission sections updated

## Completion Summary
All diplomatic state transitions now emit typed WorldEvents into the authoritative pipeline, which flow through `recent_world_events` into `CampaignOrchestrator._extract_narrative_entries()` as `NarrativeLedgerEntry` records. The `events_from_transitions()` helper in `diplomatic_state_machine.py` handles deduplication and correct categorization (WAR_DECLARED, PEACE_TREATY, ALLIANCE_FORMED). `_SIGNIFICANCE_MAP` updated with all three new categories. All 95 affected tests green. Known uppercase/lowercase naming gap deferred to E53Da.
