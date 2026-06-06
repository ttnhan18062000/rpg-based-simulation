# TCK-20260419-MD-TASK1-FREEZE-CONCURRENCY-CONTRACT

## Title
Milestone D - Task 1: Audit and Freeze the Bounded Concurrency Contract

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit the existing concurrency documentation and draft a finalized contract that resolves all naming drift and explicitly defines the laws for packets, results, and commit ordering.

## Scope
- Align `WorkClass` terminology between code and contract.
- Formalize the Deterministic Commit Law (Priority-based).
- Lock the One-Result-Per-Entity law.

## Out of Scope
- Code implementation of the new commit law (Task 2).
- Hardening of fallback logic (Task 3).

## Acceptance Criteria
- [ ] `docs/engine/bounded_concurrency_contract_md.md` updated and frozen.
- [ ] Priorities correctly mapped to `CRITICAL`, `PERIODIC`, `OPPORTUNISTIC`, `DEFERRED`.
- [ ] Non-authoritative fallback boundary explicitly documented.

## Related Tickets
- None

## Related Docs
- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/archive/resource_implementation_v2_milestone_d.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/core/work.py`
- `src/core/concurrency_law.py`

## Assumptions / Open Questions
- Assumption: The existing `WorkClass` names are the authoritative domain names we want to keep.

## Implementation Notes
- Drafted initial alignment plan.
- Identified priority drift in existing document.
