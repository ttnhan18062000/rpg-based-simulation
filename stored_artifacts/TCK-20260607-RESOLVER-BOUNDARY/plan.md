# TCK-20260607-RESOLVER-BOUNDARY — Implementation Plan

## Summary

Narrow `WorldAssemblyResolver.resolve_module_contribution()` from accepting
`WorldModuleSpec | NormalizedWorldModule` to accepting only `NormalizedWorldModule`,
add a runtime isinstance guard, and add two tests (snapshot + guard).

## Files Changed

1. `src/worldassembly/resolver.py`
2. `tests/unit/worldassembly/test_resolver.py`

## Steps

### Step 1 — Update signature and add runtime guard in resolver.py

**Location:** `resolve_module_contribution()` definition, lines 652–657.

Change:
```python
def resolve_module_contribution(
    self,
    module: WorldModuleSpec | NormalizedWorldModule,
    prefix: str = "",
    param_vals: Dict[str, Any] = None
) -> ResolvedModuleContribution:
```

To:
```python
def resolve_module_contribution(
    self,
    normalized_module: NormalizedWorldModule,
    prefix: str = "",
    param_vals: Dict[str, Any] = None
) -> ResolvedModuleContribution:
```

Add at the top of the function body (after `if param_vals is None`):
```python
if not isinstance(normalized_module, NormalizedWorldModule):
    raise TypeError(
        f"resolve_module_contribution requires NormalizedWorldModule, got "
        f"{type(normalized_module).__name__}. "
        "Call WorldModuleAuthoringNormalizer.normalize() before resolving."
    )
```

Rename all uses of `module` → `normalized_module` within the function body.

Remove the now-unused `WorldModuleSpec` from the function's local type annotation.
`WorldModuleSpec` import can be removed from the type annotation of this function
(it may still be used elsewhere in the file — check before removing the import line).

**Scope guard:** Do NOT rename the `spec` local variable in `assemble()` (line 271).
It is already a `NormalizedWorldModule` at that point — only the call
`self.resolve_module_contribution(spec, ...)` at line 286 needs verification (it is correct).

### Step 2 — Verify WorldModuleSpec import is still needed

`WorldModuleSpec` is NOT imported at the top of `resolver.py` (the import block at lines 1–41
does not include `WorldModuleSpec` from `src.worldmodules.schema`). The union type in the
signature was the only use of the name `WorldModuleSpec` in that file's type hints.
Therefore no import changes are required.

### Step 3 — Add tests to test_resolver.py

Add two new test functions after the existing `test_v2_service_refs_assembly_is_documented_gap`:

**test_contribution_snapshot_after_normalization** — snapshot test for contribution field structure.

**test_resolve_module_contribution_rejects_raw_spec** — TypeError guard test.

Both tests reuse the existing `base_repo` fixture. They require:
- `from src.worldmodules.schema import WorldModuleSpec`
- `from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer, NormalizedWorldModule`
- `from src.worldmodules.repository import WorldModuleRepository`
- `from src.worldassembly.resolver import WorldAssemblyResolver`

## Scope Guards

- Do NOT change `assemble()` internals — it already normalizes correctly.
- Do NOT change `NormalizedWorldModule` field types — companion ticket TCK-20260607-NORMALIZEDMODULE-TYPING (DONE).
- Do NOT add overloads.
- Do NOT change `ResolvedModuleContribution` schema.
- Do NOT change the return type of `assemble()`.

## Unresolved Questions

None.
