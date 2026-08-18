---
status: active
layer: observability
authority: P1
audience: agent
tags: [observability]
---

# Epic Plan — Error-Handling Hygiene

**Tracking ticket:** `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §D, §J (R7, R8)
**Priority:** P2 — explicitly targeted, not a blanket sweep.

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
