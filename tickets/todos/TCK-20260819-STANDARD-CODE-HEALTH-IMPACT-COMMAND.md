---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
phase: open
date: 2026-08-19
tags: [architecture, testing]
---

# TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Title
Build the code-health impact <path> command from graphify + tests/architecture + docs/REGISTRY.yaml

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Item 2 of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, the next item in that epic's
own dependency chain, extracted once concretely investigated. Verified all 3 of the epic's claimed
data sources against real, current state (not the epic doc's framing taken on faith): `graphify`'s
CLI has no ready-made "find dependents of path X" verb (needs a custom graph traversal over
`graphify-out/graph.json`, not just wiring); `tests/architecture/`'s 17 current boundary test
files are real and directly usable; `docs/REGISTRY.yaml`'s `related_code_areas` field is only
53.3% filled and sometimes contains bare symbol names rather than resolvable paths, requiring a
resolution step, not a literal path match.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- New script (e.g. `tools/code_health_impact.py`) implementing `code-health impact <path>`.
- Dependents lookup via direct `graphify-out/graph.json` traversal (BFS/DFS over import/use
  edges), with an explicit, documented transitive-depth cap.
- Architecture-rule matching against `tests/architecture/`'s current 17 boundary test files by
  subsystem heuristic.
- Required-test inference combining `docs/REGISTRY.yaml`'s `related_code_areas` (with symbol-name/
  bare-filename resolution, not literal path matching) and the existing `src/`→`tests/` naming
  convention already documented in `.claude/agents/test-scoper.md`'s Test Directory Map.
- Criticality tier from churn × centrality, reusing `TCK-20260819-STANDARD-CODEBASE-HEALTH-
  BASELINE-TARGET`'s churn computation once that ticket lands, cross-referenced with graphify edge
  degree for centrality — not duplicated.
- Verified against D24 §L's `src/engine/pipeline.py` worked example plus at least one additional,
  differently-profiled real path.

## Out of Scope
- Historical snapshots, scorecard, and the PR/AI report generator — remain Epic K's own bundled
  scope, built on top of this command's output shape once it exists.
- Perfect precision on architecture-rule matching or required-test inference — a discovery/triage
  aid, not a certified coverage oracle.

## Acceptance Criteria
- [ ] `code-health impact src/engine/pipeline.py` produces the same shape of output as D24 §L's
      worked example, and correctly includes `engine/kernel.py` as a direct dependent.
- [ ] The command generalizes to at least one other real path with a different
      churn/centrality profile, not just the one example it was designed against.
- [ ] `related_code_areas` entries containing bare symbol names or filenames (not full paths) are
      resolved, not silently mishandled — and the command degrades gracefully (clearly labeled,
      not crashing) when a target path has zero `related_code_areas` hits.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC (item extracted from here; epic remains
  open for its other 2 items — historical snapshots/scorecard, PR report generator)
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET (sibling item from the same epic; this
  ticket's criticality-tier step reuses that ticket's churn computation once it lands — no other
  dependency)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§L — worked design + example)
- docs/plans/codebase_health_observatory_tooling_epic.md
- .claude/agents/test-scoper.md (reusable src/→tests/ mapping reference)

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/

## Related Code Areas
- graphify-out/graph.json
- tests/architecture/
- docs/REGISTRY.yaml
- tools/ (new script)

## Assumptions / Open Questions
- Exact transitive-dependent depth cap is left to the implementer — D24 §L's own worked example
  only shows direct dependents, so there's no existing precedent to match exactly.
- Whether this ticket's churn/centrality reuse can proceed before
  `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET` is actually implemented, or must wait
  for it, is an implementation-order decision for whoever picks these up — not resolved here.

## Implementation Notes
(pending — implementation by a separate agent, per this ticket's own scope)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
