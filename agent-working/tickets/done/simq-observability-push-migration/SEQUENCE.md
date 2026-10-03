# Implementation Sequence — simq-observability-push-migration

Epic: `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`. Implements the recommendation from
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE` (DONE): migrate COMBAT/ECONOMY/FACTION
event emission from post-tick snapshot diffing to apply-layer push-based emission. User-designated
top priority, with an explicit instruction to check this carefully and make sure no existing
defined event is missed — deferred, not skipped, if it can't be implemented in the current design.
**Strict sequential order, not parallelizable** — each step depends on the one before it, unlike
the sibling `simq-pillar-lifecycle-depth` batch.

## Order

1. **TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX** (hotfix, P1) — **DONE.**
   Scope grew during Investigate: found and fixed a wrong-attribute-name bug that had silently
   broken `attacker_id`/`killer_id` for every real combat event, caught a design flaw in the
   originally-proposed fix before shipping. `INFRA-323`.
2. **TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT** (standard, P1) — **DONE.** Full event-coverage
   audit (epic-level) confirmed exactly which of COMBAT's 9 related events migrate, defer, or are
   pre-existing dead code — none silently dropped. Built the shaper registry + `CombatShaper` (6
   events migrated), confirmed via direct trace that no hook into `ApplyPath.apply_generation()`/
   `apply_plan.py` is needed at all — `prior_state` + `update` suffice. Found and disclosed 2 more
   apply-time-only HP-mutation sources as a bounded, named limitation carried into step 4.
   `INFRA-324`.
3. **TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION** (standard, P1) — **DONE.** Migrated 7 of 12
   ECONOMY events and 8 of 9 FACTION events; re-confirmed all 6 deferrals against fresh source
   reads. Verified via real kernel run against `dungeon_crawl` — output matched this session's
   earlier independent raw-event counts exactly (`diplomatic_transition: 29`,
   `hazard_drain_applied: 10`). `INFRA-325`.
4. **TCK-20260806-PUSH-SHADOW-VALIDATION-PERF** (standard, **P0**) — **next, the hard gate.** Corpus-wide
   event-stream parity check (old diffing vs. new shapers, all 3 domains) plus a full performance
   re-validation against the existing `test_simq_isolation_overhead.py` harness. Also carries an
   explicit named check for step 2's disclosed compounding-tick payload-divergence limitation —
   not just event-type match rates. Must land after #2 and #3. **DONE — GO verdict.** Built real
   comparison tooling, ran 6 worlds x 500 ticks (exceeded the 5-world minimum), found and drove
   the fix for 2 real bugs by reopening #2 (entity_killed hazard false-positive; missing
   volumization rule). Post-fix: 130/131 active ticks match the old extractor exactly, 0
   payload-value mismatches, no measurable performance overhead across 2 reduced-scope runs.
6. **TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION** (standard, P1) — **DONE.** Cleared to
   proceed by #4's go verdict. Cut over live delivery for the migrated events; deviated from the
   literal "remove the branches" scope to flag-gated retention (real rollback lever) and a
   narrowed (not removed) `entity_killed`/`hero_death_unrecorded` condition — both deviations
   reasoned through and recorded in the ticket's investigation.md. Mandatory full-corpus
   verification (`make simq-full-audit-full`) surfaced 32 grade-regression failures; root-caused
   via a decisive flag-on/flag-off differential repro to the pre-existing, already-tracked
   INFRA-273 tick-budget-watchdog mechanism, not a migration regression — `grade_anchors.json`
   left untouched. `INFRA-273` updated with this session's confirming evidence.

## Deferred events (explicitly tracked, not silently dropped — per user instruction)

Recorded in full in the epic's own `investigation.md` "Full event-coverage audit" section, and
each carried into the relevant ticket's own Related Docs. Summary:

- **COMBAT**: `demographic_mortality` (despawn branch, broader than combat). `combat_resolved`/
  `attrition_threshold_crossed` are pre-existing dead code (never emitted anywhere) — disclosed,
  not a migration target.
- **ECONOMY**: `gold_transferred` (pure `entity.inventory.gold` state diff, no typed record),
  `resource_node_depleted`/`resource_node_regenerated`/`node_recharged` (pure `resource_nodes`
  dict diff, no typed per-node record), `conservation_law_verified` (meta/derived from other
  events already emitted this tick + tick-cadence gate).
- **FACTION**: `faction_extinct` (full entity-census scan across all entities, not a single
  update-record read).

None of these are architecturally impossible — each would need new instrumentation (a typed
update record for the state-diff cases) or a genuinely different mechanism (incremental tracking
for `faction_extinct`, end-of-tick aggregation for `conservation_law_verified`). Revisit as a
Phase 2 once Phase 1's 3 domains are fully cut over and validated.

## Notes

- This is a strictly sequential chain, unlike `tickets/todos/simq-pillar-lifecycle-depth/`'s mostly-
  parallel tickets — do not attempt to parallelize steps 3-5, each genuinely depends on the
  previous one's validated output.
- If step 4 finds a real divergence that traces to a design flaw in step 2 or 3's shaper, the
  correct response is reopening that ticket (or filing a small follow-up fix ticket under it), not
  patching around the issue inside step 4 or 5.
- Once all 5 land, the epic ticket itself closes with a full completion summary and
  `docs/audits/D20_simq_quality_status_review.md` is updated to reflect the finished migration.
