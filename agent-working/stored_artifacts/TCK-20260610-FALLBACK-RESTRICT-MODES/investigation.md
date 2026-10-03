---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-FALLBACK-RESTRICT-MODES
artifact_type: investigation
tags: [fallback, restrict, modes]
---

# TCK-20260610-FALLBACK-RESTRICT-MODES — Investigation

## Fallback Entrypoints

### 1. `bootstrap_registries()` in `src/runtime/bootstrap.py` (line 71)
Already has mode guard: raises `HardcodedFallbackError` for CATALOG_STRICT and CATALOG_WITH_COMPATIBILITY when `catalog_repo is None` (lines 89-96). All acceptance criteria 1-4 are already met here.

### 2. `seed_phase1_content()` in `src/core/registries.py` (line 562)
Has a catalog detection block (lines 571-582). When catalog_repo resolves to None (data/content missing), falls through to the `else` branch at line 637 which silently logs a warning and seeds hardcoded content. NO mode guard exists here. This is the silent fallback gap.

### 3. Module-level auto-seed (line 729)
```python
seed_phase1_content(mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
```
Runs on every import of `registries.py`. In production/tests, `data/content` exists so catalog is always used — no fallback triggered. But in a broken environment, would silently fall back. After adding the guard, this call would raise for COMPAT mode if data/content is missing. Must change to LEGACY_FALLBACK.

## Circular Import Analysis
- `bootstrap.py` imports from `registries.py` (EnemyRegistry, ItemRegistry, etc.)
- `registries.py` imports from `modes.py` (RuntimeContentMode, AdapterHeuristicUsage)
- `modes.py` has no imports from registries or bootstrap → SAFE to add error class here

## Existing Tests Coverage
All 7 existing tests in `test_registry_bootstrap_modes.py` test `bootstrap_registries`, not `seed_phase1_content` directly. The acceptance criteria are met for `bootstrap_registries` but NOT for `seed_phase1_content` called directly.

## Error Message Gap
Current: `"[mode={mode.value}] Hardcoded fallback is not permitted. Catalog not found; hardcoded fallback is not permitted in this mode."`
Missing: suggestion of catalog replacement path.
