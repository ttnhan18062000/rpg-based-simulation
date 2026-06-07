# TCK-20260607-RESOLVER-BOUNDARY

## Title
Narrow resolve_module_contribution to NormalizedWorldModule only and add snapshot test

## Status
OPEN

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
Investigation phase must grep `resolve_module_contribution(` in all .py files to identify call sites before changing the signature.

## Test Summary
```
pytest tests/unit/worldassembly/ -q
```

## Files Changed
- `src/worldassembly/resolver.py`
- `tests/unit/worldassembly/test_resolver.py`

## Completion Summary
(to be filled)
