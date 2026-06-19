---
ticket_id: TCK-20260619-P0-DETERMINISM
phase: plan
---

# Plan — TCK-20260619-P0-DETERMINISM

## Approach

Replace all bare `random.` calls in the four offending files with `DeterministicRNG` calls, following the sub-seeding pattern already used across the codebase (domain + tick + entity_id + sub_id). Extend the existing lint test to assert zero bare-random calls remain.

## Changes Per File

### src/engine/kernel.py
- Remove `import random` (was inlined at call site)
- Add `from src.core.enums import Domain`
- Replace `random.randint(1000, 9999)` with `self._rng.get_int(Domain.INIT, 0, 0, 1000, 9999)`
- Kernel already owns `self._rng` — no new field needed

### src/worldbuilding/compiler.py
- Remove `import random`
- Add `from src.platform.rng import DeterministicRNG; from src.core.enums import Domain`
- Replace `rng = random.Random(seed)` with `rng = DeterministicRNG(seed)`
- Replace `rng.randint(min_x, max_x)` → `rng.get_int(Domain.WORLD, 0, next_id, min_x, max_x, sub_id=0)` (and y → sub_id=1) for resource, building, entity placement loops

### src/worldbuilding/recipe.py
- Remove `import random` and the unused `rng = random.Random(seed)` initialization
- No other random usage existed in this file

### src/worldgeneration/generator.py
- Remove `import random`
- Add `from src.platform.rng import DeterministicRNG; from src.core.enums import Domain`
- Replace `rng = random.Random(intent.seed)` → `rng = DeterministicRNG(intent.seed)` (main pipeline)
- Replace `rng.choice(...)` and `rng.randint(...)` with `rng.choice(Domain.WORLD, ...)` / `rng.get_int(Domain.WORLD, ...)`
- Replace `param_rng = random.Random(intent.seed)` → `param_rng = DeterministicRNG(intent.seed)` (param sampling)
- Replace `param_rng.choice(...)` and `param_rng.get_int(...)` with domain-qualified calls

### tests/integration/kernel/test_phase2_determinism.py
- Extend `_scan_for_bare_random()` test to assert the result is empty for all of `src/` (allowlist: `src/platform/rng.py` excluded)

## Parity Ledger Updates

- SUBSTRATE-NEW-002: update description + v2_evidence to reference DeterministicRNG
- SUBSTRATE-NEW-011: same
- SUBSTRATE-NEW-012: new entry for bare-random lint gate (P0, verified)
