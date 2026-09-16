---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION

No new test file — this ticket is a registry data change (new `depends_on` edges), not new tool
code. Coverage comes from the existing registry test suite continuing to pass against the new
edges, plus direct manual verification recorded in investigation.md:

1. `make mechanism-registry-validate` — the 6-invariant validator (acyclicity, layer declaration,
   depends_on resolution, etc.) must still pass with the new edges (proves no cycle was introduced
   and every new edge resolves to a real mechanism id).
2. `tools/mechanism_registry_graphify_check.py` — run against the full updated edge set (done,
   recorded in investigation.md), not just spot-checked.
3. Direct manual check: `movement`'s own transitive-dependent count and priority, before and after,
   read directly from the regenerated `mechanism_priority_view.md` — not assumed from the edge
   count alone (transitive closure could in principle not propagate as expected; confirmed it did:
   14 transitive dependents, priority 70, #1 in the ranking).
4. Full scoped suite (`tests/unit/tools/ tests/unit/engine/test_capability_registry.py
   tests/mechanic_scenarios/`) re-run to confirm no existing test's real-data assertions broke
   from the new edges (e.g. any test hardcoding a specific transitive-dependent-count for a
   mechanism this ticket touched) — `graphify-out/` genuinely moved aside and restored.
