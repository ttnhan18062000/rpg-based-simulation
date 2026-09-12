---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION
phase: open
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION

## Title
`budget_manager.py`'s imperative, stateful per-tick budget-enforcement primitive — genuinely missing, no live equivalent; should it be built?

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
DETERMINATION/investigation.md`, section 2). Filed as its own ticket per peer review's explicit
instruction: this is a "should we build this" design question, not a cleanup, and a different
specific question than `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`'s
own — each capability needs its own real decision.

`PhaseBudgetManager.check_and_consume()` is a **stateful, imperative** running-total tracker:
call it every time a phase is about to spend (time, entities, provider calls, trace events), it
increments internal counters and rejects with a specific reason once any one is exceeded mid-tick.

The live budget system (`GovernorPolicy`/`PhaseBudgets`, `src/engine/policy.py`,
`src/engine/phase_governor.py`) is architecturally different, not merely differently-numbered: it
is **declarative and pre-computed** — a set of per-tick limit numbers (`candidate_budget`,
`movement_budget`, `strategic_budget`, `scan_policy`) decided once before any phase runs, which
individual phases are expected to respect by convention on their own. Nothing provides
`PhaseBudgetManager`'s own reusable "consume and get told no, with a reason, mid-tick" enforcement
primitive. No live enforcement of `max_provider_calls_per_tick` or `max_trace_events_per_tick`
specifically was found anywhere (see `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-
DETERMINATION` and investigation.md section 8 for the related, but distinct, provider-call and
trace-volume findings).

## Scope
- Determine whether an imperative, mid-tick budget-enforcement primitive is actually needed —
  i.e., are there real phases that need to be told "no, stop, you're over budget" partway through
  their own work, as opposed to being handed a pre-tick number and trusted to respect it? This is
  the real question, not "should we wire `PhaseBudgetManager` in as-is" — its specific numbers/API
  shape were never validated against real usage, since nothing has ever called it.
- Check whether the declarative `GovernorPolicy`/`PhaseBudgets` numbers (`candidate_budget`, etc.)
  are actually respected by the phases that read them today, or whether "respect by convention" has
  its own real gaps that an imperative enforcement primitive would close — real evidence, not
  assumption.
- Check for overlap with `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`
  specifically on provider-call budgeting (`PhaseBudgetManager`'s own `max_provider_calls_per_tick`
  vs. `ProviderBudgetEnforcement`'s own `max_calls`) — flagged as a real possibility by the origin
  investigation, not resolved there.
- If determined worth building: route the real implementation shape through peer review before
  implementing, per this repo's standing convention for real design decisions.

## Out of Scope
- The other 4 follow-up tickets from the same determination — each has its own scope.
- `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`'s own disposition — a
  separate "should we build this" question, checked for overlap here but not decided here.

## Acceptance Criteria
- [ ] Real evidence on whether phases that read `GovernorPolicy`/`PhaseBudgets`' declarative limits
      actually respect them, or whether that convention has real, evidenced gaps.
- [ ] The overlap question with `provider_enforcement.py`'s own determination is checked and
      recorded, either way.
- [ ] A peer-routed build/don't-build decision, obtained before implementation.
- [ ] If built: real test evidence the primitive actually gets exercised by a real phase under real
      pressure, not just a unit test of the primitive in isolation.
- [ ] If "not needed, delete": verify non-import references too, not just Python-level ones (CI
      workflow paths, `Makefile` targets, doc file listings) before deleting the module/its test
      file — a real, confirmed blind spot from the diagnostics/memory-limits deletions in this same
      package (`TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`'s own zero-references
      grep missed two hardcoded CI path arguments, caught only by CI itself).

## Related Tickets
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (origin)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C1)
- `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION` (sibling — check for
  overlap on provider-call budgeting)

## Related Docs
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/
  investigation.md` (section 2, full evidence)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/optimization/budget_manager.py`
- `src/engine/policy.py`, `src/engine/phase_governor.py` (the live declarative budget system)

## Assumptions / Open Questions
- Whether this primitive is actually needed is the entire point of this ticket — deliberately not
  pre-judged. "Not needed, delete" is as valid an outcome as "needed, build it (rescoped)."

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
