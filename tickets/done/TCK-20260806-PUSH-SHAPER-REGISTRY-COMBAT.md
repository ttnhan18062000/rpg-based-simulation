---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT
phase: done
date: 2026-08-06
tags: [observability, engine, combat, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT

## Title
Build the apply-layer shaper registry mechanism and implement it for COMBAT (pilot domain), under
FeatureMode.SHADOW

## Status
DONE (reopened once — see Implementation Notes' Reopen Notes for the 2 real bugs
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s shadow comparison found and this ticket fixed:
`entity_killed` false-positive on hazard-caused death, and a missing volumization rule causing
`combat_damage` to over-fire in sustained combat)

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`. Builds the generic shaper
registry mechanism — `{update_type: [Shaper(...)]}`, mirroring `QualityHub.SCORER_REGISTRY`'s
proven shape — and implements it for COMBAT only, as the pilot domain, to prove the pattern before
repeating it for ECONOMY/FACTION in the next child ticket. Wired into `ApplyPath.apply_generation()`
under `FeatureMode.SHADOW`: constructs events from the same tick pass that's already mutating
state, but does not yet deliver them to the live `BoundedObservabilityQueue` — output is
constructed and comparable, not consumed, until `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`
validates it.

**Must land after `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`** (now DONE) —
the shaper reuses that fix's `_real_combat_update`-style discriminant (`attacker_id is not None`,
not a plain `outcome_kind` check — see that ticket's parity ledger entry `INFRA-323` for the full
reasoning, including why an `outcome_kind`-only filter is unsafe).

**Full event-coverage audit completed at the epic level** (see
`staging_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md`'s "Full
event-coverage audit" section) — this ticket's scope is now precise, not exploratory:

| Event | Verdict |
|---|---|
| `combat_initiated`, `combat_damage`, `combat_kill`→`entity_killed`, `near_death_survival` | **MIGRATE** — this ticket's core scope |
| `hazard_drain_applied`, `hero_death_unrecorded` | **DECISION POINT** — migrate alongside (recommended, same code area/pattern) or explicitly defer; this ticket's Investigate phase must decide and document, not silently pick either way |
| `demographic_mortality` (despawn branch) | **DECISION POINT**, lean defer (broader than combat — covers all non-combat death causes too) |
| `combat_resolved`, `attrition_threshold_crossed` | **DEAD** — never emitted by any code path in this repo (confirmed by the epic-level audit); disclose in this ticket's Implementation Notes, do not attempt to implement (there is nothing to migrate) |
| `combat_hard_law_violation` | **OUT OF SCOPE** — separate mechanism (`kernel.py`'s hard-law translation), not part of `event_extractor.py`'s diffing at all |

## Scope
1. Design the shaper interface: a callable/class taking a typed update record (e.g. `CombatUpdate`)
   plus tick/entity context, returning zero or more `SimulationEvent`-shaped constructs (or `None`).
   Keep the interface generic enough that ECONOMY/FACTION shapers (next ticket) can implement it
   without redesigning it.
2. Implement `CombatShaper`: reads `CombatUpdate.attacker_id`/`outcome_kind` using the same
   discriminant as the hotfix's `_real_combat_update()` (attacker_id-primary, outcome_kind
   defense-in-depth), producing the same `combat_damage`/`combat_initiated`/`near_death_survival`/
   `entity_killed` event shapes the current (fixed) extractor produces, so shadow-mode comparison
   in the validation ticket is apples-to-apples.
3. **Decide and document** whether `hazard_drain_applied`/`hero_death_unrecorded` migrate alongside
   COMBAT in this ticket or are explicitly deferred — do not leave this ambiguous or silently
   drop either.
4. **Decide and document** whether `demographic_mortality`'s despawn-branch fix belongs here or is
   deferred to a later phase.
5. **Disclose, do not implement**: `combat_resolved` and `attrition_threshold_crossed` — confirm via
   a fresh grep (do not trust this ticket's citation blindly) that they remain unemitted anywhere,
   then note this as a pre-existing, out-of-migration-scope gap in Implementation Notes.
6. **Design refinement (see epic investigation.md's "Design refinement" section): the dispatch
   point does NOT need to touch `ApplyPath.apply_generation()`/`apply_plan.py` at all.** Every
   migrated COMBAT event can be derived from `prior_state` + `update` alone (both already available
   as `apply_generation()`'s own input parameters, before any state reconstruction). Add the
   registry dispatch as a new call alongside the existing `EventExtractor.extract()` call inside
   `kernel.py`'s `_phase_observability()` (`kernel.py:897+`), reading `prior_state`/`update`
   directly — not `self._state`/`current_state`. Gate it behind `FeatureMode.SHADOW` — confirm the
   exact flag-check mechanism to reuse (new flag vs. `ENABLE_ENHANCED_TRACE_EVENTS`; decide
   explicitly during Investigate, don't assume).
7. In SHADOW mode, log/record shaper output (e.g. to a comparison-only buffer or debug log) without
   pushing to `BoundedObservabilityQueue` — the live queue is untouched by this ticket.
8. Unit tests: the registry mechanism generically (e.g. with a dummy update type/shaper), plus the
   COMBAT shaper specifically (hazard-tagged updates produce no combat event; real combat outcomes
   produce the expected shape; biological damage — same collision risk the hotfix found — also
   excluded).

## Out of Scope
- ECONOMY/FACTION shapers — `TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION`'s scope.
- Removing anything from `event_extractor.py` — the old diffing path stays fully live and
  unmodified; this ticket only adds a parallel, non-delivering shadow path.
- Delivering shaper output to the live queue — that's the cutover ticket's job, after validation.
- Any change to `CombatUpdate`, `combat.py`, or `world_dynamics.py` — this ticket only reads
  already-correct typed records, it doesn't change how they're produced.
- Implementing `combat_resolved`/`attrition_threshold_crossed` — dead code, nothing to migrate;
  wiring them up for real would be new scoring/instrumentation work, a distinct decision from this
  migration.

## Acceptance Criteria
- [ ] Generic shaper registry mechanism implemented, documented with a short design note (interface
      shape, why it mirrors `SCORER_REGISTRY`)
- [ ] `CombatShaper` implemented for all 4 core events, using the hotfix's proven discriminant
- [ ] `hazard_drain_applied`/`hero_death_unrecorded`/`demographic_mortality` decisions made
      explicitly and documented (migrated or deferred, with reasoning — not silently either way)
- [ ] `combat_resolved`/`attrition_threshold_crossed` dead-code status re-confirmed and disclosed,
      not silently ignored
- [ ] Wired into `ApplyPath.apply_generation()` under an explicit SHADOW-mode gate, verified inert
      (no live queue delivery) by a test that asserts the queue is unaffected when the shaper runs
- [ ] Unit tests cover the registry mechanism generically and the COMBAT shaper specifically
- [ ] `event_extractor.py` is untouched by this ticket (confirmed via diff)
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (parent epic)
- TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX (should land first, or this
  ticket's shaper independently applies the same fix — see Request Summary)
- TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION (next child ticket — depends on this one's registry
  design)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §4.8 (`QualityHub.SCORER_REGISTRY` — the
  pattern being mirrored), §5 COMBAT
- `stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/investigation.md`
  Finding 4 (coverage audit establishing COMBAT is push-ready)

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT/` during
implementation.

## Related Code Areas
- `src/engine/kernel.py` (`_phase_observability`, `kernel.py:897+` — new dispatch call site,
  alongside the existing `EventExtractor.extract()` call)
- `src/core/updates.py` (`CombatUpdate` — read only, not modified)
- `src/simulation_quality/quality_hub.py` (`SCORER_REGISTRY` — reference pattern)
- `src/domains/optimization/feature_flags.py` (`FeatureMode.SHADOW`)
- `src/engine/apply.py` (reference only, not modified — confirmed during epic-level investigation
  that `prior_state`+`update` suffice, no hook into apply internals needed)

## Assumptions / Open Questions
- Exact SHADOW-mode gating mechanism (new flag vs. reuse of an existing one) is left to Investigate
  to decide with evidence, not assumed here.
- Whether `REJECTED` combat intents should produce any event is explicitly flagged as a decision
  this ticket must make, not inherit silently from the old extractor's behavior (which never
  checked `outcome_kind` at all).

## Implementation Notes
All 3 decision points from investigation.md were resolved before implementation began: migrate
`hazard_drain_applied`/`hero_death_unrecorded` alongside COMBAT (same typed-record read, physically
colocated); defer `demographic_mortality` (broader than combat); re-confirm
`combat_resolved`/`attrition_threshold_crossed` as dead code via a fresh grep, disclosed not
implemented.

The bigger discovery was architectural: traced `ApplyPath.apply_generation()`/`ApplyPlanBuilder`
directly and found the shaper doesn't need to hook into either at all — `prior_state` + `update`
(both already `apply_generation()`'s own input parameters) carry everything needed
(`CombatUpdate.hp_delta`/`alive_set`/`attacker_id`/`outcome_kind`), so the dispatch point is a new
sibling call inside `Kernel._phase_observability()`, not a patch to the hottest reconstruction
code in the engine. This was verified, not assumed — confirmed via direct trace of both files.

Before finalizing the design, checked every apply-time HP-mutation path in `apply.py` itself (not
just the already-known hazard/biological sources) and found 2 more:
`_compute_entity_changes()`'s passive health-decay branch (lines 93-110) and its level-up
heal/stat-clamp branch (lines 463-495) — both mutate HP without ever touching
`EntityUpdate.combat`, since `changes` is a local dict never written back to the original update
object. Confirmed this doesn't affect event-*type* correctness (both old and new correctly exclude
these via the `attacker_id is not None` check, since neither source sets it), but disclosed a
narrow, real limitation: shaper payload *values* (`damage`/`hp`/`is_lethal`) could diverge from the
old extractor's in the rare case both a real combat hit and one of these apply-time-only mechanisms
land on the same entity in the same tick. Carried forward explicitly into
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s own scope as a named check, not silently absorbed or
ignored.

Also found, while verifying the flag mechanism: `FeatureFlagManager.set_flag_mode()` silently
no-ops for any flag not already registered in `__init__`'s dict — confirmed this doesn't block the
design (the shaper reads `prior_state.feature_flags` directly, bypassing `FeatureFlagManager`
entirely) but registered `ENABLE_PUSH_EVENT_SHAPERS` anyway for documentation consistency, with an
explicit doc note on why it's mechanistically different from the other 11 flags.

Verified via real (non-mocked) kernel runs, not just unit tests: 300 ticks against a generic
fallback scenario (0 shadow events — expected, matches this session's earlier finding that combat
content is absent from generic fixtures) and 500 ticks against the real `dungeon_crawl` world with
`ENABLE_PUSH_EVENT_SHAPERS=SHADOW`, producing genuine non-zero output (2 real combat episodes) with
zero crashes and zero live-queue delivery.

Architecture-Verify surfaced a pre-existing `durable_state_mutation` FAIL in `kernel.py` (9 frozen-
dataclass mutation sites in unrelated hard-law-violation tracking code, lines 549-855). Verified
directly against `git show HEAD:src/engine/kernel.py` that this is byte-identical to the
pre-session committed state — not introduced or worsened by this ticket. Disclosed, not fixed
(distinct, unrelated scope) and not silently ignored.

## Test Summary
`tests/unit/observability/test_event_shapers.py` (new, 14 tests): registry mechanism, all 6
migrated COMBAT events, hazard/biological-damage exclusion (re-verified independently of the
hotfix's own tests — same collision risk, new code path), entity-not-in-prior-state/no-combat-field
edge cases, SHADOW-mode queue-inertness (checked via real import inspection, not a naive substring
match — the first version of this test false-failed on a docstring mention, caught and fixed).
`tests/unit/config/test_phase10_feature_flags.py`: 12/12 pass, unaffected by the new flag.
`tests/unit/kernel/`: 53/53 pass, no regression from the new `_phase_observability` call.
`tests/unit/observability/` full directory: 779 passed, 6 skipped (up from 759 pre-ticket).
Architecture-Verify: `event_shapers.py` and `feature_flags.py` clean; `kernel.py`'s one FAIL
confirmed pre-existing and unrelated (see Implementation Notes).

## Files Changed
- `src/observability/event_shapers.py` (new) — `EventShaper` protocol, `CombatShaper`,
  `SHAPER_REGISTRY`, `run_shadow_shapers()`; reopen fixes: `entity_killed` gated on
  `outcome_kind=="KILL"`, `mode: ObservabilityMode` parameter + volumization rule added
- `src/engine/kernel.py` — new SHADOW-mode dispatch call in `_phase_observability()`; reopen fix:
  `obs_mode` threaded through to `run_shadow_shapers()`
- `src/domains/optimization/feature_flags.py` — `ENABLE_PUSH_EVENT_SHAPERS` added, default OFF
- `tools/calibrate_simq.py` — `ENABLE_PUSH_EVENT_SHAPERS` added to `_KNOWN_FLAGS`
- `tests/unit/observability/test_event_shapers.py` (new, 15 tests post-reopen: 10 original + 5
  from the reopen's fix cycle)
- `docs/guides/feature_flags.md` — flags table updated (11→12), 2 stale count references fixed,
  new flag's distinct mechanism (not `FeatureFlagManager`-routed) documented explicitly
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-324` updated in place with an "UPDATE
  2026-08-06" note documenting the reopen, both bugs, and post-fix re-verification numbers
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-324` entry (P1, verified), schema-validated

## Completion Summary
Built the shaper registry mechanism and piloted it on COMBAT, migrating 6 of the domain's events
(4 core + 2 colocated) to a SHADOW-only apply-layer path, with the 3 remaining events explicitly
deferred or disclosed as dead code rather than silently dropped. The most consequential finding
was architectural: the design doesn't need to touch `apply.py`/`apply_plan.py` at all — verified by
tracing both files directly, not assumed from the epic-level investigation's summary.

**Reopened once**, by `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s real, non-mocked 6-world
comparison against the old diffing extractor — exactly the process this epic was designed to
enforce. Found and fixed 2 real bugs here rather than patching around them downstream: (1)
`entity_killed` false-firing on hazard-caused death, root-caused to conflating
`CombatComponent.alive` (what `alive_set` actually sets) with `LifecycleComponent.active` (what
the event semantically needs) — two different fields governed by different pipeline rules; (2) a
missing volumization rule, a plain omission from the original implementation, causing
`combat_damage` to over-fire in every sustained-combat sequence since the observability default
mode is LIGHT. Both fixes disclosed a narrower, precisely-understood, and — per the validation
ticket's real-corpus measurement — rare (1 in 3,000 world-ticks sampled) limitation in
`entity_killed`'s coverage, rather than silently expanding scope to chase full parity with the old
extractor's broader (any-cause, any-timing) kill-events branch. Post-fix re-verification: 15/15
unit tests, 798/798 in the full observability suite, and 130/131 active ticks matching the old
extractor exactly across the same 6-world real comparison (0 payload-value mismatches). A
pre-existing, unrelated architecture-reviewer finding in `kernel.py` was investigated, confirmed
not caused by this ticket (byte-identical to the pre-session committed state), and disclosed rather
than silently worked around.
