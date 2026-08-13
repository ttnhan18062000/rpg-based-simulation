---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE
phase: open
date: 2026-08-13
tags: [adventure, agency, cognition, observability, schema]
---

# TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE

## Title
Restore `last_routing_family`/`last_routing_tick` emission for winning `ADVENTURE_ROUTE`
candidates — requires a new `StrategicUpdate` schema field, not a one-line observability patch

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed as the required code-fix follow-up from
`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`'s Decision 1 (see that ticket's
stored `plan.md`/`investigation.md` for the full technical detail already gathered — this ticket
should read those first rather than re-deriving from scratch).

`AdventureDecisionPhase.apply()` (deleted by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`) was
the sole writer of `last_routing_family`/`last_routing_tick`, written unconditionally on every
**winning** `ADVENTURE_ROUTE` candidate (pre-deletion `src/domains/adventure/phase.py:178-179`,
readable via `git show 1825f914^:src/domains/adventure/phase.py`). `event_shapers.py:750-773`
(live path) and `event_extractor.py:594-618` (rollback path) both read `last_routing_family` to
emit `route_selected`, `action_executed`, and `route_family_first_use` — 3 of the AGENCY SimQ
pillar's 4 adventure-routing event types. No replacement site writes this property today, so all
three event types are silently dead for every routing-capable world
(`docs/guidelines/intentional_divergences.md` §2.41, broadened by the originating ticket to
disclose this).

This is deliberately **not** a narrow observability patch. Direct code reads (originating ticket's
Plan phase, re-derived independently from investigation.md's more tentative framing) found:
- `src/core/updates.py:474-517` (`StrategicUpdate` dataclass): no field exists today that could
  carry an arbitrary `{"last_routing_family": ...}` key.
- `src/core/updates.py:613-645` (`EntityUpdate` dataclass): `strategic: Optional[StrategicUpdate]`
  and `property_updates: Dict[str, Any]` are sibling fields, not nested — `property_updates` is
  never populated from `.strategic`'s contents anywhere.
- `src/systems/strategic_systems/intelligence.py:917-927` (the only call site that merges a
  `StrategicUpdate` returned by `evaluate_strategic_intent()` into the tick's `EntityUpdate`):
  merges into `ent_upd.strategic` only, never touches `ent_upd.property_updates`, and does not
  have the route family value available at this point anyway.
- `src/domains/adventure/mapper.py:31-47` (`RouteToProjectMapper._MAP`): 15 `RouteFamily` values
  map onto `ProjectKind`s with real collisions (e.g. `RECOVER`/`OWN_SURVIVAL` both ->
  `ProjectKind.RECOVERY`; `TAKE_EASY_QUEST`/`QUEST_OPPORTUNITY` both -> `ProjectKind.QUEST`). The
  committed `ProjectState.kind` at the outer merge site cannot be reversed into the original
  `RouteFamily` — the family only exists inside `evaluate_strategic_intent()`'s own
  `ADVENTURE_ROUTE` branch as `best_candidate.metadata.get("route_family")`
  (`intelligence.py:1489`, sourced from `adventure_scorer.py:217`'s
  `GoalScore.metadata={"route_family": family, ...}`).

## Scope
- Add a field to the `StrategicUpdate` dataclass (`src/core/updates.py`) capable of carrying the
  route family (and tick) through to a committed `EntityUpdate` — exact shape (a dedicated
  `last_routing_family`/`last_routing_tick` pair vs. a general `property_updates`-equivalent field
  on `StrategicUpdate`) is an Investigate/Plan decision, not pre-decided here.
- Update `StrategicUpdate.merge()` to propagate the new field.
- Thread the value from the `ADVENTURE_ROUTE` win branch
  (`src/systems/strategic_systems/intelligence.py:1478-1495`, where `family` is known via
  `best_candidate.metadata.get("route_family")`) through to the outer refine-loop merge site
  (`intelligence.py:917-927`) so it lands in `EntityUpdate.property_updates` (or wherever the new
  field resolves to) on a real committed update.
- New regression test verifying a winning `ADVENTURE_ROUTE` candidate's materialization produces
  an update carrying the route family, so `route_selected`/`action_executed`/
  `route_family_first_use` can fire again — see
  `staging_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/test_plan.md`'s
  New Test item 3 for a starting shape (illustrative, not binding).
- Recalibrate `grade_anchors.json` AGENCY back up for the routing-capable run_keys once emission is
  restored (this will re-flip the 6 run_keys the originating ticket just recalibrated down to
  0/0.0/C — expected and correct once this fix lands).
- Update `docs/guidelines/intentional_divergences.md` §2.41 to record that the `last_routing_family`
  half is now restored (leave the `last_defer_reason` half's `Bounded` status untouched, see Out of
  Scope).
- Update `docs/parity_ledger/infrastructure.yaml` INFRA-237's `support_boundary` with a further
  addendum recording the fix.

## Out of Scope
- `last_defer_reason` — stays `Bounded`/deliberately-not-ported per §2.41's existing rationale (the
  DEFER_WITH_REASON candidate is discarded by the shared tier-5 utility-floor check,
  `intelligence.py:1450`, `if g_score.utility < 20.0 or (...): continue`, before any
  `StrategicUpdate`-returning site is reached — porting it requires special-casing sub-floor scores
  inside the shared tier-5 loop itself, a change affecting every `GoalKind` scorer, not just
  adventure's). Do not fold that into this ticket.
- Any change to `evaluate_project_switch()`'s own lock/margin/retention decision logic
  (STRAT-185/186/187) — not touched under any circumstance.
- `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`.

## Acceptance Criteria
- [ ] `StrategicUpdate` carries the route family through a real schema field (not a `reason` string
      or free-form metadata), with a defined lifecycle and `merge()` support
- [ ] A winning `ADVENTURE_ROUTE` candidate's materialization produces a committed `EntityUpdate`
      carrying `last_routing_family`, verified by a new regression test
- [ ] `route_selected`, `action_executed`, `route_family_first_use` events fire again for
      routing-capable worlds (verified via a fresh `tools/calibrate_simq.py` run against
      `simq_routing_test`/`hero_guild_routing`)
- [ ] `grade_anchors.json` AGENCY recalibrated for all affected run_keys to reflect restored
      emission
- [ ] `docs/guidelines/intentional_divergences.md` §2.41 and
      `docs/parity_ledger/infrastructure.yaml` INFRA-237 updated to record the restoration
- [ ] No change to `last_defer_reason`'s `Bounded` status or `evaluate_project_switch()`'s decision
      logic

## Related Tickets
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (filed this follow-up; its own
  stored `plan.md` Decision 1 and `investigation.md` Risk #1 contain the full evidence trail)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (deleted the sole writer of
  `last_routing_family`/`last_defer_reason`)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.41
- docs/parity_ledger/infrastructure.yaml (INFRA-237)
- docs/simulation_quality/eval_matrix_results.md (AGENCY — Cross-World Design Note)

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/ (once moved —
  plan.md's Decision 1 is the primary evidence source for this ticket's scope)

## Related Code Areas
- src/core/updates.py (`StrategicUpdate`, `EntityUpdate`)
- src/systems/strategic_systems/intelligence.py (`evaluate_strategic_intent()`'s `ADVENTURE_ROUTE`
  branch, the outer refine-loop merge site)
- src/domains/adventure/mapper.py (`RouteToProjectMapper`)
- src/ai/goals/adventure_scorer.py (`AdventureGoalScorer.score()`, `GoalScore.metadata`)

## Assumptions / Open Questions
- Exact shape of the new `StrategicUpdate` field (dedicated typed field vs. a general
  `property_updates`-equivalent) is not pre-decided — Investigate/Plan should weigh both against
  existing `StrategicUpdate` field conventions.
- Whether this fix should also address any other `GoalKind` scorer's own metadata-loss pattern (if
  a similar gap exists elsewhere) is out of scope unless Investigate finds a directly analogous
  case — do not widen speculatively.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
