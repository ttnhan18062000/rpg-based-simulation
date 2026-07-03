---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE
phase: open
date: 2026-07-03
tags: [simulation_quality, calibration, performance, tooling]
---

# TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE

## Title
Apply the proven `no_frame_pacing` speedup to `calibrate_simq.py` so long calibration runs complete quickly

## Status
OPEN

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
- [ ] `calibrate_simq.py` passes `no_frame_pacing: True` (or equivalent) to the kernel for every run
- [ ] A short calibration run's output (`quality_report.json`) is byte-for-byte identical
      before/after this change, proving no logic change
- [ ] A long calibration run (≥2000 ticks) measurably completes faster after this change (report
      the before/after wall-clock times)
- [ ] `make evaluate --dry-run` exits 0 (0 regressions — this change should not move any grade)

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
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
