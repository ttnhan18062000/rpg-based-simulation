---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE
phase: done
date: 2026-07-03
tags: [simulation-quality, calibration, performance, tooling]
---

# TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE

## Title
Apply the proven `no_frame_pacing` speedup to `calibrate_simq.py` so long calibration runs complete quickly

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`tools/calibrate_simq.py`'s `_run_engine()` does not pass `flags={"no_frame_pacing": True}` to the
kernel. `TCK-20260628-E-LONGRUN-REGRESSION`'s Completion Summary documents this exact discovery for
a different long-run harness: without it, the kernel sleeps ~500ms/tick for real-time pacing, so a
5,000-tick run takes ~45 minutes; with it, the same run completes in well under 10 minutes on
Hardware Class B. `calibrate_simq.py` does not use this flag, so any calibration run at meaningful
tick counts (the `dungeon_crawl_seed42_5200t` diagnostic run performed during
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` took a large fraction of that ticket's wall-clock
time) is unnecessarily slow. This blocks fast iteration on any future long-horizon SimQ work
(e.g. validating `calamity_spawned` at its 5000-tick force interval, or the world-corpus expansion
in `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`).

This is the same class of fix as the regression harness's, just applied to a different call site —
no new mechanism to invent, reuse what's already proven correct.

## Scope
1. Find `calibrate_simq.py`'s `_run_engine()` (or equivalent kernel-construction call site) and add
   `flags={"no_frame_pacing": True}` (or merge it into any existing `extra_flags` dict already
   passed), mirroring `tests/regression/test_behavioral_5k.py`'s usage.
2. Confirm this does not change simulation *logic* — only real-time pacing/sleep behavior between
   ticks. Verify by re-running an existing short calibration scenario (e.g.
   `urban_political_seed42_200t`) before/after and diffing `quality_report.json` — must be
   byte-for-byte identical (same seed, same tick count, same events, same grades).
3. Time a longer run (e.g. re-run the `dungeon_crawl_seed42_5200t` diagnostic from
   `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`) before/after to confirm the expected speedup.

## Out of Scope
- Changing any simulation logic, scoring formula, or grade threshold
- Adding new calibration scenarios (see `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`)
- Investigating or fixing the `calamity_spawned` hero-death content precondition found in
  `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` (this ticket only makes it *cheaper* to test that
  scenario length, not fixes the underlying content gap)

## Acceptance Criteria
- [x] `calibrate_simq.py` passes `no_frame_pacing: True` (or equivalent) to the kernel for every run
- [x] A short calibration run's output (`quality_report.json`) is byte-for-byte identical
      before/after this change, proving no logic change
- [x] A long calibration run (≥2000 ticks) measurably completes faster after this change (report
      the before/after wall-clock times)
- [x] `make evaluate --dry-run` exits 0 (0 regressions — this change should not move any grade)

## Related Tickets
- TCK-20260628-E-LONGRUN-REGRESSION (done) — source of the `no_frame_pacing` discovery, being
  reused here for a second call site
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER (done) — the `dungeon_crawl_seed42_5200t` diagnostic
  run that motivated this ticket
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — benefits from this ticket landing first

## Related Docs
- `docs/audits/D20_simq_integration.md` §SimQ Uplift Batch 2 — residual `calamity_spawned` finding
  this ticket makes cheaper to eventually close

## Related Stored Artifacts
- `stored_artifacts/TCK-20260628-E-LONGRUN-REGRESSION/` (if present) — original discovery context

## Related Code Areas
- `tools/calibrate_simq.py` — `_run_engine()`, kernel construction call site
- `tests/regression/test_behavioral_5k.py` — reference usage of `no_frame_pacing`
- `src/engine/kernel.py` — where `no_frame_pacing` is consumed (confirm exact flag-check location
  during investigation)

## Assumptions / Open Questions
- UQ-1: Confirm `no_frame_pacing` is a `RuntimeProfile`/flags-dict key recognized by `Kernel`
  construction as used by `calibrate_simq.py` (which may build its kernel differently from the
  regression harness) — trace the exact call path before assuming the same flag name/mechanism
  applies unchanged.

## Implementation Notes
Investigation (UQ-1) confirmed the flag name/mechanism: `no_frame_pacing` is a key in the `flags`
dict passed directly to the `Kernel.__init__` constructor kwarg (`src/engine/kernel.py`), consumed
at the tick-pacing sleep gate (`if target_ms > 0 and not self._no_frame_pacing:` around L401). This
is a **separate mechanism** from `calibrate_simq.py`'s existing `extra_flags` parameter, which feeds
a different dict (`ENABLE_*` domain feature flags merged into `state.feature_flags` for the
optimization/feature-flag subsystem). The two are easy to conflate because of the similar naming,
but they don't overlap — `tests/regression/test_behavioral_5k.py` (L78-81) confirmed the Kernel
constructor usage pattern: `Kernel(profile=profile, state=state, rng=..., flags={"no_frame_pacing":
True})`.

Prior to this change, `calibrate_simq.py`'s single `Kernel(...)` construction call site (line 228)
passed no `flags=` argument at all, so there was nothing to merge/clobber — the fix simply adds
`flags={"no_frame_pacing": True}` to that one call.

Verification performed:
1. **Short-run identity check** (`urban_political_seed42_200t`, 200 ticks, seed 42): ran once with
   the old code (via `git stash`) and once with the new code, comparing `quality_report.json`.
   After masking two known non-deterministic bookkeeping fields — `generated_at` (wall-clock ISO
   timestamp) and the embedded epoch portion of `run_id` (both stamped at report-generation time,
   unrelated to simulation logic) — the reports were **identical**, including `overall_score`
   (1.916170045459261), `overall_grade` (A), every pillar's `raw_score`/`normalized_score`/`grade`/
   `event_count`, and every individual event's `delta`/`entity_id`/`event_type`/`pillar`/`reason`.
   The only per-event field that differed was `event_id`, which is `uuid.uuid4().hex`
   (`src/observability/events.py` L56) — a non-seeded UUID stamped independently of simulation
   state on every run, before and after this change.
2. **Long-run event-count check** (`dungeon_crawl_seed42_2000t`, 2000 ticks, seed 42): ran with old
   code, then twice with new code. All 9 non-NARRATIVE pillars had identical `event_count`/
   `raw_score`/`grade` across all three runs. The NARRATIVE pillar's `event_count` varied slightly
   across all three runs (86 / 83 / 79) — including *between the two same-code new-code runs*,
   proving this jitter is pre-existing, unrelated to `no_frame_pacing`, and traces to the async
   observability drain-worker queue (`src/observability/queue.py`, bounded queue with
   `dropped_count` under backpressure — `src/observability/event_recorder.py` L95 "Phase 21
   non-blocking queue and async drain worker"), not to simulation logic. `overall_grade` stayed `B`
   in all three runs; the score delta (0.0635 → 0.0627 → 0.0620) is within existing jitter and does
   not cross any grade-threshold boundary — confirmed separately by `make evaluate` (250/250 pillars
   PASS, 0 regressions).
3. **Timing**: see Test Summary below for concrete before/after wall-clock numbers. Speedup is
   consistent with the documented mechanism — `PROD_SMALL.max_tick_budget_ms=100.0`, so every tick
   whose real work takes <100ms real time previously slept the remainder; `no_frame_pacing` removes
   that sleep entirely.

No simulation logic, scoring formula, or grade threshold was touched — only the `flags=` kwarg on
one `Kernel(...)` call in a calibration tool.

## Test Summary
- `urban_political_seed42_200t` (200 ticks): before 23.01s engine / 24.907s total wall-clock;
  after 3.94s engine / 5.881s total wall-clock (~4.2x speedup). `quality_report.json` identical
  modulo non-deterministic `event_id` (uuid4) and timestamp fields (see Implementation Notes).
- `dungeon_crawl_seed42_2000t` (2000 ticks): before **3m51.302s** (231.3s) total wall-clock; after
  **27.781s** total wall-clock (~8.3x speedup); a repeat after-run measured 29.142s (consistent).
  All pillars except NARRATIVE identical event counts/grades across before/after; NARRATIVE jitter
  shown to be pre-existing (present between two same-code after-runs too) and does not move
  `overall_grade` (stayed `B` in all three runs).
- `make evaluate` (which invokes `tools/evaluate_simq.py --dry-run`): **250 pillars checked — 0
  regressions — 0 missing**, exit code 0.
- `pytest tests/simulation_quality/test_kernel_simq_integration.py
  tests/unit/observability/test_event_extractor_simq.py -q`: 25 passed.
- Cleaned `data/runs/*` and `reports/release_proof/*` after testing (gitignored, no tracked diff).

## Files Changed
- `tools/calibrate_simq.py` — added `flags={"no_frame_pacing": True}` to the single `Kernel(...)`
  construction call in `_run_engine()`.

## Completion Summary
Applied the same `no_frame_pacing` speedup already proven in
`tests/regression/test_behavioral_5k.py` to `calibrate_simq.py`'s kernel construction. Confirmed via
git-stash before/after comparison that simulation logic, scores, and grades are unchanged (modulo
pre-existing non-deterministic UUID/timestamp bookkeeping fields and a pre-existing NARRATIVE
observability-drain-worker event-count jitter, both independent of this change and both verified not
to move any grade). Long-run calibration (2000 ticks) is ~8x faster (231s → 28s);
`make evaluate --dry-run` shows 0 regressions across all 250 tracked pillar/scenario combinations.
