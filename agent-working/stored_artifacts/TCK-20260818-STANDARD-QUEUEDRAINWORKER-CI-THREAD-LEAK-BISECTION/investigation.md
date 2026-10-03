---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION
artifact_type: investigation
tags: [observability, investigation, testing, root-cause]
---

# Investigation — TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION

## Session Continuity Note

This ticket resumes a prior, interrupted session. The prior session's own conversation context
(including whatever specific pytest output or bisection state it had reached) was **not
recoverable** — no ticket file, staging artifact, or `agent-monitoring/` record existed for it at
resume time (confirmed via `search_docs`, `graphify query "QueueDrainWorker"`, `grep` across
`tickets/`, `stored_artifacts/`, `agent-monitoring/{runs,events}.jsonl`). What *was* recoverable:
two sibling tickets closed earlier in this same overall session —
`TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION` and
`TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE` — both of which independently
reference **"the sibling `QueueDrainWorker` thread-leak finding from the same CI run"** as an
established fact, confirming a real leak was genuinely observed in CI run `32046239870`'s "Slow
regression" job (`Slow tests (includes 5k behavioral regression)` step, which failed; the
job as a whole ran 42m6s). Neither sibling ticket names the specific leaking test — both treat it
as a parallel investigation's (this ticket's) responsibility. This investigation had to be
resumed from that partial evidence alone, without the original session's specific findings.

## Ground Truth Attempted But Unavailable

`gh run view 32046239870 --log-failed` (and `--job=<id> --log`, and direct `gh api .../logs`)
all fail in this sandbox — not a real TLS/cert problem despite the error text ("tls: failed to
verify certificate"). Following the signed blob-storage URL `gh api` itself resolved
(`productionresultssa6.blob.core.windows.net/...`) with `curl -sk` returns an HTML page: *"Fortinet
Secure DNS Service Portal — Web Page Blocked! You have tried to access a web page which belongs to
a category that is blocked."* This is a hard network-policy block on this sandbox's DNS/proxy for
the Azure blob-storage domain GitHub Actions uses to deliver full job logs — not bypassable with
`-k`/insecure flags, since the request never reaches GitHub/Azure at all. `gh run view <id>` and
`gh run view <id> --json ...` (which use the regular GitHub REST API, not blob storage) work fine
and gave the job/step list and annotations, but no annotation contained pytest output — this
workflow doesn't emit `::error`/`::warning` commands from pytest itself.

**Conclusion: the exact original CI failure text (which test, what the sentinel message said) is
unrecoverable in this environment.** This investigation proceeded by reconstructing the CI
scope exactly and reproducing it locally instead.

## What Actually Failed in CI Run 32046239870

`gh run view 32046239870` (job list, not blob logs):
- All 11 fast-lane jobs (API/tools/logging, Agent orchestration/codex/replay, Simulation quality,
  Unit·gameplay, Unit·core/world, Unit·infra/observability, Integration, Migration lanes,
  Architecture/docs/static, Perf/cert/arena, Type check) — **all passed (✓)**.
- `Slow regression` (42m6s) — **failed (X)**, specifically at the step
  `Slow tests (includes 5k behavioral regression)`. The preceding step,
  `Slow tests — corpus diversity (isolated per-test, TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-
  LOAD-FLAKE)`, **passed**. `Legacy regression` shows `-` (skipped, job already failed by then).

Per `.github/workflows/test.yml:264-266`, the failing step's exact command is:
```
pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q \
  --ignore=tests/unit/worldassembly/test_corpus_diversity.py
```
GitHub Actions sets `CI=true` automatically for every job (standard GHA behavior, not
workflow-specific config) — confirmed relevant because 6 tests in this repo carry
`@pytest.mark.skipif(os.environ.get("CI") == "true", ...)` guards (3 in
`tests/certification/test_cert_long_run_stability.py`, 1 in
`tests/integration/world/test_long_run_stability.py`, 1 in `tests/perf/test_profiler_integrity.py`
— the perf ticket's own 4 in-scope guards were already removed by
`TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION`).

This is also this repository's **first-ever completed run** of the `Slow regression` job (it only
triggers on `main`/PRs targeting `main`, and every prior run in `gh run list` completed in 2-6
minutes — too fast to have entered this job at all — until this 42-minute run). All three
findings from this run (perf calibration gaps, a determinism watchdog issue, and the
QueueDrainWorker leak) are therefore genuinely first-time-observed backlog, not regressions from
a specific recent commit.

## Reproduction Strategy

Since the exact original failure text is unrecoverable, this investigation reproduced the failing
step's **entire scope**, chunked into tool-timeout-sized batches (the sandbox's Bash tool caps
foreground commands at 600s; several of these test files run multi-hundred-tick `Kernel`
simulations that individually approach that ceiling), each run synchronously (no
background-and-wait) with `CI=true` and `--resource-budget large` to exactly match the real CI
step:

1. `tests/perf` (all `-m "slow or extra_slow"`) — 43 passed, 3 skipped (matches
   `test_profiler_integrity.py`'s guard + 2 others), 419.6s. **No leak.**
2. `tests/simulation_quality` (`test_grade_regression.py`, `test_performance.py`,
   `test_broker_feed_integration.py`) — 9 failed (all pre-existing `grade_anchors.json` score-
   tolerance drift, the same class extensively recalibrated across today's
   `TCK-20260817-STANDARD-SIMQ-*` ticket batch), 6 passed, 12 skipped, 4.34s. **No leak.**
3. `tests/integration/certification`, `tests/integration/scenarios`,
   `tests/unit/engine/test_scenario_checkpointer.py`, `tests/unit/social/test_multi_hero.py`,
   `tests/arena/test_arena_regional_control.py`,
   `tests/integration/kernel/test_milestone_b_closure.py`, `tests/regression/test_behavioral_5k.py`,
   `tests/unit/economy/test_economy_health_monitor.py`,
   `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` — 47 passed,
   1 skipped, 1 xfailed, 576.4s. **No leak.**
4. `tests/certification/test_cert_long_run_stability.py` — all 3 skip under `CI=true` (matches
   real CI's own `skipif` guards exactly — these tests never execute in CI at all). **N/A.**
5. `tests/arena/test_arena_stress.py::test_arena_stress_50v50` — 1 passed, 67.15s. **No leak** —
   this file has prior thread-leak history (`TCK-20260623-FIX-ARENA` added
   `kernel2.shutdown()` in `try/finally`); confirmed that fix still holds.
6. `tests/tools/test_knowledge_search.py`, `test_kgmcp_phase{2,3,4}_*` — grep-confirmed these
   files never construct `Kernel`/`EventRecorder`/`QueueDrainWorker` at all (semantic-search
   corpus tests, unrelated subsystem) — deprioritized/not exhaustively run to completion given
   they cannot structurally cause this class of leak.

Combined with a separate, earlier, even broader pass across the **entire non-slow fast-lane
scope** (`-m "not slow and not extra_slow"`, matching all 9 passing fast-lane jobs' own test
selection, run in ~10 directory-sized chunks covering all of `tests/unit/*`, `tests/integration/*`,
`tests/api`, `tests/engine`, `tests/observability`, `tests/simulation_quality`,
`tests/certification`, `tests/arena`, `tests/replay`, `tests/world`, `tests/scenarios`, all 16
newly-CI-wired directories from `TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS`, and every
other top-level `tests/` subdirectory) — **zero occurrences** of
`tests/conftest.py`'s `_observability_worker_thread_sentinel` failure message
(`"QueueDrainWorker thread leak detected: ..."`) anywhere, across either scope.

## Assessment

This investigation could not confirm the exact leaking test(s) the prior (unrecoverable) session
found, and a full, CI-scope-matching local reproduction (both the fast-lane 9-job scope and the
exact failing slow-lane step, run under `CI=true --resource-budget large`) did not reproduce the
`QueueDrainWorker thread leak detected` sentinel failure at all. Two hypotheses remain open,
neither of which this investigation could rule in or out without the original CI log:

1. **Hardware-timing-dependent leak**: the CI runner may be slower than this dev machine. If any
   slow/extra_slow test's `Kernel`/`EventRecorder` construction is interrupted mid-flight by
   `tests/conftest.py`'s `SIGALRM`-based per-test timeout handler (fired via `--resource-budget
   large`'s 600s window) without a `try/finally`-guarded `shutdown()`, the resulting orphaned
   worker thread would only appear on a CI runner slow enough to hit that 600s ceiling — which
   this dev machine, empirically, did not (the closest case, `test_arena_stress_50v50`, completed
   in 67s here vs. presumably much longer on CI hardware given the job's 42-minute total runtime).
   This is consistent with, but not proven by, the evidence gathered.
2. **Session/ordering-dependent leak**: CI runs the single unchunked command
   `pytest tests/ -m "slow or extra_slow" ...` across the whole tree in one process/collection
   order; this investigation ran the same test set in several separately-invoked chunks (required
   by the sandbox's 600s per-command ceiling), which resets Python's module/thread state between
   chunks. A leak that only manifests from specific cross-test ordering or accumulated global
   state within one long-lived process would not surface under chunked reproduction. This could
   not be tested within this session's time/tooling constraints (a true single-command run of the
   full ~166-test slow/extra_slow scope was attempted once and did not complete within any single
   available synchronous window).

Per this repo's Hard Rule against guessing when uncertainty affects behavior/architecture, no
speculative `src/` change was made against either hypothesis. See `plan.md` for the disclosed
recommendation (re-run the real CI slow job now that its blocking siblings — perf calibration,
determinism — are already fixed; if the sentinel fires again, GitHub's own log UI, viewed by a
human or an environment without this sandbox's DNS block, will show line-level attribution that
this investigation's tooling cannot obtain).
