---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION
phase: done
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION

## Title
`provider_enforcement.py`'s provider-call rate limiting and global-scan rejection — genuinely missing at any scope; should it be built?

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
- [x] Real evidence on whether unbounded/unscoped provider calls are a real, observed risk: no
      evidence found of an observed problem. Separately, and more decisively: the module's own
      calling convention (`entity_id`/`region_id` kwarg scoping) doesn't match how real providers
      are actually called (`ResourceOpportunityProvider.get_opportunities()` takes a full entity,
      derives scope internally) — the module targets a shape the codebase doesn't use, same
      aged-out pattern as the sibling `ORPHANED-CAPABILITY-DETERMINATION`'s capabilities 1/2/4.
- [x] The overlap question with `budget_manager.py`'s own determination is checked and recorded:
      both ask a version of "is provider-call volume a real risk" — answered once, here, and
      `ORPHANED-CAPABILITY-DETERMINATION`'s own capability 3 inherits this finding rather than
      re-investigating it.
- [x] A peer-routed (and user-routed) build/don't-build decision: don't build — delete, record the
      idea, same reasoning as the sibling determinations.
- [x] "If built" AC does not apply.
- [x] Non-import-reference guard applied: `.github/workflows/*.yml`/`Makefile` checked for
      hardcoded references to `provider_enforcement.py`/`ProviderBudgetEnforcement`/its test file
      before deleting — zero hits. Confirmed the containing test directory
      (`tests/unit/world/providers/`) retains other real coverage
      (`test_resource_opportunity_provider.py`), not left hollow.

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
Full evidence in
`stored_artifacts/TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION/investigation.md`.
Reported to peer alongside the sibling determinations' own findings; disposition (delete, record)
is the user's own decision. This ticket's own finding (the calling-convention mismatch) was the
decisive evidence peer cited for treating this the same as `ORPHANED-CAPABILITY-DETERMINATION`'s
capabilities 1/2/4 — an artifact of infrastructure that moved on or never arrived, not a shortcut
to a real capability.

Deleted `provider_enforcement.py` and its dedicated test file
(`tests/unit/world/providers/test_phase10_provider_budget_enforcement.py`). Recorded the "provider
call-rate limiting" idea in `docs/plans/design_enhancement/performance_milestones_epic.md`'s shared
new section, explicit that a fresh implementation would need its own signature design against real
provider call sites, not a revival of this module's own.

## Test Summary
Covered by the shared regression sweep for all three tickets (1528 passed, 1 skipped).
`tests/unit/world/providers/test_resource_opportunity_provider.py` (the real, live provider's own
test) confirmed unaffected. Post-deletion grep confirms zero remaining references to
`ProviderBudgetEnforcement`/`provider_enforcement.py`.

## Files Changed
- `src/domains/optimization/provider_enforcement.py` — deleted.
- `tests/unit/world/providers/test_phase10_provider_budget_enforcement.py` — deleted.
- `docs/plans/design_enhancement/performance_milestones_epic.md` — new "Preserved capability
  ideas" section, shared with the two sibling tickets.

## Completion Summary
Found the module targets a calling convention (`entity_id`/`region_id` scoping) real live
providers don't use — the decisive evidence for this batch's own "aged-out infrastructure, not a
withheld capability" framing. Answered the provider-call-volume question once here rather than
duplicating it in the sibling `ORPHANED-CAPABILITY-DETERMINATION`. Determined not needed now, same
reasoning as the sibling tickets: deleted the module, recorded the idea. No known material gap left
unstated.
