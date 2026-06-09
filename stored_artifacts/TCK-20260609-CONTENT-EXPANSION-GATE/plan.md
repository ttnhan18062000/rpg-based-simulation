---
ticket: TCK-20260609-CONTENT-EXPANSION-GATE
phase: plan
---

# Plan

- tests/integration/content/test_expansion_gate.py (12 gate items)
- docs/testing/expansion_gate.md (gate documentation)
- Makefile target: gate-expansion

Gate items: 01 registry complete, 02 fail-closed schema, 03 ref graph, 04 no dead data,
05 archetypes present, 06 population→archetype refs, 07 modules normalize, 08 compositions load,
09 adapters project, 10 scenario schema, 11 world assembly (xfail CAT-REL-099), 12 migration map.
