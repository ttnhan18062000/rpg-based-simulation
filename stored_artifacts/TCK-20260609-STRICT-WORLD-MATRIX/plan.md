---
ticket: TCK-20260609-STRICT-WORLD-MATRIX
phase: plan
---

# Plan

## New file
`tests/integration/content/test_strict_world_matrix.py`

## Matrix rows (parameterized)
7 cumulative compositions: frontier_only → + wolf_den → + goblin_camp → + old_mine
→ + bandit_road → + undead → + moon_cult

## Test groups

### Pre-assembly (always pass)
- test_each_module_loads_from_repository
- test_each_module_normalizes_without_error
- test_each_module_has_deterministic_fingerprint
- test_catalog_seeds_runtime_registries (once, not per-row)

### Full-assembly (xfail: CAT-REL-099)
- test_row_produces_world_spec
- test_row_produces_compile_context_with_seeded_entities
- test_row_assembly_has_no_blocking_errors
- test_row_assembly_is_deterministic
- test_row_no_hidden_legacy_fallback_in_archetype_entities
