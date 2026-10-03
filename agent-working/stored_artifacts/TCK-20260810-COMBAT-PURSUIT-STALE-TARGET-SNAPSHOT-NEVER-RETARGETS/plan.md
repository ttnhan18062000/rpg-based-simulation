---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS
artifact_type: plan
tags: [combat, engine]
---

# Plan: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS

## Approach
1. Extract COMB-304's own live-retargeting logic (currently duplicated inline in
   `route_movement_intent`) into one shared static helper on `MovementCandidateSelector`, taking
   a plain entity-id-to-EntityState mapping rather than a full state/packet object.
2. Apply the shared helper at the 2 real gap sites found during Investigate
   (`MovementCandidateSelector.select()`, and both `ENTITY_MOVE` work-item dispatchers) plus
   `route_movement_intent` itself (replacing its own inline copy, so all 4 sites can never drift
   out of sync again).
3. Re-verify the specific frozen pair, then the real, decisive corpus-wide measure
   (`combat_resolved`/`entity_killed`/`combat_damage` event counts).
4. Run a full regression sweep given the changed files are shared, core engine dispatch paths.

## Rejected Alternatives
- **Fix only `route_movement_intent`'s own `has_fresh_decision` semantics** (e.g., add a
  "was this genuinely re-decided" flag distinct from "target_set is non-None") — rejected as
  riskier and less targeted: it would require threading a new signal through the ENTITY_MOVE
  dispatch's own `WorkerPacket`/`WorkItem` protocol, a much larger surface than a shared,
  drop-in helper reused verbatim at the existing call sites.
- **Remove the `NavigationUpdate(target_set=...)` reaffirmation from the ENTITY_MOVE dispatchers
  entirely** (since it's arguably redundant with the persisted `entity.navigation.target` field
  route_movement_intent already falls back to) — rejected: risk of breaking OTHER, non-pursuit
  ENTITY_MOVE work (WANDER/RETREAT/objective movement) that may rely on this field being
  reaffirmed each tick for a reason not fully traced; live-refreshing it at the source (keeping
  the existing "always reaffirm" contract, just with a live value) is the smaller, safer diff.
- **Preserve `outcome`/`reason` in the stuck-attack-task reset payload** (to satisfy the 2
  conflicting integration tests found during Test) — rejected after live corpus re-verification
  showed it reintroduces a partial version of the original bug; the tests were the ones that
  needed updating, not the already-verified-correct production behavior.

## Verification Plan
- 4 new unit tests targeting `MovementCandidateSelector.resolve_live_tracking_target` and
  `select()`'s own new fallback, confirmed via git-stash bisection to genuinely fail pre-fix.
- Full scoped regression sweep across movement/combat/tactical/kernel/core/engine/actions/
  strategic/observability/entities/integration-combat/integration-pipeline.
- Real corpus re-verification via a direct `Kernel.tick_once()` loop (not the calibration tool's
  own replay, matching this session's own established methodology), comparing combat event
  counts before and after.
