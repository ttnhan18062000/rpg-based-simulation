---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality, performance, progression]
---

# TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC

## Title
Epic: Phase 2 — migrate all remaining `event_extractor.py` domains to apply-layer push-based
emission, plus a standing cumulative performance regression gate

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` (DONE) migrated COMBAT/ECONOMY/FACTION —
18 events — from post-tick diffing to the apply-layer shaper registry (`src/observability/
event_shapers.py`), leaving `event_extractor.py`'s original architecture investigation's own
hedge unresolved: "PROGRESSION (quest) ... needs new instrumentation ... demographic/XP domains
also read as diff-based on a quick pass, same category as quest ... a full per-domain table
across all ~10 [pillars] is Scope work for whichever ticket implements this."

This ticket **is** that scope work. A direct field-level audit of every one of the 51 event types
`event_extractor.py` still constructs (computed by diffing `event_shapers.py`'s already-migrated
`event_type` set against `event_type_coverage.md`'s full scored-event list) found the original
hedge was overly cautious: **the overwhelming majority are push-ready today**, via typed update
records that already exist but that `event_extractor.py` simply never adopted (it predates or
never revisited this architecture) — confirmed directly against `src/core/updates.py`:

| Record | Fields confirmed to already carry exactly what's needed |
|---|---|
| `IdentityUpdate` | `evolution_points_delta`, `evolution_level_set`, `learned_skills`, `traits_add`, `breakthroughs_add`, `unspent_ap_delta`/`_set` — covers **all** of PROGRESSION's core events directly |
| `StrategicUpdate` | `leads_add_or_update`, `current_project_id_set`, `concerns_add_or_update`, `contracts_add_or_update` — covers most of COGNITION/INFORMATION/AGENCY and SOCIAL's contract lifecycle |
| `EntityUpdate.property_updates` | a generic per-tick key/value bag already read directly (no diffing) for `route_selected`/`action_executed`/`defer_with_reason`/`self_model_updated`/`belief_assimilated`/`belief_updated`/`cooperation_event` — these are *already* implemented as direct reads, just not relocated to a shaper |
| `WorldUpdate` | `trauma_delta`, `owner_faction_id_set`, `kind_set`, `hazard_level_set`, `calamity_intensity_set` — covers most of WORLD dynamics |
| `StateUpdate` | `entities_add`/`entities_remove` — covers `demographic_birth`/`demographic_mortality`/`boss_spawned`/`raid_party_spawned`/`spawn_cadence_fired` directly (Phase 1 had classified `demographic_mortality` as needing deferral; that was premature — it's push-ready via `entities_remove` + the already-shared `_real_combat_update` helper) |
| `SocialUpdate` | `trust_delta`, `reputation_set`, `betrayal_increment` — likely covers `reputation_delta`/`social_memory_created`, pending exact-semantics confirmation in that child's own Investigate phase |

Genuine exceptions found (need either shaper-local per-run state, same pattern as existing dedup
sets, or new instrumentation):
- `progression_plateau_detected` — cross-tick derived ("XP unchanged for 50 ticks"), same category
  as COMBAT's `near_death_survival` threshold logic — solvable with shaper-local state, not new
  instrumentation.
- `conservation_law_verified` — meta/derived from other same-tick events; already correctly
  deferred by Phase 1's own audit for the identical reason (COMBAT/ECONOMY/FACTION scope) — same
  classification here.
- `resource_node_depleted`/`resource_node_regenerated`/`node_recharged` — pure `resource_nodes`
  dict diff, no typed per-node update record exists (same finding Phase 1 already made for
  ECONOMY's identical gap — this is the same underlying gap, not a new one).
- `faction_extinct` — needs a full entity-census scan, not a single update-record read (same
  finding Phase 1 already made).
- `group_joined`/`group_expelled` — reads `entity.group_id` (materialized diff); no `group_id_set`
  field confirmed yet on any update record — needs confirmation in that child's own Investigate
  phase, not assumed either way here.

**Second, cross-cutting ask this epic also covers**: a standing, formal performance regression
gate for the shaper registry's *cumulative* cost as more domains are added to it. Phase 1's
performance validation (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`) was a real but one-off,
reduced-scope, uncommitted comparison script — not a standing gate wired into the test suite.
`tests/perf/test_simq_isolation_overhead.py` (the existing, committed harness) currently has no
knowledge of `ENABLE_PUSH_EVENT_SHAPERS` at all. As Phase 2 adds 4-5x more shapers than Phase 1,
a one-off spot check per phase is not enough — a committed, standing gate is needed so overhead
accumulation is caught automatically, not re-discovered by hand each phase.

## Scope
Break down into 8 child tickets, sequenced in `SEQUENCE.md`:

1. **Performance regression gate** (build first, so every subsequent child is gated by it)
2. **STRATEGY shaper** (AGENCY + COGNITION + INFORMATION + `cooperation_event`, ~17 events, SHADOW)
3. **PROGRESSION shaper** (7 events, SHADOW)
4. **WORLD DYNAMICS shaper** (WORLD + demographic + NARRATIVE co-fires, ~15 events, SHADOW; closes
   Phase 1's `demographic_mortality` deferral)
5. **SOCIAL shaper** (7 events, SHADOW)
6. **Deferred-instrumentation closure** (new typed records for resource-node lifecycle,
   `conservation_law_verified`, `faction_extinct` — closes Phase 1's 3 remaining genuine
   deferrals, enables their shapers)
7. **Shadow validation + full-registry perf re-run** (mandatory pre-cutover gate, mirrors Phase 1
   Child 4, but now validates the *combined* registry — all Phase 1 + Phase 2 domains together —
   not just the domains added in this phase)
8. **Cutover** (irreversible step: flag-gated mutual exclusion, default flip, final corpus
   verification — mirrors Phase 1 Child 5's proven deployment-mechanism decision)

Each child runs its own full `implement-ticket.js` pipeline. This epic ticket does not implement
anything directly.

## Out of Scope
- `quest_event` (quest_started/completed/failed) — confirmed via raw JSONL inspection this
  session to already come from `quest_system`, a separate live-emission source, **not**
  `event_extractor.py`'s diffing pass. Not part of "full replacement of event_extractor" by
  definition. Whether `quest_system`'s emission should also route through the shaper-registry
  pattern for architectural consistency is a separate, smaller question, not scoped here.
- Campaign/scenario-gated events (`chronicle_entry_created`, `scenario_objective_*`,
  `scenario_stalled`) — `event_type_coverage.md` §4 P0-A Blocked; not exercised by any calibration
  scenario, no urgency to migrate.
- `camp_constructed` — `event_type_coverage.md` §3.9 confirms no engine path exists at all; not
  an observability-layer question.
- Any change to scoring rules, weights, or grade calculation — same boundary Phase 1 held.
- Removing `EventExtractor` as a class — even after this epic, it stays as the documented rollback
  mechanism for both phases' migrated domains (same flag-gated-mutual-exclusion pattern as Phase 1).

## Acceptance Criteria
- [x] All 8 child tickets filed to `tickets/todos/simq-observability-push-migration-phase2/`, with
      `SEQUENCE.md` establishing build → validate → cutover order
- [x] Child 1 (perf gate) lands before any shaper-build child begins
- [x] Children 2-5 (shaper builds) each independently SHADOW-validated before child 7
- [x] Child 6 closes all 3 of Phase 1's remaining named deferrals (resource-node lifecycle,
      `conservation_law_verified`, `faction_extinct`) with real new instrumentation, not skipped —
      resource-node events needed no new instrumentation after all (corrected assumption, existing
      `StateUpdate.node_updates` sufficed)
- [x] Child 7 (shadow validation) is DONE, any divergence found investigated and resolved, before
      child 8 (cutover) begins — GO verdict, 1/6 world mismatch root-caused to `INFRA-273`
- [x] Child 8 completes: old diffing code for every migrated event flag-gated (not deleted, same
      rollback-preserving pattern as Phase 1), live queue fed by the new path
- [x] Every one of the 51 audited events is accounted for by name in this epic's own investigation
      trail: migrated, deferred-with-reason, or confirmed out of scope — none silently dropped
- [x] `docs/audits/D20_simq_quality_status_review.md` updated with this epic's outcome once
      complete (Finding 13)

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (DONE — Phase 1, the pattern this epic
  repeats at larger scale)
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE (DONE — original investigation; its own
  "full per-domain table ... is Scope work for whichever ticket implements this" is what this
  epic's Request Summary now delivers)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (unblocked, `tickets/todos/simq-pillar-
  lifecycle-depth/` — that ticket designs a *new* PROGRESSION scoring rule; this epic instead
  migrates PROGRESSION's *existing* event emission mechanism. Sequencing between them is not yet
  decided — flagged as an open question below, not assumed)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` (authoritative source for the full 84-event
  scored list this audit was computed against)
- `docs/simulation_quality/quality_scoring_contract.md` §5
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-324`, `INFRA-325` — Phase 1's shaper-registry
  parity entries, same mechanism this epic extends)
- `docs/audits/D20_simq_quality_status_review.md` Finding 12

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/` (parent investigation)
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/` (Phase 1, the proven
  pattern)
- `stored_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/` (Phase 1's cutover —
  includes the `INFRA-273` load-sensitivity finding relevant to any future full-corpus verification
  in this phase too)

## Related Code Areas
- `src/observability/event_extractor.py` (the remaining ~51-event diffing pass being relocated)
- `src/observability/event_shapers.py` (the registry being extended with 4 new shaper classes)
- `src/engine/kernel.py` (`_phase_observability` — no change expected, already generic over the
  registry)
- `src/core/updates.py` (`IdentityUpdate`, `StrategicUpdate`, `WorldUpdate`, `SocialUpdate`,
  `StateUpdate` — the typed records this epic's shapers read from)
- `tests/perf/test_simq_isolation_overhead.py` (extended by child 1)

## Assumptions / Open Questions
- Whether `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` (new PROGRESSION scoring rule
  design) should land before or after this epic's PROGRESSION shaper child (3) is not decided
  here — that ticket adds a *new* rule reading existing `ScoringContext` state, largely orthogonal
  to *how* PROGRESSION's existing events reach the queue, but worth a quick cross-check at that
  child's own Investigate phase in case of overlap.
- `group_joined`/`group_expelled`'s typed-record status is genuinely unconfirmed (unlike every
  other domain in this audit, which found a concrete matching field) — child 5's own Investigate
  phase resolves this, not assumed here either way.
- Whether `quest_system`'s live emission (out of scope, see above) should eventually also route
  through the shaper-registry pattern for architectural consistency is noted but not scoped.

## Implementation Notes
(epic — no direct implementation; all 8 child tickets carried implementation, each hand-
orchestrated through the full `implement-ticket.js` pipeline sequentially, in `SEQUENCE.md`'s
order, stopping on the first non-DONE result — none occurred, all 8 completed DONE.)

## Test Summary
(epic — no direct implementation; see `staging_artifacts` → `stored_artifacts` migration's
`test_plan.md` for the full per-child testing account.)

## Files Changed
(epic — no direct implementation; see each child ticket's own Files Changed section. Net new
production file: `src/observability/event_shapers.py`. Modified: `event_extractor.py`,
`feature_flags.py`, `kernel.py`. 6 new test files under `tests/unit/observability/`, plus
extensions to `tests/perf/test_simq_isolation_overhead.py`.)

## Completion Summary
All 8 child tickets are DONE, in strict `SEQUENCE.md` order, none reopened. Phase 2's ~50
remaining events (AGENCY/COGNITION/INFORMATION/PROGRESSION/WORLD/SOCIAL) are now live apply-layer
emission by default via `PHASE2_SHAPER_REGISTRY`, mirroring Phase 1's own proven
flag-gated-mutual-exclusion cutover pattern exactly — a real, verified rollback to the old
diffing `event_extractor.py` path remains in place for both phases' migrated domains.

**Event coverage — this epic's own governing instruction honored in full**: every one of the 51
originally-remaining events was individually accounted for by name. ~50 migrated across 5 shaper
classes (`StrategyShaper`, `ProgressionShaper`, `WorldDynamicsShaper`, `SocialShaper`,
`DeferredInstrumentationShaper`); exactly 1 (`gold_transferred`/`gold_transaction`) remains
deliberately deferred with a documented reason (no typed record exists for the raw
`entity.inventory.gold` diff); the rest confirmed genuinely out of scope
(`quest_event`/`quest_system`, campaign/scenario-gated events, `camp_constructed`). None silently
dropped.

**Real bugs found and fixed across the 8 children** (not process theater — each caught by
real-kernel verification, not unit tests alone): a Phase-1-registry double-fire risk (child 2,
led to the separate `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag design used by every subsequent
child), a recurring any-update-vs-specific-update gating bug class (children 2 and 3), a
same-tick dual-signal double-count bug (child 5, `contract_expired_offer`), and — the most
consequential — child 8's own `run_shadow_shapers()` default-lockstep total-blackout bug, found
via real-kernel verification of the actual post-cutover default state, not assumed safe from unit
tests alone (`INFRA-326`).

**Regression discipline held throughout**: every grade-regression drift found (Phase 1's 32/69,
Phase 2's 37/69 failures) was root-caused via decisive differential-repro to the same
pre-existing, already-documented `INFRA-273` tick-budget-watchdog mechanism — never assumed,
never silently waved through, never used as an excuse to reflexively recalibrate
`grade_anchors.json` against an unrelated infrastructure issue.

The push-based observability migration is now functionally complete: `TCK-20260806-SIMQ-
OBSERVABILITY-PUSH-MIGRATION-EPIC` (Phase 1: COMBAT/ECONOMY/FACTION) plus this epic (Phase 2: the
remaining 6 pillars) together deliver live apply-layer emission for the entire scored event
surface `event_extractor.py` originally diffed, save one deliberately-deferred event with a real,
documented reason.
