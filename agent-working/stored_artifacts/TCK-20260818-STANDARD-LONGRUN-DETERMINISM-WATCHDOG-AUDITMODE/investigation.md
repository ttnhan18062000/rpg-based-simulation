---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE
artifact_type: investigation
tags: [engine, determinism, bug, debugging, root-cause, testing]
---

# Investigation — TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE

## Trigger

Two independent hash-parity tests failed on the "Slow regression" CI job's first-ever completed
run (2026-08-17/18):

```
tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity
  AssertionError: Determinism parity broken! Hash1: 5a3e2a10... != Hash2: 07718a29...

tests/integration/world/test_long_run_stability.py::test_long_run_stability
  AssertionError: DIVERGENCE: Long-run simulation is not deterministic!
```

A third test in the same cert file, `test_long_run_pure_stability`, failed with a plain
`TimeoutError: Test execution exceeded the resource time limit.`

## Context Scan (mandatory order followed)

1. `mcp__knowledge-search__search_docs("long-run determinism divergence hash mismatch")` —
   surfaced `docs/engine/deterministic_execution.md` (the canonical determinism contract) and
   `docs/audits/D10_test_coverage.md`'s F3 (bare-random-usage finding, unrelated — already fixed
   per `TCK-20260619-P0-DETERMINISM`).
2. `mcp__knowledge-search__search_docs("spawn RNG consumption determinism collision resolution")`
   — surfaced `TCK-20260521-OCC-COLLISION` and `docs/engine/architecture.md`'s RNG section, neither
   implicating today's spawn-collision fix in per-tick behavior.
3. `graphify query "test_long_run_determinism_parity"` — confirmed the test's real dependency
   graph: `LongRunStabilityHarness` (`src/perf/long_run_harness.py`), not `WorldCompiler`.
4. `graphify query "WorldCompiler compile determinism"` — confirmed `WorldCompiler.compile()` is
   used only during world compilation, with no edge into the per-tick `Kernel` resolution loop.
5. Checked `tickets/`, `docs/`, `stored_artifacts/` for prior work — found
   `tickets/done/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE.md` (the suspected
   cause, investigated and ruled out below) and, critically,
   `tickets/done/TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION.md` — a **sibling ticket
   from this same session**, already closed (commit `305236bf`), which explicitly scoped
   `tests/certification/test_cert_long_run_stability.py` and
   `tests/integration/world/test_long_run_stability.py` OUT of its own scope ("owned by the sibling
   determinism-investigation agent" — this ticket) and independently, read-only, ruled
   `test_long_run_pure_stability`'s TimeoutError as *not* sharing root cause with these 2
   determinism bugs (see "Ruling on the TimeoutError" below — fully corroborates this ticket's own
   independent finding).

## Step 1 — Ruling out the spawn-collision RNG fix as the cause

`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (commit `0ecd2a83`) changed
`WorldCompiler.compile()`'s entity-placement RNG consumption (`src/worldbuilding/compiler.py`) to
add collision-resolution rerolls. This was the prime suspect per the parent task's own framing.

**Real bisection performed** (not guessed): created an isolated `git worktree` at
`db6335ad` (the commit immediately before `0ecd2a83`) under
`/tmp/claude-.../scratchpad/wt-prefix`, entirely separate from the shared main working tree (never
touched by `git add`/`git commit`/destructive ops). Ran the exact failing test
(`tests/integration/world/test_long_run_stability.py::test_long_run_stability
--resource-budget large`) there:

```
FAILED tests/integration/world/test_long_run_stability.py::test_long_run_stability
1 failed in 411.01s
```

**Identical divergence reproduced on the commit BEFORE the spawn-collision fix landed.** This
conclusively rules out `0ecd2a83` as the cause — the bug is pre-existing, unrelated to today's
session's spawn-collision work. Worktree removed after the check (`git worktree remove`).

## Step 2 — Mechanism A: wall-clock tick-budget watchdog / mid-tick emergency throttle

Direct reproduction of `test_long_run_stability` on HEAD (`.venv/bin/python3 -m pytest
tests/integration/world/test_long_run_stability.py::test_long_run_stability --resource-budget
large -v -s`) confirms the divergence and shows the mechanism directly in the log:

```
WARNING kernel.py:435 Tick 100 exceeded budget: 201.55ms vs limit 20.00ms. Aborting next tick if sustained.
CRITICAL [ALERT] type=WatchdogTrip ... tick=100 ...
WARNING kernel.py:435 Tick 201 exceeded budget: 195.48ms vs limit 20.00ms. ...
WARNING kernel.py:435 Tick 1221 exceeded budget: 49.08ms vs limit 20.00ms. ...
```

Run 2 (same seed) trips the SAME kind of watchdog but at **different tick numbers**
(20, 100, 103, 137, 201, 302, 305, 1229, ... vs. run 1's 100, 201, 302, 1221, 1239, ...).

**Root cause, `src/engine/kernel.py`:**
- `tick_once()` lines 431-453: after every tick, compares `self._final_compute_ms` (measured via
  `time.perf_counter_ns()`, real wall-clock) against an **adaptive** threshold
  `limit_ms = max(20.0, avg_ms * 2.0)` where `avg_ms` is the *previous tick's own measured
  wall-clock compute time*. If exceeded, logs a watchdog trip, calls
  `self._status.record_dropped_work(9999)`, and routes a `WatchdogTrip` alert.
- `_phase_resolution()` lines 585-612 (the "mid-tick emergency throttle"): mid-resolution, checks
  `elapsed = (time.perf_counter_ns() - self._start_perf_ts) / 1e6` every 10 results; if it exceeds
  `self._profile.max_tick_budget_ms`, it **drops the remaining resolution-queue work items for
  that tick** (`break`, dropping `len(self._final_results) - i` entity updates) and force-sets
  `RuntimeMode.DEGRADED`.

Both gates are `not self._audit_mode`-conditioned — i.e. **disabled entirely when
`audit_mode=True`**.

Real wall-clock timing inherently varies run-to-run on any real machine (OS scheduling, GC
pauses, cache warmth, I/O jitter) — this is exactly what the parent task's own framing predicted
("state-mutation-order sensitivity... RNG-consumption-order changes" was the guess, but the actual
mechanism is a third category: **real-time-derived control flow**, explicitly forbidden by the
engine's own contract, see below).

**This is not a new discovery — it is a previously-documented, already-tracked finding ("F6"):**
- `docs/audits/D06_longrun_health.md` §F6 ("Wall-Clock-Dependent Non-Determinism at Long Tick
  Counts (Tick-Budget Throttle)"), discovered 2026-07-09 via
  `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`. Status: **"Documented, not
  fixed — intentional engine behavior, not a bug."** Exact same two code locations
  (`kernel.py:420-442`, `kernel.py:574-601` — line numbers have since shifted slightly but the
  mechanism is identical).
- `docs/parity_ledger/infrastructure.yaml` id `INFRA-273` (status: verified, P2) documents the
  same mechanism extending across SOCIAL/ECONOMY/COMBAT/PROGRESSION/NARRATIVE/WORLD pillars for
  SimQ anchor scoring.
- **Established, deliberate remedy pattern for SimQ anchor tests** (tolerance-banded behavioral
  tests): leave the throttle active, convert to statistical-tolerance assertions — NOT
  `audit_mode`, because "`audit_mode=True` would verify a materially different (unthrottled,
  unrealistically optimistic) scenario" (D06 §F6). This ticket does **not** touch that precedent
  or `kernel.py`'s throttle/watchdog/`ResourceGovernor` logic — matching F6's own explicit scope
  guard ("did not touch kernel.py's watchdog/throttle logic").
- **Established, deliberate remedy pattern for STRICT hash-equality tests** (a different category
  — this is what `test_long_run_stability` is): use `audit_mode=True`, which "guarantees 100%
  exact determinism by zeroing wall-clock time signals" (comment already present in
  `src/perf/long_run_harness.py:316`). This pattern is **already used** by
  `src/certification/harness.py` (3 call sites), `tests/unit/kernel/test_replay_determinism.py`,
  and `LongRunStabilityHarness.verify_determinism_parity()` itself (the method backing
  `test_long_run_determinism_parity`). `docs/engine/deterministic_execution.md`'s own "Extension
  rules" §5 states outright: **"`audit_mode` should be enabled in all CI runs that verify the
  determinism guarantee."** `docs/engine/deterministic_execution.md`'s "Rule 1" also explicitly
  forbids `time.time()` / wall-clock reads in tick-path code — the watchdog/throttle mechanism is
  a pre-existing, documented, deliberate exception to that rule for real-time responsiveness, not
  a new violation.

`tests/integration/world/test_long_run_stability.py::test_long_run_stability` is unambiguously in
the second category (`assert hash1 == hash2`, no tolerance) but its `run_sim()` constructs
`Kernel(profile, state, rng)` with **no `flags` at all** — it never adopted the established
pattern the sibling tests/harness already use. This looks like a straightforward oversight: the
test was written to prove the determinism guarantee but never wired up the one flag the engine's
own documentation says is required to prove it.

**Verified fix** (see Step 4): adding `flags={"audit_mode": True}` to both `Kernel(...)`
constructions in `run_sim()` produces bit-identical hashes across repeated runs — see verification
below.

## Step 3 — Mechanism B: a second, deeper, previously undocumented divergence (audit_mode alone is insufficient for the cert `metropolis` scenario)

`test_long_run_determinism_parity` (`tests/certification/test_cert_long_run_stability.py`) calls
`LongRunStabilityHarness.verify_determinism_parity()`, which **already** sets
`"audit_mode": True` (has done so since the file's first commit, `788072fc`, months before this
session). Yet it still failed on real CI with a hash mismatch. Reproduced directly:

```
.venv/bin/python3 -m pytest tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity \
  --resource-budget large --tb=long -v -s
FAILED — AssertionError: Determinism parity broken!
Hash1: fa8ad2c2... != Hash2: 1618f752...
```

Confirmed 0 watchdog trips / 0 `WatchdogTrip` alerts in the log (`grep -c "exceeded budget\|WatchdogTrip"` → 0)
— `audit_mode` is genuinely suppressing Mechanism A here. The divergence is real and separate.

**Isolated the exact divergence point** using a standalone script (not the full 1000-tick pytest
run, to keep iteration cheap) that hashes `AuthoritativeState` after every tick for two independent
runs of the same `verify_determinism_parity()` code path (metropolis scenario, seed 303, 500
entities, `audit_mode=True`):

```
First diverging tick: 30
Prev tick (29) hash1 == hash2 (bit-identical)
Tick 30: hash1 != hash2
```

A field-level diff of the canonical state at tick 30 (`CanonicalStateHasher.to_canonical_data()`)
shows the divergence is a genuine STRATEGIC-COGNITION decision difference, not cosmetic reordering:

```
.entities.1.strategic.current_objective_id => combat_engage_201 | combat_retreat_town_center
.entities.1.strategic.projects.proj_combat_engage_9.status => ACTIVE | SUSPENDED
.entities.1.strategic.projects.proj_combat_retreat_29 => <missing> | {...ACTIVE retreat project...}
.entities.31.strategic.concerns.concern_low_hp => <missing> | {urgency: 0.77, ...}
```

Multiple entities (1, 21, 31, 41 — all landing on the "engage" branch in run 1 and the "retreat"
branch in run 2) diverge simultaneously at tick 30. Entity 31 additionally shows a
`concern_low_hp` present ONLY in run 2 — meaning the entities' actual combat/HP state, not just
downstream goal selection, already differs by this point.

**A separate, contributing, pre-existing bug was also found and is very likely why this
specific scenario (and not the 2-entity `test_long_run_stability` scenario) trips Mechanism B**:
`src/perf/scenarios.py::build_metropolis_state()` (lines 375-381) computes each entity's spawn
position from `(i % 10, (i // 10) % 10)` relative to its assigned region, a formula that repeats
every 100 entities. Entities spaced exactly 100 or 200 apart in builder-iteration order land on
the literal same tile (confirmed: entity 30 & 130, entity 60 & 260, entity 10 & 110, etc. — 35
such pairs in a 500-entity build). This produces ~550+ `LAW-OCCUPANCY-COLLISION` warnings per run
(HardLawMonitor, non-mutating LIGHT-mode log only) starting at tick 1 — and this position overlap
is itself **deterministic and identical between the two runs** (confirmed: `check_occupancy()`'s
detected collision set, captured via a monkeypatch spy on `HardLawMonitor.check_occupancy`, is
byte-identical in content and iteration order between two independent runs at tick 1). This is a
**different code path than `WorldCompiler.compile()`** (which the spawn-collision ticket fixed) —
it is the perf/long-run-harness's own separate scenario builder, never touched by that ticket, and
out of scope for this ticket's Related Code Areas.

The working hypothesis (not fully proven at the exact code line, given remaining time budget) is
that dozens of entities standing on identical tiles from tick 1 creates repeated combat-adjacency
contention, and that SOME order-sensitive step in target selection or budget-constrained candidate
truncation downstream of this (most likely in `src/domains/combat_engagement/` or
`src/cognition/`/`src/strategy/`'s goal evaluation, neither of which this investigation traced to
the exact line) produces genuinely different combat/HP outcomes between the two runs by tick 30 —
even with the wall-clock throttle (Mechanism A) fully disabled. This is **not** covered by
`docs/engine/deterministic_execution.md`'s "Known non-determinism sources (pre-existing, out of
scope to fix)" list (concurrent mode / external I/O / float precision — none apply here:
`max_worker_count=0`, no I/O, and the diff shows discrete enum/string field changes, not
float-rounding noise), and is **not** the same mechanism as F6/INFRA-273 (watchdog trips = 0).

**Per this ticket's own scope discipline and the parent task's explicit instruction ("if
root-causing genuinely can't be completed in reasonable time, it is FAR better to stop and report
your findings honestly... than to guess at a fix or paper over it"): Mechanism B is reported,
precisely localized, but NOT fixed in this ticket.** Tracing it to the exact non-deterministic
instruction would require further instrumentation of the combat-engagement and strategic-cognition
pipelines beyond this investigation's time budget, and guessing at a fix for a P0/P1 architectural
correctness bug without full certainty would violate CLAUDE.md's Hard Rules ("Do not guess when
uncertainty affects behavior or architecture"). Flagged as a required follow-up ticket (see
Related Tickets in the main ticket file).

## Step 4 — Ruling on the TimeoutError (`test_long_run_pure_stability`)

`execute_run()` (the method backing both `test_long_run_pure_stability` and
`test_long_run_runtime_stability`) runs a single straight loop of `kernel.tick_once()` calls with
**no hash comparison, no second run, no replay/retry logic at all** — it cannot be "non-
deterministic" in the hash-parity sense because it never compares two runs. Its assertions
(`rss_bounded`, `latency_stable`, `caches_bounded`, `gc_stable`, `passed_certification`) are all
single-run, tolerance-banded invariants.

Confirmed by an independent, already-closed sibling ticket in this same session
(`tickets/done/TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION.md`, commit `305236bf`),
which read-only-investigated this exact TimeoutError (explicitly declining to edit the file, since
it was reserved for this investigation) and reached the same conclusion independently: `RunMode.
PURE`'s code path has no hash/replay/retry machinery, and that ticket's own `test_perf_strategic`
measurements (900-1090ms p95 per tick at 1000 entities) make a 5100-tick run at 1000-entity scale
plausibly exceed the 600s `--resource-budget large` ceiling on this hardware tier regardless of
any determinism bug.

**Conclusion: the TimeoutError is a separate, unrelated, genuine hardware/resource-budget
calibration gap — not a symptom of Mechanism A or B.** Matches the test's own pre-existing
`skipif` rationale ("CI persistence I/O inflates tick latency, causing false latency-drift
failures"). Not fixed here — recalibrating a 5000-tick/1000-entity budget is a distinct,
already-precedented class of work (see the sibling ticket's own methodology) that would need its
own dedicated ticket, and this ticket's Related Code Areas do not include
`src/perf/long_run_harness.py`'s `execute_run()` timing budget.

## Step 5 — Verified fix (Mechanism A only)

Standalone reproduction of `test_long_run_stability`'s exact scenario (2 entities, seed 999, 2000
ticks) with `flags={"audit_mode": True}` added to both `Kernel(...)` calls, run 3 times
independently (2 in one process, 1 in a fresh separate process):

```
run1 hash: 64d512def2f14f8f66e7cc48174b0d2b77dbbe0769b4c15e6c1fa2db70ca50c9
run2 hash: 64d512def2f14f8f66e7cc48174b0d2b77dbbe0769b4c15e6c1fa2db70ca50c9  (same process)
run3 hash: 64d512def2f14f8f66e7cc48174b0d2b77dbbe0769b4c15e6c1fa2db70ca50c9  (fresh process)
```

Bit-identical across all 3 runs, and 0 watchdog trips logged. Also confirmed `audit_mode=True`
alone (without touching `no_frame_pacing`) is sufficient — frame-pacing `time.sleep()` calls do
not affect hashed state, only wall-clock test duration (218s/run vs. 32s/run with
`no_frame_pacing` also set — not changed here, to keep the diff minimal and behavior-preserving).
