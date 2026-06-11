---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-RESOLVER-BOUNDARY
phase: done
date: 2026-06-07
tags: [resolver, boundary]
---

# TCK-20260607-RESOLVER-BOUNDARY

## Title
Narrow resolve_module_contribution to NormalizedWorldModule only and add snapshot test

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`resolve_module_contribution()` in `src/worldassembly/resolver.py` accepts a
`WorldModuleSpec | NormalizedWorldModule` union type. The internal `assemble()` flow
always normalizes before calling it, so the union is safe internally. But the signature
is a public footgun — external callers can bypass normalization entirely, producing
un-normalized modules that pass type-checking but fail silently at runtime.

No test validates what the contribution record looks like after normalization, making
regression invisible.

## Scope

### Fix 1 — Narrow `resolve_module_contribution()` signature

Current:
```python
def resolve_module_contribution(
    spec: WorldModuleSpec | NormalizedWorldModule, ...
) -> ResolvedModuleContribution:
```

Target:
```python
def resolve_module_contribution(
    normalized_module: NormalizedWorldModule, ...
) -> ResolvedModuleContribution:
```

Add runtime guard at the top of the function:
```python
if not isinstance(normalized_module, NormalizedWorldModule):
    raise TypeError(
        f"resolve_module_contribution requires NormalizedWorldModule, got {type(normalized_module).__name__}. "
        "Call WorldModuleAuthoringNormalizer.normalize() before resolving."
    )
```

### Fix 2 — Snapshot test for contribution record

Add to `tests/unit/worldassembly/test_resolver.py`:
```python
def test_contribution_snapshot_after_normalization():
    """Contribution record fields must match the normalized module's structure."""
    spec = WorldModuleSpec(...)   # minimal known-good fixture
    normalized = WorldModuleAuthoringNormalizer().normalize(spec)
    contribution = resolve_module_contribution(normalized, ...)
    assert contribution.resource_refs == {}   # or whatever the fixture produces
    assert contribution.building_refs == {}
    assert contribution.service_refs == {}
    assert isinstance(contribution.resource_refs, dict)
    assert isinstance(contribution.building_refs, dict)
    assert isinstance(contribution.service_refs, dict)
```

The test doesn't need real data — a minimal empty-field module is sufficient.

### Fix 3 — Update internal call sites if any still pass `WorldModuleSpec`

Grep `resolve_module_contribution(` across `src/` and verify all call sites pass
`NormalizedWorldModule`. Update any that don't.

## Out of Scope
- Do not change `assemble()` internals (it already normalizes correctly)
- Do not change `NormalizedWorldModule` field types (separate ticket: TCK-20260607-NORMALIZEDMODULE-TYPING)
- Do not add overloads

## Acceptance Criteria
- [ ] `resolve_module_contribution()` parameter is `NormalizedWorldModule`, not a union
- [ ] Runtime `isinstance` guard raises `TypeError` if a raw `WorldModuleSpec` is passed
- [ ] Snapshot test exists and passes
- [ ] All existing `assemble()` call paths pass type-checking
- [ ] No external caller bypasses normalization

## Related Tickets
- TCK-20260607-NORMALIZEDMODULE-TYPING (companion — typed fields)

## Related Docs
- `world_phase_20_28_repair_remaining.md` R2.1, R2.2

## Related Code Areas
- `src/worldassembly/resolver.py:resolve_module_contribution`
- `tests/unit/worldassembly/test_resolver.py`

## Assumptions / Open Questions
- Are there external callers outside `assemble()` that currently pass `WorldModuleSpec`? — investigation step must grep for these.

## Implementation Notes
- Renamed `module` parameter to `normalized_module` in `resolve_module_contribution()` signature.
- Changed type annotation from `WorldModuleSpec | NormalizedWorldModule` to `NormalizedWorldModule` only.
- Added `isinstance` guard at top of function body raising `TypeError` with descriptive message.
- Renamed all internal `module.` references to `normalized_module.` within the function body (regions, factions, biomes, ecologies, relationships, services, populations, resources, buildings sections).
- `WorldModuleSpec` was never imported in `resolver.py` — no import changes required.
- All four existing call sites already passed `NormalizedWorldModule`; no callers broken.
- Added `test_contribution_snapshot_after_normalization` and `test_resolve_module_contribution_rejects_raw_spec` to `tests/unit/worldassembly/test_resolver.py`.

## Test Summary
```
pytest tests/unit/worldassembly/ tests/unit/worldmodules/ -q
```

## Files Changed
- `src/worldassembly/resolver.py` — signature narrowed, isinstance guard added, body refs renamed
- `tests/unit/worldassembly/test_resolver.py` — two new tests added

## Completion Summary
Narrowed resolve_module_contribution() signature to NormalizedWorldModule only (removed WorldModuleSpec union arm). Added isinstance guard raising TypeError. Renamed parameter from 'module' to 'normalized_module' throughout body. Added snapshot test (contribution structure) and TypeError guard test. All existing call sites already passed NormalizedWorldModule — zero callers broken.
