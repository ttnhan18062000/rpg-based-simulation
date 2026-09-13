---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION
phase: done
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION

## Title
`budget_manager.py`'s imperative, stateful per-tick budget-enforcement primitive — genuinely missing, no live equivalent; should it be built?

## Status
DONE

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
- [x] Real evidence on whether phases that read `GovernorPolicy`/`PhaseBudgets`' declarative limits
      actually respect them: zero documented incidents found of a phase exceeding its own
      declarative budget uncaught. **Corrected finding, not just "no evidence either way"**: a real,
      live, coarser backstop already exists — the wall-clock mid-tick throttle
      (`kernel.py`'s `_phase_resolution()`) plus `governor.py`'s `tick_compute_ms` mode-escalation
      genuinely catches real overruns (drops work, forces DEGRADED/SURVIVAL). This reclassifies the
      origin C1 audit's own "genuinely missing, no live equivalent" label to "partially covered by
      a coarser live mechanism" — the same partial-supersession shape C1 established for most of
      the rest of the package, found by checking, not inherited from the survey.
- [x] The overlap question with `provider_enforcement.py`'s own determination is checked and
      recorded: both ultimately ask "is provider-call volume a real risk" — answered once, under
      `PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`, not duplicated here.
- [x] A peer-routed (and user-routed) build/don't-build decision: don't build — delete, record the
      idea. A finer-grained version of something already live, addressing zero documented
      incidents, in a performance category the user's own standing direction defers to a dedicated
      future effort.
- [x] "If built" AC does not apply.
- [x] Non-import-reference guard applied: `.github/workflows/*.yml`/`Makefile` checked for
      hardcoded references to `budget_manager.py`, `PhaseBudgetManager`, and its dedicated test
      files before deleting — zero hits.

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
Full evidence in
`stored_artifacts/TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION/investigation.md`.
The corrected classification (partial supersession by the wall-clock/governor backstop, not
genuinely missing) was reported to peer alongside the provider-enforcement and orphaned-capability
findings in one batch; peer explicitly flagged this correction as mattering more than the
disposition itself, since it corrects the origin C1 audit's own classification. Disposition
(delete, record) is the user's own decision, applying the same "real capability, zero observed
need, performance work deferred" reasoning established for the sibling `ORPHANED-CAPABILITY-
DETERMINATION`'s capabilities 3/5/6.

Deleted `budget_manager.py`. A first grep for its dedicated test file missed one —
`tests/unit/perf/test_phase10_phase_budget_manager.py` — caught on a second, class-name-targeted
pass; also deleted `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` (confirmed
entirely dependent on the deleted class via a real 5-scenario perf-benchmark test, no independent
coverage riding along — its incidental `FeatureFlagManager()` instantiation is dead-in-test-body,
never used to gate anything, and that class has its own extensive, unaffected coverage elsewhere).
Recorded the "per-category, mid-tick imperative budget enforcement" idea in
`docs/plans/design_enhancement/performance_milestones_epic.md`'s shared new section.

## Test Summary
Covered by the shared regression sweep for all three tickets (1528 passed, 1 skipped). Post-deletion
grep confirms zero remaining references to `PhaseBudgetManager`/`budget_manager.py` in
`src/`/`tests/`, and zero hardcoded references in `.github/workflows/*.yml`/`Makefile`.

## Files Changed
- `src/domains/optimization/budget_manager.py` — deleted.
- `tests/unit/perf/test_phase10_phase_budget_manager.py` — deleted.
- `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` — deleted.
- `docs/plans/design_enhancement/performance_milestones_epic.md` — new "Preserved capability
  ideas" section, shared with the two sibling tickets.

## Completion Summary
Corrected the origin audit's own "genuinely missing" classification to "partially covered by a
coarser live mechanism" (the wall-clock/governor backstop) — a real finding independent of the
eventual disposition. Determined not needed now: the finer-grained enforcement it would add
addresses zero documented incidents, in a performance category the user has deferred. Deleted the
module and both its test files, recorded the underlying idea for the future performance effort. No
known material gap left unstated.
