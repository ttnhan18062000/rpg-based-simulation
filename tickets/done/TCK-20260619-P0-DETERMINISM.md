---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-DETERMINISM
phase: done
date: 2026-06-19
tags: [determinism, rng, bare-random, phase-0, p0-foundation, p0]
---

# TCK-20260619-P0-DETERMINISM

## Title
P0-2 · Determinism Enforcement — Replace bare random calls and add CI lint gate

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
Four files in `src/` contained bare `random.` calls that violated the P0 engine contract (`DeterministicRNG` is the only allowed RNG source). Replay diverged without error — two runs with the same seed produced different outcomes. A CI lint rule prevents recurrence.

Source: `docs/audits/D10_determinism.md` F3; confirmed via grep.

## Scope
- Replace all bare `random.` usage in:
  - `src/worldbuilding/recipe.py`
  - `src/worldbuilding/compiler.py`
  - `src/engine/kernel.py`
  - `src/worldgeneration/generator.py`
- Each replacement: derive a sub-seed from the calling context (entity_id, tick, operation name) via `DeterministicRNG` at `src/platform/rng.py:L10`
- Add a CI static analysis step (can be a `pytest` test or `make` target) that fails if `import random` or `random.` appears in `src/` outside `src/platform/rng.py`
- Update `tests/integration/kernel/test_phase2_determinism.py` (existing `_scan_for_bare_random()` test) to cover the new lint rule; remove the files once fixed

## Out of Scope
- Changing RNG seeding strategy beyond what's needed to replace bare calls
- Performance changes to RNG usage
- Audit of `tests/` directory for bare random (test files may use random freely)

## Acceptance Criteria
- `grep -r "import random\|random\." src/ --include="*.py"` returns zero results outside `src/platform/rng.py`
- Two 1000-tick runs with identical seeds produce identical event logs (verified by `tests/integration/kernel/test_phase2_determinism.py`)
- CI lint step fails the build if a new bare `random.` call is added to `src/`

## Related Tickets
- TCK-20260501-E4-PHASE-ONE (prior RNG hardening — partial, 4 files still outstanding)

## Related Docs
- `docs/engine/contracts/deterministic_execution.md`
- `docs/plans/long_term_development_roadmap.md` § P0-2
- `docs/parity_ledger/substrate.yaml` (SUBSTRATE-NEW-002, SUBSTRATE-NEW-011 updated; SUBSTRATE-NEW-012 added for lint gate)
- `docs/guidelines/design_patterns.md` (no bare `random.` calls in `src/` outside `src/platform/rng.py`)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-P0-DETERMINISM/`

## Related Code Areas
- `src/platform/rng.py:L10` (DeterministicRNG)
- `src/worldbuilding/recipe.py`
- `src/worldbuilding/compiler.py`
- `src/engine/kernel.py`
- `src/worldgeneration/generator.py`
- `tests/integration/kernel/test_phase2_determinism.py`

## Assumptions / Open Questions
_None outstanding._

## Implementation Notes
All four files replaced `random.`/`random.Random(seed)` with `DeterministicRNG` calls using the domain/tick/entity sub-seeding pattern consistent with existing codebase usage. `src/worldbuilding/recipe.py` had an unused `rng = random.Random(seed)` that was simply removed. `src/engine/kernel.py` used `self._rng` (already present on the kernel instance) for the run-ID suffix. Parity ledger entries SUBSTRATE-NEW-002 and SUBSTRATE-NEW-011 updated to reflect the new DeterministicRNG references; SUBSTRATE-NEW-012 added for the lint gate.

## Test Summary
- 27 determinism tests pass (`tests/integration/kernel/test_phase2_determinism.py` and related suite)
- Lint gate (`_scan_for_bare_random()` in test_phase2_determinism.py) asserts zero bare random calls in `src/`
- `test_replay_determinism.py::test_transaction_trace_determinism` — two identical-seed runs produce identical event logs

## Files Changed
- `src/engine/kernel.py` — replaced `random.randint` with `self._rng.get_int(Domain.INIT, ...)`; added `from src.core.enums import Domain`
- `src/worldbuilding/compiler.py` — replaced `import random` + `random.Random(seed)` with `DeterministicRNG`; all `rng.randint` calls → `rng.get_int(Domain.WORLD, ...)`
- `src/worldbuilding/recipe.py` — removed unused `import random` and `rng = random.Random(seed)`
- `src/worldgeneration/generator.py` — replaced `import random` + two `random.Random(intent.seed)` instances with `DeterministicRNG`; all rng/param_rng calls updated to domain-qualified API
- `tests/integration/kernel/test_phase2_determinism.py` — extended lint test to assert `_scan_for_bare_random()` returns empty for all of `src/`
- `docs/parity_ledger/substrate.yaml` — updated SUBSTRATE-NEW-002, SUBSTRATE-NEW-011; added SUBSTRATE-NEW-012

## Completion Summary
All bare `random.` calls in `src/` eliminated. DeterministicRNG is now the sole RNG source. A lint test enforces this at CI time. 27 determinism tests pass. Parity ledger updated with 3 entries revised/added.
