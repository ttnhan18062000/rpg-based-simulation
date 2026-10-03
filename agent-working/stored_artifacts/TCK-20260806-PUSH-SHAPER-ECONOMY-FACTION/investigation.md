---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION
artifact_type: investigation
tags: [observability, engine, economy, faction, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION

## Summary

Re-verified every event's mechanism against the current `event_extractor.py` directly (line
numbers shifted since the epic-level audit; re-located, not trusted blindly) before implementing.
All 6 deferral verdicts from the epic audit confirmed unchanged. One additional detail resolved
during implementation: `paid_info_changed_goal`'s condition compares
`entity.strategic.current_project_id` (post-mutation) against `prior_ent.strategic
.current_project_id` — confirmed `StrategicUpdate.current_project_id_set: Optional[str]` (the
"_set" suffix convention already used elsewhere in this codebase, e.g. `alive_set`) carries the
NEW value directly on the typed update record, so this is derivable from `prior_state` + `update`
alone, no post-mutation state needed — consistent with every other migrated event.

## Re-confirmed deferrals (fresh source reads, not cited from memory)

- `gold_transaction`→`gold_transferred`: `event_extractor.py` lines ~253-261, computed from
  `entity.inventory.gold - prior_ent.inventory.gold` — pure state diff, confirmed still no typed
  record backs it.
- `resource_node_depleted`/`resource_node_regenerated`/`node_recharged`: lines ~822-849, iterates
  `current_state.resource_nodes.items()` directly against `prior_state.resource_nodes` — confirmed
  still state-dict diffing, not per-entity, no typed per-node record.
- `conservation_law_verified`: lines ~878-891, scans the `events` list already built earlier in
  the same `extract()` call for economy-transaction event types, gated `tick % 50 == 0` — confirmed
  still a meta/aggregate derivation.
- `faction_extinct`: lines ~1137-1167, confirmed still a full entity-census scan over
  `current_state.entities`/`prior_state.entities` to compute per-faction living-member counts —
  not a single update-record read.

## Implementation

`EconomyShaper.shape()`: iterates `entity_updates[eid].intent_results[]`, branches on
`source_kind`, matches `event_extractor.py`'s payload shapes exactly for all 7 core events.
`FactionShaper.shape()`: iterates `update.faction_updates[]` for 6 events plus
`update.world_events_add[]` for 2 more, matching the existing `_seen_diplo_pairs`-style
per-ordered-pair dedup (implemented as a local `set()` scoped to one `shape()` call, matching the
old extractor's own per-call scoping — confirmed this is the correct behavior, not a design
question, since the old extractor's `_seen_diplo_pairs` is also a fresh local variable per
`extract()` invocation).

## Verification

Real (non-mocked) kernel integration run against `dungeon_crawl_seed42_500t` (same world/seed/tick
count as this session's much earlier raw-event investigation) with all 3 shapers active:
`{'diplomatic_transition': 29, 'hazard_drain_applied': 10, 'entity_killed': 2}` — the
`diplomatic_transition` and `hazard_drain_applied` counts match that earlier investigation's raw
`simulation_events.jsonl` counts exactly (29 and 10 respectively), a strong positive correctness
signal beyond unit-test coverage alone, though the formal event-for-event comparison remains
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s job.

Confirmed tick-budget warnings appear in this sandbox regardless of `ENABLE_PUSH_EVENT_SHAPERS`
(25 warnings in a baseline run with the flag entirely absent) — consistent with
`docs/performance/simq_isolation_overhead.md`'s already-documented swap-pressure caveat for this
environment, not a regression introduced by this ticket. Formal quantification remains
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s job.
