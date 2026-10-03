---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-FALLBACK-RESTRICT-MODES
artifact_type: plan
tags: [fallback, restrict, modes]
---

# TCK-20260610-FALLBACK-RESTRICT-MODES — Plan

## Changes

### 1. `src/core/modes.py`
Add `FallbackRestrictedError(RuntimeError)` with `mode` attribute and catalog suggestion in message.

### 2. `src/runtime/bootstrap.py`
- Import `FallbackRestrictedError` from `src.core.modes`
- Change `HardcodedFallbackError` to a subclass of `FallbackRestrictedError` (backward compat: existing `isinstance(e, HardcodedFallbackError)` and `isinstance(e, FallbackRestrictedError)` both work)
- Improve error message to suggest catalog path
- Re-export `FallbackRestrictedError` so tests can import it from bootstrap

### 3. `src/core/registries.py`
- Add `from src.core.modes import FallbackRestrictedError` in the else branch (local import to avoid circular import at module level)
- In else branch: raise if mode not in (LEGACY_FALLBACK, TEST_MANUAL)
- Change line 729 auto-seed to use `LEGACY_FALLBACK` mode

### 4. Tests
New file `tests/unit/runtime/test_fallback_restrict_modes.py`:
- seed_phase1_content with CATALOG_STRICT and no catalog raises FallbackRestrictedError
- seed_phase1_content with CATALOG_WITH_COMPATIBILITY and no catalog raises FallbackRestrictedError
- seed_phase1_content with LEGACY_FALLBACK and no catalog succeeds
- seed_phase1_content with TEST_MANUAL and no catalog succeeds (or doesn't fall back)
- Error message names mode and contains catalog path suggestion
- FallbackRestrictedError is importable from bootstrap
- HardcodedFallbackError is still importable from bootstrap (backward compat)
- FallbackRestrictedError is a supertype of HardcodedFallbackError

## Non-Breaking Guarantees
- All existing tests in test_registry_bootstrap_modes.py still pass unchanged
- Module-level auto-seed uses LEGACY_FALLBACK → allowed to fall back on import if needed
