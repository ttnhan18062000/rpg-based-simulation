---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
artifact_type: investigation
tags: [observability]
---

# Investigation — TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC

This supersedes the placeholder `investigation.md` written while this ticket was still epic-tier
(scope-only). The ticket was downgraded to standard tier on 2026-08-18 with a concrete Scope and
Acceptance Criteria, so this is the real pre-implementation investigation.

## Current Behavior

### 1. `WebhookAlertSink` backoff/circuit-breaker gap

**`src/observability/alerts/sinks.py`** (97 lines total, verified directly):

- `WebhookAlertSink.__init__` (lines 45–51): takes `webhook_url`, `enabled`, `timeout_seconds`,
  `max_retries` (default 3). Builds a dedicated 2-thread `ThreadPoolExecutor` — this is a real
  bulkhead, delivery can never block the sim loop.
- `send()` (lines 53–59): enqueues `_dispatch_with_retry` onto the executor and returns
  immediately (fire-and-forget from the caller's perspective).
- `_dispatch_with_retry()` (lines 61–92): the retry loop. Confirmed exactly as the ticket claims:
  - Line 87 comment reads `# Short sleep before retry (exponential backoff)`.
  - Line 89 is the actual delay: `time.sleep(0.5 * attempt)` — this is **linear**, not
    exponential (attempt 1 → 0.5s, attempt 2 → 1.0s, attempt 3 → not reached since the sleep is
    only applied `if attempt < self.max_retries`). A real exponential schedule would be
    `base * (2 ** (attempt - 1))`.
  - No jitter anywhere in the method.
  - No circuit breaker: every single `send()` call — for every alert, indefinitely — re-runs the
    full `max_retries`-length retry sequence against the configured `webhook_url`, even if the
    previous 500 calls all failed against the same dead endpoint. Confirmed via
    `grep -r "circuit_breaker\|CircuitBreaker" src/` → zero results repo-wide; there is no
    existing circuit-breaker implementation anywhere in this codebase to reuse.
  - `requests.RequestException` is the only caught exception type (line 81) — connection errors,
    timeouts, DNS failures. A non-2xx/2xx-adjacent status code (line 76–80) is handled as a soft
    failure (logged, loop continues) rather than raising.
  - `shutdown()` (lines 94–96) drains the executor; called by `AlertsManager.reset()`.

**Confirmed against the source audit**: `docs/audits/D23_architecture_resilience.md` §D and
finding R7 (line 221) match the code exactly, including the specific line numbers.

### 2. Surrounding `AlertsManager`/`AlertRouter`/`AlertEvent` structure

- **`src/observability/alerts/manager.py`** (`AlertsManager`, 82 lines): a class-level singleton
  (`_router: Optional[AlertRouter]`, `threading.Lock`) built lazily in `get_router()`. Reads
  `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED`/`SIM_ALERTS_WEBHOOK_TIMEOUT`/
  `SIM_ALERTS_WEBHOOK_RETRIES` (falling back to `RPG_ALERTS_*` legacy names) to construct one
  `WebhookAlertSink` alongside a default `LogAlertSink`, registered on one shared `AlertRouter`.
  A circuit breaker's tunables (failure threshold, half-open cooldown) would naturally follow this
  same `SIM_ALERTS_WEBHOOK_*`-env-var pattern if made configurable — confirm at Plan time whether
  the AC requires configurability or a fixed default is acceptable (ticket doesn't specify).
  `reset()` (lines 69–81) shuts down all sinks that expose `.shutdown` inside a
  `try/except Exception: pass` — swallows shutdown errors silently, but this is test-support-only
  code (docstring: "mainly useful for testing configurations"), not a production path.
- **`src/observability/alerts/router.py`** (`AlertRouter`, 113 lines): `route()` filters by
  severity threshold, deduplicates via `AlertDeduplicator`, then dispatches to every registered
  sink inside a per-sink `try/except Exception` (lines 78–91) so one broken sink can never break
  delivery to the others or crash the caller. `WebhookAlertSink.send()` itself never raises (all
  its own exceptions are already caught inside `_dispatch_with_retry`, which runs on the executor
  thread anyway) — this per-sink guard is defense-in-depth, not currently load-bearing for the
  webhook sink specifically.
- **`src/observability/alerts/models.py`** (`AlertEvent`, 101 lines): a plain dataclass with
  `to_dict()` and three factory methods (`create_hard_law_violation`,
  `create_watchdog_trip`, `create_critical_anomaly`) plus a fourth
  (`create_stream_backpressure`) not mentioned by name in the ticket but present. No changes
  needed here — this ticket doesn't touch alert construction, only delivery.

**This module is not a quiet corner.** `docs/parity_ledger/infrastructure.yaml` entry `INFRA-358`
(verified, P0 — see Parity Ledger Overlap below) wired `SimulationWatchdog`'s critical escalation
through this exact `AlertsManager` → `AlertRouter` → `WebhookAlertSink` stack, reusing it as-is.
`WebhookAlertSink` currently ships default-disabled (`SIM_ALERTS_WEBHOOK_ENABLED` unset), so the
backoff/circuit-breaker gap is latent, not actively firing in production today — but the stack it
sits in is real, tested, and one env var away from being live for watchdog trips.

### 3. Targeted broad-except review (state mutation, persistence, replay)

Ticket scope explicitly limits this to "the highest-consequence sites only (state mutation,
persistence, replay)," not a repo-wide sweep. `grep -rn "except Exception" src/ | wc -l` → 475,
plus `grep -rnE '^\s*except\s*:' src/ | wc -l` → 9, total 484 (D23/D24's cited "481" is close
enough to be the same src/-only count taken at a slightly earlier commit — confirmed **not**
inflated by `tests/`, which has 25 + 1 = 26 more broad-except sites of its own that the audit
figure excludes). Reviewed by area:

- **`src/engine/apply.py`** (the authoritative mutation apply path — the one place "durable state
  should be committed" per this repo's own architecture rule): **zero** broad-except sites. Clean.
- **`src/core/registries.py`** (7 sites, content/catalog adapters, lines 277/315/366/385/499/534/
  578): every site follows the same pattern — `except Exception as e: raise AdapterError(...)
  from e`. This *converts* a broad catch into a typed, re-raised exception rather than swallowing
  it — already the correct pattern this ticket would otherwise recommend. No action needed.
- **`src/engine/kernel.py`** (25 broad-except sites — the highest concentration of any single
  file reviewed): sampled beyond what D23 already covered (its own citation was lines
  452-462/481-484/610-611, metrics/alert-routing/listener-notification). Additional sites checked
  directly: lines 782-799/866-884 (hard-law-violation `.jsonl` audit-log writes, wrapped in
  `except Exception: logger.exception(...)` — a failure here loses only the audit trail, not
  authoritative state, and `CERTIFICATION`/`DEBUG` modes still raise `HardLawViolationError`
  separately for real enforcement); lines 999-1024 (post-commit event-listener notification,
  cognition/personality snapshot recording — explicitly post-commit, non-authoritative); lines
  1084-1110 (shutdown-path cleanup for SimQ feed/report and `DecisionTraceWriter.close()`, each
  logged as "(non-fatal)" in the message itself). All 25 sites reviewed are consistent with D23's
  own characterization: "a peripheral/observability failure structurally cannot abort a tick" —
  this is a deliberate containment pattern, not an accidental swallow.
- **`src/engine/replay_sink.py`** (2 sites, lines 88/108) and **`src/engine/replay_manager.py`**
  (4 sites, lines 159/205/292/294): every site is explicitly governed by in-code law comments —
  `# M6 Law: Non-authoritative fallback`, `# M7 Law` (atomic write, bounded flush budget),
  `# Budget check must never stall the replay pipeline (INFRA-060)`. Replay persistence is
  documented, by design, as best-effort: `persist_chunk`/`write_manifest` return `bool`, log on
  failure, and the caller (`_execute_persistence`, line 253-296) treats persistence failure as a
  metrics/status update, never a crash. This matches the repo's own stated Durable State Rule
  scoping — replay is a diagnostic trace, not authoritative gameplay state. No action needed.
- **`src/engine/worker_manager.py`** (4 sites, lines 38/152/163/203): worker-execution isolation.
  `_wrap_work` (line 184) catches `Exception` and converts it into a typed
  `WorkerResult(status=ResultStatus.FAILURE)` rather than swallowing — the failure is signaled
  structurally to the caller, not silently dropped. Consistent bulkhead pattern.
  `src/engine/tactical.py` (2 sites, lines 133/158) and `src/engine/combat_rewards.py` (1 site,
  line 109) follow the same shape: each has an adjacent code comment explaining the fallback
  behavior (permissive perception-gate fallback; legacy `EntityRole` reward-classification
  fallback when the relation service is unavailable) rather than an unexplained catch-all.

**Disposition of the targeted review**: of the areas sampled (authoritative apply path,
content-registry adapters, kernel tick loop, replay persistence, worker execution, tactical/reward
fallbacks), none contain a genuinely dangerous broad-except site — every one reviewed either (a)
re-raises as a typed exception, (b) converts the failure into a typed status/result value, or (c)
is explicitly documented as an intentional non-authoritative fallback. This is itself the
deliverable the ticket's third acceptance criterion asks for: "names specific sites reviewed and
their disposition — not a count-reduction metric applied blindly." **No broad-except site found
during this investigation needs fixing under this ticket's scope.** If Plan/Implement wants a
second opinion, `src/api/` (routes) and `src/lab/` (workflow orchestration) were not sampled here
and are the largest remaining unreviewed pools of broad-except sites outside this survey — flagged
as an open question below rather than assumed clean.

## Mechanics / Engine Constraints

This ticket touches observability/infrastructure code, not gameplay mechanics — no
`docs/mechanics/` chapter directly governs webhook delivery or exception handling. The relevant
constraints are architectural, from root `CLAUDE.md`:

- **Durable State Rule**: "Durable changes must be represented through typed records/updates,"
  "Authoritative application is the only place durable state should be committed." Confirms why
  `src/engine/apply.py` having zero broad-except sites is the correct, expected state, and why
  none of the reviewed sites outside it touch authoritative mutation directly.
- Root `CLAUDE.md`'s Hard Rules: "Do not create hidden or implicit durable behavior" — a circuit
  breaker's open/closed/half-open state is itself a small piece of durable-for-the-process-lifetime
  state. It should live as explicit instance attributes on `WebhookAlertSink` (mirroring
  `RedisStreamConsumer._consecutive_failures`, see Prior Work below), not a module-level global or
  hidden closure variable.

## Docs Requiring Update

- `docs/plans/error_handling_hygiene_epic.md`: describes the pre-fix state ("linear... despite an
  in-code comment claiming exponential... No jitter. No circuit breaker") as current/open; once
  implemented this needs a status note (mirroring how sibling epic docs — e.g.
  `docs/plans/redis_stream_resilience_epic.md` — got a `## Status: Resolved` section added) so the
  roadmap table in `docs/plans/architecture_resilience_remediation_roadmap.md` stays accurate.
- `docs/plans/architecture_resilience_remediation_roadmap.md`: Epic H's row/section currently has
  no `Status: Resolved` marker (unlike Epics A, B, E, G which already do) — update once this
  ticket completes, following the exact pattern those four epics already established.
- `docs/audits/D23_architecture_resilience.md`: R7 in its findings table (line 221) and the
  narrative in §D describe the linear-backoff/no-circuit-breaker state as current fact. This is a
  point-in-time audit document, not a live contract — confirm at Plan time whether this project's
  convention is to retroactively annotate audit docs after a finding is fixed (no example of that
  pattern found in the sibling A/B/E/G resolutions, which annotated their *epic plan* docs and the
  *roadmap*, not the audits themselves) or leave the audit as a historical snapshot. Recommend:
  leave the audit untouched (historical record) and let the epic-plan + roadmap docs carry the
  "resolved" status, consistent with precedent.

## Parity Ledger Overlap

- **`INFRA-358`** (`docs/parity_ledger/infrastructure.yaml:10565`, status `verified`, priority
  `P0`) — from `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`. Documents `SimulationWatchdog` routing
  a `WatchdogTrip` `AlertEvent` through `AlertsManager`/`AlertRouter`/`WebhookAlertSink`, "reused
  as-is, no new sink code." **This ticket's fix must not change `WebhookAlertSink.send()`'s
  public contract** (still takes an `AlertEvent`, still returns `bool`, still fire-and-forget via
  the executor) — INFRA-358's `test_path` includes
  `tests/unit/observability/test_watchdog.py::test_run_cycle_trip_routes_alert_event`, which is
  regression surface for this ticket even though it doesn't test backoff/circuit-breaker behavior
  directly.
- **`INFRA-361`** (`docs/parity_ledger/infrastructure.yaml:10625`, status `verified`, priority
  `P1`) — from `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`. Documents `RedisStreamConsumer`'s
  exponential-backoff-with-jitter (`_compute_backoff_delay`), capped, resetting after a successful
  connect. Not overlapping scope (different class/file) but the direct in-repo precedent for the
  formula and constant-naming convention this ticket's `WebhookAlertSink` fix should follow (see
  Prior Work).
- No existing `docs/parity_ledger/*.yaml` entry documents `WebhookAlertSink`'s retry/backoff
  behavior itself (searched all `*.yaml` for `WebhookAlertSink`/`sinks.py` — only the two INFRA-358
  mentions above, which are about the watchdog wiring, not the backoff algorithm). A **new**
  `infrastructure.yaml` entry is required once this ticket implements the fix — no P0 test-path
  gate applies since the new entry itself won't be P0 (this is a P2-priority ticket), but should
  cite whatever new/updated test(s) cover the corrected backoff and the circuit breaker.

## Prior Work

- **`TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`** (done, this session) is the closest in-repo
  precedent for "fix a linear/naive retry loop into real exponential backoff+jitter."
  `src/observability/stream/consumer.py` (`RedisStreamConsumer`) now defines:
  ```python
  BACKOFF_BASE_SECONDS = 0.2
  BACKOFF_CAP_SECONDS = 30.0
  BACKOFF_JITTER_RATIO = 0.2

  def _compute_backoff_delay(self, attempt: int, rng: Optional["random.Random"] = None) -> float:
      capped = min(self.BACKOFF_CAP_SECONDS, self.BACKOFF_BASE_SECONDS * (2 ** max(0, attempt - 1)))
      jitter = capped * self.BACKOFF_JITTER_RATIO
      r = rng or random
      return max(0.0, capped + r.uniform(-jitter, jitter))
  ```
  This is a directly reusable shape for `WebhookAlertSink._dispatch_with_retry`'s replacement
  delay calculation — class-level tunable constants, an injectable `rng` for deterministic
  testing, capped exponential with a proportional jitter band. `stored_artifacts/
  TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC/plan.md` documents the design rationale in full if
  Plan wants to consult it directly.
- **No circuit-breaker precedent exists anywhere in this codebase** (`grep -r "circuit_breaker\|
  CircuitBreaker" src/` → zero hits, confirmed independently of the D23 audit's own claim of the
  same). This will be genuinely new code, not an adaptation of an existing pattern — Plan should
  size it accordingly (simple 3-state open/half-open/closed counter, not a library dependency).
- **`TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`** (done, this session) is the ticket that made this
  module load-bearing in practice — see Parity Ledger Overlap (`INFRA-358`) above. Its
  `stored_artifacts/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC/investigation.md` and `test_plan.md`
  are useful background but don't touch backoff/circuit-breaker specifically (out of that ticket's
  scope).
- `tests/integration/observability/test_alert_webhook_sink.py` (existing, `TestWebhookAlertSinkIntegration`
  + `TestAlertsManagerIntegration`, added for "Milestone 40" per its module docstring) is the
  existing regression surface for this sink — see Test Plan for detail. No prior investigation
  artifact for that milestone was found under `stored_artifacts/` (predates this session's
  ticket/artifact convention).

## Risks and Open Questions

- **Timing-based tests are inherently flaky for backoff verification.** The existing integration
  test `test_server_error_does_not_crash` asserts exact received-payload counts after a fixed
  `time.sleep(4.0)` wall-clock wait tuned to the *current* linear schedule
  (`0.5 * attempt` seconds). Changing to exponential backoff changes the real-world delay between
  attempts, which will likely require updating this sleep constant or refactoring the test to use
  a mocked/injectable clock — flag for Test Plan, this is a real regression-surface consequence,
  not hypothetical. (See `New Tests Required`/`Regression Surface` in test_plan.md.)
- **Circuit-breaker state scope is unresolved.** Open question: does the circuit breaker live
  per-`WebhookAlertSink`-instance (simplest, matches `AlertsManager`'s current one-sink-per-process
  singleton lifecycle) or would a future multi-endpoint use case need it keyed per-`webhook_url`?
  The ticket's AC doesn't specify multi-endpoint support, `AlertsManager` currently only ever
  constructs one `WebhookAlertSink`, and the current codebase is exactly one webhook URL
  process-wide — per-instance state is very likely sufficient. Flagged as unblocking (default to
  per-instance) but worth Plan explicitly confirming rather than silently assuming.
- **No config surface was specified in the ticket for circuit-breaker tunables** (failure
  threshold to open, half-open cooldown duration). `AlertsManager.get_router()` already has a
  precedent (`SIM_ALERTS_WEBHOOK_RETRIES` env var) for exposing `WebhookAlertSink` constructor
  params as env vars — Plan should decide whether the circuit breaker gets the same treatment or
  ships with fixed constants (mirroring `RedisStreamConsumer`'s class-constant approach, which has
  no env-var override either). Not a blocker — either choice satisfies the AC as written.
- **The "highest-consequence broad-except sites" review above is a sample, not exhaustive.**
  `src/api/` and `src/lab/` were not reviewed. If Plan or a future reviewer wants stronger
  confidence, these are the next places to look — explicitly flagged rather than silently assumed
  covered.

## Anti-Drift Hazards

- **Do not turn this into a blanket broad-except sweep.** Both source audits (D23 §D/§J, D24 §K)
  and this ticket's own Out of Scope explicitly forbid it. The correct outcome of the
  broad-except portion of this ticket may legitimately be "reviewed N specific sites, found no
  fix needed" — that is not scope failure, it's the AC's own definition of success ("names
  specific sites reviewed and their disposition — not a count-reduction metric applied blindly").
- **Do not add retry/backoff to any subsystem beyond `WebhookAlertSink`** — explicitly Out of
  Scope, even though `RedisStreamConsumer`'s pattern is being reused as a *shape* reference here.
- **Do not change `WebhookAlertSink.send()`'s external contract** (signature, return type,
  fire-and-forget semantics) — `AlertRouter.route()` and `INFRA-358`'s watchdog-trip wiring both
  depend on it staying a synchronous `bool`-returning enqueue call.
- **Do not let the circuit breaker silently drop alerts without a signal.** When open, `send()`
  should still return a well-defined value (likely `False`, matching the existing "sink did not
  deliver" convention `LogAlertSink`/webhook success/failure already use) — a circuit breaker that
  makes failures indistinguishable from "not enabled" or successful delivery would regress
  observability of the exact failure this ticket is trying to make less severe.
- **`AlertsManager.reset()`'s sink-shutdown swallow (`except Exception: pass`, manager.py:78-80)**
  is test-support code, not something this ticket should "fix" as a drive-by — it's out of the
  ticket's named scope (`WebhookAlertSink`'s own backoff/circuit-breaker behavior and the targeted
  broad-except review), and touching it isn't needed for either AC.
