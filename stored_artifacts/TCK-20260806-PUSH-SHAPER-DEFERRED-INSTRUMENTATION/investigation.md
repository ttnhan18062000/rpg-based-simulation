---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION

## Key finding 1: resource-node events did NOT need new instrumentation after all

Phase 1's own audit (and this epic's own initial scoping) classified `resource_node_depleted`/
`resource_node_regenerated`/`node_recharged` as "pure `resource_nodes` dict diff, no typed
per-node record" — genuinely needing new instrumentation. **This was wrong.** Tracing the real
mutation site (`src/engine/apply_plan.py:152-177`) found `StateUpdate.node_updates: Dict[int,
ResourceNodeUpdate]` (`src/core/updates.py:701-713`) already exists, with
`charges_delta: int` giving exactly the needed signal — the same "prior_state + this-tick delta"
reconstruction pattern used throughout this epic (`new_charges = prior_node.remaining_charges +
charges_delta`). No new dataclass fields, no new mutation-site wiring — this ticket's scope for
these 3 events shrank from "design new instrumentation" to "relocate an existing typed read,"
same as most of Children 2-5's work. The earlier classification wasn't a deep architectural
finding, just an assumption made without tracing the actual apply-layer code closely enough at
the time.

## Key finding 2: `faction_extinct` needs full-population reconstruction, and faithfully reproduces a pre-existing extractor quirk

Genuinely needs to scan the full living-entity population, not a single update record — same cost
profile as the old extractor's own full census scan (`current_state.entities` + `current_state.
factions`), just reconstructed from `prior_state.entities` + this tick's `entities_add`/
`entities_remove`/`entity_updates[eid].identity.faction_set` deltas instead of reading
`current_state` directly.

**Found and deliberately did NOT fix a real bug in the old extractor**: `event_extractor.py`'s
own HP-alive check reads `getattr(entity, "hp", None)` (`event_extractor.py:1193`) — but
`EntityState` has no top-level `hp` attribute (confirmed directly: `hasattr(EntityState(...),
"hp")` is `False`; only `entity.combat.hp` exists). This makes the HP check dead code, always
`True`, for every entity. In practice this causes no wrong behavior — dead entities are removed
from `current_state.entities` entirely (not just HP-zeroed), so the inert HP check never actually
excludes a genuinely-dead-but-still-present entity. This shaper faithfully reproduces the old
extractor's *actual* behavior (entity presence + faction match, no real HP filtering) rather than
its *documented intent* (an HP-alive check) — fixing this dead code is a separate, small,
out-of-scope cleanup for a future ticket, not something to silently change here (this migration's
job is to reproduce existing behavior exactly, not improve it along the way).

## Key finding 3: `conservation_law_verified` implemented as a cross-shaper aggregation step, not a shaper class

Confirmed this is genuinely a meta/derived check (fires when any of 5 economy event types
appeared in `run_shadow_shapers()`'s own already-computed Phase 1 output for the tick, tick%50
throttled) — not representable as a single domain shaper reading a typed record. Implemented
inside `run_shadow_shapers()` itself, immediately after computing Phase 1's `events` list, subject
to the same `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` ON/SHADOW gating as every other Phase 2 event
(added to `phase2_events`, not `events` directly).

## Verification

Real, non-mocked kernel runs across `dungeon_crawl` (500t), `urban_political` (500t), and
`sandbox_world` (2000t) found **zero real hits** for all 5 of this ticket's event types —
including Phase 1's own already-validated, already-cutover `resource_harvested`/`item_crafted`/
`shop_transaction`, which also showed zero in these same runs. This confirms the zero-hit result
is an environmental characteristic of these calibration profiles (sparse economic activity without
additional scenario/flag setup this investigation didn't attempt to construct), not a defect in
this ticket's new code — Phase 1's own already-migrated-and-validated economy events showing the
identical zero-hit pattern in the identical runs rules out a shaper-specific bug. Relied on
comprehensive mocked unit tests for direct logic verification of all 3 pieces instead. `SHADOW`
mode confirmed to run cleanly with no exceptions across a full 500-tick run.

## Docs Requiring Update

- `docs/parity_ledger/town_resource.yaml`: `TOWN-190` updated in place, closes the resource-node
  deferral.
- `docs/parity_ledger/faction.yaml`: `FAC-013` updated in place, closes the `faction_extinct`
  deferral.

## Parity Ledger Overlap

`town_resource.yaml` (`TOWN-190`), `faction.yaml` (`FAC-013`) — both updated in place, not
duplicated.

## Prior Work

- `TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION` (Phase 1, DONE) — original `TOWN-190`/`FAC-013`
  deferrals this ticket closes.
- Children 2-5 (Phase 2, DONE) — the `PHASE2_SHAPER_REGISTRY`/flag-split mechanism and the
  reconstruction patterns this ticket reuses.

## Risks and Open Questions

None left open.

## Anti-Drift Hazards

- `DeferredInstrumentationShaper` has no per-run dedup cache (all 3 sub-events are purely
  this-tick-derived) — no `reset_run_state()` needed, unlike `StrategyShaper`/
  `ProgressionShaper`/`SocialShaper`.
- The `conservation_law_verified` aggregation reads `events` (Phase 1's output, computed
  unconditionally at the top of `run_shadow_shapers()`) — if Phase 1's own shaper set is ever
  restructured, this dependency must be preserved or explicitly re-derived.
