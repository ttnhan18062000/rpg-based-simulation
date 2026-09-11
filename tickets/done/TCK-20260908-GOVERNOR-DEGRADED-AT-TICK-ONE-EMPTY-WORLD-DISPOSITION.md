---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION

## Title
Determine why the adaptive governor enters RuntimeMode.DEGRADED at tick 1 of an essentially empty, trivial-compute kernel

## Status
DONE

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
- [x] A real trace establishes the specific condition that causes `DEGRADED` entry at tick 1 for
      this `RuntimeProfile`/kernel construction. **Found**: `WorkerManager.get_stats()`
      (`src/engine/worker_manager.py:229-232`) sets `worker_utilization = 1.0` unconditionally
      whenever `max_workers <= 0` (the division-by-zero guard's fallback value). `ScenarioRuntimeService.
      _build_kernel()` constructs its `RuntimeProfile` with `max_worker_count=0`. `ResourceGovernor.
      _get_indicated_mode()` (`src/engine/governor.py:87`) reads `worker_utilization >= 0.9` as a
      `DEGRADED` trigger — `1.0` trivially satisfies this on every tick regardless of real load.
- [x] A disposition (confirmed intended / confirmed mis-trigger) is recorded with rationale.
      **Confirmed mis-trigger, not intended.** `peak_active` is always `0` in this mode (no workers
      exist to be active) — the `1.0` figure is a pure sentinel artifact of the division guard,
      not a real utilization measurement, and the governor has no way to distinguish it from
      genuine 100% saturation. **Re-observed 2026-09-11 with the now-real 16-entity
      `campaign_life_arc` world** (post `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`): the
      mis-trigger reproduces identically — entity count was never the cause, confirming this is
      the real, general finding, not an empty-world artifact. **Confirmed general, not Campaign-
      specific**: 3 real production call sites construct `RuntimeProfile(max_worker_count=0)` —
      `src/engine/scenario_runtime.py:395` (any `ScenarioRuntimeService` consumer),
      `src/engine/scenario_checkpoint.py:94` (`ScenarioCheckpointer`), and
      `src/config/loader.py:74` (`BROKER_DISABLED=1`, a real, documented operational config mode).
- [x] If genuinely trivial to fix (a real off-by-one or missing warm-up guard): fixed, with test
      evidence. **Not trivial** — see next AC.
- [x] If not trivial: this ticket closes with the disposition recorded and, if warranted, a new
      standard-tier ticket filed for the real fix — not implemented here. **Done**: this is
      foundational governance logic (`WorkerManager`/`ResourceGovernor`, tagged with 5 compliance
      IDs in `governor.py`'s own header) touching 3 real call sites including a documented
      operational mode — deciding the correct semantic (should `worker_utilization` become `0.0`,
      or should the governor's own evaluation skip the check entirely when `max_worker_count<=0`?)
      and verifying no other caller depends on the current sentinel is real investigation/test work,
      not a one-line patch. Filed `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-
      MISTRIGGER` (standard tier) for the real fix.

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
Real, uninstrumented probe (`CampaignManifest`/`CampaignOrchestrator`/`ScenarioRuntimeService`,
real `Kernel.step()` calls, no monkeypatching), `campaign_life_arc`-shaped scenario, 10 real ticks:
`kernel._current_policy.mode == RuntimeMode.DEGRADED` (`== 2`, confirmed via
`src/core/governance.py`'s `IntEnum`) and `.scan_policy == ScanPolicy.EXACT_DIRTY` from tick 1
through tick 10, with the now-real 16-entity world, despite `event_count` varying (0-37) across
ticks — i.e. `DEGRADED` does not correlate with real compute pressure at all, exactly matching the
sentinel-artifact hypothesis. Read `governor.py`'s `_get_indicated_mode()` directly (not inferred)
to find the exact `worker_utilization >= 0.9` trigger, then `worker_manager.py`'s `get_stats()` to
find the `1.0`-when-`max_workers<=0` sentinel that feeds it. Confirmed 3 real call sites via direct
grep, not assumed — `ScenarioRuntimeService`, `ScenarioCheckpointer`, and the `BROKER_DISABLED=1`
env-gated config path.

No code changed here — hotfix-tier, disposition-only, per this ticket's own explicit scope
boundary. The real fix (deciding and implementing the correct `worker_utilization` semantic for
`max_workers<=0`, with test coverage across all 3 real call sites) is filed as
`TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER`.

## Test Summary
Investigation/disposition only — no code changed, no new automated test added by this ticket
itself (the probe script used to gather evidence lived in scratch, not committed). The real fix
ticket will need its own test coverage per its own Acceptance Criteria.

## Files Changed
None — disposition-only, per this ticket's own hotfix-tier scope boundary (do not implement a
governor logic change unless genuinely trivial; this was not).

## Completion Summary
Confirmed the governor's tick-1 `DEGRADED` entry for `campaign_life_arc` (and any other
`max_worker_count=0` caller) is a real mis-trigger, not intended behavior: `WorkerManager.
get_stats()`'s `worker_utilization=1.0` sentinel for disabled workers is read by `ResourceGovernor`
as genuine 100% saturation. Re-observed directly with the now-real, entity-populated
`campaign_life_arc` world (the origin ticket's "empty world" framing turned out not to be the
cause) and confirmed general across 3 real production call sites, one of which is a documented
operational config mode (`BROKER_DISABLED=1`). Not fixed here — foundational governance logic with
real blast radius, not a trivial patch — filed `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-
DEGRADED-MISTRIGGER` (standard tier) for the real fix, per this ticket's own AC4.
