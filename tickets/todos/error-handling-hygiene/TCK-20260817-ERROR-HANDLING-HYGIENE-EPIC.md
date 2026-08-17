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
EPIC_SCOPED

## Tier
epic

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
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/error_handling_hygiene_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (WebhookAlertSink backoff/circuit-breaker fix, targeted broad-except review), producing
  investigated child tickets in `tickets/todos/error-handling-hygiene/`.

## Out of Scope
- Any blanket "replace every broad except" initiative — explicitly not recommended by either
  source audit.
- Adding retry/backoff to any subsystem beyond `WebhookAlertSink` unless the targeted review
  finds a specific, confirmed need.

## Acceptance Criteria
- [ ] `docs/plans/error_handling_hygiene_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

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
- Which specific broad-except sites count as "highest-consequence" (state mutation, persistence,
  replay per the source audit) needs confirming at Plan time for the eventual child ticket.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
