---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-PHASE2
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-CUTOVER-PHASE2

## Precondition confirmed

Read child 7's own Completion Summary directly: GO verdict confirmed.

## Deviation from this ticket's own stated premise

This ticket's own Request Summary claimed "no new flag or default change is needed here — Phase
2's shapers register into the *same* `SHAPER_REGISTRY` and respect the *same* flag." **This was
written before `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` existed** (it was added during
`TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`, specifically *because* reusing the same flag/registry
double-fired). The actual cutover mechanism is: flip `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`'s own
default from `OFF` to `ON` (`src/domains/optimization/feature_flags.py`), mirroring
`ENABLE_PUSH_EVENT_SHAPERS`'s own Phase 1 flip exactly, just on the separate flag Phase 2 actually
uses. Recorded here explicitly as a deviation, not silently substituted.

## Scope item 2-3: flag-gating every Phase 2 branch, checked individually

Added `_push_shapers_phase2_active` (mirroring `_push_shapers_active`'s exact pattern) to
`event_extractor.py`, then went through every one of Phase 2's ~50 event constructions
individually, checking each for a Phase-1-style "broader old-branch scope" complication before
assuming wholesale flag-gating was safe:

- **demographic_mortality/demographic_birth**: co-located with `LifecycleEvent` (despawn/spawn),
  which is NOT a migrated event — guarded only the `SimulationEvent` construction, left
  `LifecycleEvent` unconditional.
- **xp_granted/level_up**: clean, whole `if hasattr(entity, "identity")` block guarded.
- **route_selected through cooperation_event**: clean, but co-located in the SAME `if e_upd_ext is
  not None:` block as the already-guarded (Phase 1) `intent_results` economy loop — guarded only
  the strategy-events portion, left the (separately-flagged) economy loop's own guard untouched.
- **lead_certainty_changed through decision_divergence_detected**: clean, whole block guarded.
- **group_joined/group_expelled, reputation_delta+social_memory_created, contract lifecycle**:
  clean, each guarded individually. The contract-lifecycle block is immediately followed by the
  Quest progress lifecycle block (`QuestEvent`, NOT migrated — separate `quest_system` source,
  out of this epic entirely) — confirmed the block boundary precisely, left Quest logic
  unconditional.
- **skill_unlocked through progression_plateau_detected**: clean, whole block guarded.
- **resource_node_depleted/regenerated/node_recharged**: clean, whole block guarded.
- **ecology_cycle_completed, spawn_cadence_fired, conservation_law_verified**: each is its own
  top-level `if` block — guarded individually.
- **region_trauma_delta through region_transformed**: clean, whole `world_updates` loop guarded.
- **building_sabotaged**: separate loop, guarded independently.
- **calamity_spawned, boss_spawned/narrative_milestone(boss)/raid_party_spawned**: each guarded
  individually.
- **world_emergence_event + narrative_milestone (war/sovereignty variant)**: **the one genuine
  complication found**, matching the ticket's own warning. These live in the SAME
  `world_events_add` loop as Phase 1's already-guarded `war_declared`/`military_conflict_resolved`
  if/elif (`ENABLE_PUSH_EVENT_SHAPERS`, a *different* flag). Only the `world_emergence_event` +
  `narrative_milestone` construction was wrapped in its own `if not
  _push_shapers_phase2_active:`, leaving Phase 1's own independent guard on the war/military
  if/elif completely untouched — the two guards now coexist in the same loop, each gating a
  disjoint set of constructs on its own flag.
- **faction_extinct**: clean, whole block guarded.

Every event verified individually, none assumed clean without checking — exactly one genuine
co-location complication found (`world_emergence_event`/`narrative_milestone` sharing a loop with
Phase 1's own guard), handled without disturbing the existing Phase 1 guard.

## Real bug found and fixed via real-kernel verification (post-cutover default check)

After flipping `feature_flags.py`'s default and flag-gating `event_extractor.py`, ran the same
5-world event-stream check with **no explicit flag override** (the real, default post-cutover
state) to confirm delivery matches child 7's SHADOW-validated baseline. Found: **every world
showed `event_extractor=0` (correctly suppressed) AND `event_shapers=0` (nothing delivered
either)** — a total blackout, not the expected live-delivery state.

Root cause: `src/observability/event_shapers.py`'s own `run_shadow_shapers()` function reads
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` with its **own, separate, hardcoded default of `"OFF"`**
(`event_shapers.py:1473`, written during `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`, correctly
`"OFF"` at that time since Phase 2 wasn't cut over yet). This ticket only updated
`feature_flags.py`'s default and `event_extractor.py`'s own default read
(`_push_shapers_phase2_active`) — but never updated `run_shadow_shapers()`'s own independent
default, since that file wasn't in this ticket's initial mental model of "where the flag is read."
With the extractor's branches now correctly suppressed (reading the new `"ON"` default) but the
shaper registry still defaulting to not deliver (reading its own stale `"OFF"` default), the two
defaults fell out of lockstep, producing a total blackout for every Phase 2 event with no explicit
override — exactly the kind of gap this epic's own governing instruction ("make sure the new push
is not missing any existing defined event") exists to catch.

**Fix**: updated `run_shadow_shapers()`'s own default from `"OFF"` to `"ON"`, with an explicit
comment noting the two defaults (`event_extractor.py`'s and `event_shapers.py`'s) must stay in
lockstep — a coupling this codebase's own architecture doesn't enforce structurally (two
independent reads of the same flag string, in two different files), so it can only be caught by
verification, not the type system.

**Verified the fix directly**: re-ran the same 5-world default-state check. All 5 worlds now show
`event_extractor=0` (no leak) and real, non-zero `event_shapers` delivery counts (43-845 depending
on world activity level). Verified the rollback path too: explicit
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF` on `hero_guild_routing` restores `event_extractor=911`
delivery (old path), confirming genuine, working rollback.

## Full scoped pytest run — 2 pre-existing, unrelated failures found and disclosed

Running the full `tests/perf/` suite (beyond just `test_simq_isolation_overhead.py`) surfaced 2
failures not previously encountered in this epic's narrower test scopes:

- `test_observability_scale_validation.py::test_scale_performance_and_footprint` — places all 100
  test entities at the identical `(10.0, 10.0)` coordinate, triggering a genuine
  `LAW-SPAWN-OCCUPANCY` hard-law violation, which then fails the test's own
  zero-telemetry-accumulation assertion. Confirmed pre-existing (the file's only commit predates
  this session by a large margin) and unrelated to observability event-shaping — the violation
  comes from spatial-placement law-checking, a code path this epic never touches.
- `test_profiler_integrity.py::test_recorded_tick_compute_includes_all_phases` — errors only when
  run immediately after the above test in the same session; passes standalone. A test-isolation
  artifact of the same pre-existing failure, not an independent second bug.

Filed `TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG` rather than silently absorbing or
ignoring these — same discipline as Child 2's pre-existing test finding.

One test needed updating (not a bug, expected): `test_event_shapers_strategy.py`'s own
`test_run_shadow_shapers_default_off_excludes_phase2_events` tested the PRE-cutover default
(events excluded by default) — now stale by design, since this ticket's whole point is flipping
that default. Renamed to `test_run_shadow_shapers_default_includes_phase2_events` (asserting the
new, correct default behavior) and added a new
`test_run_shadow_shapers_explicit_off_excludes_phase2_events` (verifying the rollback path
explicitly, which the old test never covered).

## Full calibration corpus — 37/69 grade-regression failures found, root-caused as `INFRA-273`

`make simq-full-audit-full` (79 scenarios) run post-cutover. `test_grade_regression.py` showed
**37 failed, 32 passed, 18 deselected** — up from Phase 1's own cutover result (32/69 failures,
`hero_guild_routing_seed42_500t`-class COMBAT/ECONOMY/FACTION zeroing). Not silently waved
through, per this repo's rule against treating a failing gate as an obstacle to route around.

Two of the newly-failing tests are novel to this cutover's own scope —
`test_urban_political_selfmodel_cognition_isolated_grade_anchor` and
`test_urban_political_selfmodel_execution_isolated_grade_anchor`, both isolated single-profile
grade-anchor probes (not part of the 79-scenario corpus loop) — showing score-tolerance drift on
COMBAT, PROGRESSION, and SOCIAL. These pillars are directly touched by this cutover (PROGRESSION,
SOCIAL now live-delivered via Phase 2 shapers), so they needed a real differential-repro before
concluding anything, not an assumption either way.

**Decisive confirming experiment** (same methodology as Phase 1's own `INFRA-273` confirmation):
drove the kernel directly for `urban_political_selfmodel_probe_seed42_200t` twice — once with
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` forced `OFF` (bypassing `calibrate_simq.py`'s own flag-parser,
which — like Phase 1's own investigation found for its flag — only recognizes `ON`/`STRICT`/
`SHADOW`, not `OFF`; drove the kernel directly with an explicit `feature_flags` dict instead),
once with it forced `ON`. Results:

| Pillar | OFF | ON |
|---|---|---|
| COMBAT | grade=C norm=+0.0000 events=0 | grade=C norm=+0.0000 events=0 |
| PROGRESSION | grade=C norm=-0.1569 events=1 | grade=C norm=-0.1569 events=1 (identical to 4 decimals) |
| SOCIAL | grade=S norm=+7.3500 events=715 | grade=S norm=+6.8550 events=704 (same grade, small variance) |

`COMBAT` and `PROGRESSION` are byte-identical between the two pipelines — proving their drift is
not attributable to this cutover at all. `SOCIAL` shows a small (~1.5%) event-count variance
(715 vs 704) with the same letter grade in both — consistent with the same tick-budget-watchdog
mechanism (`WatchdogTrip` CRITICAL alerts fired in **both** runs, confirmed in the raw log, not
assumed) rather than a shaper-vs-extractor correctness difference. This is the identical
conclusion shape as Phase 1's own `INFRA-273` confirming experiment: same mechanism, now visible
on a wider set of pillars because Phase 2 widened live delivery to AGENCY/COGNITION/INFORMATION/
PROGRESSION/WORLD/SOCIAL — `INFRA-273`'s own pre-existing documentation already named
SOCIAL/PROGRESSION (among others) as susceptible pillars, predating this epic by three weeks.

**Conclusion**: the 5 additional failures beyond Phase 1's 32 (37 total) are the same
pre-existing `INFRA-273` tick-budget-watchdog mechanism, not a Phase 2 regression. `grade_anchors
.json` left unrecalibrated, per this ticket's own Scope Guard (recalibrating against a
pre-existing, unrelated infrastructure issue would silently mask it under this cutover's commit).
See `docs/parity_ledger/infrastructure.yaml`'s `INFRA-273` entry and `docs/audits/
D20_simq_quality_status_review.md`'s Finding 13 for the recorded outcome.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-247` updated in place to note the
  cutover to live delivery.
- `docs/parity_ledger/progression.yaml` — `PROG-117` updated in place to note the cutover to
  live delivery.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-115` updated in place to note the cutover to
  live delivery.
- `docs/parity_ledger/social_narrative.yaml` — `SOC-239`/`SOC-240` updated in place to note the
  cutover to live delivery.
- `docs/parity_ledger/town_resource.yaml` — `TOWN-190` updated in place (third update) to note
  the cutover to live delivery.
- `docs/parity_ledger/faction.yaml` — `FAC-013` updated in place (third update) to note the
  cutover to live delivery.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-326` entry for this cutover's own finding
  (the `run_shadow_shapers()` default-lockstep bug), plus `INFRA-273` updated in place with this
  ticket's own confirming differential-repro experiment.
- `docs/audits/D20_simq_quality_status_review.md` — Finding 13, epic completion.

## Parity Ledger Overlap

All files listed above — each already has a SHADOW-mode entry from its own build child; this
ticket updates each in place to note the cutover, not duplicating.

## Prior Work

- `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (Phase 1, DONE) — the exact
  deployment-mechanism pattern this ticket repeats.
- `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2` (child 7, DONE) — the GO verdict and
  `INFRA-273` awareness this ticket builds on.

## Risks and Open Questions

None left open.

## Anti-Drift Hazards

- The two independent flag-default reads (`event_extractor.py`'s `_push_shapers_phase2_active`
  and `event_shapers.py`'s `run_shadow_shapers()` own read) are NOT structurally coupled — any
  future change to one without the other will silently reintroduce either a double-fire or a
  blackout. Both now carry an explicit comment cross-referencing the other, but this is a
  documentation-level safeguard, not an enforced invariant. Worth flagging for a future Phase 3+
  cutover to check explicitly, not assume fixed by precedent alone.
