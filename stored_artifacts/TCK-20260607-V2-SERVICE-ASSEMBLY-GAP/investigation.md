# Investigation — TCK-20260607-V2-SERVICE-ASSEMBLY-GAP

## Finding

`WorldModuleAssemblyResolver.resolve_module_contribution()` resolves and validates
`service_refs: Dict[str, int]` at step 6 (lines ~703-709). But `assemble()` has:
- v2 resource merge loop (lines ~456-481) ✅
- v2 building merge loop (lines ~507-533) ✅
- NO v2 service merge loop ❌

`contribution.service_refs` is computed but never consumed. `WorldSpec` has no `services`
field — there is nowhere to write the service data to.

## Root Cause

`WorldSpec` (lines ~562-574) outputs `regions`, `factions`, `entities`, `resources`,
`buildings`. No `services` slot exists. The service merge loop cannot be added until
`ServiceNodeSpec` and `WorldSpec.services: List[ServiceNodeSpec]` are defined.

## Decision

**Scope to documentation + guard test only.** Do not add a half-wired loop with no output.
- Add explanatory comment in `assemble()` at the service gap site.
- Add `test_v2_service_refs_assembly_is_documented_gap` — a guard that fails the moment
  `WorldSpec` gains a `services` field, reminding the implementer to add the merge loop.
- Record in parity ledger (`SUB-367`) and `v2_intentional_divergences.md` (entry 2.19).

## Current runtime impact

Zero. All 7 real world modules are `schema_version: "worldmodule.v1"`. The v2 service
resolution code path is never exercised by real data.
