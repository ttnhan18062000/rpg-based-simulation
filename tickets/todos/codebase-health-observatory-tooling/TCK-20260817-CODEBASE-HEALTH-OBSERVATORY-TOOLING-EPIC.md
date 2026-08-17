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
Build codebase-health observatory tooling: baseline target, impact command, historical scorecard

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
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (`make codebase-health-baseline`, `code-health impact <path>` command, historical snapshot
  file, scorecard), producing investigated child tickets in
  `tickets/todos/codebase-health-observatory-tooling/`.

## Out of Scope
- Building any of this before `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` lands, since
  the impact command explicitly depends on those tests being trustworthy.
- A single aggregate "health score" — trend arrows across multiple dimensions instead, per the
  source audit's own explicit guidance.

## Acceptance Criteria
- [ ] `docs/plans/codebase_health_observatory_tooling_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Sequencing after Epic G (architecture boundary hardening) is respected when this epic is picked up.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC (prerequisite — impact command depends on
  hardened boundary tests)

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
