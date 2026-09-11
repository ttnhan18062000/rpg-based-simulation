---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260628-E21C-COMPILER-REGEN
phase: done
date: 2026-06-28
tags: [resource, ecology, regen, compiler, economy, p3]
---

# TCK-20260628-E21C-COMPILER-REGEN

## Title
Fix: Compiler-seeded resource nodes never regenerate (regen_rate_per_tick=0 default)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
All resource nodes created by `WorldCompiler.compile()` have `regen_rate_per_tick=0`
(the `ResourceNodeState` default). Ecology only regenerates nodes where
`regen_rate_per_tick > 0`. Result: every compiler-seeded node permanently depletes
with no recovery — no depletion/recovery cycles, no boom/bust ecology.

This is the single highest-impact fix for the Resource Ecology epic.

## Scope
1. Add `regen_rate: int = Field(1, ...)` to `ResourceNodeSpec` in `src/worldbuilding/schema.py`
   (default=1 means all existing world YAML specs automatically get regen).
2. Pass `regen_rate_per_tick=res_spec.regen_rate` in the `ResourceNodeState(...)` constructor
   call in `src/worldbuilding/compiler.py` (line ~208).
3. Update `docs/world/ecology_and_calamity_contract.md` to remove the
   "compiler-seeded nodes retain regen_rate_per_tick=0" note.
4. Update parity ledger `docs/parity_ledger/town_resource.yaml` if an entry covers this.

## Out of Scope
- Density-dependent regen (E21D).
- Cross-region propagation (E21E).
- Changing `max_charges` or ecology cadence.

## Acceptance Criteria
- [ ] `ResourceNodeSpec` has `regen_rate: int = Field(1, ...)`.
- [ ] Compiler passes `regen_rate_per_tick=res_spec.regen_rate` to `ResourceNodeState`.
- [ ] A world compiled with default spec has all nodes with `regen_rate_per_tick=1`.
- [ ] Existing ecology tests pass.
- [ ] Parity ledger updated.

## Related Tickets
- Parent: TCK-20260628-E-RESOURCE-ECOLOGY
- Ecology service: TCK-20260619-E21B-REGEN-SERVICE (DONE — service already handles regen)

## Related Docs
- `docs/world/ecology_and_calamity_contract.md` — must update
- `docs/mechanics/03_economic_laws.md` — resource harvesting laws
- `docs/parity_ledger/town_resource.yaml`

## Related Code Areas
- `src/worldbuilding/schema.py` — ResourceNodeSpec
- `src/worldbuilding/compiler.py` — ResourceNodeState constructor call (~line 208)
- `src/world/ecology.py` — regen logic (read-only reference)

## Assumptions / Open Questions
- Default `regen_rate=1` is appropriate for all existing worlds. World authors can
  override to 0 for permanently static nodes if needed.

## Implementation Notes
- Added `regen_rate: int = Field(1, ge=0, ...)` to `ResourceNodeSpec` in schema.py.
- Passed `regen_rate_per_tick=res_spec.regen_rate` to `ResourceNodeState(...)` in compiler.py.
- Updated `docs/world/ecology_and_calamity_contract.md` to reflect new default.
- Added parity entry TOWN-186 to `docs/parity_ledger/town_resource.yaml`.
- Existing world specs unchanged — default=1 applies automatically.

## Test Summary
- 112 existing tests pass (worldbuilding + ecology suite).
- Added: `test_compiler_resource_node_regen_rate` — default=1 verified.
- Added: `test_compiler_resource_node_explicit_zero_regen` — regen_rate:0 override works.

## Files Changed
- `src/worldbuilding/schema.py` (+1 field: ResourceNodeSpec.regen_rate)
- `src/worldbuilding/compiler.py` (+1 kwarg: regen_rate_per_tick=res_spec.regen_rate)
- `docs/world/ecology_and_calamity_contract.md` (updated node seeding description)
- `docs/parity_ledger/town_resource.yaml` (+TOWN-186)
- `tests/unit/worldbuilding/test_world_compiler.py` (+2 tests)

## Completion Summary
Two-line fix: added `regen_rate: int = Field(1, ...)` to ResourceNodeSpec and wired it
into the compiler's ResourceNodeState constructor. All compiler-seeded nodes now default
to regen_rate_per_tick=1, enabling ecology-cycle charge recovery (~1000 ticks per full
depletion cycle). World authors may set `regen_rate: 0` for intentionally static nodes.
