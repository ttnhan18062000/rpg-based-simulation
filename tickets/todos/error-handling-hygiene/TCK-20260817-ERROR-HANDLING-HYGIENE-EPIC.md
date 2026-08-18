---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
phase: open
date: 2026-08-17
tags: [observability]
---

# TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC

## Title
Fix WebhookAlertSink's backoff/circuit-breaker gap; targeted review of highest-consequence broad-except sites

## Status
OPEN

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
- [ ] `WebhookAlertSink`'s backoff behavior matches its own in-code documentation (real
      exponential+jitter, or an honest comment).
- [ ] A circuit breaker prevents indefinite full-sequence retries against a dead endpoint.
- [ ] The targeted broad-except review names specific sites reviewed and their disposition — not
      a count-reduction metric applied blindly.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/error_handling_hygiene_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/observability/alerts/sinks.py

## Assumptions / Open Questions
- Which specific broad-except sites count as "highest-consequence" needs confirming at Plan time.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; two related, contained threads of work under
  one "error-handling hygiene" theme — one standard ticket, not a multi-ticket initiative.
  `staging_artifacts/TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC/` not yet created.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
