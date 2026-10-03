---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY
artifact_type: plan
tags: [combat, observability, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY

## Real event shapes

### `combat_engagement_started`
- Fires alongside the existing `combat_initiated` gate, inside `CombatShaper.shape()`.
- `entity_id` = defender (`eid`), `target_id` = `real_combat.attacker_id`.
- `payload`: `trigger_reason` (`"GOAL_ENGAGE"` | `"OPPORTUNITY_ATTACK"`), `attacker_snapshot`,
  `defender_snapshot` (both via the new `_combat_entity_snapshot()` helper).

### `combat_engagement_ended`
- Fires inside `CombatShaper.shape()` on 3 of its 4 real conditions (KILL, CAUGHT_FLEEING,
  PURSUIT_ABANDONED — all readable from `prior_state`+`update` alone); the 4th (ESCAPED) needs one
  new, real, additive tag written at the source in `movement.py`, then read here the same way.
- `payload`: `outcome` (`"KILL"` | `"ESCAPED"` | `"CAUGHT_FLEEING"` | `"PURSUIT_ABANDONED"`), plus
  the relevant snapshot(s) and, for `PURSUIT_ABANDONED`, the real `reason` string
  (`LEASH_RETURN`/`STALEMATE_BREAK`) for extra fidelity at no real cost (already available).

## Real source-level change (the one non-observability-layer edit)
`src/engine/movement.py`: inside the existing `if engaged_hostiles and not skip_oa:` block's own
sibling case — when `engaged_hostiles` is non-empty **and** `skip_oa` is `True` (the real
successful-evasion case) — add a real `property_updates` entry to the entity's own
`EntityUpdate`, mirroring the file's own already-established `"movement_resolution":
"POSITION_SWAP"` pattern exactly: `property_updates={"combat_escape": "EVASIVE_SUCCESS",
"combat_escape_evaded_ids": list(engaged_hostiles)}`. Purely additive — no change to the real
`skip_oa`/opportunity-attack resolution logic itself.

## Rejected alternatives
- **Replacing `combat_initiated`/`entity_killed` instead of adding alongside**: rejected —
  existing consumers of those event types (real, already-registered in `event_type_coverage.md`)
  must keep working unchanged; this ticket is purely additive.
- **Building a full "engagement ID" that ties a start event to its own later end event**:
  considered and rejected as disproportionate for this ticket's own high-level scope — each event
  carries enough real identity (`entity_id`/`target_id`/tick) for a later analysis to correlate
  starts and ends by entity-pair-and-tick-proximity without a new stateful engagement-tracking
  mechanism. A dedicated engagement-ID system is real, valuable, future scope, not required here.
- **Snapshotting BOTH entities' post-tick state**: rejected — the shaper's own real architecture
  is prior_state + update only (no post-mutation `current_state`, an established, load-bearing
  design constraint this whole file already documents). Defender's real end-state HP is derivable
  from `new_hp` (already computed) without needing a second EntityState read.

## Verification plan
- Real unit tests for the new `_combat_entity_snapshot()` helper and all 5 real trigger
  conditions (2 for `combat_engagement_started`, 4 for `combat_engagement_ended`), using the same
  hand-constructed-`EntityState` precedent this session's own sibling event-observability tickets
  established for low-real-frequency events.
- **Real corpus re-verification** (the user's own explicit expectation this ticket "might end up
  we need more tests for scenario"): a live `Kernel.tick_once()` run against `dungeon_crawl`/
  `urban_political` at 2000 ticks, confirming all 5 real trigger conditions fire at genuine,
  non-zero, honestly-reported volume — not assumed safe from unit tests alone, matching this
  whole session's own established discipline. If any condition doesn't fire naturally at this
  scale (a real possibility for `PURSUIT_ABANDONED`/`ESCAPED`, both narrower real paths), disclose
  that honestly rather than force a synthetic-only "verified" claim.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms the real architecture | Done |
| New high-level event types land, entity snapshots included | Implement phase |
| Registered in event_type_coverage.md §5 | Document-Update phase |
| Real corpus re-verification, non-zero honest volume | Test phase |
| Scoped pytest passes | Test phase |
