---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
phase: open
date: 2026-08-19
tags: [architecture, testing]
---

# TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

## Title
Add a permanent make codebase-health-baseline target for LoC/churn snapshots, excluding bookkeeping noise

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Item 1 (Phase 1, item 4) of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, extracted
once confirmed concrete and self-contained. Cross-referencing D24's own 11-item master plan
against this session's completed work found Phases 1-2 (7 of 11 items) already done, and Epic K's
own stated prerequisite (Epic G, boundary-test hardening) confirmed done — Epic K is now genuinely
unblocked. This specific item has no dependency on the rest of Epic K's scope (impact command,
scorecard, PR report generator, which are genuinely sequential and stay bundled in the epic) and
is ready to build now: a permanent, `make`-invokable LoC/churn snapshot reproducing the shape of
`docs/audits/D24_codebase_health_observatory.md` §C's table, computed fresh each run, with known
append-only bookkeeping files excluded from the churn measurement specifically (without that
exclusion, every report is dominated by expected bookkeeping noise, not real signal).

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- New script (e.g. `tools/codebase_health_baseline.py`) computing: source/test LoC and file
  counts, test:source ratio, top-level `src/` package count, test subdirectory count, commit
  count, `.md` doc count, `docs/REGISTRY.yaml` size, dead-bytecode file count.
- Churn measurement excludes `agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
  `docs/REGISTRY.yaml` via a git pathspec exclusion, not a post-hoc filter.
- New `make codebase-health-baseline` target.
- Explicit, documented decision on CI-wiring vs. on-demand-only (default to on-demand-only,
  matching this session's finding that sibling tools in this family are Makefile-only).

## Out of Scope
- The `code-health impact <path>` command, historical snapshots/scorecard, and PR/AI report
  generator — remain Epic K's own bundled scope (genuinely sequential, not independently
  extractable).
- A single aggregate "health score" — any future scorecard built on this data must use trend
  arrows across dimensions, per the source audit's explicit guidance.

## Acceptance Criteria
- [ ] `make codebase-health-baseline` exists and runs, producing the full metrics table.
- [ ] Bookkeeping-file churn (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
      `docs/REGISTRY.yaml`) is excluded from the churn measurement, verified by a fixture proving
      synthetic noise in those files doesn't move the computed churn metric.
- [ ] A live run produces numbers that meaningfully differ from D24 §C's stale, hardcoded
      snapshot (e.g. dead-bytecode count now 0, not 601) — proves live measurement, not an echoed
      cached value.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC (item extracted from here; epic remains
  open for its other 3, genuinely-sequential items)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC (Epic K's own prerequisite, confirmed done —
  context only, not a blocker for this specific item)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§B, §C, §L, §M — source data and methodology)
- docs/plans/codebase_health_observatory_tooling_epic.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET/

## Related Code Areas
- tools/ (new script)
- Makefile

## Assumptions / Open Questions
- Exact "source" vs. "test" file-classification rule (beyond the obvious `src/` vs `tests/` split)
  is left to the implementer to infer from how the repo already partitions these directories.
- CI-wiring vs. on-demand-only is a real decision to make explicitly, not left ambiguous — see
  plan.md step 3.

## Implementation Notes
(pending — implementation by a separate agent, per this ticket's own scope)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
