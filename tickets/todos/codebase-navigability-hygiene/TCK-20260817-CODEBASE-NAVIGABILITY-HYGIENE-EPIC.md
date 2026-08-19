---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC
phase: open
date: 2026-08-17
tags: [testing, architecture]
---

# TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC

## Title
Verify pipeline.py/tactical.py test coverage; resolve tests/helpers/ under-utilization

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P3

## Request Summary
Four independent, low-risk navigability/discoverability items originally surfaced by the codebase
health audit. Three are now resolved outside this ticket (see Scope below): the
`src/lab/workflows.py` split and the `tests/unit/domains/` placement inconsistency were each
extracted into their own standalone standard-tier ticket once concretely investigated; the
`src/observability/mining/` naming-overlap question was resolved directly (not duplicative) by an
AST-level structural investigation. What remains: `pipeline.py`/`tactical.py` (both top-5 by churn
and centrality) have no exactly-named dedicated unit test file, plausibly but not confirmed
covered indirectly — plus the related `tests/helpers/` under-utilization question.

- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/codebase_navigability_hygiene_epic.md`. Detailed, investigated child tickets are
  not created yet.
- **(2026-08-19)** Item 3 (`tests/unit/domains/` vs. flat domains-subpackage test-dir placement)
  extracted into its own standalone standard-tier ticket,
  `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`, once the exact split (13 nested / 6 flat) was
  concretely verified.
- **(2026-08-19)** Item 1 (`src/lab/workflows.py` split) extracted into its own standalone
  standard-tier ticket, `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`, once concretely
  investigated (AST structural parse: 8 milestone-numbered pipeline classes + 1 shared helper,
  10 import call sites, all facade-preservable).
- **(2026-08-19)** Item 2 (`src/observability/mining/` naming-overlap investigation)
  **resolved: not duplicative.** AST-level structural parsing (class/function signatures +
  docstrings, no full-body read) of all 9 files in `src/observability/mining/` found 4 classes
  matching the audit's "similarly-named" concern, each with a distinct, non-overlapping stated
  responsibility: `MiningExperimentController` (`controller.py`) orchestrates *execution* of
  large-scale experiment runs; `AIAgentInvestigationRunner` (`orchestrator.py`) orchestrates
  *LLM-driven diagnostic sweeps* over evidence packs from completed runs; `MiningReviewWorkflow`
  (`workflow.py`) is *human* verification/labeling of AI findings, promoting accepted ones to the
  engineering backlog; `MiningQualityGate` (`workflow.py`) is a *CI gate* evaluating experiment
  outcomes against invariants — a different lifecycle point entirely. Together these form one
  coherent pipeline (run → AI-investigate → human-review → CI-gate), sharing a `Mining` naming
  prefix only because they live in the same package, not because they overlap in responsibility.
  **Caveat:** this rests on signatures/docstrings, not full method-body behavior — reasonable
  confidence for closing a "Suspicious, not confirmed" flag, not an ironclad proof; re-open with
  an actual behavioral read if a future incident suggests otherwise. No consolidation ticket
  needed.
- This epic's remaining scope is item 4 only (`pipeline.py`/`tactical.py` coverage verification;
  `tests/helpers/` under-utilization is a closely related fifth thread tracked alongside it). When
  work begins: run `create-tickets` against a proposal document scoped to that remaining item,
  producing investigated child tickets in `tickets/todos/codebase-navigability-hygiene/`.

## Out of Scope
- Any consolidation of `src/observability/mining/`'s classes — resolved as not needed (see Scope).
- Writing new tests for `pipeline.py`/`tactical.py` unless the coverage-verification step
  confirms a real gap.

## Acceptance Criteria
- [ ] A documented answer (not an assumption) exists on whether `pipeline.py`/`tactical.py` are
      genuinely covered, and whether `tests/helpers/` under-utilization reflects hand-rolled
      duplication or invisible `conftest.py`-fixture reuse.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action on its
      remaining item.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT (item 1 extracted from here, 2026-08-19)
- TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING (item 3 extracted from here, 2026-08-19)

## Related Docs
- docs/plans/codebase_navigability_hygiene_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/unit/engine/ (pipeline.py/tactical.py coverage question)
- tests/helpers/

## Assumptions / Open Questions
- Whether `tests/helpers/` under-utilization reflects hand-rolled duplication or invisible
  `conftest.py`-fixture reuse is unconfirmed.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
