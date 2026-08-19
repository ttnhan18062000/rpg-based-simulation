---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
artifact_type: plan
tags: [observability]
---

# Implementation Plan — TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC

## Summary

`WebhookAlertSink` (`src/observability/alerts/sinks.py`) gets two additive changes to its private
retry internals — a real capped-exponential-with-jitter backoff (replacing the linear
`time.sleep(0.5 * attempt)`) and a 3-state (closed/open/half-open) circuit breaker gated in front
of dispatch — while `send(alert: AlertEvent) -> bool`'s external signature and fire-and-forget
semantics stay byte-for-byte unchanged, since `AlertRouter.route()` and `INFRA-358`'s
watchdog-trip wiring depend on it as-is. Both new mechanisms follow the shape of the sibling
`RedisStreamConsumer._compute_backoff_delay` precedent (class-level constants, injectable `rng`),
adapted to this sink. Circuit-breaker tunables ship as fixed class constants, not new env vars —
see Step 2's Change section for the concrete decision and justification. The targeted
broad-except review is already complete as investigation (no dangerous site found); this plan's
only broad-except deliverable is transcribing that disposition into the ticket body, not a code
change. Two parity/doc updates close out the ticket per repo convention.

## Steps

### Step 1 — Real exponential backoff with jitter, replacing the linear sleep

**Files:** `src/observability/alerts/sinks.py`

**Change:** In `WebhookAlertSink` (class body starts at `sinks.py:39`, confirmed by direct read):

1. Add three class-level constants directly under the class docstring (mirroring
   `RedisStreamConsumer.BACKOFF_BASE_SECONDS`/`BACKOFF_CAP_SECONDS`/`BACKOFF_JITTER_RATIO` at
   `src/observability/stream/consumer.py:19-21`, confirmed by direct read):
   ```python
   BACKOFF_BASE_SECONDS = 0.5
   BACKOFF_CAP_SECONDS = 10.0
   BACKOFF_JITTER_RATIO = 0.2
   ```
   `BACKOFF_BASE_SECONDS = 0.5` is chosen to match the current formula's first-attempt delay
   (`0.5 * 1` today, confirmed at `sinks.py:89`), so the common case (`max_retries=3`, the
   constructor default at `sinks.py:45`) doesn't get slower than today — only the *growth* from
   attempt to attempt changes from linear to exponential. `BACKOFF_CAP_SECONDS = 10.0` bounds
   worst case if `SIM_ALERTS_WEBHOOK_RETRIES` is configured higher than the default 3 (read at
   `src/observability/alerts/manager.py:42-46`).
2. Add a `_compute_backoff_delay` method, directly adapted from
   `consumer.py:41-45` (confirmed by direct read):
   ```python
   def _compute_backoff_delay(self, attempt: int, rng: Optional["random.Random"] = None) -> float:
       capped = min(self.BACKOFF_CAP_SECONDS, self.BACKOFF_BASE_SECONDS * (2 ** max(0, attempt - 1)))
       jitter = capped * self.BACKOFF_JITTER_RATIO
       r = rng or random
       return max(0.0, capped + r.uniform(-jitter, jitter))
   ```
   Requires adding `import random` to `sinks.py` (not currently imported — confirmed, only
   `logging, requests, json, time` are imported at `sinks.py:1-4`).
3. Replace the sleep call at `sinks.py:89` (`time.sleep(0.5 * attempt)`) with
   `time.sleep(self._compute_backoff_delay(attempt))`.
4. Correct the misleading comment at `sinks.py:87` (`# Short sleep before retry (exponential
   backoff)`) — after this change the comment becomes literally true, but reword it to name the
   actual mechanism: `# Exponential backoff with jitter before retry (capped)`.

**Do NOT touch:** `_dispatch_with_retry`'s loop structure (`for attempt in range(1, self.max_retries
+ 1)`, `sinks.py:65`), the `requests.RequestException` catch (`sinks.py:81`), or the status-code
handling (`sinks.py:73-80`) — none of that is in scope for the backoff fix.

**Verify:** `tests/unit/observability/test_webhook_alert_sink.py::test_backoff_delay_is_exponential_not_linear`
and `::test_backoff_has_jitter` (new, written in this step — see Step 4 for exact assertions).

---

### Step 2 — Circuit breaker (closed / open / half-open)

**Files:** `src/observability/alerts/sinks.py`

**Change:**

**Decision on config surface (resolving the investigation's open question):** circuit-breaker
tunables ship as **fixed class-level constants**, not new `SIM_ALERTS_WEBHOOK_*` env vars.
Justification, checked against the actual code (not inferred):
- `AlertsManager.get_router()` (`manager.py:16-67`, confirmed by direct read) resolves exactly
  four `WebhookAlertSink`-related env-var pairs today — `SIM_ALERTS_WEBHOOK_URL`,
  `_ENABLED`, `_TIMEOUT`, `_RETRIES` (lines 30-46) — each mapped straight to an existing
  constructor parameter (`webhook_url`, `enabled`, `timeout_seconds`, `max_retries`, passed at
  lines 57-62). There is no existing "extra tunable, no constructor param" precedent in this
  file to extend from.
- The nearest sibling precedent for *this exact kind of addition* — a resilience mechanism newly
  added to an existing class in this same session (`RedisStreamConsumer`'s backoff, `INFRA-361`)
  — shipped as fixed class constants (`consumer.py:19-21`) with **no** env-var override, despite
  `RedisStreamConsumer` having its own env-var-free constructor precedent it could have followed
  instead. Fixed constants is the established pattern for *new* resilience knobs in this
  codebase, not configurable ones.
- The ticket's AC #2 only requires that "a circuit breaker prevents indefinite full-sequence
  retries" — it does not require operators to tune it. Adding new env vars would require touching
  `manager.py`'s config-resolution block (lines 21-46), which is out of this ticket's named scope
  (`src/observability/alerts/sinks.py` per the ticket's Related Code Areas) and is unnecessary
  scope growth for a P2 ticket with exactly one process-wide singleton sink today.

Constants (add alongside the Step 1 constants):
```python
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5   # consecutive failed full-dispatch cycles to open
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60.0  # time in OPEN before a half-open probe is allowed
```
"Failed full-dispatch cycle" = one call to `_dispatch_with_retry` that exhausts all
`max_retries` attempts without a 2xx response (i.e. it returns `False`) — not one HTTP attempt.
This matches the ticket Scope's literal wording, "open after N consecutive failures," where the
unit of failure in the existing code is already the per-alert dispatch, not the per-attempt POST.

State (add to `__init__`, `sinks.py:45-51`), instance-scoped per the investigation's Mechanics
constraint (durable-for-process-lifetime state must be explicit instance attributes, not a
module-level global — no other `WebhookAlertSink` instance exists to share state with today, and
`AlertsManager` constructs exactly one per `get_router()` call):
```python
self._circuit_state = "closed"          # "closed" | "open" | "half_open"
self._consecutive_failures = 0
self._circuit_opened_at = 0.0
self._circuit_lock = threading.Lock()   # requires `import threading`, not currently imported
```

Gate in `send()` (`sinks.py:53-59`), **before** `self._executor.submit(...)`, so an
open-and-not-cooled-down circuit never spends an executor thread:
```python
def send(self, alert: AlertEvent) -> bool:
    if not self.enabled or not self.webhook_url:
        return False
    if not self._circuit_allows_dispatch():
        return False
    self._executor.submit(self._dispatch_with_retry, alert)
    return True
```
`_circuit_allows_dispatch()` (new private method, holds `self._circuit_lock` for its full body):
- `closed` → return `True`.
- `open` → if `time.time() - self._circuit_opened_at >= self.CIRCUIT_BREAKER_COOLDOWN_SECONDS`,
  transition state to `"half_open"` and return `True` (this call becomes the probe); else return
  `False` without mutating state.
- `half_open` → return `False` (a probe is already in flight; only the call that performed the
  `open`→`half_open` transition gets to dispatch — this prevents concurrent probes since the
  2-worker executor could otherwise race two probes at once).

At the end of `_dispatch_with_retry` (`sinks.py:61-92`), after the existing final
`logger.error(...)` / before `return False`, and immediately before each existing `return True`
inside the loop, call a new `_record_outcome(success: bool)` helper (holds `self._circuit_lock`
for its full body) instead of returning directly:
- `success=True`: `self._consecutive_failures = 0`; if state was `half_open`, set state to
  `"closed"`. (A success while `closed` is a no-op beyond the reset, which was already 0.)
- `success=False`: `self._consecutive_failures += 1`; if state was `half_open`, set state back to
  `"open"` and reset `self._circuit_opened_at = time.time()` (reopen, restart cooldown). If state
  was `closed` and `self._consecutive_failures >= self.CIRCUIT_BREAKER_FAILURE_THRESHOLD`, set
  state to `"open"` and `self._circuit_opened_at = time.time()`.

This satisfies the investigation's anti-drift hazard directly: when the circuit is open, `send()`
returns `False` (the sink's existing "did not deliver" convention, same value already returned
for the disabled-sink case at `sinks.py:55`) rather than silently discarding the alert with no
signal — the caller (`AlertRouter.route()`, unaffected, still gets a `bool` back) cannot tell
"disabled" apart from "circuit open" from this return value alone, which is acceptable since
neither case is new information loss beyond what `send()`'s contract already exposes today
(it never distinguished failure *reasons* via return value; that's what `logger.warning`/`.error`
calls are for).

**Do NOT touch:** `send()`'s signature (`alert: AlertEvent) -> bool` must not change), `router.py`
or `manager.py`'s env-var resolution block (`manager.py:21-46`), or add a `CircuitBreaker` class —
per investigation, no such class exists anywhere in `src/` and none is needed; a few instance
attributes plus two small methods on `WebhookAlertSink` is the full scope, sized as the
investigation recommended ("simple 3-state open/half-open/closed counter, not a library
dependency").

**Verify:**
`tests/unit/observability/test_webhook_alert_sink.py::test_circuit_breaker_opens_after_consecutive_failures`,
`::test_circuit_breaker_half_open_retry_recovers`,
`::test_circuit_breaker_open_send_returns_false_not_silent`.

---

### Step 3 — Update the timing-sensitive integration regression test

**Files:** `tests/integration/observability/test_alert_webhook_sink.py`

**Change:** `test_server_error_does_not_crash` (lines 108-135, confirmed by direct read) uses
`max_retries=2` and waits `time.sleep(4.0)` (line 130) before asserting `len(_received.payloads)
== 2`. With `max_retries=2`, the retry loop (`sinks.py:65`, `if attempt < self.max_retries` at
`sinks.py:88`) only sleeps once, after `attempt=1`. Under the new formula
(`BACKOFF_BASE_SECONDS=0.5`, exponent `2**(1-1)=1`, so `capped = min(10.0, 0.5*1) = 0.5`, jitter
`±0.1`), the single inter-attempt delay is in `[0.4, 0.6]` seconds — materially the same order of
magnitude as today's `0.5 * 1 = 0.5` fixed delay. The existing `4.0` second wait has ~3.4s of
slack over this, so **run the test after Steps 1-2 land and confirm it still passes as-is** rather
than assuming; only shorten/lengthen the `time.sleep(4.0)` constant if the actual run shows it's
needed (do not preemptively guess a new value — this is the test-plan's explicit instruction:
"verify it still passes rather than assuming the existing sleep budget covers the new schedule").

Also re-run (unmodified, no code change expected) as regression confirmation: `test_successful_delivery`
(lines 75-106), `test_connection_timeout_does_not_crash` (lines 137-158),
`test_disabled_sink_does_not_send` (lines 160-178), and all of `TestAlertsManagerIntegration`
(lines 181-201) — none of these touch the retry loop or circuit breaker, they exist to confirm
Steps 1-2 didn't regress the sink's other paths (disabled-sink short-circuit, single-shot success,
manager singleton lifecycle across `reset()`).

**Do NOT touch:** `webhook_server` fixture, `_MockWebhookHandler`, `reset_state` fixture — no
reason for these to change.

**Verify:** `pytest tests/integration/observability/test_alert_webhook_sink.py -v` — all 7
existing tests pass.

---

### Step 4 — New unit test file for backoff math and circuit-breaker state

**Files:** `tests/unit/observability/test_webhook_alert_sink.py` (new file — none exists today for
`sinks.py` at the unit level, confirmed: only `tests/integration/observability/test_alert_webhook_sink.py`
exists, per `ls tests/unit/observability/` not containing this name)

**Change:** Add the five tests specified in `test_plan.md`'s "New Tests Required" #1, #2, #4, #5,
#6 (skip #3 per test_plan's own recommendation — "do not add a test that only asserts
prose-matching"):

1. `test_backoff_delay_is_exponential_not_linear` — call `sink._compute_backoff_delay(attempt,
   rng=random.Random(<fixed seed>))` for attempt=1,2,3 with jitter neutralized by asserting on the
   `capped` midpoint (or by computing expected value with the same seeded RNG) — assert the ratio
   between successive delays is ≈2x (not the ≈1.33x/1.5x pattern linear growth would show for
   these attempt numbers), per AC #1.
2. `test_backoff_has_jitter` — call `_compute_backoff_delay(2, rng=random.Random(1))` and
   `_compute_backoff_delay(2, rng=random.Random(2))`, assert the two results differ.
3. `test_circuit_breaker_opens_after_consecutive_failures` — construct a `WebhookAlertSink`
   pointed at an unreachable/mocked-failing URL, call `_dispatch_with_retry` (or `send` +
   `shutdown(wait=True)` to flush the executor) `CIRCUIT_BREAKER_FAILURE_THRESHOLD` times with
   `requests.post` patched to raise, then assert a further call does not invoke `requests.post`
   again (mock call count stays flat) — per AC #2, mirrors test_plan's exact spec.
4. `test_circuit_breaker_half_open_retry_recovers` — trip the breaker open as above, advance past
   `CIRCUIT_BREAKER_COOLDOWN_SECONDS` (patch `time.time` or the cooldown constant down to a small
   test value via monkeypatch rather than a real 60s sleep — the test_plan explicitly says avoid
   real wall-clock waits for unit-level tests), patch `requests.post` to now succeed, call `send`
   again, assert the probe request fires and the breaker closes (subsequent calls dispatch
   normally).
5. `test_circuit_breaker_open_send_returns_false_not_silent` — with the breaker open (not yet
   cooled down), assert `send(alert)` returns `False` synchronously and `requests.post` is never
   called for that call.

**Do NOT touch:** the existing integration test file structure from Step 3 — these are new,
separate unit tests, not a replacement for the integration coverage.

**Verify:** `pytest tests/unit/observability/test_webhook_alert_sink.py -v` — all 5 new tests pass.

---

### Step 5 — Transcribe the broad-except review disposition into the ticket

**Files:** `tickets/inprogress/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC.md`

**Change:** This step makes no source-code change. Fill the ticket's `## Implementation Notes`
section with a condensed version of `investigation.md`'s "Disposition of the targeted review"
(the paragraph starting "of the areas sampled..."): name the six areas reviewed
(`src/engine/apply.py`, `src/core/registries.py`, `src/engine/kernel.py`,
`src/engine/replay_sink.py`/`replay_manager.py`, `src/engine/worker_manager.py`,
`src/engine/tactical.py`/`combat_rewards.py`) and the finding for each (zero sites / typed
re-raise / documented non-authoritative pattern / typed result value), plus the explicit
disposition: no site found needing a fix under this ticket's scope. Note `src/api/` and
`src/lab/` were not reviewed and are flagged as the next places to look if a future ticket wants
broader confidence — do not review them now, that is new scope. This satisfies AC #3 as written
("names specific sites reviewed and their disposition").

**Do NOT touch:** the actual exception-handling code in `src/engine/apply.py`,
`src/core/registries.py`, `src/engine/kernel.py`, `src/engine/replay_sink.py`,
`src/engine/replay_manager.py`, `src/engine/worker_manager.py`, `src/engine/tactical.py`, or
`src/engine/combat_rewards.py` — investigation already concluded every reviewed site there is
already defensible (typed re-raise, typed result value, or documented intentional fallback); this
ticket's AC #3 deliverable is the review-and-disposition writeup, not a code change to any of
those files. Do not review or touch `src/api/` or `src/lab/` — out of the sampled scope, flagged
as future work, not this ticket's.

**Verify:** No automated test — AC #3 is satisfied by the written disposition existing in the
ticket body (and already existing in more detail in `investigation.md`), per test_plan.md #7:
"there is no single test that can assert 'the review was targeted, not blind.'"

---

### Step 6 — Parity ledger entry and doc status updates

**Files:** `docs/parity_ledger/infrastructure.yaml`, `docs/plans/error_handling_hygiene_epic.md`,
`docs/plans/architecture_resilience_remediation_roadmap.md`

**Change:**
1. Add a new entry to `docs/parity_ledger/infrastructure.yaml`, `id: INFRA-362` (confirmed next
   available ID — the file's highest existing ID is `INFRA-361` at line 10625, added by the
   sibling `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` this same session, confirmed by direct
   read; no `INFRA-362` exists yet). Mirror the shape of `INFRA-361` (lines 10625-10636, confirmed
   by direct read):
   ```yaml
   - id: INFRA-362
     text: 'WebhookAlertSink retries with capped exponential backoff and jitter, and opens a
       circuit breaker after consecutive full-dispatch failures against a dead endpoint,
       half-open-probing after a cooldown -- TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC.'
     status: verified
     priority: P2
     legacy_evidence: null
     v2_evidence: 'src/observability/alerts/sinks.py: WebhookAlertSink._compute_backoff_delay,
       WebhookAlertSink._circuit_allows_dispatch, WebhookAlertSink._record_outcome.'
     test_path: tests/unit/observability/test_webhook_alert_sink.py::test_circuit_breaker_opens_after_consecutive_failures
     divergence_note: null
   ```
   (No P0 gate applies — this is a P2-priority ticket per investigation's Parity Ledger Overlap
   section — but citing a real test path is still required practice.)
2. `docs/plans/error_handling_hygiene_epic.md`: add a `## Status: Resolved` section (mirroring
   the pattern investigation.md cites for `docs/plans/redis_stream_resilience_epic.md`), noting the
   linear→exponential+jitter fix and the new circuit breaker, with a pointer to `INFRA-362`.
3. `docs/plans/architecture_resilience_remediation_roadmap.md`: mark Epic H's row/section with the
   same `Status: Resolved` marker Epics A, B, E, G already carry (per investigation, confirmed
   these four already have it — follow their exact existing format).

**Do NOT touch:** `docs/audits/D23_architecture_resilience.md` — investigation's explicit
recommendation is to leave this as an untouched historical snapshot, consistent with how the A/B/E/G
resolutions handled their own source audits (they annotated epic-plan + roadmap docs only, never
the audit itself).

**Verify:** No test — this is a documentation/traceability step. Confirm via `grep -n "INFRA-362"
docs/parity_ledger/infrastructure.yaml` that the entry parses (run
`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` to
confirm valid YAML, matching this repo's usual parity-ledger update practice) and via a final
re-read that the roadmap/epic-plan doc edits match the A/B/E/G precedent format exactly.

## Scope Guards

- Do not modify `RedisStreamConsumer` (`src/observability/stream/consumer.py`) — its
  `_compute_backoff_delay` shape is referenced/mirrored for Step 1, never edited.
- Do not change `WebhookAlertSink.send()`'s external signature, return type, or fire-and-forget
  semantics — `AlertRouter.route()` and `INFRA-358`'s watchdog-trip wiring (test:
  `tests/unit/observability/test_watchdog.py::test_run_cycle_trip_routes_alert_event`) depend on
  it exactly as-is.
- Do not add new `SIM_ALERTS_WEBHOOK_*`/`RPG_ALERTS_WEBHOOK_*` env vars or touch
  `AlertsManager.get_router()`'s config-resolution block (`manager.py:21-46`) — Step 2's decision
  is fixed class constants, not env-configurable tunables.
- Do not touch `AlertsManager.reset()`'s `except Exception: pass` sink-shutdown swallow
  (`manager.py:79`) — investigation explicitly flags this as test-support-only code, out of this
  ticket's named scope.
- Do not perform a blanket `except Exception` → typed-exception sweep anywhere in the repo. The
  481/484-site count is explicitly not a target metric per the ticket's Out of Scope.
- Do not modify the actual exception-handling code in `src/engine/apply.py`,
  `src/core/registries.py`, `src/engine/kernel.py`, `src/engine/replay_sink.py`,
  `src/engine/replay_manager.py`, `src/engine/worker_manager.py`, `src/engine/tactical.py`, or
  `src/engine/combat_rewards.py` — investigation already dispositioned every reviewed site there
  as defensible; this ticket's broad-except deliverable is the Step 5 review writeup, not a code
  change to any of these files.
- Do not review or touch `src/api/` or `src/lab/` — flagged by investigation as unreviewed and
  out of this ticket's sampled scope; a future ticket's concern, not this one's.
- Do not add retry/backoff logic to any subsystem other than `WebhookAlertSink` — explicitly Out
  of Scope in the ticket even though `RedisStreamConsumer`'s pattern is reused as a shape
  reference.
- Do not retroactively annotate `docs/audits/D23_architecture_resilience.md` — leave it as a
  historical snapshot per investigation's recommendation and existing A/B/E/G precedent.
- Do not introduce a standalone `CircuitBreaker` class/module — the scope is a few instance
  attributes and two private methods on `WebhookAlertSink`, per investigation's explicit sizing
  guidance.

## Dependency Map

- Step 1 and Step 2 both edit `src/observability/alerts/sinks.py` but touch disjoint regions
  (backoff constants/method vs. circuit-breaker constants/state/methods) — implement in order
  (Step 1 then Step 2) to avoid merge friction within the same file, but Step 2 does not
  functionally depend on Step 1's output.
- Step 3 depends on Steps 1 and 2 being complete (the timing assertion under test depends on the
  actual backoff formula and on the circuit breaker not interfering with a 2-attempt sequence
  below its `CIRCUIT_BREAKER_FAILURE_THRESHOLD=5` threshold).
- Step 4 depends on Steps 1 and 2 (tests exercise the methods/constants those steps add).
- Step 5 is independent of Steps 1-4 — it transcribes already-complete investigation findings and
  can run at any point, but is sequenced last-but-one since it's a ticket-closure task.
- Step 6 depends on Steps 1-4 being complete and verified (the parity entry's `v2_evidence` and
  `test_path` must point at real, passing code/tests).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: backoff behavior matches its own in-code documentation (real exponential+jitter, or an honest comment) | Step 1 | `test_backoff_delay_is_exponential_not_linear`, `test_backoff_has_jitter` (Step 4); `test_server_error_does_not_crash` (Step 3, regression) |
| AC #2: a circuit breaker prevents indefinite full-sequence retries against a dead endpoint | Step 2 | `test_circuit_breaker_opens_after_consecutive_failures`, `test_circuit_breaker_half_open_retry_recovers`, `test_circuit_breaker_open_send_returns_false_not_silent` (Step 4) |
| AC #3: the targeted broad-except review names specific sites reviewed and their disposition | Step 5 (transcription); underlying review already done in `investigation.md`'s "Disposition of the targeted review" section | No test — documentation deliverable, per test_plan.md #7 |

## Anti-Drift Notes

- **Do not let this become a blanket broad-except sweep.** Both source audits and the ticket's own
  Out of Scope forbid it; "reviewed N sites, found no fix needed" is a valid, complete AC #3
  outcome, not an incomplete one.
- **`send()`'s contract is load-bearing outside this file.** `INFRA-358` (P0, verified) wired
  `SimulationWatchdog`'s critical escalation through this exact sink stack "reused as-is." Any
  change to `send()`'s signature, return semantics, or synchronous/fire-and-forget behavior is a
  regression against that P0 parity entry even though this ticket is P2.
- **Circuit-breaker state must stay instance-scoped**, never a module-level global or class-level
  mutable default — `AlertsManager.reset()` (existing tests `test_manager_singleton_returns_same_router`,
  `test_manager_reset_creates_new_router`) must produce a fresh `WebhookAlertSink` with a closed
  circuit after each reset, not inherit a prior instance's open state.
- **Avoid wall-clock sleeps in the new unit tests** for cooldown/half-open verification — patch
  `time.time` or inject a shortened cooldown value rather than sleeping 60 real seconds in a unit
  test; the existing integration tests' use of real sleeps is acceptable precedent only at the
  integration level, per test_plan.md.
- **The Step 3 sleep-constant question is empirical, not assumed.** The arithmetic in this plan
  shows the new formula's single-retry delay for `max_retries=2` is close to today's, but Step 3
  requires actually running the test to confirm rather than trusting the arithmetic alone —
  jitter and real network/thread scheduling variance are not fully captured by the formula alone.
- **This ticket does not touch `WebhookAlertSink.__init__`'s existing four constructor
  parameters** (`webhook_url`, `enabled`, `timeout_seconds`, `max_retries`) or their env-var
  wiring in `manager.py` — only new attributes are added, nothing existing is renamed or
  re-plumbed.

## Deviations

- **Step 4 added one extra unit test beyond the plan's five**: `test_backoff_delay_caps_at_bound`
  (asserts `_compute_backoff_delay(100, rng=...)` stays at or below
  `BACKOFF_CAP_SECONDS * (1 + BACKOFF_JITTER_RATIO)`), directly mirroring
  `RedisStreamConsumer`'s own `test_reconnect_backoff_caps_at_bound`
  (`tests/unit/observability/test_stream_consumer_resilience.py`). Purely additive coverage for
  the cap behavior the plan's constants introduce; does not replace or modify any of the five
  plan-specified tests.
- **Step 3 required zero code changes**, confirmed empirically rather than assumed: the plan
  flagged this as an open question requiring an actual test run rather than trusting the
  arithmetic. `test_server_error_does_not_crash` was run three times total (once as part of the
  full integration suite, twice more in isolation) and passed every time with comfortable margin
  (~4.3-4.7s observed vs. the 4.0s wait plus the up-to-~0.6s single retry delay) — the existing
  `time.sleep(4.0)` constant needed no adjustment.
- No other deviation from the plan's 6 steps, scope guards, or acceptance-criteria mapping.
