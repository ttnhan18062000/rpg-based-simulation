---
status: open
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260623-FIX-KERNEL-PHASES
phase: open
date: 2026-06-23
tags: [test-repair, kernel, pipeline, ItemStack, determinism, P0]
---

# TCK-20260623-FIX-KERNEL-PHASES

## Title
Fix kernel phase contract + ItemStack.position (~35 failures)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Two root causes block kernel and pipeline integration tests.

**Root Cause 1 — _phase_init missing from Kernel.tick_once (D10 F5):**
`test_final_kernel_law_compliance` fails: `Kernel.tick_once` does not contain `_phase_init`. Per `docs/engine/kernel.md`, the 6-phase deterministic loop is: Init → Governance → Scheduling → Packetization → Resolution → Persistence. The `_phase_init` call was removed or renamed without updating the kernel contract. This also causes Milestone B/C/D closure test failures.

**Root Cause 2 — ItemStack.position AttributeError (D10 F2):**
`src/engine/world_index.py:151` calls `.position` on an `ItemStack` object. `ItemStack` does not have a `position` attribute — it was removed/renamed when the ItemStack model changed. This breaks spatial indexing and cascades into race condition tests, authoritative outcome truth, event replay, and movement pipeline tests.

Source: D10 audit F2, F5. Errors confirmed by direct test sampling 2026-06-23.

## Scope
- Restore or rename `_phase_init` in `Kernel.tick_once` to match what `docs/engine/kernel.md` mandates, OR update the kernel contract doc + test if the phase was intentionally restructured
- Fix `world_index.py:151` to use the correct attribute/method for getting item position (inspect `ItemStack` model to find current position accessor)
- Do NOT change kernel semantics — this is a naming/wiring alignment fix

## Out of Scope
- Kernel phase logic changes
- ItemStack model restructuring
- Performance optimization

## Acceptance Criteria
- `tests/integration/kernel/test_milestone_a_closure.py::test_final_kernel_law_compliance` passes
- `tests/integration/kernel/test_milestone_b_closure.py::test_milestone_b_operational_gate` passes
- `tests/integration/kernel/test_milestone_c_desimulation.py` — both tests pass
- `tests/integration/kernel/test_milestone_d_closure.py` passes
- `tests/integration/kernel/test_race_conditions_v2.py` — all 4 tests pass
- `tests/integration/kernel/test_event_replay.py` passes
- `tests/integration/kernel/test_authoritative_outcome_truth.py` passes
- `tests/integration/pipeline/test_mutation_boundary.py` — all 7 tests pass
- `tests/integration/pipeline/test_movement_micro_arena_position_swap.py` — all 4 tests pass
- `tests/unit/movement/test_position_swap.py` — all 3 tests pass
- `tests/unit/movement/test_tactical_movement.py` — 3 tests pass

## Related Tickets
- D10 audit F2 (ItemStack.position), F5 (kernel phase contract)

## Related Docs
- `docs/engine/kernel.md` (6-phase loop contract)
- `docs/engine/authoritative_pipeline.md`
- `docs/parity_ledger/infrastructure.yaml` (kernel phase parity entries)
- `docs/parity_ledger/combat_movement.yaml` (movement parity entries)

## Related Code Areas
- `src/engine/kernel.py` (`tick_once`, `_phase_init`)
- `src/engine/world_index.py:151` (ItemStack position access)
- `src/domains/movement/` (position swap)
- `tests/integration/kernel/`
- `tests/integration/pipeline/`

## Assumptions / Open Questions
- Was `_phase_init` renamed to something else in the kernel, or removed entirely? If renamed, the test assertion string needs updating and the doc needs updating.
- What is the current attribute/method on `ItemStack` that provides position?

## Implementation Notes
Investigation order:
1. `graphify query "Kernel tick_once _phase_init"` to find current kernel structure
2. Read `src/engine/kernel.py` tick_once method
3. Read `src/engine/world_index.py:145-160` for ItemStack access pattern
4. Read `ItemStack` model to find current position field name

Parity ledger entries to update: any kernel phase entries in `docs/parity_ledger/infrastructure.yaml` or `combat_movement.yaml` that reference `_phase_init`.

## Test Summary
Run: `pytest tests/integration/kernel/ tests/integration/pipeline/test_mutation_boundary.py tests/integration/pipeline/test_movement_micro_arena_position_swap.py tests/unit/movement/ -m "not slow"`

## Files Changed
_To be filled during implementation._

## Completion Summary
_To be filled on completion._
