---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC
artifact_type: investigation
tags: [observability, engine, simulation-quality, performance, progression]
---

# investigation.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC

## Summary

The epic's own ticket body already carries the full field-level readiness audit (the
`IdentityUpdate`/`StrategicUpdate`/`EntityUpdate.property_updates`/`WorldUpdate`/`StateUpdate`/
`SocialUpdate` table and the 5-item genuine-exceptions list) — not duplicated here. This
investigation instead records the outcome of executing all 8 child tickets, since the epic itself
made no direct code changes.

## Full event-coverage accounting — the epic's own governing instruction honored

Per the epic's own instruction ("make sure the new push is not missing any existing defined
event, if it cannot be implemented in the current design, defer it not skip it"), all 51
originally-remaining events were individually accounted for by name across children 2-6's own
Investigate phases:

- **Migrated** (~50 events): `StrategyShaper` (14: AGENCY+COGNITION+INFORMATION+
  `cooperation_event`), `ProgressionShaper` (7), `WorldDynamicsShaper` (14, including
  `demographic_mortality` — Phase 1's premature deferral corrected), `SocialShaper` (10),
  `DeferredInstrumentationShaper` (5: resource-node lifecycle x3, `conservation_law_verified`,
  `faction_extinct` — all 3 of Phase 1's remaining named deferrals, closed via child 6's own
  fresh mutation-site tracing, not new instrumentation as originally assumed for the resource-node
  events).
- **Deliberately still deferred, with reason** (1 event): `gold_transferred`/`gold_transaction` —
  no typed record exists for `entity.inventory.gold`'s raw diff. Confirmed still the case at child
  6's own Investigate phase; carried forward, not silently dropped.
- **Confirmed out of scope** (unchanged from the epic's own Out of Scope section): `quest_event`/
  `quest_system` (separate live-emission source), campaign/scenario-gated events, `camp_constructed`
  (no engine path exists).

**Zero events were silently dropped.** Every deferred or out-of-scope event carries a specific,
traced reason, confirmed via direct source reads in the responsible child's own Investigate phase,
not assumed from this epic's original audit alone.

## Real bugs found across the 8 children (not exhaustive prose — see each child's own
## stored_artifacts/investigation.md for full detail)

- Child 2 (`STRATEGY`): registering Phase 2 shapers directly into Phase 1's `SHAPER_REGISTRY`
  double-fires (Phase 1's flag already defaults `ON`) — fixed by introducing the separate
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag + `PHASE2_SHAPER_REGISTRY`, the pattern every subsequent
  child reused.
- Child 3 (`PROGRESSION`): `progression_plateau_detected` needed any-update gating, not
  identity-update gating — the same *class* of bug as child 2's `belief_stale`, confirmed
  recurring, not a one-off.
- Child 5 (`SOCIAL`): `contract_expired_offer` double-fired when two independent mutation
  functions (`check_expirations()`/`reap_expired_offers()`) produced overlapping same-tick signals
  for the same contract — invisible to the old extractor's single-materialized-view design, real
  for a shaper reading raw update lists independently.
- Child 8 (`CUTOVER`): the critical finding — `event_shapers.py`'s `run_shadow_shapers()` read
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` via its own separate, stale default, causing a total blackout
  of all ~50 Phase 2 events under the real post-cutover default state. Found via real-kernel
  verification (unit tests alone, MagicMock-based, could not have caught this), fixed, verified in
  both directions. See `docs/parity_ledger/infrastructure.yaml` `INFRA-326`.

## Full-corpus outcome (child 8's own scope item 4)

`make simq-full-audit-full` (79 scenarios) post-cutover: 37/69 `test_grade_regression.py`
failures (up from Phase 1's 32/69). Root-caused via a decisive differential-repro
(`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` forced OFF vs ON, kernel driven directly for
`urban_political_selfmodel_probe_seed42_200t`) as the same pre-existing `INFRA-273`
tick-budget-watchdog mechanism, now visible on more pillars because Phase 2 widened live delivery
— not a Phase 2 regression. `grade_anchors.json` left unrecalibrated. Full detail in
`stored_artifacts/TCK-20260806-PUSH-CUTOVER-PHASE2/investigation.md`.

## Conclusion

The push-based migration is now functionally complete for both this epic's own scope and the
original `event_extractor.py` audit's full intent: COMBAT/ECONOMY/FACTION (Phase 1) plus
AGENCY/COGNITION/INFORMATION/PROGRESSION/WORLD/SOCIAL (Phase 2) are all live apply-layer emission
by default, each with a real, verified, flag-gated rollback to the old diffing extractor. Only
`gold_transferred`/`gold_transaction` remains on the old path, deliberately deferred.
