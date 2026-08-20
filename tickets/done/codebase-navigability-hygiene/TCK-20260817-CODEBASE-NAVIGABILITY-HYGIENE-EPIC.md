---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC
phase: done
date: 2026-08-17
tags: [testing, architecture]
---

# TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC

## Title
Codebase navigability & test hygiene: all 4 original items resolved or extracted (2026-08-19)

## Status
DONE

## Tier
epic

## Type
refactor

## Priority
P3

## Request Summary
Four independent, low-risk navigability/discoverability items originally surfaced by the codebase
health audit. All 4 are now resolved or extracted (see Scope below): items 1 and 3 became
standalone standard-tier tickets once concretely investigated; items 2 and 4 (plus the closely
related `tests/helpers/` question) were resolved directly, with documented findings, once
investigated — neither needed an implementation ticket.

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
- **(2026-08-19)** Item 4 (`pipeline.py`/`tactical.py` coverage) **resolved: genuinely, extensively
  covered — not a gap.** No exactly-named `test_pipeline.py`/`test_tactical.py` file exists (the
  audit's literal observation was correct), but that's not the same as untested. Verified via
  `grep` for actual call sites (not just imports): `AuthoritativeApplyPipeline.refine()` — the
  pipeline's real entry point — is called directly by **71 test files**; `TacticalDecisionSystem`'s
  two public static methods (`evaluate_entity_intent`, `select_best_target`) are called directly
  by **15 test files**, plus 6 more reference the class in architecture-guard tests. Both classes
  are exercised through the distributed per-domain integration/unit pattern this repo already uses
  for its central pipeline (dedicated `tests/integration/pipeline/`, 9 files, plus dozens of
  domain-specific unit/integration tests calling through it) — not via one monolithic file, which
  is a reasonable, expected shape for the "singular bottleneck for authoritative truth," not a gap.
- **(2026-08-19)** `tests/helpers/` under-utilization **resolved: real, but explained — not
  invisible reuse.** Confirmed via `grep`: zero `conftest.py` files import `tests/helpers/` at
  all, so the epic's own hypothesized explanation (invisible fixture-based reuse) is **false**. The
  real explanation: only 3 of 1,140+ test files import `tests/helpers/` directly (matching the
  audit's original 7-of-1,140 count, most of those 7 hits being internal cross-references within
  `tests/helpers/` itself), while **359 test files** use `V2EntityBuilder` (the production code's
  own fluent entity builder) directly instead. `tests/helpers/` is a parallel, test-only
  construction helper that never gained adoption because the production builder already serves the
  same need — low severity, not neglect. No action taken; a future, separate, optional decision
  could trim `tests/helpers/` to its 3 genuinely-used modules, but that's marginal value not
  ticketed here.
- All 4 original items are now resolved or extracted; this epic has no remaining unscoped work of
  its own. It stays open per its own Acceptance Criteria until the 2 extracted sibling tickets
  (`TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`, `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-
  NESTING`) reach `tickets/done/`.

## Out of Scope
- Any consolidation of `src/observability/mining/`'s classes — resolved as not needed (see Scope).
- Writing new tests for `pipeline.py`/`tactical.py` — resolved as already extensively covered.
- Trimming or removing `tests/helpers/`'s under-used modules — a real but marginal, optional
  follow-up, not scoped here.

## Acceptance Criteria
- [x] A documented answer (not an assumption) exists on whether `pipeline.py`/`tactical.py` are
      genuinely covered (yes — 71 + 15 direct call sites), and whether `tests/helpers/`
      under-utilization reflects hand-rolled duplication or invisible `conftest.py`-fixture reuse
      (neither — it's genuine low adoption, explained by `V2EntityBuilder` already covering the
      same need).
- [x] All 4 original items have a documented resolution — 2 extracted to standalone tickets, 2
      resolved directly with no code change needed.
- [x] This epic is not closed until the 2 extracted sibling tickets reach `tickets/done/` —
      confirmed 2026-08-20: both `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT` and
      `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` are present in `tickets/done/`.

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
- src/engine/pipeline.py (`AuthoritativeApplyPipeline`)
- src/engine/tactical.py (`TacticalDecisionSystem`)
- tests/helpers/
- src/core/builder.py (`V2EntityBuilder` — the reason `tests/helpers/` stayed under-adopted)

## Assumptions / Open Questions
None remaining — all 4 original items resolved or extracted.

## Implementation Notes
No implementation performed by this ticket itself — 2 items extracted to standalone tickets for
separate implementation, 2 items resolved as no-code-change-needed findings, documented in Scope
above.

## Test Summary
No direct tests — a documentation/scoping ticket. The extracted sibling tickets each carry their
own test plan.

## Files Changed
- This ticket file and `docs/plans/codebase_navigability_hygiene_epic.md` (findings documented)

## Completion Summary
All 4 original navigability/discoverability items resolved or extracted: item 1
(`src/lab/workflows.py` split) and item 3 (`tests/unit/domains/` nesting) extracted into
standalone standard-tier tickets, both now DONE (`TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`,
`TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`); item 2 (`src/observability/mining/` naming
overlap) and item 4 (`pipeline.py`/`tactical.py` coverage), plus the `tests/helpers/`
under-utilization question, resolved directly with documented findings, no code change needed.
Closed 2026-08-20 once the gate condition (both extracted siblings in `tickets/done/`) was
confirmed satisfied. `docs/plans/codebase_navigability_hygiene_epic.md` archived alongside this
closure.
