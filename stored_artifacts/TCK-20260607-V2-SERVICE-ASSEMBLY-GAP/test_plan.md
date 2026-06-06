# Test Plan — TCK-20260607-V2-SERVICE-ASSEMBLY-GAP

## Tests added

- `test_v2_service_refs_assembly_is_documented_gap` — guard test that:
  1. Verifies `ResolvedModuleContribution.service_refs` is `Dict[str, int]` (contribution schema intact).
  2. Asserts `WorldSpec` has no `services` field — fails with a clear message if the field is added
     without the assembly loop, prompting the implementer to complete the wiring.

## No new behavior tests

Since all current modules are v1 and `service_refs` is always empty at runtime, there is no
observable behavior to test. The guard test documents intent and prevents silent regression.

## Run

```
pytest tests/unit/worldassembly/test_resolver.py -q
```
