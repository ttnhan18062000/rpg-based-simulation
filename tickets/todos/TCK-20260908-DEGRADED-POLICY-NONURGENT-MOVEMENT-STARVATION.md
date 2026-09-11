---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION
phase: open
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION

## Title
Under RuntimeMode.DEGRADED (ScanPolicy.EXACT_DIRTY), a freshly-spawned entity with a real navigation.target but no AI-driven activity can never become a movement candidate — permanent starvation, not mere throttling

## Status
OPEN

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
- [ ] Real measurement (not reasoning-only) of how often/under what conditions `DEGRADED`/
      `EXACT_DIRTY` triggers in practice, separated as cleanly as possible from debug-instrumentation
      artifacts.
- [ ] Real determination of whether `DEGRADED` mode self-recovers or can persist for a run's
      remainder once triggered.
- [ ] A real disposition decision recorded (accept-and-document vs. scoped fix), with rationale.
- [ ] If accepted as a known consequence: `docs/guidelines/intentional_divergences.md` (or wherever
      the existing wall-clock throttle divergence is recorded) amended to include this consequence
      explicitly, cross-referenced from `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`'s own deferred
      verification note.
- [ ] If a scoped fix is decided: real test evidence the starvation loop is broken, without
      regressing `EXACT_DIRTY`'s own intended compute-budget protection.

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

## Test Summary
_(pending — the full ticket's own real measurement/disposition work has not started; this partial
re-check used a throwaway scratch probe script, not a committed test)_

## Files Changed
_(pending — no code changed by this partial re-check)_

## Completion Summary
_(pending — ticket remains open; only one additional, honestly-scoped data point was added)_
