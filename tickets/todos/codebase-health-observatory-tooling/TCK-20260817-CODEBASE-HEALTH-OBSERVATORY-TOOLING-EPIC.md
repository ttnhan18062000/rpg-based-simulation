---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
phase: open
date: 2026-08-17
tags: [architecture, testing]
---

# TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC

## Title
Build codebase-health observatory tooling: historical scorecard, PR report generator

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
Most of what a "codebase health observatory" needs already exists in some form in this repo —
`graphify-out/`'s dependency graph, `tests/architecture/`'s boundary tests, `docs/REGISTRY.yaml`'s
`related_code_areas` field. The gap is wiring these together and adding two genuinely missing
pieces: a permanent, noise-excluding LoC/churn baseline target, and a mechanism to persist
metrics over time. Deliberately the lowest-sequenced epic in the whole roadmap — its own `impact`
command design explicitly depends on the boundary tests being hardened first (Epic G).

## Scope
- Scope-only epic: full findings and proposed remediation steps (including a worked
  `code-health impact src/engine/pipeline.py` example) are in
  `docs/plans/codebase_health_observatory_tooling_epic.md`. Detailed, investigated child tickets
  are not created yet.
- **(2026-08-19)** Cross-referenced D24's own 11-item master implementation plan (§M) against this
  session's completed work: Phases 1-2 (7 of 11 items) are now done, and this epic's own stated
  prerequisite (`TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`) is confirmed done — this epic
  is now genuinely unblocked, not just theoretically scoped. Item 1
  (`make codebase-health-baseline`) was extracted into its own standalone standard-tier ticket,
  `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`, once confirmed self-contained (no
  dependency on the rest of this epic's scope).
- **(2026-08-19, continued)** Item 2 (`code-health impact <path>` command) was also extracted,
  into `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`, once its 3 claimed data sources were
  individually verified against real, current state (one real implementation gap found — no
  ready-made graphify CLI verb for "dependents of path X," needs a custom graph traversal; one
  real data-quality nuance found — `docs/REGISTRY.yaml`'s `related_code_areas` is only 53.3%
  filled and sometimes holds bare symbol names, not paths). This epic's remaining scope is now
  only the other 2 items — historical snapshots/scorecard, and the PR/AI report generator — which
  stay bundled since the report generator is explicitly built on top of the impact command's
  output shape, and the scorecard's exact dimension set remains an open design decision.
- When work begins on the remaining 2 items: run `create-tickets` against a proposal document
  scoped to them, producing investigated child tickets in
  `tickets/todos/codebase-health-observatory-tooling/`.

## Out of Scope
- A single aggregate "health score" — trend arrows across multiple dimensions instead, per the
  source audit's own explicit guidance.

## Acceptance Criteria
- [x] Sequencing after Epic G (architecture boundary hardening) is respected — confirmed done,
      this epic is unblocked.
- [ ] Child tickets are created via `create-tickets` once the remaining 2-item scope is chosen for
      action.
- [ ] This epic is not closed until `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`,
      `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`, and the remaining 2 items' eventual
      child tickets all reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC (prerequisite — confirmed done 2026-08-19)
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET (item 1 extracted from here, 2026-08-19)
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND (item 2 extracted from here, 2026-08-19)

## Related Docs
- docs/plans/codebase_health_observatory_tooling_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- graphify-out/
- docs/REGISTRY.yaml
- tests/architecture/
- agent-monitoring/runs.jsonl (pattern precedent for historical snapshots)

## Assumptions / Open Questions
- Exact scorecard dimensions/format are an open design decision for whoever scopes the child
  ticket — the source audit recommends trend arrows, not a single score, but doesn't fully
  specify the dimension set.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
