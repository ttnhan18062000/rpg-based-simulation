---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS
artifact_type: test_plan
tags: [world, investigation]
---

# Test plan

- (g): a composition with one `enabled: false` ref whose module exists must not report ASM-COMP-001; a composition naming a module absent from the repository still must.
- (d): a duplicate `module_refs` entry either composes twice under two namespaces or raises, per the decision.
- (e): per decision, an `order` test (authored order decides the merge sequence, or the field is rejected) and a dangling-`requires` test.
- (i): per decision.
- Guards: `test_resolved_snapshot_freshness` (24 worlds re-resolve byte-identically), the world-assembly unit and integration tests, `tests/unit/tools` serially under MemoryMax=3G, `make code-health`, `make lint-imports`, paired --neutral 1000t.
