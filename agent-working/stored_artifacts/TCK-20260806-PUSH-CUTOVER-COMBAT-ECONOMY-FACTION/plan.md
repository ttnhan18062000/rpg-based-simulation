---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
artifact_type: plan
tags: [observability, engine, combat, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION

## Unresolved Questions

None — the deployment-mechanism decision (investigation.md) and the entity_killed narrow-exclude
fix are both resolved with explicit reasoning.

## Steps

1. Flip `ENABLE_PUSH_EVENT_SHAPERS`'s default in `FeatureFlagManager.__init__` from `OFF` to `ON` —
   this is now the live, validated, default path for COMBAT/ECONOMY/FACTION.
2. In `event_extractor.py`'s `extract()`, add a module-level flag read at the top:
   `_push_shapers_active = getattr(prior_state, "feature_flags", {}).get(
   "ENABLE_PUSH_EVENT_SHAPERS", "ON") == "ON"` (default `"ON"` matches the new
   `FeatureFlagManager` default when `state.feature_flags` doesn't explicitly override it — a run
   with no explicit override should get the new default behavior, not silently fall back to OFF).
3. Guard `combat_damage`/`combat_initiated`/`near_death_survival`/`hazard_drain_applied` branches
   with `if not _push_shapers_active:` — full removal-equivalent when the flag is ON, exact
   original behavior preserved when OFF (rollback).
4. Narrow (not remove) the Kill-events branch: `is_shaper_owned_kill = (_push_shapers_active and
   real_combat_upd is not None and real_combat_upd.outcome_kind == "KILL")`; only construct
   `CombatKillEvent`/`hero_death_unrecorded` `if not is_shaper_owned_kill`. When flag is OFF,
   `is_shaper_owned_kill` is always False, so behavior is byte-identical to pre-cutover.
5. Guard all 7 ECONOMY branches and all 8 FACTION branches the same way (`if not
   _push_shapers_active:`).
6. In `kernel.py`'s `_phase_observability`, change the SHADOW-only construct-and-log behavior:
   when `mode_value == "ON"`, deliver each shaper-constructed event to
   `self._event_recorder.record(event)` and `self._entity_timeline_store.record(event)` (matching
   exactly what happens to `generated_events` a few lines below) instead of only logging a count.
   `"SHADOW"` mode keeps the current construct-only, log-only behavior (useful for future
   regression comparisons, e.g. validating Phase 2 additions the same way this epic validated
   Phase 1).
7. Run the full calibration corpus (`make simq-full-audit-full`) and confirm event counts/grades
   match the validated shadow-mode baseline.
8. Update parity ledger (`combat_movement.yaml`, `town_resource.yaml`, `faction.yaml`) and
   `docs/audits/D20_simq_quality_status_review.md`.
9. Recalibrate `grade_anchors.json` only if a genuine, understood difference is found.

## Scope guard

`ApplyPath.apply_generation()`/`apply_plan.py` remain untouched — the delivery mechanism lives
entirely in `kernel.py`'s existing `_phase_observability()` call site, consistent with every prior
child ticket in this epic.

## Acceptance-criteria map

| Ticket AC (original) | How satisfied, with the revised deployment mechanism |
|---|---|
| Validation ticket's go verdict confirmed | Done — read directly, not assumed |
| event_extractor.py branches removed | Revised: flag-gated, not deleted — see investigation.md's deployment-mechanism decision; net effect (default path is push-based) is the same |
| Shaper registry delivers live | Step 6 |
| Full corpus re-run matches shadow baseline | Step 7 |
| grade_anchors.json unchanged unless genuine difference | Step 9 |
| Parity ledger + docs updated | Step 8 |
| Full scoped pytest passes | Verify phase |
