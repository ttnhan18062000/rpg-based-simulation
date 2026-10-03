---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION
artifact_type: plan
tags: [observability, investigation, testing, root-cause]
---

# Plan — TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION

## Objective

Identify and fix the specific test(s) responsible for the `QueueDrainWorker` thread-leak finding
from CI run `32046239870`'s `Slow regression` job, referenced (but not detailed) by two sibling
tickets from the same session (`TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION`,
`TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE`).

## Steps Taken

1. Context scan: `search_docs`, `graphify query "QueueDrainWorker"`, grep across
   `tickets/`, `stored_artifacts/`, `agent-monitoring/` for any recoverable prior session state —
   none found (see `investigation.md`, "Session Continuity Note").
2. Attempted to fetch the real CI run's raw log text via `gh run view --log-failed`, `--job=<id>
   --log`, and the underlying signed blob-storage URL directly via `curl -sk` — blocked at the
   network/DNS level by this sandbox's Fortinet DNS security policy (confirmed via the literal
   "Web Page Blocked!" response body, not a real cert failure despite the reported error text).
3. Reconstructed the exact failing CI command from `.github/workflows/test.yml` and reproduced
   its full test scope locally, chunked into synchronous (non-backgrounded) batches under
   `CI=true --resource-budget large` to match the real CI environment exactly.
4. Separately reproduced the **entire fast-lane scope** (`-m "not slow and not extra_slow"`,
   matching all 9 passing fast-lane CI jobs combined) across essentially every `tests/` directory,
   in case the leak was mis-attributed to the slow lane.
5. Zero occurrences of the `_observability_worker_thread_sentinel` failure
   (`tests/conftest.py:199-218`) in either scope.

## Outcome

**No fix was made.** The leak could not be reproduced locally under either CI-matching scope, and
the original CI log (the only source of the specific failing test/session detail) is unreachable
in this sandbox. Per this repo's Hard Rule against acting on unvalidated context or guessing when
uncertainty affects architecture, no speculative code change was made. This is reported as
**BLOCKED**, not DONE (a definitive "no bug exists" conclusion is not warranted — two independent
sibling tickets treat the leak as an established, real finding from the same CI run, which this
investigation has no basis to contradict) and not a fabricated fix.

## Recommendation (disclosed, not executed — requires human/orchestrator decision)

1. Now that this CI run's two other blocking findings are already fixed and committed
   (`305236bf` perf calibration, and the uncommitted-but-complete
   `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE` determinism fix — not touched by
   this ticket, left for its own owning session to commit), the next real CI run of the `Slow
   regression` job will either (a) reproduce the leak with full, human-readable log access via
   GitHub's own UI (unaffected by this sandbox's network block), giving exact test attribution, or
   (b) not reproduce it, which would itself be informative (suggesting a hardware-timing-window
   interaction with tests already touched by the sibling fixes, or a genuinely transient/flaky
   leak).
2. If it reproduces again: bisect by re-running the CI step's exact command
   (`pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q
   --ignore=tests/unit/worldassembly/test_corpus_diversity.py`) as a **single unchunked** CI-native
   invocation (this sandbox's 600s foreground-command ceiling could not fit this; a real CI runner
   or a less time-boxed environment can) so that cross-test/ordering-dependent leaks (this
   investigation's hypothesis 2, see `investigation.md`) are not masked by chunking.
3. Do not add a broad `try/except` swallow or loosen the sentinel's tolerance to make the gate
   pass — per this repo's explicit Hard Rule, that would hide the underlying leak rather than fix
   it.
