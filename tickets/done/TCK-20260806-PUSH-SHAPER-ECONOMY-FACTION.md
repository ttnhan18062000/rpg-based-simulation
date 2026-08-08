---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION
phase: done
date: 2026-08-06
tags: [observability, engine, economy, faction, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION

## Title
Extend the shaper registry with ECONOMY and FACTION shapers, under FeatureMode.SHADOW

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`. Extends the shaper registry
mechanism proven by `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT` (DONE) with two more shapers, still
SHADOW-mode only, no live delivery. Reuses that ticket's registry design, `run_shadow_shapers()`
entry point, and `ENABLE_PUSH_EVENT_SHAPERS` flag mechanism exactly — do not redesign any of them.

**Full event-coverage audit already completed at the epic level** (see
`staging_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md`'s "Full
event-coverage audit" section) — this ticket's scope is precise, not exploratory:

| Event | Mechanism | Verdict |
|---|---|---|
| `resource_harvested`, `item_crafted`, `shop_transaction`/`trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`, `paid_information_transaction`/`paid_info_transaction`/`paid_info_changed_goal` | `entity_updates[eid].intent_results[].source_kind` (typed record) | **MIGRATE** — this ticket's ECONOMY core scope |
| `gold_transaction`→`gold_transferred` | pure `entity.inventory.gold` state diff, no typed record | **DEFER** — disclose, do not implement |
| `resource_node_depleted`, `resource_node_regenerated`, `node_recharged` | pure `state.resource_nodes` dict diff, no typed per-node record | **DEFER** — disclose, do not implement (all 3 share this mechanism) |
| `conservation_law_verified` | derived from other events already appended this tick + `tick % 50 == 0` gate — meta/aggregate, not a single update-record read | **DEFER** — needs an end-of-tick aggregation design, structurally different from a per-update shaper |
| `diplomatic_transition`, `alliance_proposed` (needs `prior_state.factions` — confirmed available, same parameter `CombatShaper` already reads), `alliance_accepted`, `territory_ownership_changed`, `resource_seized`, `faction_tension_delta`, `war_declared`, `military_conflict_resolved` | `update.faction_updates[]` / `update.world_events_add[]` (typed records) | **MIGRATE** — this ticket's FACTION core scope (8 of 9 events) |
| `faction_extinct` | full entity-census scan (iterates ALL of `current_state.entities` AND `prior_state.entities` to determine per-faction living-member counts) — not a single update-record read at all | **DEFER** — would need incrementally-tracked per-faction living-member counts (new state-tracking machinery); re-verify this characterization directly against `event_extractor.py` (lines shifted since the epic-level audit — do not trust cited line numbers blindly) before concluding |

## Scope
1. Implement `EconomyShaper.shape(prior_state, update, tick)` for the 7 MIGRATE-verdict ECONOMY
   events, matching `event_extractor.py`'s current payload shapes exactly — verify against the
   source directly (line numbers have shifted since earlier reads; re-locate, don't assume).
2. Implement `FactionShaper.shape(prior_state, update, tick)` for the 8 MIGRATE-verdict FACTION
   events, including the `alliance_proposed` read of `prior_state.factions` and the
   `_seen_diplo_pairs`-style ordered-pair dedup (per-call local state, not persisted across ticks —
   confirm this matches the old extractor's own per-call scoping, don't assume).
3. **Disclose, do not implement**: `gold_transferred`, `resource_node_depleted`/`regenerated`,
   `node_recharged`, `conservation_law_verified`, `faction_extinct` — confirm each verdict via a
   fresh read of the cited mechanism (don't trust the epic audit's citations blindly), then note in
   Implementation Notes.
4. Register both shapers in `SHAPER_REGISTRY` alongside `CombatShaper` — no registry redesign.
5. Unit tests for each shaper: correct event shape/payload for each `source_kind`/diplomatic
   transition, no duplicate events for the same ordered faction pair in one tick, `alliance_proposed`
   correctly reads prior diplomatic state.
6. Confirm (via test, not assumption) that SHADOW mode still delivers nothing to the live queue
   with all 3 shapers active together.

## Out of Scope
- COMBAT shaper changes — already done.
- Any change to `event_extractor.py` — untouched until cutover; this includes the deferred events'
  handling, which stays exactly as-is on the diffing path.
- Implementing any of the 6 deferred events — each would need new instrumentation (a typed update
  record for the state-diff cases) or a different mechanism entirely (`faction_extinct`); that is
  future Phase-2 work, not this ticket's.
- Delivering to the live queue.

## Acceptance Criteria
- [ ] `EconomyShaper` implements exactly the 7 MIGRATE-verdict events, matching current output shape
- [ ] `FactionShaper` implements exactly the 8 MIGRATE-verdict events, including `alliance_proposed`
- [ ] All 6 deferred events' verdicts re-confirmed against fresh source reads and disclosed in
      Implementation Notes — not silently dropped, not silently implemented as a scope surprise
- [ ] Both registered in the shaper registry from the COMBAT pilot ticket, no registry redesign
- [ ] Unit tests for both shapers, including the FACTION ordered-pair dedup behavior
- [ ] SHADOW-mode inertness re-confirmed with all 3 shapers active
- [ ] `event_extractor.py` still untouched (confirmed via diff)
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (parent epic)
- TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT (**must be DONE first** — this ticket reuses its
  registry design)
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF (next child ticket — validates this one's output)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 ECONOMY, §5 FACTION
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/investigation.md`
  Finding 4

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION/` during
implementation.

## Related Code Areas
- `src/observability/event_shapers.py` (extend `SHAPER_REGISTRY`, add `EconomyShaper`/`FactionShaper`)
- `src/core/update_models/resources.py` (`ResourceTransferIntent`)
- `src/core/updates.py` (`FactionUpdate`)
- `src/observability/event_extractor.py` (reference only, not modified — re-locate the economy/
  faction/deferred-event blocks directly, line numbers have shifted since earlier session reads)
- `src/engine/apply.py` (reference only, not modified — confirmed unnecessary by the COMBAT ticket)

## Assumptions / Open Questions
- Whether `_seen_diplo_pairs`-style per-tick dedup state needs new handling in the apply-layer
  context (vs. the diff-extractor's existing per-call scoping) is a real question for this ticket's
  own Investigate phase, not assumed here.

## Implementation Notes
Re-verified all 6 deferral verdicts from the epic-level audit against fresh reads of
`event_extractor.py` (not trusted from citation) before implementing — all confirmed unchanged.
Implemented `EconomyShaper` (7 events, `intent_results[].source_kind`-driven) and `FactionShaper`
(8 events, `faction_updates[]`/`world_events_add[]`-driven), both registered in `SHAPER_REGISTRY`
alongside `CombatShaper`, no registry redesign needed.

One real design detail resolved during implementation: `paid_info_changed_goal`'s condition needed
confirming whether it required post-mutation state. Traced `StrategicUpdate.current_project_id_set`
directly and confirmed it carries the new value on the typed update record (same "_set" suffix
convention as `alive_set` elsewhere), so no exception to the "prior_state + update only" design was
needed.

Verified beyond unit tests: a real, non-mocked kernel run against `dungeon_crawl_seed42_500t` (the
exact world/seed/tick-count used in this session's much earlier raw-event investigation) produced
`diplomatic_transition: 29` and `hazard_drain_applied: 10` — matching that earlier investigation's
real recorded counts exactly. Also checked whether tick-budget warnings seen during this run were a
regression from the new code: ran the same scenario with the flag entirely absent and found 25
budget warnings anyway, confirming this is a pre-existing sandbox characteristic (matches
`docs/performance/simq_isolation_overhead.md`'s documented swap-pressure caveat), not something
this ticket introduced.

## Test Summary
`tests/unit/observability/test_event_shapers_economy_faction.py` (new, 20 tests, all passing on
first run): registry extension, all 7 EconomyShaper events, both `paid_info_changed_goal` cases,
all 8 FactionShaper events including diplomatic-pair dedup and both `alliance_proposed` prior-state
branches. Full `tests/unit/observability/` directory: 793 passed, 6 skipped (up from 779).
Architecture-Verify on `event_shapers.py`: clean (durable-state-mutation and reason-metadata-
smuggling both PASS).

## Files Changed
- `src/observability/event_shapers.py` — `EconomyShaper`, `FactionShaper` added, both registered
- `tests/unit/observability/test_event_shapers_economy_faction.py` (new, 20 tests)
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-325` entry (P1, verified), schema-validated

## Completion Summary
Extended the shaper registry with ECONOMY (7 of 12 related events migrated, 5 deferred) and
FACTION (8 of 9 migrated, 1 deferred) shapers, reusing the COMBAT ticket's proven registry design
and flag mechanism without modification. All 6 deferred events were re-confirmed against fresh
source reads rather than trusted from the earlier epic-level audit, and each is named explicitly in
this ticket's own docs and the parity ledger entry — none silently implemented as a scope surprise,
none silently dropped. Verified with real kernel integration output that numerically matches this
session's earlier independent investigation of the same world/seed, a stronger correctness signal
than unit tests alone provide. `event_extractor.py`/`apply.py`/`apply_plan.py`/`kernel.py` all
remain untouched by this ticket, confirmed via diff.
