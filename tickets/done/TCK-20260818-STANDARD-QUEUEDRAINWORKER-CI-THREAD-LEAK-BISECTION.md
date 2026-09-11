---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION
phase: done
date: 2026-08-18
tags: [observability, investigation, testing, root-cause]
---

# TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION

## Title
Resume and complete an interrupted `QueueDrainWorker` thread-leak bisection from CI run
`32046239870`'s `Slow regression` job — investigation could not recover the original session's
findings and could not reproduce the leak locally under CI-matching conditions

## Status
BLOCKED

## Tier
standard

## Type
bug (investigation — no live defect reproduced; see Completion Summary)

## Priority
P1

## Request Summary
A prior session was investigating a `QueueDrainWorker` thread leak (tests/conftest.py's
session-scoped `_observability_worker_thread_sentinel`) and had launched a background bisection
run to identify the specific leaking test(s), then stopped without a driver to bring it forward,
leaving the investigation stalled with no ticket, staging artifact, or `agent-monitoring/` record
of what it had found. This ticket resumes that investigation from scratch. Two sibling tickets
closed earlier in the same overall session (`TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-
CALIBRATION`, `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE`) both independently
reference "the sibling `QueueDrainWorker` thread-leak finding from the same CI run" as an
established fact from CI run `32046239870`'s `Slow regression` job, but neither names the specific
test — confirming a real leak was observed, without providing the detail needed to fix it.

## Scope
- Recover any persisted state from the prior session (tickets, staging artifacts, monitoring
  records, git status/stash/reflog) — none found.
- Attempt to obtain the original CI run's raw failure log for exact test attribution.
- Reconstruct and locally reproduce the exact failing CI step
  (`pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q
  --ignore=tests/unit/worldassembly/test_corpus_diversity.py`, `CI=true`) to identify the leaking
  test(s) via the `_observability_worker_thread_sentinel` fixture.
- Also reproduce the full fast-lane scope in case of mis-attribution.
- Fix the real leak in `src/`/`tests/` **if found** — not found; see Completion Summary.

## Out of Scope
- The two sibling findings from the same CI run (perf calibration, determinism watchdog) — both
  already closed by their own tickets, not touched here.
- `tests/integration/world/test_long_run_stability.py`, `docs/audits/D06_longrun_health.md` —
  currently uncommitted, in-flight changes owned by
  `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE`'s session; explicitly not
  modified or committed by this ticket (shared working tree).
- Loosening or removing the `_observability_worker_thread_sentinel` sentinel, or any other change
  that would make a real leak stop being detected — explicitly disallowed regardless of outcome.

## Acceptance Criteria
- [x] Context Scan run before investigation (`search_docs`, `graphify query`, grep across
      `tickets/`, `stored_artifacts/`, `agent-monitoring/`)
- [x] Attempted recovery of the original background bisection task/output — not recoverable
      (no process, no output file, no `agent-monitoring` record under any plausible run_id)
- [x] Attempted to fetch the real CI log for exact test attribution — blocked at the network/DNS
      level in this sandbox (see Completion Summary), not a fixable-in-scope issue
- [x] Reproduced the exact failing CI step's full test scope locally under matching conditions
      (`CI=true --resource-budget large`), synchronously, without background-and-wait
- [x] Reproduced the full fast-lane scope as a cross-check
- [ ] Specific leaking test(s) identified — **not achieved**; see Completion Summary
- [ ] Fix applied and verified — **not achieved**, correctly: no reproducible defect to fix would
      mean fabricating a change with no real effect, explicitly disallowed
- [x] Full standard-tier ticket/staging-artifact discipline followed

## Related Tickets
- TCK-20260610-WORKER-SINGLETON-GUARD (DONE — prior real fix, `get_or_start_global_worker()`)
- TCK-20260610-THREAD-LEAK-CONFTEST (DONE — added the session-scoped sentinel this investigation
  relies on)
- TCK-20260623-FIX-OBS-QUEUE, TCK-20260623-FIX-ARENA, TCK-20260624-FIX-MOCK-SERIAL,
  TCK-20260624-FIX-PERF-BUDGETS, TCK-20260624-FIX-WORKER-SHUTDOWN (DONE — prior leak fixes;
  spot-verified still holding, e.g. `test_arena_stress_50v50` still passes clean)
- TCK-20260702-OBSISO-TRACE-ASYNC (DONE — most recent related observability/QueueDrainWorker fix)
- TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION (DONE — sibling, same CI run, perf
  calibration; explicitly notes no shared root cause with this leak)
- TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE (DONE — sibling, same CI run,
  determinism watchdog fix; explicitly notes this leak as a separate, unresolved finding)
- TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS (DONE — wired 16 previously-never-run
  directories into fast-lane CI this session; ruled out as the leak source, all now run clean)

## Related Docs
None created/modified — investigation-only.

## Related Stored Artifacts
staging_artifacts/TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION/ (migrated to
stored_artifacts/ at Finalize)

## Related Code Areas
- `tests/conftest.py` (`_observability_worker_thread_sentinel`, read only, not modified)
- `tests/tools/memory_probe.py` (`count_drain_workers()`, read only)
- `src/observability/queue.py` (`QueueDrainWorker`, `get_or_start_global_worker()`, read only)
- `.github/workflows/test.yml` (`slow` job definition, read only)
- Every `tests/` file constructing a real `Kernel`/`EventRecorder` (~70 files, enumerated in
  `investigation.md`) — exercised via full CI-scope reproduction, none modified

## Assumptions / Open Questions
- Whether the leak is CI-hardware-timing-dependent (a `SIGALRM`-interrupted `Kernel`/
  `EventRecorder` construction without `try/finally` cleanup, only reachable on slower CI
  hardware) or session/ordering-dependent (only manifests in one unchunked ~166-test process, not
  this investigation's necessarily-chunked reproduction) — both left open, disclosed in
  `investigation.md`, neither can be resolved without either CI log access or a genuinely
  non-time-boxed single-process reproduction.
- Whether the leak still reproduces at all now that the two sibling CI-blocking findings from the
  same run are fixed — genuinely unknown; the next real CI run of the `Slow regression` job will
  answer this with full log access unaffected by this sandbox's network block.

## Implementation Notes
No `src/` or `tests/` file was changed by this ticket. Full evidence chain, reproduction command
list, and the two open hypotheses are in `staging_artifacts/.../investigation.md`. Recommendation
(not executed, requires human/orchestrator follow-through) is in `plan.md`.

## Test Summary
See `test_plan.md` for the full list of ~15 reproduction commands run synchronously across both
the fast-lane and slow-lane CI-matching scopes. Net result: zero occurrences of
`tests/conftest.py`'s `"QueueDrainWorker thread leak detected"` sentinel failure in either scope;
all other failures encountered are pre-existing and independently tracked (SimQ calibration
drift, live-server-subprocess `pydantic`-missing connection failures, one perf-flake timing
assertion).

## Files Changed
None under `src/`, `tests/`, or `config/`. This ticket, its staging artifacts,
`agent-monitoring/`, `tickets/working_log.csv`, and `docs/REGISTRY.yaml` are the only repo
changes made by this ticket.

## Completion Summary
Resumed an interrupted `QueueDrainWorker` thread-leak investigation with no recoverable prior
session state. Confirmed via two sibling tickets that a real leak was genuinely observed in CI run
`32046239870`'s `Slow regression` job, but could not obtain the original log (this sandbox's
network policy — a Fortinet DNS security portal — blocks the Azure blob-storage domain GitHub
Actions uses to deliver job logs; confirmed by following `gh`'s own signed URL directly with
`curl`, which returned an explicit "Web Page Blocked!" page rather than real log content).
Reconstructed the exact failing CI command from `.github/workflows/test.yml` and reproduced its
full test scope locally in `CI=true --resource-budget large` mode, synchronously and without
background-and-wait, across ~15 chunked batches (required by this sandbox's 600s per-command
ceiling) covering every `tests/` file that constructs a real `Kernel`/`EventRecorder`/
`QueueDrainWorker` in both the slow-lane (exact failing step) and fast-lane (all 9 passing jobs)
scopes. Found zero occurrences of the leak sentinel firing in either scope — only pre-existing,
already-independently-tracked failures (SimQ grade-anchor drift, live-server-subprocess
environment issues, one perf timing flake). Per this repo's Hard Rule against acting on
unvalidated context or fabricating a fix for a defect that doesn't reproduce, no speculative
`src/` change was made. Reported as BLOCKED (not DONE, since two independent sibling
investigations corroborate a real leak existed in that CI run, so "no bug" cannot be honestly
concluded either) with two disclosed, unresolved hypotheses (CI-hardware-timing-dependent
interrupt-during-construction, or single-process/ordering-dependent state) and a concrete
recommendation: re-run the real CI slow job now that its two sibling blockers are fixed, and if it
reproduces, use GitHub's own log UI (unaffected by this sandbox's network block) for exact
attribution.
