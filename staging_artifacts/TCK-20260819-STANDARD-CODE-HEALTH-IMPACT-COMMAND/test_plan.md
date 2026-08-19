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
1. **Dependents lookup correctness**: a fixture graph (small, synthetic `graph.json`-shaped data)
   with a known dependency chain — assert the command finds the correct direct dependents and
   respects whatever transitive-depth cap the implementer chose.
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
