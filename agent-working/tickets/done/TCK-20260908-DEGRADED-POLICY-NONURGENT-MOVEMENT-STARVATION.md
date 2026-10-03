---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION

## Title
Under RuntimeMode.DEGRADED (ScanPolicy.EXACT_DIRTY), a freshly-spawned entity with a real navigation.target but no AI-driven activity can never become a movement candidate — permanent starvation, not mere throttling

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while writing a real-Kernel-run regression test for `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`
(that ticket's own spawned raiders never moved toward their target in a real multi-tick run,
despite every movement-system component — `NavigationSystem.get_next_step()`,
`LegalityServiceV2.verify_movement_legality()`, `MovementSystem.resolve_move()` — working correctly
in isolation). Independently traced by the orchestrating session, independently re-verified by peer
review (`rpg-feature-planning`) before filing, per the user's standing rule that a real observed
issue gets a ticket rather than a note.

**Root-caused, confirmed via direct phase-graph tracing (this is NOT
`TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`'s gap)**:
`movement_routing`'s own `should_run_phase()` check returns `True` unconditionally in every traced
tick (`update.dirty_set is None` at that point in `refine()`'s sequence, so that gate never applies
to this path) — the phase genuinely runs every tick. The real cause is the adaptive governor's own
policy: once the world enters `RuntimeMode.DEGRADED` (`src/engine/policy.py`,
`GovernorPolicy.mode`), `PhaseBudgets.scan_policy` becomes `ScanPolicy.EXACT_DIRTY`.
`MovementCandidateSelector.select()` (`src/engine/candidate_selector.py:138-140`) has:

```python
if mode == MovementMode.WANDER: ...  # (separate, unrelated cadence gate for non-degraded policy)
...
if scan_policy == ScanPolicy.EXACT_DIRTY:
    # Under heavy degraded mode, skip non-urgent moves entirely
    continue
```

Candidacy under any policy requires one of 5 urgency conditions (`candidate_selector.py:128-133`):
`target_changed` (requires a fresh `EntityUpdate` setting `navigation.target_set` THIS tick),
`is_dirty` (requires membership in `dirty_set.movement_entities`, which itself requires having
already moved or received an update), `tile_blocked`, `interaction_req`, or `strategic_req`. A
freshly-spawned entity with a static `navigation.target` baked in at construction (not set via a
per-tick `EntityUpdate`) and no active AI goal, interaction, or strategic project satisfies **none**
of these — and critically, it can only ever satisfy them **by moving or being flagged dirty**,
which itself requires being selected as a candidate first. **This is a genuine starvation loop, not
mere throttling**: while `EXACT_DIRTY` holds, such an entity has no path — by any action available
to it — to ever become urgent and escape exclusion. Confirmed via direct reproduction: 3 spawned
`goblin_raider` entities, real `navigation.target` set at spawn, zero net position change across 30
real ticks once `EXACT_DIRTY` engaged.

**Newly-observed consequence of an already-known, deliberately-deferred issue** — not a new root
cause. `RuntimeMode.DEGRADED` is triggered by the Kernel's wall-clock mid-tick throttle
(`src/engine/kernel.py`'s `_phase_resolution()`, `should_throttle = not self._audit_mode and
elapsed > hard_cap`), already confirmed and recorded as a real determinism-breaking issue under
`audit_mode=False` in a prior investigation (previously recorded as "non-deterministic state," the
user having said to let it sit). What's new here is the observed blast radius: it was recorded as
state divergence between runs, not as "a spawned entity with no active AI goal can permanently stop
moving for the remainder of a degraded run, on some hardware/timing and not others, with the same
seed." That is a substantially more visible and gameplay-legible consequence than what is currently
on record for that deferred issue.

**Honest uncertainty, stated plainly**: the orchestrating session could not fully separate whether
`DEGRADED` entry in its own reproduction was genuine compute pressure from the real simulation, or
partly inflated by its own heavy Python-level debug instrumentation (monkeypatching several phases,
printing every tick) slowing ticks down. Budget-exceeded warnings appeared even in an
un-instrumented first reproduction, so it is at least partly real, but the exact split is not
established. This uncertainty is part of the finding, not a gap in it — resolving it (or not) is
this ticket's own job, not assumed here.

## Scope
**Investigation-first, per the deferred wall-clock-throttle issue's own precedent — do not implement
a fix without a real decision on the disposition.**

- Determine how often, and under what real (non-debug-instrumented) conditions, `RuntimeMode.
  DEGRADED`/`ScanPolicy.EXACT_DIRTY` is actually entered in practice — a real calibration/long-run
  measurement, not reasoning from a debug-instrumented reproduction alone.
- Determine whether `DEGRADED` mode, once entered, is self-recovering (the governor eases back to a
  less restrictive policy once compute pressure subsides) or can persist for the remainder of a run
  once triggered — this materially changes how bad the starvation consequence is in practice.
- Confirm the exact set of entity classes vulnerable to this permanent-starvation pattern (any
  entity whose only path to urgency requires an action it cannot take without first being a
  candidate) versus entity classes that can naturally escape (e.g., an entity already engaged in
  combat/interaction, or one that receives external `EntityUpdate`s from other systems).
- Record a real disposition decision: (a) accept as a known, documented consequence of the already-
  deferred wall-clock throttle issue (a divergence-note amendment, not a code fix — matching that
  issue's own "let it sit" disposition), or (b) a real, scoped fix (e.g., excluding freshly-spawned
  entities with a static target from `EXACT_DIRTY`'s non-urgent skip for at least one tick after
  spawn, or a different urgency condition covering this case) — per standing user direction, fix
  only if this is a hard failure, not a performance-tuning exercise; if the fix shape is
  performance-adjacent rather than correctness-adjacent, route it to the planned performance effort
  instead of fixing here.

## Out of Scope
- The wall-clock mid-tick throttle itself (`kernel.py`'s `_phase_resolution()`) — already a known,
  separately-deferred issue; this ticket only extends its recorded consequences, does not re-open
  its own disposition.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`'s own spawn/targeting correctness — already proven and
  closed independently of this finding.
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` — confirmed via direct tracing to
  be a different mechanism (`should_run_phase()` returns `True` unconditionally for this path); do
  not conflate the two.

## Acceptance Criteria
- [x] Real measurement (not reasoning-only) of how often/under what conditions `DEGRADED`/
      `EXACT_DIRTY` triggers in practice, separated as cleanly as possible from debug-instrumentation
      artifacts. Three real, uninstrumented measurements recorded in Implementation Notes: the
      original finding no longer reproduces post-sentinel-fix; the mechanism is real and
      independently reproducible under genuine sustained load, isolated from any fresh spawn
      injected while DEGRADED was already confirmed active via a real watchdog trip.
- [x] Real determination of whether `DEGRADED` mode self-recovers or can persist for a run's
      remainder once triggered. Under sustained ever-growing real load specifically, did not
      recover within the tested window (escalated to SURVIVAL); general self-recovery under a
      transient load spike was not separately tested (stated honestly, not resolved here).
- [x] A real disposition decision recorded: scoped fix, per the standing user rule (an entity that
      can never re-enter candidacy by any action available to it is a logic defect, not
      performance-tuning).
- [x] Cross-referenced into the deferred wall-clock-throttle determinism issue's own code sites
      (no single canonical doc/ticket found for it on search -- see Implementation Notes) --
      `governor.py`'s `tick_compute_ms` DEGRADED trigger and `kernel.py`'s `_phase_resolution()`
      mid-tick `should_throttle` both now cross-reference this ticket directly in-code.
- [x] Scoped fix implemented: `MovementCandidateSelector`'s `EXACT_DIRTY` branch grants
      reduced-cadence candidacy (not full re-admission) keyed on the real, general condition -- an
      unreached navigation target -- rather than a spawn-time special case, per
      `rpg-feature-planning`'s explicit correction of the first-proposed shape. Real test evidence
      the starvation loop is broken (unit + real-Kernel regression + the exact 300-entity
      acceptance-bar re-measurement), without regressing `EXACT_DIRTY`'s own work-shedding purpose
      (bounded-fraction-per-tick admission, verified directly).

## Related Tickets
- TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX (origin of this finding; its own real-run movement
  verification is deferred to this ticket)
- TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION (a different, already-ruled-out
  mechanism for the same symptom class — confirmed not the cause here)
- TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION — **shared-root-cause hypothesis tested
  and RULED OUT for that specific ticket (2026-09-08)**, without weakening this ticket's own
  standing evidence. A real, uninstrumented per-tick probe of a `campaign_life_arc` episode
  confirmed `governor_mode=DEGRADED`/`scan_policy=EXACT_DIRTY` from tick 1 onward (the mechanism
  this ticket investigates is real and present there) — but that episode's world has **zero
  entities** throughout (`CampaignOrchestrator._build_initial_state()` never spawns any; see that
  ticket's own Implementation Notes). With nothing alive to select as a movement candidate,
  `EXACT_DIRTY`'s non-urgent-exclusion mechanism cannot be what silenced that specific run — the
  real cause there is upstream (no entities ever exist), not this ticket's own starvation
  mechanism. **This does not disprove or weaken this ticket's own findings** — the real,
  reproduced starvation (3 spawned `goblin_raider` entities, real `navigation.target`, zero net
  position change across 30 real ticks once `EXACT_DIRTY` engaged, from
  `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`) is separate, real evidence on its own and stands
  unaffected; it simply isn't what killed `campaign_life_arc` specifically. Keep the two findings
  distinct — one confirmed-real mechanism (this ticket) and one confirmed-different root cause for
  a specific symptom that briefly looked like it might share the same cause (the campaign ticket).

## Related Docs
- Wherever the existing Kernel wall-clock mid-tick throttle determinism finding is recorded
  (project memory references `kernel.py:585-596`'s `_phase_resolution()` throttle as a confirmed,
  deliberately-deferred determinism issue under `audit_mode=False`) — locate and cross-reference
  during Investigate rather than assumed here.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/engine/candidate_selector.py` (`MovementCandidateSelector.select()`, the exclusion logic)
- `src/engine/policy.py` (`GovernorPolicy`, `RuntimeMode`, `PhaseBudgets`, `ScanPolicy`)
- `src/engine/governor.py`, `src/engine/phase_governor.py` (where `RuntimeMode.DEGRADED` gets
  entered/exited)
- `src/engine/kernel.py` (`_phase_resolution()`'s wall-clock throttle — the upstream trigger)

## Assumptions / Open Questions
- Whether `DEGRADED` mode is self-recovering is not yet established — left for this ticket's own
  Investigate phase, not assumed here.
- The genuine-pressure-vs-instrumentation-artifact split for the specific reproduction that
  surfaced this is not resolved — stated as an open uncertainty per the Request Summary, not
  something this filing resolves.

## Implementation Notes
_(pending — full disposition work not yet picked up; this ticket's own AC list remains open)_

**Partial re-check only (2026-09-11, Batch A triage, per `rpg-feature-planning`): a real,
non-raider scenario does NOT show this ticket's specific starvation pattern — recorded honestly as
a genuine negative data point, not evidence the mechanism itself is safe or fixed.** Ran a real,
uninstrumented 40-tick `campaign_life_arc`-shaped episode (same construction pattern as the sibling
`GOVERNOR-DEGRADED-AT-TICK-ONE` re-check, real `Kernel` ticks, no monkeypatching) with the now-real
16-entity world. Confirmed `scan_policy == ScanPolicy.EXACT_DIRTY` active throughout (per the
sibling governor ticket's own finding — this is now known to be a general mis-trigger, not organic
pressure, but the `EXACT_DIRTY` gate itself is real and active regardless of why). Tracked every
entity's `navigation.position` from spawn to tick 40: **all 16/16 entities had moved from their
initial (scattered) position by tick 40** — zero entities showed the permanent zero-net-movement
pattern the original `goblin_raider` reproduction found.

**This does not weaken the original raider evidence, and should not be read as "the starvation
mechanism doesn't exist."** The likely reason it didn't reproduce here: this ticket's own precondition
is narrow — "a freshly-spawned entity with a real `navigation.target` baked in at construction but
no active AI goal, interaction, or strategic project." The `goblin_raider` reproduction specifically
constructed entities matching that exact profile. This campaign scenario's real, catalog-spawned
entities (via `CatalogScenarioStateBuilder`/`WorldEntitySpawner`) were not checked for whether they
match that same precondition at spawn — plausibly they don't (no baked-in static
`navigation.target`, and/or they pick up a real strategic project or interaction quickly through
normal cognition/goal-scoring, satisfying `strategic_req`/`interaction_req` before ever needing pure
non-urgent movement candidacy). **This was not verified either way** — a real, disclosed gap in this
particular check, not glossed over. A genuine second confirmation would need an entity that matches
the raider ticket's own exact precondition within a non-raider scenario, which this check did not
specifically construct or verify for.

**Honest summary of what this check does and doesn't establish:**
- Does NOT reproduce the pattern in this real campaign scenario — a real, if narrower-scope-than-
  hoped, data point.
- Does NOT invalidate the raider evidence, which stands independently and is unaffected.
- Does NOT establish that campaign-spawned entities are immune to the starvation mechanism — only
  that none of them happened to be in the exact vulnerable state (no active goal + a baked-in
  static target) during this one 40-tick run at this seed.
- This ticket's own full AC list (real measurement of DEGRADED frequency in practice, self-recovery
  determination, disposition decision, possible fix/documentation) remains entirely unaddressed —
  left OPEN, not closed by this partial check.

**Full re-check (2026-09-13, per `rpg-feature-planning`, re-measured against the now-fixed
`TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER` sentinel): the exact original
precondition no longer reproduces under normal conditions, AND the underlying mechanism is
independently confirmed real under genuine sustained load. Both halves measured, not reasoned.**

**Measurement 1 — exact original precondition, real production Kernel config, current (fixed)
code.** Rebuilt the raider repro faithfully: `RaidService.spawn_raid()` (real production
construction, `src/world/raid.py`), 3 `goblin_raider` entities with static `navigation.target`
baked in at spawn, no AI goal, run against the real Kernel config `ScenarioRuntime._build_kernel()`
actually uses in production (`src/engine/scenario_runtime.py:400-410` — `max_worker_count=0`,
`max_tick_budget_ms=200.0`; this is the exact condition that triggered the now-fixed
worker-utilization sentinel, and is very likely — though not directly confirmed, the original
reproducer's own script was not preserved — what the original reproduction ran under, since it is
the only real production Kernel-construction site using `max_worker_count=0`). 30 real,
uninstrumented ticks: **0/30 ticks entered DEGRADED**; all 3 raiders moved toward target every
tick. The specific reproduction that motivated this ticket does not reproduce anymore. Consistent
with `rpg-feature-planning`'s own prediction.

**Measurement 2 — genuine sustained load, same real Kernel config, no mocking.** Confirmed the
starvation mechanism is not merely dead now — it is real, and still reachable under real (not
sentinel-driven) pressure. Built a real 300-entity world (20 real raid waves via the same
`RaidService.spawn_raid()`), same production Kernel config. Real, uninstrumented ticks: DEGRADED
engaged at tick 23 (`tick_compute_ms` genuinely exceeded the 200ms budget — confirmed via the
Kernel's own real watchdog alert, `compute_ms: 214-343ms` across the DEGRADED/SURVIVAL window, with
real per-phase costs attached, not a forced/mocked signal), then escalated to SURVIVAL by the
following few ticks and did not recover within the tested window. A wave of 15 raiders spawned
*before* DEGRADED engaged (and thus already carrying `is_dirty`/movement history from earlier
NORMAL/CONSTRAINED ticks) all kept moving fine even while DEGRADED was active — confirming the
precondition really is "freshly spawned, zero prior dirty-set membership," not "spawned recently."

**Measurement 3 — the decisive one: a genuinely fresh spawn injected mid-run, while the Kernel was
already confirmed in real DEGRADED.** Once real DEGRADED was confirmed active (measurement 2, tick
23), injected 5 more real `goblin_raider` entities (same `RaidService.spawn_raid()` construction,
static target, zero prior ticks) directly into the live Kernel state between `tick_once()` calls.
Result: **5/5 permanently stuck — zero net movement across all 15 subsequent ticks**, while the
Kernel stayed in DEGRADED/SURVIVAL the entire window. This is the exact starvation pattern the
ticket describes, reproduced under real, uninstrumented, non-mocked sustained-load conditions —
independent of the worker-utilization sentinel bug entirely.

**Disposition evidence, not yet a decision — recorded here, sent to peer review for the actual
call:**
- The specific finding that motivated filing this ticket (3 raiders under `max_worker_count=0`)
  was very likely a symptom of the (now-fixed) worker-utilization sentinel bug, not organic
  compute pressure — it no longer reproduces.
- The underlying mechanism is real and independently reproducible under genuine sustained load —
  not dead code, not only a sentinel artifact. Matches `rpg-feature-planning`'s own predicted
  framing exactly: "a real mechanism that only bites under genuine sustained load — a much
  narrower ticket than the one filed."
- Self-recovery: not observed to recover within the tested window once entered under sustained
  load in this specific ever-increasing-load stress scenario (300 entities, growing dirty sets)
  — this does not establish general self-recovery behavior for a transient load spike specifically,
  which was not separately tested.
- This is genuinely an extension of the already-deferred wall-clock-throttle issue's own blast
  radius (the real trigger in measurement 2/3 is `tick_compute_ms >= max_tick_budget_ms`, the same
  mechanism as the deferred determinism finding), but the CONSEQUENCE (permanent, unrecoverable
  starvation of a specific entity class, not mere slowdown or state divergence) is a distinct,
  concretely-reproduced failure mode worth its own disposition call, not silently folded into the
  deferred issue's existing "let it sit."

**Disposition (2026-09-13, per `rpg-feature-planning`): scoped fix, and reshaped.** Peer's own
correction-vs-performance framing settled it: degradation means "moves less often," not "moves
never" -- an entity that can never re-enter candidacy by any action available to it is a logic
defect in the policy, not the performance pressure that triggers it, matching the standing user
rule ("fix only if hard failure, not perf-tuning").

Peer explicitly rejected my first-instinct shape ("one guaranteed candidacy tick for
freshly-spawned entities") as a workaround shaped like a fix: every urgency condition in
`select()` is change-driven, so the real defect is general (any entity whose target/state never
changes), not spawn-time-specific. Peer also flagged the real constraint I hadn't weighed: full
re-admission of every entity with an unreached target would, under real load where most entities
plausibly have one, re-admit nearly everything and defeat `EXACT_DIRTY`'s own work-shedding
purpose -- trading a starvation bug for a performance regression on a system already exceeding its
tick budget.

**Implemented: reduced-cadence candidacy**, keyed on the real, already-established condition (an
unreached navigation target) rather than a spawn-time special case.
`MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO = 20`
(`src/engine/candidate_selector.py`): under `EXACT_DIRTY`, an otherwise-non-urgent entity with a
real target is admitted on `(state.tick + entity_id) % 20 == 0` instead of never. The real
readiness/move-cost gameplay gate (previously only reachable for non-`EXACT_DIRTY` policies) was
moved earlier so it applies uniformly and isn't bypassed by the new branch. The 5 existing urgency
conditions are entirely untouched -- a genuinely urgent entity is still selected every tick.

**Acceptance-bar verification, both halves required by peer, both confirmed:** re-ran the exact
300-entity sustained-load scenario from measurement 2/3 with the fix applied. Fresh raiders
injected mid-run, after DEGRADED was independently confirmed active: **5/5 now show real movement**
within the 15-tick post-injection window (each moved once, at a different tick matching its own
`entity_id`-based cadence offset -- not simultaneously, confirming the bounded-fraction admission
is real, not a full re-admission in disguise). DEGRADED stayed engaged throughout the same window
(real `tick_compute_ms` continued exceeding budget every tick, real watchdog alerts present) -- the
fix did not neutralize the governor.

**Folded the relationship into the deferred wall-clock-throttle issue's own record.** Searched for
a dedicated ticket/doc first (Context Scan order, per standing instruction) -- found none; the
closest committed trace is a structurally related but distinct F6 finding in
`docs/parity_ledger/infrastructure.yaml` (grade-anchor load-sensitivity under sustained
calibration-sweep load, not this specific movement-candidacy mechanism). The "user said let it
sit" record for the exact `kernel.py:585-596` mechanism appears to be an informal, session-only
finding with no committed doc/ticket home. Given no single canonical file to edit, added direct
cross-reference comments at both real code sites that force `RuntimeMode.DEGRADED` from wall-clock
pressure -- `governor.py`'s `tick_compute_ms` check (the confirmed real driver in this ticket's own
measurements) and `kernel.py`'s `_phase_resolution()` mid-tick `should_throttle` abort (which also
directly calls `force_mode(RuntimeMode.DEGRADED, ...)`, confirmed via direct read to be a second,
structurally separate path to the same mode) -- so a future reader revisiting either sees that
their consequences reach movement candidacy, not only tick timing.

Also strengthened `tests/integration/world/test_camp_raid_targeting.py` (the real-Kernel test that
originally surfaced this ticket): its docstring previously asserted, as settled fact, that raiders
could never move under `EXACT_DIRTY` -- now corrected to past tense with a pointer to this fix, and
the test itself extended to run a full reduced-cadence window past raid spawn and assert real
movement, proving the fix in the exact scenario that found the bug.

## Test Summary
Real, uninstrumented scratch measurement scripts (`remeasure_degraded_starvation.py`,
`remeasure_degraded_starvation_under_load.py`, `remeasure_fresh_spawn_during_real_degraded.py`,
re-run post-fix) -- not committed as tests (single-purpose acceptance-bar verification per peer's
own request, reproducible from the scripts' own construction pattern, documented here rather than
duplicated as committed test code).

Committed test evidence:
- `tests/unit/domains/optimization/test_movement_candidate_selector.py` -- 5 new tests covering
  the reduced-cadence fix in isolation: off-cadence exclusion, on-cadence admission, the readiness
  gate still applying, genuinely-urgent entities unaffected, and a 200-entity bounded-fraction
  proof (only the cadence-eligible subset admitted, not all 200).
- `tests/integration/world/test_camp_raid_targeting.py` -- extended with a real-Kernel post-spawn
  tick run proving eventual movement in the exact scenario that surfaced this ticket.

`pytest tests/unit/kernel/ tests/unit/resource/ tests/unit/domains/optimization/
tests/integration/world/test_camp_raid_targeting.py tests/integration/kernel/ -q -m "not slow and
not extra_slow"`: 384 passed, 1 skipped, 3 deselected -- no regression.

## Files Changed
- `src/engine/candidate_selector.py` -- `MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO`
  constant added; `select()`'s `EXACT_DIRTY` branch changed from unconditional non-urgent
  exclusion to reduced-cadence admission; the readiness/move-cost gate moved earlier so it applies
  uniformly across scan policies.
- `src/engine/governor.py` -- comment added at the `tick_compute_ms` DEGRADED trigger,
  cross-referencing this ticket's fix and the related `kernel.py` mechanism.
- `src/engine/kernel.py` -- comment added at `_phase_resolution()`'s mid-tick `should_throttle`
  `force_mode(DEGRADED)` call, cross-referencing this ticket and the `governor.py` mechanism.
- `tests/unit/domains/optimization/test_movement_candidate_selector.py` -- 5 new tests (see Test
  Summary).
- `tests/integration/world/test_camp_raid_targeting.py` -- docstring corrected from present-tense
  "can never move" to past-tense with a fix pointer; test extended to assert real post-spawn
  movement over a full reduced-cadence window.

## Completion Summary
Re-measured against the fixed worker-utilization sentinel per peer's explicit instruction: the
original finding no longer reproduces (0/30 DEGRADED ticks, exact original precondition), but the
underlying mechanism is real and independently confirmed under genuine sustained load (a fresh
spawn injected mid-run, after DEGRADED was already confirmed active via a real watchdog trip,
stayed permanently stuck pre-fix). Peer's prediction -- "a real mechanism that only bites under
genuine sustained load, a much narrower ticket than filed" -- was confirmed both ways by
measurement, not assumed.

Disposition: scoped fix, per the standing user rule distinguishing a genuine logic defect
(permanent, unescapable exclusion) from performance-tuning (throttled-but-eventual movement).
Peer corrected the first-proposed fix shape twice: rejected a spawn-time-only exemption as too
narrow for the general defect, and flagged that full re-admission would defeat `EXACT_DIRTY`'s own
work-shedding purpose under real load. Implemented reduced-cadence candidacy instead, keyed on the
real condition (an unreached navigation target). Verified against peer's own explicit acceptance
bar (both required, both confirmed): injected raiders eventually move, and DEGRADED stays engaged
with `tick_compute_ms` still bounded -- the governor was not neutralized.

Folded the relationship into the deferred wall-clock-throttle issue's own record via direct
in-code cross-references at both real `RuntimeMode.DEGRADED`-forcing sites, since no single
canonical doc/ticket for that deferred issue was found on search. No known material gap left
unstated: general self-recovery under a transient (non-sustained) load spike was not separately
tested, and is stated as such rather than assumed.
