---
status: historical
layer: testing
authority: P1
audience: agent
maturity: shipped
archived: 2026-08-20
tags: [testing, architecture]
---

# Epic Plan — Codebase Navigability & Test Hygiene

**Tracking ticket:** `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`
**Source:** `docs/audits/D24_codebase_health_observatory.md` §D, §F, §I
**Priority:** P3

## Problem

Four independent, low-risk navigability/discoverability items, none urgent individually:

1. **(2026-08-19) Extracted to `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`.**
   `src/lab/workflows.py` — 2,694 LoC, the single largest file in `src/`, containing 9 distinct
   `*Workflow` classes. AST parse confirmed: 8 milestone-numbered (M96-M102 + Revert),
   independently-sized (104-507 line) pipeline-stage classes + 1 shared helper — a mild
   file-organization smell, not a god-class, and mechanically splittable (10 import call sites,
   all facade-preservable).
2. **(2026-08-19) Resolved: not duplicative — no ticket needed.** `src/observability/mining/` (10
   files, 2,302 LoC) has 4 similarly-named orchestration classes (`MiningExperimentController`,
   `MiningReviewWorkflow`, `MiningQualityGate`, `AIAgentInvestigationRunner`) whose boundary was
   unclear from names alone. AST-level structural investigation (signatures + docstrings, not full
   bodies) found each has a distinct, non-overlapping responsibility — see the tracking ticket's
   `## Scope` for the full writeup. Was **Inferred, not confirmed** before; now resolved at
   signature/docstring confidence (not full-behavioral confidence).
3. **(2026-08-19) Extracted to `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`.**
   `tests/unit/domains/` vs. flat domains-subpackage test dirs (`tests/unit/domains/campaigns/`,
   `tests/unit/domains/faction/`, etc.) is a directory-naming inconsistency, not a coverage gap — verified
   exact split: 13 of 19 `src/domains/` subpackages nested correctly, 6 (`campaigns`, `chronicle`,
   `culture`, `faction`, `feature_packs`, `optimization`, 61 files) flat. Once concretely
   evidenced, this stopped needing the epic's `create-tickets` pass and became directly
   actionable, same as this parent tree's other now-downgraded siblings.
4. **(2026-08-19) Resolved: genuinely, extensively covered — not a gap.** `pipeline.py`/
   `tactical.py` (both top-5 by git churn, high graph centrality) have no exactly-named dedicated
   unit test file — the audit's literal observation was correct, but not the same as untested.
   `grep` for actual call sites (not just imports) found `AuthoritativeApplyPipeline.refine()`
   called directly by 71 test files, and `TacticalDecisionSystem`'s two public static methods
   called directly by 15 more (+ 6 referencing the class in architecture guards). Both are
   exercised through this repo's existing distributed per-domain integration/unit pattern
   (dedicated `tests/integration/pipeline/`, plus dozens of domain suites calling through it) —
   expected shape for a central pipeline, not a smell.

Separately, the closely related `tests/helpers/` question: **(2026-08-19) Resolved: real, but
explained.** Only 3 of 1,140+ test files import `tests/helpers/` directly (matching the audit's
original count). `grep` confirmed zero `conftest.py` files import it either — the hypothesized
"invisible fixture reuse" explanation is false. The real explanation: 359 test files use
`V2EntityBuilder` (the production code's own builder) directly instead — `tests/helpers/` is a
parallel, test-only construction helper that never gained adoption because the production builder
already serves the same need. Low severity, not neglect; no action taken.

## Scope for the eventual `create-tickets` pass

None — all 4 original items (plus the related `tests/helpers/` question) are now resolved or
extracted; nothing remains for a `create-tickets` pass.

## Out of scope

- Trimming or removing `tests/helpers/`'s under-used modules — a real but marginal, optional
  follow-up, not scoped here or anywhere yet.

## Acceptance signal for this epic (not yet broken into child tickets)

All 4 items now have a documented resolution:
- `src/lab/workflows.py` split: see `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`.
- `mining/` naming overlap: resolved above, not duplicative.
- Domains test-directory placement: see `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`.
- `pipeline.py`/`tactical.py` coverage (+ `tests/helpers/`): resolved above, both genuinely fine.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic J)
- `docs/audits/D24_codebase_health_observatory.md` (§D, §F, §I, §M Phase 2 item 7)
