---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
artifact_type: test_plan
tags: [architecture, testing]
---

# Test Plan — TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Tests to add (e.g. `tests/tools/test_code_health_impact.py`)
1. **Dependents lookup correctness — updated during Review to match the corrected design (reuse
   `graphify affected`, don't hand-roll BFS/DFS)**: (a) a fixture proving path→symbol-node
   resolution against a small synthetic `graph.json`-shaped structure — given a file path, assert
   the correct symbol/class node(s) defined in that file are found; (b) a test proving multi-symbol
   aggregation/dedup — when a file defines 2+ symbols each with overlapping `affected` results, the
   final per-file dependent list has no duplicates; (c) a test that the "no unique node match"
   case (a file with zero resolvable symbols, e.g. a pure-constants module) degrades to a clearly-
   labeled empty result, not a crash.
2. **`related_code_areas` mixed-shape resolution**: a fixture `REGISTRY.yaml`-shaped entry with a
   bare symbol name (not a path) in `related_code_areas` — assert the command resolves it via the
   graphify node index rather than failing or silently ignoring it (the specific gap this
   investigation found).
3. **Empty `related_code_areas` degradation**: assert the command still produces a sensible
   (non-crashing, clearly-labeled-as-partial) result when the target path has zero
   `related_code_areas` hits — true for ~47% of real registry entries per investigation.md.
4. **Real-path smoke test against D24 §L's worked example**: run against `src/engine/pipeline.py`
   and confirm the output includes `engine/kernel.py` as a direct dependent (per the audit's own
   confirmed example) — not a golden-value pin on the full output (which will legitimately change
   as the codebase evolves), just this one stable fact.
5. **Second real-path test with a different profile**: a low-centrality, low-churn file, to prove
   the command generalizes beyond the one example it was designed against.

## Acceptance-criteria mapping
| Acceptance criterion | Verified by |
|---|---|
| Command produces D24 §L's output shape for `pipeline.py` | Test 4 |
| Command generalizes to at least one other real path | Test 5 |
| Mixed-shape `related_code_areas` data is handled, not silently mishandled | Tests 2-3 |
