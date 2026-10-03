---
ticket_id: TCK-20260619-P0-DETERMINISM
phase: investigation
---

# Investigation — TCK-20260619-P0-DETERMINISM

## Finding

Four files in `src/` contained bare `import random` / `random.` calls, violating the P0 engine contract that `DeterministicRNG` (at `src/platform/rng.py`) is the only allowed RNG source. The violation caused replay divergence: two runs with the same seed produced different outcomes because stdlib `random` holds global state that is not seeded per-run.

## Violation Inventory (pre-fix)

| File | Usage | Nature |
|---|---|---|
| `src/engine/kernel.py:L117-118` | `import random; random.randint(1000, 9999)` | Run-ID suffix generation |
| `src/worldbuilding/compiler.py` | `import random; rng = random.Random(seed); rng.randint(...)` | Resource/building/entity x,y placement |
| `src/worldbuilding/recipe.py:L118` | `import random; rng = random.Random(seed)` | Template expansion (rng created but unused after fix) |
| `src/worldgeneration/generator.py` | `import random; rng = random.Random(intent.seed); param_rng = random.Random(intent.seed)` | World generation + param sampling |

## Existing Infrastructure

- `src/platform/rng.py` — `DeterministicRNG` class, seeded per-run, exposes `get_int`, `get_float`, `choice` with domain/tick/entity sub-seeding to prevent cross-domain correlation.
- `src/core/enums.py` — `Domain` enum consumed by DeterministicRNG calls.
- `tests/integration/kernel/test_phase2_determinism.py` — had `_scan_for_bare_random()` helper; extended to assert zero results.
- Kernel already holds `self._rng: DeterministicRNG` — kernel fix used that instance.

## Parity Ledger State (pre-fix)

- SUBSTRATE-NEW-002 and SUBSTRATE-NEW-011 described the generator using `random.Random(seed)` — both marked `status: verified` based on the old behavior. Both updated.
- No entry existed for the bare-random lint gate — added as SUBSTRATE-NEW-012.
