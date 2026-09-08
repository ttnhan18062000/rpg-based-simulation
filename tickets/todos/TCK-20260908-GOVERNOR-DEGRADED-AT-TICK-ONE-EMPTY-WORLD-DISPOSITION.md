---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION
phase: open
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION

## Title
Determine why the adaptive governor enters RuntimeMode.DEGRADED at tick 1 of an essentially empty, trivial-compute kernel

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found during `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s root-cause determination
(a real, uninstrumented per-tick probe of a `campaign_life_arc` episode — no monkeypatching, just
reading `kernel._current_tick_event_count`/`kernel._current_policy` after each real
`ScenarioRuntimeService.step()` call). That episode's world has zero entities throughout (see the
originating ticket's own Implementation Notes for the full trace — unrelated root cause, already
determined). Independent of that: `kernel._current_policy.mode == RuntimeMode.DEGRADED` and
`.scan_policy == ScanPolicy.EXACT_DIRTY` from **tick 1**, the very first tick, before any
meaningful simulation work has had a chance to accumulate real compute pressure.

**Why this is worth its own look, not dismissed as expected**: the adaptive governor's own design
intent (per `docs/architecture/simulation_watchdog.md` and the deferred wall-clock throttle
determinism finding already on record — see
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own citation of it) is to degrade
under *real, accumulated* compute pressure. A kernel with zero entities, on its very first tick,
has essentially nothing to compute — there is no plausible organic load story for `DEGRADED`
triggering that early. Per the base rate this session's own batch has established (dead code and
"suspicious but out of scope" findings have repeatedly turned out to be real, e.g.
`decay_stale_beliefs()`, the raid discard stub, `BiologicalSystem.update()`), this deserves a real
look rather than being waved off as tuning noise.

## Scope
- Trace why `RuntimeMode.DEGRADED` is entered at tick 1 specifically for this
  `ScenarioRuntimeService`-constructed kernel — check the `RuntimeProfile` used by
  `ScenarioRuntimeService._build_kernel()` (`src/engine/scenario_runtime.py:390-400`;
  `max_worker_count=0` in particular looks like a plausible candidate — does the governor read a
  zero worker count as itself a degraded-capacity signal, independent of actual load?) against
  `GovernorPolicy`'s/the adaptive governor's own evaluation logic
  (`src/engine/policy.py`, `src/engine/governor.py`/`src/engine/phase_governor.py`).
- Determine whether this is specific to `ScenarioRuntimeService`'s own `RuntimeProfile`
  construction (i.e. would NOT reproduce via `V2EngineManager`'s own kernel construction, which
  uses a different profile) or a more general governor behavior that would also affect real,
  populated runs through this same entrypoint (Campaign mode, and any other
  `ScenarioRuntimeService` consumer).
- Record a disposition: **confirmed intended** (e.g. `max_worker_count=0` is a deliberate
  single-threaded-mode signal that correctly maps to a conservative policy, not a bug) or
  **confirmed a real mis-trigger** (the governor's tick-1 evaluation has no real signal to act on
  yet and should default to `NORMAL` until it has at least one real measurement).
- Hotfix-tier, disposition-only — do not implement a governor logic change here unless the fix is
  genuinely trivial (e.g. a true off-by-one in a warm-up guard); if it requires real governor
  redesign, re-file as its own standard-tier ticket instead of scope-creeping this one.

## Out of Scope
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own scope (what happens once
  `DEGRADED`/`EXACT_DIRTY` is entered) — this ticket is only about why/when it's entered this
  early, not its own downstream consequences, already covered there.
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own entity-spawn fix — unrelated;
  this governor question is independent of whether the world has entities or not.
- The Kernel wall-clock mid-tick throttle's own general determinism disposition — already a known,
  separately-deferred issue (user said let it sit); this ticket investigates a different, narrower
  question (tick-1 entry specifically), not that issue's own broader disposition.

## Acceptance Criteria
- [ ] A real trace establishes the specific condition that causes `DEGRADED` entry at tick 1 for
      this `RuntimeProfile`/kernel construction.
- [ ] A disposition (confirmed intended / confirmed mis-trigger) is recorded with rationale.
- [ ] If genuinely trivial to fix (a real off-by-one or missing warm-up guard): fixed, with test
      evidence that a fresh kernel starts in `NORMAL` mode and only degrades once real signal
      exists.
- [ ] If not trivial: this ticket closes with the disposition recorded and, if warranted, a new
      standard-tier ticket filed for the real fix — not implemented here.

## Related Tickets
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (origin of this finding)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` (the downstream consequence this
  ticket's own trigger condition feeds into, once entered)

## Related Docs
- `docs/architecture/simulation_watchdog.md` (adaptive governor design intent)

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/engine/scenario_runtime.py` (`ScenarioRuntimeService._build_kernel()`, the `RuntimeProfile`
  construction)
- `src/engine/policy.py` (`GovernorPolicy`, `RuntimeMode`, `ScanPolicy`)
- `src/engine/governor.py`, `src/engine/phase_governor.py` (governor evaluation logic)

## Assumptions / Open Questions
- Whether this reproduces via any other `ScenarioRuntimeService` consumer (not just
  `campaign_life_arc`) is not yet checked — deliberately left for this ticket's own Investigate
  phase.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
