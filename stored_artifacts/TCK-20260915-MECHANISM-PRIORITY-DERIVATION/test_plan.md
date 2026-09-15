---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-PRIORITY-DERIVATION
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260915-MECHANISM-PRIORITY-DERIVATION

## Regression Surface

Extends `tools/mechanism_registry.py` (Foundation + Verification-Axis). All 43 existing tests in
`tests/unit/tools/test_mechanism_registry.py`, the 6/7 graphify-check tests, and the 9
capability-registry tests must keep passing unmodified.

## New Tests (in a new file, `tests/unit/tools/test_mechanism_priority_derivation.py`)

1. **`test_transitive_dependents_matches_real_data`** — against the real committed registry,
   `action_pacing_readiness` has exactly 23 transitive dependents (the exact number computed and
   reported to peer in investigation.md). A real-data regression guard: if the registry's own edges
   change later without this number being re-derived, this test fails loudly rather than silently
   drifting.
2. **`test_transitive_dependents_raises_on_cycle`** (AC #6) — a deliberately invalid fixture (`a
   depends_on b`, `b depends_on a`) passed directly to the traversal function; assert it fails
   loudly (raises or returns an explicit error), proven from this ticket's own code path, not
   assumed from Foundation's schema-level `validate()`.
3. **`test_priority_is_rank_times_transitive_dependents`** — fixture arithmetic: a mechanism with
   known rank and known transitive-dependent-count produces the expected product.
4. **`test_unverified_priority_ranking_excludes_verified_mechanisms`** — fixture with one verified
   and one unverified mechanism; assert the ranking contains only the unverified one.
5. **`test_unverified_priority_ranking_orders_by_priority_descending`** — fixture with 2+ unverified
   mechanisms at different priorities; assert output order.
6. **`test_chart_generator_single_layer_paginates_when_over_threshold`** — real case: the `entity`
   layer's own generated chart (43 mechanisms, over the 40-node threshold) produces more than 1
   page.
7. **`test_chart_generator_ancestors_of_produces_a_real_subgraph`** — a real mechanism with a known
   `depends_on` chain (e.g. `combat_resolution` → `tactical_decision`/`combat_engagement` →
   `action_pacing_readiness`); assert those real ids appear in the generated output.
8. **`test_chart_generator_never_emits_a_diagram_over_the_threshold`** (AC #5, load-bearing) — for
   every generated diagram (all layers, a sample of ancestors-of calls, the top-N view at various
   N), count mermaid node declarations in the output and assert none exceeds the threshold.
9. **`test_direction_is_a_parameter_not_hardcoded`** — call the generator with an explicit
   `direction="TB"`; assert the emitted mermaid source contains `flowchart TB`, confirming the
   default (`BT`) is a parameter, not a literal baked into the template.
10. **`test_wiring_map_classdef_derives_from_registry_state`** — for each node in the wiring map's
    3 existing diagrams that maps to a real mechanism id, assert its mermaid `class` assignment
    matches what the registry's own `state` (mapped through the documented state→classDef table)
    would produce — catches drift between the two going forward, not just proves the one-time edit.

## Scoped Pytest Command

```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_priority_derivation.py tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_graphify_check.py tests/unit/engine/test_capability_registry.py -v
```

## Anti-Drift Test Guards

- Test 1's real-data number (23) must be re-derived independently (a direct computation against
  the committed registry within the test itself, or a value pinned with a clear "re-derive if the
  registry's edges change" comment) — never silently drift into being wrong without the test
  catching it.
- Test 8 must inspect every generated diagram's actual node count programmatically, never assert
  "it looks fine" from a hardcoded small sample — this is the test that actually enforces AC #5.
- Test 10 must not be satisfied by a one-time hand-edit alone; it re-derives the expected classDef
  from the live registry each run, so a future registry `state` change that isn't mirrored into the
  wiring map's own hand-authored file is caught, not silently accepted.
