# Plan — TCK-20260607-V2-SERVICE-ASSEMBLY-GAP

## Changes

1. `src/worldassembly/resolver.py`
   - Add a comment block after the v2 building loop in `assemble()` explaining the deferral,
     referencing the divergences doc and parity ledger entry.

2. `tests/unit/worldassembly/test_resolver.py`
   - Add `test_v2_service_refs_assembly_is_documented_gap`:
     - Asserts `ResolvedModuleContribution.service_refs` field exists as `Dict[str, int]`.
     - Asserts `WorldSpec.model_fields` does NOT contain `"services"` — fails if the field
       is added without the corresponding assembly loop.

3. `docs/parity_ledger/substrate.yaml`
   - Add entry `SUB-367` with `status: divergent` documenting the gap.

4. `docs/guidelines/v2_intentional_divergences.md`
   - Add entry `2.19 v2 Service Assembly Gap` with rationale class `Stabilized` and unblock condition.
   - Add table row for `World Assembly | v2 Service Assembly`.

## No schema changes

`ResolvedModuleContribution`, `WorldSpec`, `NormalizedWorldModule` — all unchanged.
