---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS

## Scoped suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/ -q
```

Same scope as the sibling registry tickets this epic (T4, priority-weight fix, dependency-graph
population, motivation_doctrine correction) — covers the registry schema validator, atlas/
capabilities/wiring-map regenerators and their mapping tables, the verification/priority view
generators, and the mechanic-verification scenarios.

## Cases

- **Schema validity**: `mechanisms.yaml` parses and validates after all 11 additions
  (`OK: ... valid, 86 mechanisms`).
- **Atlas mapping regression** (`test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms`,
  renamed from `test_mapping_covers_exactly_73_of_75_mechanisms`): the atlas-carded-mechanism count
  stays at 73; the `unmapped` set grows from `{nest, lair}` to include all 11 newly registered
  mechanisms (13 total), since none of them have an atlas card. Not a regression — the whole point
  of this pass is registering mechanisms the atlas never carded.
- **No other existing test's expectations change**: the 11 new mechanisms have no `depends_on`
  edges into the existing graph (out of scope, per plan.md), so `transitive_dependents`/`priority`
  regression tests for existing mechanisms are unaffected.
- **`graphify-out/`-absent re-verification**: move `graphify-out/` aside, run the full scoped
  suite, confirm 147/147 pass, restore it. Standing epic discipline — confirms no test secretly
  depends on the graph artifact being present.

## Result

147 passed, both with `graphify-out/` present and with it genuinely moved aside and restored.
