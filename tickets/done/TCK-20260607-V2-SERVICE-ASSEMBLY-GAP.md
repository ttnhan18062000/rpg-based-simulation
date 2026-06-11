---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-V2-SERVICE-ASSEMBLY-GAP
phase: done
date: 2026-06-07
tags: [v2, service, assembly, gap]
---

# TCK-20260607-V2-SERVICE-ASSEMBLY-GAP

## Title
Track and close v2 service_refs assembly gap in worldassembly/resolver.py

## Status
DONE

## Tier
standard

## Type
gap

## Priority
P3

## Request Summary
`src/worldassembly/resolver.py:assemble()` has a v2 resource merge loop (lines 456-481) and a v2 building merge loop (lines 507-533) that correctly consume `contribution.resource_refs` and `contribution.building_refs` into the assembled world state. However, there is NO v2 service merge loop — `contribution.service_refs` (a `Dict[str, int]`) is validated and populated during `resolve_module_contribution()` but is never consumed by `assemble()`. Since all current real world modules are `schema_version: "worldmodule.v1"`, this gap has no runtime impact today. It will silently drop service data if any module is migrated to v2.

## Scope

### Root Cause

`resolve_module_contribution()` builds:
```python
service_refs: Dict[str, int] = {}
for svc_id, count in module.service_refs.items():
    service_refs[svc_id] = service_refs.get(svc_id, 0) + count
contribution = ResolvedModuleContribution(
    ...,
    service_refs=service_refs,
    ...
)
```

`assemble()` iterates contributions and merges resource_refs and building_refs but has no corresponding block for service_refs. The dict is computed, stored in the contribution, and then abandoned.

### Fix Direction

Add a v2 service merge loop in `assemble()` parallel to the existing resource and building loops:

```python
# v2 service assembly
for contribution in contributions:
    for svc_id, count in contribution.service_refs.items():
        assembled_services[svc_id] = assembled_services.get(svc_id, 0) + count
```

The `assembled_services` dict should then be passed into the world state / registry the same way `assembled_resources` and `assembled_buildings` are.

### Prerequisite investigation needed

Before implementing: verify where `assembled_resources` and `assembled_buildings` are stored in the assembled world state, and confirm there is a corresponding service registry or slot in the world state dataclass. If no service registry exists yet, this ticket should be scoped to **only documenting the gap and adding a test that asserts it is not silently dropped** — not yet wiring the output, since there is nowhere to put it.

### Required artifacts

1. Investigation: trace where `assembled_resources` and `assembled_buildings` end up after `assemble()`.
2. Plan: decide whether to add the service merge loop with a target registry (if one exists) or add a test guard (if no registry exists yet).
3. Implementation: add loop + target, OR add assertion test that service_refs is not silently dropped.

## Out of Scope
- Do not add a service registry to the world state if one does not exist.
- Do not migrate any v1 modules to v2.
- Do not change `ResolvedModuleContribution.service_refs` type.

## Acceptance Criteria
- [ ] `contribution.service_refs` is consumed by `assemble()` — either written to a registry or explicitly documented as "deliberately deferred" with a test guard
- [ ] If deferred: a test asserts that `service_refs` is NOT silently ignored (e.g., via a stub v2 module with service_refs, verifying the dict is non-empty after contribution)
- [ ] All existing tests still pass
- [ ] Parity ledger entry in `substrate.yaml` or `town_resource.yaml` reflects the status of service assembly

## Related Tickets
- TCK-20260607-STRICT-MODE-PRODUCTION (same audit)

## Related Docs
- world_phase_20_28_repair.md Phase 22.3 (count-map normalization)
- `docs/engine/authoritative_pipeline.md` — service resolution phase

## Related Stored Artifacts
stored_artifacts/TCK-20260607-V2-SERVICE-ASSEMBLY-GAP/

## Related Code Areas
- `src/worldassembly/resolver.py:assemble()` — resource loop ~456-481, building loop ~507-533
- `src/worldassembly/schema.py` — `ResolvedModuleContribution.service_refs`
- `src/worldmodules/normalizer.py` — `NormalizedWorldModule.service_refs`
- `docs/parity_ledger/substrate.yaml` or `town_resource.yaml`

## Assumptions / Open Questions
- Does the assembled world state have a service registry slot? This must be confirmed during investigation before any code is written.
- Is service assembly intentionally deferred to a later milestone? If yes, record in `docs/guidelines/v2_intentional_divergences.md`.

## Implementation Notes
This is a P3 (future-proofing) ticket. The immediate risk is zero since all modules are v1. The gap should still be closed before any v2 module is authored to avoid a silent data loss regression.

## Test Summary
Run `pytest tests/unit/worldassembly/ tests/integration/ -q` after fix.

## Files Changed
- `src/worldassembly/resolver.py` (add service merge loop or explicit no-op with comment)
- `tests/unit/worldassembly/test_resolver.py` (add service_refs guard test)
- `docs/parity_ledger/substrate.yaml` or `town_resource.yaml` (add/update entry)
- Optionally: `docs/guidelines/v2_intentional_divergences.md` if deferred intentionally

## Completion Summary
Done. 169 tests pass.
