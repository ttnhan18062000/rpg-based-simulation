---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION
phase: open
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION

## Title
`provider_enforcement.py`'s provider-call rate limiting and global-scan rejection — genuinely missing at any scope; should it be built?

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Found and determined during `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION` (`stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION/investigation.md`, section 7). Filed as its own ticket per peer review's explicit
instruction: this is a "should we build this" design question, not a cleanup, and a different
specific question than `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION`'s own —
each capability needs its own real decision, even though the two may overlap (see below).

`ProviderBudgetEnforcement.execute_call()` wraps a generic `provider_func: Callable[[], List[Any]]`
call with a per-tick call-count budget (`max_calls`) and rejects "global scan" attempts (calls
missing both `entity_id` and `region_id` scope) unless an explicit `debug_global_scan` flag is set.

Checked every real, live rate-limiting/call-budget mechanism in the codebase for a comparable
capability, at any scope:
- `src/world/providers/`, `src/domains/information/` (the real provider-shaped call consumer paths,
  investigated extensively in `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-
  INVESTIGATION`): no live call-budget or scope-rejection logic found.
- `src/observability/performance/{models,profiler}.py`'s `provider_call_count`: a passive metrics
  counter only — records how many calls happened, does not cap or reject any.
- `src/api/admission_control.py`'s own real token-bucket rate limiter: operates per-API-client
  (`_ClientAdmissionState`, keyed by `client_id`) — a different scope entirely from per-tick,
  per-simulation-domain provider calls.

No live equivalent at any scope.

## Scope
- Determine whether provider-call rate limiting and/or global-scan rejection is actually needed —
  i.e., is there a real, evidenced risk of unbounded or unscoped provider calls in a real run that
  this would guard against? Not "should we wire `ProviderBudgetEnforcement` in as-is" — its specific
  numbers (`max_calls=10`, `max_results=5`) were never validated against real usage, since nothing
  has ever called it.
- Check for overlap with `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION`'s own
  `max_provider_calls_per_tick` tracking — flagged as a real possibility by the origin
  investigation, not resolved there. If both are determined worth building, decide whether they
  should be one mechanism or two genuinely distinct ones (e.g. per-call-site rate limiting vs.
  per-tick aggregate budget).
- If determined worth building: route the real implementation shape through peer review before
  implementing.

## Out of Scope
- The other 4 follow-up tickets from the same determination — each has its own scope.
- `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION`'s own disposition — a separate
  "should we build this" question, checked for overlap here but not decided here.

## Acceptance Criteria
- [ ] Real evidence on whether unbounded/unscoped provider calls are a real, observed risk in a
      real run (not assumed).
- [ ] The overlap question with `budget_manager.py`'s own determination is checked and recorded,
      either way.
- [ ] A peer-routed build/don't-build decision, obtained before implementation.
- [ ] If built: real test evidence it actually catches a real unbounded/unscoped call scenario, not
      just a unit test of the mechanism in isolation.

## Related Tickets
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (origin)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C1)
- `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION` (sibling — check for overlap on
  provider-call budgeting)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (the real
  provider-shaped call consumer paths, already investigated)

## Related Docs
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/
  investigation.md` (section 7, full evidence)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/optimization/provider_enforcement.py`
- `src/world/providers/`, `src/domains/information/` (the real consumer paths)
- `src/api/admission_control.py` (the real, but differently-scoped, rate-limiting precedent)

## Assumptions / Open Questions
- Whether this is actually needed is the entire point of this ticket — deliberately not pre-judged.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
