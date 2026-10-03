---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING

## Scoped suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/ -q
```

## New coverage

- `tests/unit/tools/test_mechanism_registry.py`: `implemented_by` validation — rejects non-list,
  rejects a nonexistent path (load-bearing: the whole point of the field), accepts a real existing
  path, accepts absence (optional field).
- `tests/unit/tools/test_mechanism_registry_completeness_check.py`: enumeration resolves shims not
  shim filenames (load-bearing); every `EXCLUSIONS` entry points to a real target and carries a
  real reason; `build_report()` never double-counts a target across bound/excluded/unbound;
  `mechanisms_with_binding` matches a direct recount; today's enumeration/binding/exclusion counts
  are pinned (load-bearing drift detector, mirrors the atlas mapping test's own convention).

## Regressions fixed (all real substance, not gate edits)

- `test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms`: expected `unmapped` set grew by
  3 (the new mechanisms have no atlas card, same as the completeness pass's own 13).
- `test_transitive_dependents_matches_real_data`: 24 → 25, `commitment_pressure_consequences`'s new
  `depends_on: [commitment_betrayal]` edge is transitively downstream of
  `action_pacing_readiness`.
- `test_state_change_propagates_to_all_three_real_consumers`: was failing because the real
  committed atlas hadn't yet been regenerated for `causal_spatial_memory`'s corrected state —
  fixed by running `mechanism_atlas_regenerate.py` for real, not by loosening the test's control
  assertion.
- `test_real_wiring_map_has_no_drift_against_the_real_registry`: same root cause, fixed by hand-
  editing the wiring map's `MEM` node (`:::bug` → `:::gated`, label text corrected) — the
  established surgical-edit convention from `motivation_doctrine`'s own earlier correction.
- `test_render_is_not_truncated` (HTML): off-by-one in the test itself (the `<thead><tr>` header
  row also matches the literal substring `<tr>`) — fixed the test's own assertion, not the
  generator.

## Result

165 tests passing, both with `graphify-out/` present and with it genuinely moved aside and
restored.
