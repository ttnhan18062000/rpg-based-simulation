---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
phase: done
date: 2026-08-17
tags: [observability]
---

# TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC

## Title
Fix WebhookAlertSink's backoff/circuit-breaker gap; targeted review of highest-consequence broad-except sites

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`WebhookAlertSink` — the only real retry/backoff implementation in the codebase — is linear
despite an in-code comment claiming exponential backoff, has no jitter, and no circuit breaker,
so a permanently-dead webhook endpoint receives the full retry sequence on every single alert
forever. Separately, 481 broad `except Exception`/bare `except` sites coexist with a 40+-class
exception taxonomy largely unused by callers — both source audits explicitly caution against a
blanket sweep; this epic is scoped to a targeted review of the highest-consequence sites only.

## Scope
Full findings are in `docs/plans/error_handling_hygiene_epic.md`. Concrete scope:
- Fix `WebhookAlertSink`'s misleading "exponential backoff" comment (either correct the comment
  or implement real exponential backoff+jitter).
- Add a simple circuit breaker to `WebhookAlertSink` (open after N consecutive failures,
  half-open retry).
- A targeted review of the highest-consequence broad-except sites only (state mutation,
  persistence, replay) — not a repo-wide sweep of all 481 occurrences.

## Out of Scope
- Any blanket "replace every broad except" initiative — explicitly not recommended by either
  source audit.
- Adding retry/backoff to any subsystem beyond `WebhookAlertSink` unless the targeted review
  finds a specific, confirmed need.

## Acceptance Criteria
- [x] `WebhookAlertSink`'s backoff behavior matches its own in-code documentation (real
      exponential+jitter, or an honest comment).
- [x] A circuit breaker prevents indefinite full-sequence retries against a dead endpoint.
- [x] The targeted broad-except review names specific sites reviewed and their disposition — not
      a count-reduction metric applied blindly.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/error_handling_hygiene_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/plan.md
- stored_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/investigation.md
- stored_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/test_plan.md

## Related Code Areas
- src/observability/alerts/sinks.py

## Assumptions / Open Questions
- Which specific broad-except sites count as "highest-consequence" needs confirming at Plan time.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; two related, contained threads of work under
  one "error-handling hygiene" theme — one standard ticket, not a multi-ticket initiative.
  `staging_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/` not yet created.

## Implementation Notes

**Step 1 — Real exponential backoff with jitter** (`src/observability/alerts/sinks.py`): added
`BACKOFF_BASE_SECONDS = 0.5`, `BACKOFF_CAP_SECONDS = 10.0`, `BACKOFF_JITTER_RATIO = 0.2` as class
constants on `WebhookAlertSink`, and a new `_compute_backoff_delay(attempt, rng=None)` method
directly mirroring `RedisStreamConsumer._compute_backoff_delay` (`src/observability/stream/consumer.py`).
Replaced the old `time.sleep(0.5 * attempt)` (linear) call in `_dispatch_with_retry` with
`time.sleep(self._compute_backoff_delay(attempt))`, and corrected the misleading
"exponential backoff" comment above it to "Exponential backoff with jitter before retry (capped)".
Added `import random`.

**Step 2 — Circuit breaker**: added `CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5` and
`CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60.0` as class constants. `__init__` gained four new instance
attributes: `_circuit_state` ("closed"/"open"/"half_open"), `_consecutive_failures`,
`_circuit_opened_at`, and `_circuit_lock` (a `threading.Lock`, requiring `import threading`).
Added `_circuit_allows_dispatch()` (closed→True; open→transitions to half_open and returns True
once the cooldown has elapsed, else False; half_open→False, so only the call that performed the
open→half_open transition gets to dispatch, preventing two concurrent probes racing on the
2-worker executor) and `_record_outcome(success)` (resets failure count and closes the circuit on
success from half_open; increments failure count on failure, reopening from half_open or opening
from closed once the threshold is hit). `send()` now calls `_circuit_allows_dispatch()` before
submitting to the executor and returns `False` (the sink's existing "did not deliver" convention)
if the circuit disallows dispatch — no change to `send()`'s signature or return type.
`_dispatch_with_retry` calls `_record_outcome(success=True)` on the 2xx-return path and
`_record_outcome(success=False)` on final exhaustion, both without changing its own return type.
Circuit-breaker tunables ship as fixed class constants, not new env vars, per the plan's
Step 2 justification (no existing "extra tunable" precedent in `manager.py` to extend, and the
sibling `RedisStreamConsumer` backoff addition set the same fixed-constant precedent).

**Step 3 — Timing-sensitive integration test**: ran
`tests/integration/observability/test_alert_webhook_sink.py` after Steps 1-2 landed (not assumed).
All 7 tests pass, including `test_server_error_does_not_crash` (`max_retries=2`, fixed
`time.sleep(4.0)` wait) — re-ran it twice in isolation (4.27s, 4.67s) to check for jitter-driven
flakiness. With the new formula, the single inter-attempt delay for `max_retries=2` is
`min(10.0, 0.5 * 2**0) = 0.5s ± 0.1s jitter`, i.e. in `[0.4, 0.6]`s — well inside the existing
4.0s budget. **No change was needed to the sleep constant or any other line in this file.**

**Step 4 — New unit test file**: created `tests/unit/observability/test_webhook_alert_sink.py`
(no unit-level test file existed for `sinks.py` before this ticket). Implements the 5 tests the
plan specifies (`test_backoff_delay_is_exponential_not_linear`, `test_backoff_has_jitter`,
`test_circuit_breaker_opens_after_consecutive_failures`,
`test_circuit_breaker_half_open_retry_recovers`,
`test_circuit_breaker_open_send_returns_false_not_silent`), skipping #3
(`test_comment_matches_implementation`) per the plan's and test_plan's own recommendation. Added
one additional test not in the plan's list, `test_backoff_delay_caps_at_bound`, mirroring
`RedisStreamConsumer`'s own `test_reconnect_backoff_caps_at_bound` — see plan.md Deviations. All
6 tests pass deterministically (0.26-0.41s total, no wall-clock sleeps — cooldown elapse is
simulated by monkeypatching `_circuit_opened_at` into the past rather than sleeping 60s; failure
injection uses `requests.ConnectionError`, since `_dispatch_with_retry` only catches
`requests.RequestException`, not bare `Exception` — a bare-`Exception` side effect was tried
first and correctly propagated uncaught, confirming the catch clause is not overly broad).

**Step 5 — Broad-except review disposition** (transcribed from `investigation.md`, no code
change to any of the six files below):
- `src/engine/apply.py` (the authoritative mutation apply path): **zero** broad-except sites.
  Clean by construction.
- `src/core/registries.py` (7 sites, content/catalog adapters): every site follows
  `except Exception as e: raise AdapterError(...) from e` — converts a broad catch into a typed,
  re-raised exception. Already the correct pattern; no action needed.
- `src/engine/kernel.py` (25 broad-except sites, the highest concentration reviewed): sampled
  hard-law-violation audit-log writes (`except Exception: logger.exception(...)` — losing only
  the audit trail, not authoritative state, since `CERTIFICATION`/`DEBUG` modes separately raise
  `HardLawViolationError` for real enforcement), post-commit event-listener/cognition-snapshot
  notification (explicitly post-commit, non-authoritative), and shutdown-path cleanup (each
  logged as "(non-fatal)" in its own message). Consistent with the audit's own characterization:
  a deliberate containment pattern, not an accidental swallow.
- `src/engine/replay_sink.py` (2 sites) / `src/engine/replay_manager.py` (4 sites): every site is
  governed by in-code law comments (`# M6 Law: Non-authoritative fallback`, `# M7 Law`, budget/
  INFRA-060 references). Replay persistence is documented, by design, as best-effort — failures
  become a metrics/status update, never a crash. No action needed.
- `src/engine/worker_manager.py` (4 sites): `_wrap_work` converts a caught exception into a typed
  `WorkerResult(status=ResultStatus.FAILURE)` rather than swallowing it — a structural bulkhead
  pattern, not a silent drop.
- `src/engine/tactical.py` (2 sites) / `src/engine/combat_rewards.py` (1 site): each catch has an
  adjacent comment explaining the specific fallback behavior (permissive perception-gate fallback;
  legacy `EntityRole` reward-classification fallback when the relation service is unavailable).

**Disposition: no broad-except site found across these six areas needs fixing under this
ticket's scope** — every reviewed site either (a) re-raises as a typed exception, (b) converts
the failure into a typed status/result value, or (c) is explicitly documented as an intentional
non-authoritative fallback. `src/api/` and `src/lab/` were not reviewed (flagged by
investigation.md as the largest remaining unreviewed pools of broad-except sites, and as the next
place to look if a future ticket wants broader confidence) — reviewing them is new scope, not
performed here.

**Step 6 — Parity ledger + docs**: added `INFRA-362` to `docs/parity_ledger/infrastructure.yaml`
(status `verified`, priority `P2`, `v2_evidence` citing `_compute_backoff_delay`/
`_circuit_allows_dispatch`/`_record_outcome`, `test_path` citing
`test_circuit_breaker_opens_after_consecutive_failures`); validated with
`yaml.safe_load`. Added a `## Status: Resolved` section to
`docs/plans/error_handling_hygiene_epic.md` (mirroring `dead_infra_removal_epic.md`'s format) and
marked Epic H's section in `docs/plans/architecture_resilience_remediation_roadmap.md` with the
same `Status: Resolved` marker Epics A, B, E, G already carry. `docs/audits/D23_architecture_resilience.md`
was left untouched (historical snapshot), consistent with precedent.

## Test Summary

```
pytest tests/unit/observability/test_webhook_alert_sink.py -v          -> 6 passed
pytest tests/integration/observability/test_alert_webhook_sink.py -v   -> 7 passed (incl. test_server_error_does_not_crash, re-verified twice for jitter stability)
pytest tests/unit/observability/test_alert_router.py tests/unit/observability/test_watchdog.py -v -> 26 passed
```
No test file was modified — `test_alert_webhook_sink.py` (integration) needed no change, and all
new coverage lives in the new unit test file. `send()`'s external contract regression coverage
(`test_run_cycle_trip_routes_alert_event`, `test_sink_exception_does_not_crash`) passes
unmodified, confirming `INFRA-358`'s watchdog-trip wiring is unaffected.

## Files Changed
- `src/observability/alerts/sinks.py` — real exponential backoff+jitter, 3-state circuit breaker
  (behavior change)
- `tests/unit/observability/test_webhook_alert_sink.py` — new file, 6 unit tests
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-362`
- `docs/plans/error_handling_hygiene_epic.md` — added `## Status: Resolved` section
- `docs/plans/architecture_resilience_remediation_roadmap.md` — marked Epic H `Status: Resolved`
- `staging_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/plan.md` — added Deviations section
- `staging_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/investigation.md` — written during
  the Investigate phase (pre-existing part of this run, not a later edit).
- `staging_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/test_plan.md` — written during the
  Investigate phase (pre-existing part of this run, not a later edit).
- `tickets/inprogress/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria, Status, Related
  Stored Artifacts)

## Completion Summary
Implemented all 6 plan steps for `WebhookAlertSink`: replaced its linear, comment-mismatched
retry sleep with a real capped-exponential-with-jitter `_compute_backoff_delay` (mirroring the
sibling `RedisStreamConsumer` precedent), and added a 3-state closed/open/half-open circuit
breaker (fixed class-constant tunables, instance-scoped state) that stops indefinite retry
sequences against a dead endpoint while keeping `send()`'s external signature and fire-and-forget
contract byte-for-byte unchanged. Ran the pre-flagged timing-sensitive integration test
(`test_server_error_does_not_crash`) after the change and confirmed empirically — not assumed —
that its existing `4.0`s sleep budget still comfortably covers the new schedule, so no test edit
was needed there. Added a new unit test file (6 deterministic, non-sleeping tests) covering the
backoff math and all three circuit-breaker transitions, and transcribed the investigation's
six-area broad-except review disposition (zero sites requiring a fix) into this ticket. Closed
out with a new `INFRA-362` parity ledger entry and matching `Status: Resolved` updates to both the
epic plan doc and the remediation roadmap, following the exact format the sibling A/B/E/G epics
already established.
