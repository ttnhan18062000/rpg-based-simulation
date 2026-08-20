---
status: historical
layer: observability
authority: P1
audience: agent
maturity: shipped
archived: 2026-08-20
tags: [observability]
---

# Epic Plan — Error-Handling Hygiene

**Tracking ticket:** `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §D, §J (R7, R8)
**Priority:** P2 — explicitly targeted, not a blanket sweep.

## Status
Resolved by `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC`. Both Problem items below now describe
pre-fix history, not current state.

1. `WebhookAlertSink` (`src/observability/alerts/sinks.py`) now computes delay via a new
   `_compute_backoff_delay(attempt, rng=None)` method — capped exponential
   (`BACKOFF_BASE_SECONDS * 2 ** (attempt - 1)`, capped at `BACKOFF_CAP_SECONDS`) with proportional
   jitter (`BACKOFF_JITTER_RATIO`), directly mirroring `RedisStreamConsumer`'s Epic D precedent —
   replacing the old `time.sleep(0.5 * attempt)` linear formula and its misleading comment. A new
   3-state circuit breaker (`_circuit_state`: `closed`/`open`/`half_open`, instance-scoped, guarded
   by `_circuit_lock`) opens after `CIRCUIT_BREAKER_FAILURE_THRESHOLD` (5) consecutive failed
   full-dispatch cycles against the endpoint, and allows exactly one half-open probe per
   `CIRCUIT_BREAKER_COOLDOWN_SECONDS` (60.0) cooldown; a probe success closes the circuit, a probe
   failure reopens it. `send(alert: AlertEvent) -> bool`'s external signature, return semantics,
   and fire-and-forget contract are unchanged — an open circuit makes `send()` return `False`
   synchronously (same "did not deliver" convention as the existing disabled-sink case), never a
   silent no-signal drop. Both mechanisms ship as fixed class constants, not new env vars.
2. The targeted broad-except review (state mutation, persistence, replay) sampled six areas —
   `src/engine/apply.py`, `src/core/registries.py`, `src/engine/kernel.py`,
   `src/engine/replay_sink.py`/`replay_manager.py`, `src/engine/worker_manager.py`,
   `src/engine/tactical.py`/`combat_rewards.py` — and found no site needing a fix: every reviewed
   site either re-raises as a typed exception, converts the failure into a typed status/result
   value, or is explicitly documented as an intentional non-authoritative fallback. See the
   ticket's `## Implementation Notes` for the full per-area disposition. No source file in this
   list was modified by this ticket. `src/api/` and `src/lab/` were not sampled and remain flagged
   as the next places to look if a future ticket wants broader confidence.

New parity ledger entry: `INFRA-362` (`docs/parity_ledger/infrastructure.yaml`).

## Problem

Two distinct findings:

1. `WebhookAlertSink` (`src/observability/alerts/sinks.py:39-92`) is the only real retry/backoff
   implementation in the entire codebase — bounded (3 retries), isolated in its own 2-thread
   executor so it can't block the sim loop (a real bulkhead). But the backoff is linear
   (`time.sleep(0.5 * attempt)`) despite an in-code comment claiming "exponential backoff." No
   jitter. No circuit breaker — a permanently-dead webhook endpoint receives the full retry
   sequence on every single alert, forever.
2. 481 broad `except Exception:`/bare `except:` sites exist across `src/`, coexisting with a
   40+-class custom exception taxonomy that's largely unused by callers — most failures are
   absorbed generically rather than matched to a specific type, category, or retry decision. Both
   source audits explicitly caution against a blanket "fix all broad excepts" pass — that cuts
   against this repo's own stated preference for minimal, targeted change, and it's a
   maintainability/observability erosion risk, not an acute one.

## Scope for the eventual `create-tickets` pass

- Fix the misleading "exponential backoff" comment (either correct the comment or implement real
  exponential backoff+jitter) in `WebhookAlertSink`.
- Add a simple circuit breaker to `WebhookAlertSink` (open after N consecutive failures,
  half-open retry) so a permanently-dead endpoint stops receiving full retry sequences forever.
- A **targeted** review of the highest-consequence broad-except sites only — state mutation,
  persistence, replay — not a repo-wide sweep of all 481 occurrences.

## Out of scope

- Any blanket "replace every broad except" initiative — explicitly not recommended by either
  source audit.
- Adding retry/backoff to any other subsystem beyond `WebhookAlertSink` unless a specific,
  confirmed need is found during the targeted review.

## Acceptance signal for this epic (not yet broken into child tickets)

- `WebhookAlertSink`'s backoff behavior matches its own in-code documentation (real exponential+
  jitter, or an honest comment).
- A circuit breaker prevents indefinite full-sequence retries against a dead endpoint.
- The targeted broad-except review names specific sites reviewed and their disposition — not a
  count-reduction metric applied blindly.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic H)
- `docs/audits/D23_architecture_resilience.md` (R7, R8, Stage 4-5)
