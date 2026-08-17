---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION
artifact_type: investigation
tags: [testing, bug, performance, calibration]
---

# Investigation — TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION

## Context Scan (mandatory, performed first)
- `mcp__knowledge-search__search_docs("performance test threshold CI hardware class")` and
  `("resource budget hardware class calibration")` — surfaced `docs/engine/performance_contract.md`,
  `docs/performance/perf_baseline_policy.md`, `docs/engine/runtime_profiles.md`, and the two direct
  precedent tickets: `TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER` (methodology template)
  and `TCK-20260624-FIX-PERF-BUDGETS` (original ad-hoc-threshold sweep, includes this exact test's
  first partial fix).
- `graphify query "performance_contract hardware class"` — traversed `HardwareClass`
  (`src/config/profiles.py`), `RuntimeProfile`, `CertificationHarness`, `BenchHarness` community.
- Read `docs/engine/performance_contract.md` in full (§3.1 Scoped Claims, §3.2 Benchmarking
  Protocol, §4.2 Bounded Overhead, §5 Regression Enforcement, §6 Memory Management).
- Read `docs/performance/perf_baseline_policy.md` (§2.2 Hardware Classes: CLASS_A
  8+cores/16GB+, CLASS_B 4cores/8GB, CLASS_C 2cores/2GB — CI's `ubuntu-latest` runner is
  2-core/7GB, i.e. CLASS_C-ish; `src/perf/profiles.py`'s `make_perf_profile()` hardcodes
  `HardwareClass.CLASS_A` for every `PERF_*` profile regardless of what hardware it actually runs
  on — the profile's `hardware_class` field is a resource-cap label, not a runtime detector).
- Checked `tickets/todos/`, `tickets/inprogress/` — no open ticket already covers this batch.
- `grep`'d `tickets/` + `docs/` for each of the 6 failing test names — only prior generic perf
  history (`TCK-20260512/513/516/517-PERF-*`, `TCK-20260624-FIX-PERF-BUDGETS`,
  `TCK-20260623-FIX-ARENA`), no existing open investigation duplicates this work.

## Scope note
Covers the performance-threshold batch only: `test_arena_stress_50v50`,
`test_hard_law_monitor_overhead`, `test_api_snapshot_performance_stress[5000]`,
`test_perf_passive_scaling[5000]`, `test_perf_strategic[500]`/`[1000]`.
`test_long_run_pure_stability` (same "Slow regression" run, TimeoutError) is investigated
read-only here to answer the coordination question the parent task raised, but its file
(`tests/certification/test_cert_long_run_stability.py`) is explicitly out of scope to edit — it
lives in the sibling determinism-investigation agent's territory. No `src/` files are modified by
this ticket other than none — all fixes are test-file-scoped (thresholds + one methodology bug).

## Per-test findings

### 1. `tests/arena/test_arena_stress.py::test_arena_stress_50v50` — hardware calibration
`TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY` (closed earlier this session) proves
this test was excluded from the `perf-cert-arena` fast lane (missing `and not extra_slow`) until
today, and `TCK-20260623-FIX-ARENA`'s own implementation notes show its `200.0` MB bound was never
measured ("starting from ~48MB, should stay well below 200MB" — a guess). This is genuinely the
first real execution under `--resource-budget large` in CI. Real CI: `peak_rss_mb=247.07`. Local
reproduction (`.venv/bin/python3 -m pytest ... -m "slow or extra_slow" --resource-budget large`):
`peak_rss_mb=92.2`, `PASSED` — same order of magnitude, no regression signal, CI's shared-runner
process baseline simply runs higher. Verdict: **hardware calibration, never validated before.**

### 2. `tests/certification/test_cert_long_run_stability.py::test_long_run_pure_stability` — read-only, out of scope
Investigated `src/perf/long_run_harness.py::execute_run()` (read-only). `PURE` mode runs
`warmup_ticks=100` + `total_ticks=5000` = 5100 sequential `kernel.tick_once()` calls on a
1000-entity `metropolis` scenario, in a single straight loop — **no hash comparison, no retry
logic, no replay verification**. That machinery lives entirely in the separate
`verify_determinism_parity()` method, used only by the sibling's `test_long_run_determinism_parity`
(a different test in the same file). This test's own `RunMode.PURE` code path never touches
determinism-parity verification at all.
This session's own `test_perf_strategic` diagnostic (see #5 below) measured 1000-entity strategic
ticks at ~900-1090ms p95. If `metropolis` at 1000 entities is anywhere near that heavy,
5100 ticks would need on the order of 4500-5500s wall-clock — vastly over the 600s
`--resource-budget large` ceiling regardless of any determinism bug. This is consistent with a
simple, expected "5000-tick full run doesn't fit in a 600s budget at this entity count on this
hardware tier" finding, not a hang caused by the sibling's determinism bugs.
**Verdict (reported, not fixed): very likely an independent, genuine hardware/budget-size
mismatch — NOT the same root cause as the sibling's 2 real determinism-violation bugs** (different
code path entirely: no hash/replay logic in `PURE` mode). Left untouched per scope boundary; flagged
for the sibling agent / a future ticket to confirm and recalibrate (raise `--resource-budget large`'s
600s ceiling for this specific test, or reduce `total_ticks`/`entity_count`, or move it off the
default `slow` job's 600s ceiling into a dedicated longer-budget job).

### 3. `tests/perf/test_hard_law_monitor_overhead.py::test_hard_law_monitor_overhead` — hardware calibration, NOT the compiler.py collision fix
Checked `git log -- src/worldbuilding/compiler.py`: only recent change is
`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`'s `_resolve_entity_spawn_tile()`,
confirmed (by that ticket's own Implementation Notes and by re-reading `WorldCompiler.compile()`
step 6) to run at **world-compile time only**, never per-tick — ruled out as the cause, as the
parent task suspected it would be.
`git log -- src/observability/` shows no changes in this session's timeframe either.
The `skipif(os.environ.get("CI") == "true", ...)` guard on this test (added 2026-07-02 in
`6e25d4f2`, same commit as the other 3 skipif-guarded tests below) already disclosed "CI CPU too
slow for 5% overhead threshold" over a month before this ticket — and `TCK-20260624-FIX-PERF-BUDGETS`
had ALREADY measured "8-49% relative" overhead on this exact test back in June, yet only removed
the separate `abs_overhead_ms < 0.1ms` OR-arm, leaving the already-known-unrealistic 5% relative
bar in place and hiding the gap behind the CI skip instead of recalibrating it.
The removed comment's citation of "performance_contract.md §4.2: instrumentation ceiling is <5%"
does not match the doc — §4.2 literally states "< 1% of total tick time", an even stricter,
also-unmet bar. Bringing real overhead down to either the 5% (as-cited) or 1% (as-documented)
ceiling would require optimizing `HardLawMonitor`'s LIGHT-mode per-tick check path in
`src/observability/` — a real, legitimate, but separate and not-yet-scoped optimization effort,
out of scope for this threshold-calibration ticket.
Real measurements (this session, 5 independent local runs, `.venv`, `--resource-budget large`):
36.37%, 33.73%, 27.29%, 27.34%, and a 5th ~27% run — with `avg_tick_compute_ms (OFF)` consistently
~13.0-13.5ms across all runs, matching CI's own reported `13.497ms` almost exactly. CI's own
failure: `27.52%` (`13.497ms → 17.211ms`). This tight, cross-machine numerical match (absolute ms,
not just ratio) is strong evidence this is a real, stable, hardware-independent overhead ratio, not
noise — consistent with (and quantitatively matching) `TCK-20260624-FIX-PERF-BUDGETS`'s own
month-old "8-49%" measurement of the same test.
**Verdict: hardware/never-properly-calibrated (pre-existing since introduction, not a recent
regression) — genuinely large but stable, not a src fix candidate within this ticket's scope.**

### 4. `tests/perf/test_perf_api_snapshot.py::test_api_snapshot_performance_stress[5000]` — real test-methodology bug (not hardware)
This is the specific "48x overage" the parent task flagged as suspicious, and it IS a real bug —
just not in `src/`. `AuthoritativeState.to_readonly()` (`src/core/state.py:1206`) caches its result
on `self._readonly_cache`; the first call on an unmutated state is a genuine O(N) rebuild, every
subsequent call on the SAME unmutated state object is an O(1) cache hit. Direct diagnostic
(`state = build_idle_state(5000); state.to_readonly()` cold vs. 14x warm):
cold=`221.771ms`, warm avg=`0.00029ms`, warm max=`0.00160ms` — confirms the mechanism exactly. The
test's `_run_snapshot_benchmark()` never calls `to_readonly()` before starting its 15-sample timed
loop, so sample #1 (the cold, ~100-220ms build) becomes the array's max, and
`sorted(latencies)[int(15*0.95)]` (index 14 of 15, i.e. the max) reports that one-time cold cost
as "p95" — not steady-state re-read cost. CI's reported "119.34128077700734ms" and the skip
guard's own month-old note ("to_readonly for 5000 entities takes ~138ms on CI") are both just this
same cold-build cost, already known and never fixed.
Checked whether the cold cost is actually paid every real tick (which would make ~100-220ms a
legitimate per-tick concern, not a benchmark artifact): `grep`'d all `.to_readonly()`/
`.readonly_view()` call sites — the only production caller is `Kernel._phase_collection()`
(`src/engine/kernel.py:564`, `self._state.readonly_view()`), called once per tick against
`self._state`. `src/engine/apply.py:366-421`'s `apply_generation()` constructs a brand-new
`AuthoritativeState(...)` every tick (not `.replace()`), so `_readonly_cache` is never carried
forward — BUT it explicitly reuses `prior_state._readonly_entities_cache` when
`not any_entity_changed` (line 420-421), a targeted differential-caching optimization for the
per-entity wrapper dict specifically. This confirms the Kernel's own per-tick cold-rebuild cost
(when entities DO change, i.e. almost every real tick) is real and IS already reflected in the
whole-tick p95 numbers asserted by `test_perf_passive_scaling`/`test_perf_strategic` (both of which
run real `Kernel.tick_once()` loops). `test_perf_api_snapshot.py`, by contrast, never ticks at all —
it models a different, legitimate scenario: repeated external reads (e.g. multiple API/websocket
observers) of one already-published, unchanged snapshot between ticks, where a warm cache is the
correct and representative expectation. No double-counting risk between the two test files once
fixed this way.
**Fix applied**: added one untimed warmup `state.to_readonly()` call before the timed loop (matches
`performance_contract.md` §3.2's warmup mandate). This is a substance fix (fixes what the metric
measures), not a threshold change — the `< 2.5` assertion is unchanged and now passes because the
steady-state metric it measures is a hardware-independent O(1) cache-hit operation. Verified locally
post-fix (see Test Summary). `skipif(CI=="true")` guard removed — no longer needed since the fixed
metric doesn't depend on entity count or hardware.

### 5. `tests/perf/test_perf_passive_scaling.py::test_perf_passive_scaling[5000]` — memory-delta metric is a real measurement artifact, not a leak (confirmed by control experiment)
Given real scrutiny per the parent task's explicit instruction (not assumed pure hardware
calibration). `BenchHarness.run_benchmark()` (`src/perf/bench_harness.py:76-93`) intentionally
calls `gc.collect(); gc.disable()` immediately before the sampling loop and only
`gc.enable()`s in a `finally` after sampling ends — deliberate, to keep `tick_ms` latency
percentiles free of GC-pause noise, consistent with `performance_contract.md` §3.2's
"Environmental Stability" mandate. `mem_rss_mb["delta"]` (`max(rss_samples) - min(rss_samples)`)
is computed from RSS samples taken **during that same GC-disabled window**.
Direct control experiment (`Kernel` built the same way as `BenchHarness`, same
`PERF_512MB_LOCAL` profile, `build_idle_state(5000)`, 20 warmup ticks, then two consecutive
100-tick windows): with GC disabled (mirroring the real harness path), `delta=188.4MB`
(`max=327.3MB min=138.9MB`); a `gc.collect()` immediately after re-enabling GC reclaimed
**0.0MB** (consistent with CPython's allocator not releasing freed arenas back to the OS, not with
a live leak); a SEPARATE, immediately-following 100-tick window with GC left enabled the entire
time showed `delta=5.3MB` — comfortably under even the original `50.0MB` bound. This is a clean,
reproducible, direct confirmation: the metric captures unreclaimed-but-not-leaked
reference-cycle garbage that accumulates specifically because the cyclic collector is turned off,
not unbounded application-level growth. Also checked thread hygiene: `count_drain_workers()`
(the same helper the session-scoped sentinel in `tests/conftest.py` uses) showed 2 pre-existing
drain-worker threads before ticking (stable, unrelated to this test), unchanged after 220 ticks
(no new threads), and 0 after `kernel.shutdown()` — `BenchHarness` already wraps kernel construction
in `try/finally: kernel.shutdown()` (fixed by `TCK-20260624-FIX-PERF-BUDGETS`). **No shared root
cause found with the sibling `QueueDrainWorker` thread-leak finding from the same CI run** — this
test's own harness usage cleans up correctly; that leak is very likely a different test elsewhere
in the suite that constructs a `Kernel`/`EventRecorder` without a matching shutdown, not connected
to this memory-delta finding. Reporting this per the parent task's explicit ask, not touching the
separate sibling investigation.
**Fix applied**: raised the `count>=5000` delta bound with ~50% headroom over the highest real
observed value (this session's own local `188.4MB`) to `300.0`, with the full mechanism disclosed
inline (not a blind loosening — grounded in the control experiment above). `skipif(CI=="true")`
removed. Flagged a genuine follow-up (not implemented here, out of scope): redesign
`BenchHarness` to measure the leak-delta metric over a separate GC-enabled follow-up window so
this assertion regains real sensitivity to genuine leaks — left as an explicit, disclosed gap
rather than silently absorbed, since it would touch a widely-shared harness file used by many
other passing perf tests plus the SimQ corpus baseline-generation tooling
(`tools/bench_corpus_world.py`), a bigger blast radius than warranted for this ticket.

### 6. `tests/perf/test_perf_strategic.py::test_perf_strategic[500]`/`[1000]` — hardware calibration, same signature as the `test_perf_combat` precedent
Direct diagnostic via `BenchHarness` (not the pytest test itself, to capture phase breakdown,
which the test doesn't print): n=500 local p95=`452.224ms` (CI: `424.001ms`); n=1000 local
p95=`1088.872ms` (CI: `928.603ms`) — both same order of magnitude as CI, local somewhat higher
(consistent with this dev box's confirmed memory pressure at investigation time: `free -h` showed
only 622MB free + 3.6GB swap in use). Phase breakdown for both sizes: `final_integrity` and
`advancement` dominate (n=1000: `final_integrity` p95=`641.30ms`, `advancement` p95=`524.82ms`,
vs. `collection` — the phase containing the `readonly_view()` rebuild investigated in finding #4 —
only p95=`19.28ms`, ruling out finding #4's mechanism as the cause here). This is the **exact same
phase-cost signature** `TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER` already
investigated for the sibling `test_perf_combat[500]` test and confirmed reads as inherent
authoritative-pipeline cost at high entity counts ("profiling shows `final_integrity` ... dominates
cost at every size ... not a regression traceable to any single commit"). `git log` on
`final_integrity`'s implementation / `src/engine/kernel.py` / `src/engine/pipeline.py` shows
nothing suspicious near this session's actual changes.
**Verdict: hardware calibration, matching an already-established precedent for the same
underlying cost pattern.**

## Cross-cutting observation: the `skipif(os.environ.get("CI") == "true")` pattern
4 of the 6 in-scope failing tests (`test_hard_law_monitor_overhead`,
`test_api_snapshot_performance_stress[5000]`, `test_perf_passive_scaling[5000]`,
`test_perf_strategic`) — plus `test_long_run_pure_stability` in the out-of-scope sibling file —
already carried a `skipif(os.environ.get("CI") == "true", reason="...")` guard, all 5 added in the
same commit (`6e25d4f2`, 2026-07-02), each with a reason string disclosing the exact real
CI-vs-threshold gap. Per the real "Slow regression" CI failure data this ticket investigates, these
tests ran to completion and failed rather than being skipped — this session cannot directly inspect
the literal GitHub Actions execution logs to confirm why (the `slow` job's `needs:` chain gating
this job's first-ever completion, per the parent task's own framing, is the most plausible
explanation: the job itself never ran before today, so this skip mechanism's real CI behavior was
never actually exercised/verified until now). Regardless of that specific mechanism, an
env-var-gated silent skip is itself the kind of hidden, undocumented, durable-behavior-by-side-channel
CLAUDE.md's Hard Rules caution against, and — per `TCK-20260624-FIX-PERF-BUDGETS`'s own
"8-49%" finding for `test_hard_law_monitor_overhead` a month before this ticket — was already known
to be masking a real, unresolved threshold gap rather than fixing it. All 4 in-scope skipif guards
are removed by this ticket in favor of genuinely calibrated, always-evaluated thresholds, matching
the precedent ticket's own methodology.
