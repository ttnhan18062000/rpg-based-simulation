---
status: active
layer: testing
authority: P1
audience: agent
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
   `tests/unit/domains/` vs. flat domains-subpackage test dirs (`tests/unit/campaigns/`,
   `tests/unit/faction/`, etc.) is a directory-naming inconsistency, not a coverage gap — verified
   exact split: 13 of 19 `src/domains/` subpackages nested correctly, 6 (`campaigns`, `chronicle`,
   `culture`, `faction`, `feature_packs`, `optimization`, 61 files) flat. Once concretely
   evidenced, this stopped needing the epic's `create-tickets` pass and became directly
   actionable, same as this parent tree's other now-downgraded siblings.
4. `pipeline.py`/`tactical.py` (both top-5 by git churn, high graph centrality) have no
   exactly-named dedicated unit test file in `tests/unit/engine/` — plausibly covered indirectly
   via integration/kernel determinism suites, but not confirmed either way.

## Scope for the eventual `create-tickets` pass

Only the remaining, unresolved item:

- Directly verify `pipeline.py`/`tactical.py` test coverage (confirm it's real, not assumed).
- Separately: resolve `tests/helpers/` under-utilization (only 7 of 1,140 sampled test files
  import it directly) — determine whether reuse happens invisibly via `conftest.py` fixtures
  instead, and document that pattern if so.

## Out of scope

- Writing new tests for `pipeline.py`/`tactical.py` unless the coverage-verification step
  confirms a real gap.

## Acceptance signal for this epic (not yet broken into child tickets)

- A documented answer (not an assumption) on whether `pipeline.py`/`tactical.py` are genuinely
  covered.
- (`src/lab/workflows.py` split: see `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT`. Domains
  test-directory placement: see `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`. `mining/` naming
  overlap: resolved above, not duplicative. None of the three longer tracked here.)

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic J)
- `docs/audits/D24_codebase_health_observatory.md` (§D, §F, §I, §M Phase 2 item 7)
