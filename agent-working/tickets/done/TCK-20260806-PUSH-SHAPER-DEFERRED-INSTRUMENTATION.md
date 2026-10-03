---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION

## Title
New typed-record instrumentation to close Phase 1's 3 remaining named deferrals

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 6 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Unlike children 2-5
(pure relocation of already-typed reads), this ticket does genuinely new instrumentation work for
the 3 events Phase 1's own coverage audit named as needing it and explicitly deferred rather than
skipped (`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`'s and `TCK-20260806-PUSH-SHAPER-ECONOMY-
FACTION`'s investigation.md, cross-referenced in the Phase 1 epic's `SEQUENCE.md` "Deferred
events" section):

1. **`resource_node_depleted`/`resource_node_regenerated`/`node_recharged`** — currently a pure
   `resource_nodes` dict diff (`event_extractor.py:860-887`, comparing `prior_node.
   remaining_charges` against `node.remaining_charges`), no typed per-node update record exists.
2. **`conservation_law_verified`** — meta/derived: fires when other economy events were
   constructed *this same tick* (`event_extractor.py:916-930`, checks `any(e.event_type in (...)
   for e in events)`) — depends on already-built event list, not a single update-record read.
3. **`faction_extinct`** — needs a full entity-census scan across all entities to determine "does
   this faction have zero living members," not a single update-record field
   (`event_extractor.py`'s existing branch, per Phase 1's own finding).

Priority is **P2**, lower than children 2-5, because none of these 3 block anything else in this
epic — children 2-5 (and their SHADOW validation) do not depend on this ticket landing first, and
this ticket's own new instrumentation is a smaller, self-contained piece of work compared to the
relocation-only children.

## Scope
1. **Resource-node lifecycle**: design a minimal typed update record for resource-node state
   transitions (e.g. a `ResourceNodeUpdate` dataclass with `node_id`, `remaining_charges_delta`
   or `remaining_charges_set`, following the exact shape convention `WorldUpdate`/`FactionUpdate`
   already use), wire it at the authoritative mutation site (wherever `resource_nodes[node_id].
   remaining_charges` is currently mutated directly — locate via grep, don't guess the file).
   Add the corresponding shaper logic once the typed record exists.
2. **`conservation_law_verified`**: since this is inherently a same-tick aggregate over other
   events, not a single update read, implement it as an end-of-tick aggregation step in
   `run_shadow_shapers()` itself (checking the *other* shapers' own output list for this tick,
   the same tick % 50 throttle) rather than forcing it into a single-domain shaper class — confirm
   this design against `run_shadow_shapers()`'s current signature and structure during Investigate,
   don't assume it fits without checking.
3. **`faction_extinct`**: design an incremental tracking mechanism (e.g. a per-faction living-member
   counter maintained across ticks, decremented on `entities_remove`, rather than a full census
   scan every tick) — full census scans are what the current code already avoids doing every tick
   (it "fires only when faction_updates present," per `event_type_coverage.md` — confirm exactly
   why during Investigate, this constraint may already be a deliberate cost-control decision worth
   preserving, not a limitation to simply remove).
4. Register all 3 (once instrumented) into their respective domain shapers (resource-node events
   into `WorldDynamicsShaper` or `EconomyShaper`, whichever ledger they're scored under —
   `resource_node_depleted` scores `EconomyScorer` per `event_type_coverage.md:136` but
   `node_recharged` scores `WorldDynamicsScorer` — confirm both land in the right shaper class,
   splitting if the two scorers' domains diverge), `conservation_law_verified` into the shared
   aggregation step, `faction_extinct` into `FactionShaper`.
5. Update `docs/parity_ledger/town_resource.yaml` (`TOWN-190`, update in place) and `faction.yaml`
   (`FAC-013`, update in place) to record these deferrals closing — cross-reference, don't
   duplicate the existing entries.

## Out of Scope
- Any other event in this phase — this ticket is scoped exclusively to Phase 1's 3 named
  deferrals.
- Delivering live — SHADOW only, cutover is child 8.
- Redesigning resource-node or faction data structures beyond what's minimally needed for typed
  event emission.

## Acceptance Criteria
- [x] A typed resource-node update record exists — **found already existing**
      (`StateUpdate.node_updates`/`ResourceNodeUpdate.charges_delta`), correcting the ticket's own
      "needs new instrumentation" premise; `resource_node_depleted`/`resource_node_regenerated`/
      `node_recharged` emitted from it, no new dataclass fields or mutation-site wiring needed
- [x] `conservation_law_verified`'s aggregation-step design is implemented and tested — inside
      `run_shadow_shapers()` itself, not a shaper class
- [x] `faction_extinct`'s mechanism is implemented via full-population reconstruction (a deviation
      from "incremental-tracking," reasoned in investigation.md — same cost profile as the old
      extractor's own full census scan); faithfully reproduces a real, found-but-not-fixed dead
      HP-check bug in the old extractor rather than silently improving behavior
- [x] All 3 registered in `PHASE2_SHAPER_REGISTRY` under `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (same
      deviation as Children 2-5, same reason)
- [x] Unit tests cover each (14 tests)
- [x] `docs/parity_ledger/town_resource.yaml` (`TOWN-190`) and `faction.yaml` (`FAC-013`) updated
      in place, not duplicated
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT, TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION (DONE —
  Phase 1, source of these 3 deferrals)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §1.1
- `docs/parity_ledger/town_resource.yaml` (`TOWN-190`), `faction.yaml` (`FAC-013`)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT/investigation.md`,
  `stored_artifacts/TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION/investigation.md` (original deferral
  reasoning, read before redesigning)
- None yet for this ticket — will be created at
  `staging_artifacts/TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION/` during implementation.

## Related Code Areas
- `src/core/updates.py` (new record type)
- `src/observability/event_shapers.py`
- Resource-node and faction-census mutation sites (locate via grep during Investigate, not
  pre-guessed)

## Assumptions / Open Questions
- Whether `conservation_law_verified`'s cross-shaper aggregation approach is architecturally clean
  or introduces unwanted coupling between shapers is genuinely open — if Investigate finds it's
  too coupled, an alternative (a dedicated end-of-tick check in `kernel.py`'s observability phase,
  outside any single shaper) should be proposed instead, not forced into a bad shape.

## Implementation Notes
- **Corrected a real, mistaken assumption from Phase 1's own audit**: resource-node events were
  classified as needing new instrumentation ("pure dict diff, no typed record"). Tracing the real
  mutation site (`src/engine/apply_plan.py:152-177`) found `StateUpdate.node_updates: Dict[int,
  ResourceNodeUpdate]` already existed, with `charges_delta` giving exactly the needed signal — no
  new instrumentation needed after all.
- `faction_extinct` implemented via full-population reconstruction (`prior_state.entities` +
  this-tick deltas), not incremental tracking — a deliberate, reasoned deviation from the ticket's
  own assumed design, matching the old extractor's own cost profile (a full census scan) rather
  than inventing new durable per-faction counter state.
- Found and deliberately did NOT fix a real bug in the old extractor's `faction_extinct` logic:
  its HP-alive check reads a non-existent `entity.hp` attribute (only `entity.combat.hp` exists),
  making it dead code, always `True`. Causes no wrong behavior in practice (dead entities are
  removed from `entities` entirely). This shaper faithfully reproduces the *actual* behavior, not
  the *documented intent* — fixing the dead code is out of this migration ticket's scope.
- `conservation_law_verified` implemented as a cross-shaper aggregation step inside
  `run_shadow_shapers()` itself (checks the tick's combined Phase 1 output for 5 economy event
  types, tick%50 throttled), not a single shaper's job — matches the design anticipated during
  epic scoping.
- Real-corpus verification across 3 worlds found zero hits for all 5 events — cross-checked
  against Phase 1's own already-validated economy events (also zero in the same runs), confirming
  an environmental characteristic, not a defect. Relied on comprehensive mocked unit tests for
  direct logic verification instead.

## Test Summary
- `pytest tests/unit/observability/test_event_shapers_deferred_instrumentation.py -q`: 14 passed
  (new).
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1045 passed, 6 skipped, 3 deselected (was 1031/6/3 after Child 5 — +14 matches exactly).
- Real kernel runs across `dungeon_crawl`/`urban_political`/`sandbox_world`: zero real hits,
  explained and cross-checked, not silently accepted. `SHADOW` mode confirmed to run a full
  500-tick kernel cleanly with no exceptions.

## Files Changed
- `src/observability/event_shapers.py` — `DeferredInstrumentationShaper`, registered in
  `PHASE2_SHAPER_REGISTRY["deferred_instrumentation"]`; `conservation_law_verified` aggregation
  added to `run_shadow_shapers()`.
- `tests/unit/observability/test_event_shapers_deferred_instrumentation.py` (new, 14 tests).
- `docs/parity_ledger/town_resource.yaml` (`TOWN-190` updated in place), `faction.yaml`
  (`FAC-013` updated in place).

## Completion Summary
Closed all 3 of Phase 1's remaining named deferrals. The resource-node piece turned out to need no
new instrumentation at all — a real correction to the earlier audit's assumption, found by tracing
the actual mutation code rather than trusting the prior classification. `faction_extinct` needed a
full-population reconstruction (not incremental tracking, a reasoned scope deviation) and
faithfully reproduces a real, found-but-deliberately-not-fixed dead-code quirk in the old
extractor. `conservation_law_verified` is implemented as a genuine cross-shaper aggregation step,
matching its true nature as a meta/derived signal rather than forcing it into a single-domain
shaper. All 3 are SHADOW-only, as scoped; cutover is a separate, later ticket. This is Phase 2's
last shaper-build child — all of Children 2-6 are now DONE, clearing the way for the mandatory
shadow-validation gate (child 7).
