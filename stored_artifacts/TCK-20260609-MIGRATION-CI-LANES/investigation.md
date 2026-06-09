---
ticket: TCK-20260609-MIGRATION-CI-LANES
phase: investigation
---

# Investigation

Makefile exists with test, test-quick, test-cov targets. No CI lane targets existed.
Existing markers from ticket 17 (catalog, content_graph, registry_projection, scenario_setup, strict_matrix, legacy_compat, architecture) provide the foundation for lane marker expressions.

Test counts (verified via --collect-only):
- catalog or content_graph: 15
- worldassembly and not strict_matrix: 52
- strict_matrix: 57
- registry_projection or scenario_setup: 46
- legacy_compat: 40
- architecture: 5
- all-fast combined: 118
