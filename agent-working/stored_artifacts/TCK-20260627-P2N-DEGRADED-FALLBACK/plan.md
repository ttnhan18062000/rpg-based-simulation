PHASE_TS: 2026-06-27T13:42:02Z

# Plan — TCK-20260627-P2N-DEGRADED-FALLBACK

## Summary

Three-file change. Fix the module-level default in registries.py, add a catalog accessor
in CatalogRepository, and add degraded-mode content resolution to GracefulDegradationManager.
Add one new test file. Update parity ledger and D02 audit doc.

## Ordered Steps

### Step 1 — Fix module-level default in `src/core/registries.py`

**File:** `src/core/registries.py:541`

Change:
```python
runtime_content_source: str = "legacy_hardcoded"
```
To:
```python
runtime_content_source: Optional[str] = None
```

The `Optional` import is already present (from `typing import Optional` at the top of the file —
verify and add if absent). The LEGACY_FALLBACK path at line 732 still sets the value to
`"legacy_hardcoded"` at runtime; only the declared default changes.

**Acceptance criterion addressed:** AC1 — default is no longer `"legacy_hardcoded"`.

**Dependency:** None.

---

### Step 2 — Add `get_lowest_cost_for_type()` to `CatalogRepository` in `src/content/repository.py`

Add a new method after `load_all()` (roughly after line 350):

```python
def get_lowest_cost_for_type(self, content_type: str) -> dict:
    """Return loaded catalog entries for content_type, cheapest-first.

    Used by GracefulDegradationManager in degraded mode to prefer catalog
    entries over static hardcoded defaults. Returns a plain dict (record_id →
    CatalogBaseDefinition subtype). Returns an empty dict for unknown types.

    Supported content_type values:
      'items'     — sorted ascending by ItemDefinition.base_value
      'resources' — sorted: no required_tool first, then alphabetically by id
    """
    if content_type == "items":
        return dict(
            sorted(self.items.items(), key=lambda kv: kv[1].base_value)
        )
    if content_type == "resources":
        return dict(
            sorted(
                self.resources.items(),
                key=lambda kv: (kv[1].required_tool is not None, kv[0]),
            )
        )
    return {}
```

**Acceptance criterion addressed:** enables AC2 (catalog-driven degraded selection).

**Dependency:** Step 1 is independent; this step is independent.

---

### Step 3 — Add `CatalogMissError` and `resolve_content_source()` to `GracefulDegradationManager` in `src/domains/optimization/degradation.py`

Add before the class definition:
```python
class CatalogMissError(RuntimeError):
    """Raised by GracefulDegradationManager when catalog is absent in strict mode."""
```

Add inside `GracefulDegradationManager`:
```python
def resolve_content_source(
    self,
    catalog_repo: "Optional[Any]",
    content_type: str,
    strict: bool = False,
) -> dict:
    """Return catalog entries for content_type, honoring the degradation level.

    In degraded or critical mode, catalog-driven entries are always preferred
    over hardcoded static paths.

    Args:
        catalog_repo: A loaded CatalogRepository, or None if unavailable.
        content_type: Content family to resolve ('items', 'resources', ...).
        strict: If True and catalog_repo is None, raise CatalogMissError.

    Returns:
        Dict of catalog entries (record_id → definition), cheapest-first.

    Raises:
        CatalogMissError: If strict=True and catalog_repo is None.
    """
    if catalog_repo is None:
        if strict:
            raise CatalogMissError(
                f"Catalog unavailable for content type '{content_type}' in strict mode."
            )
        return {}
    return catalog_repo.get_lowest_cost_for_type(content_type)
```

Update file imports — `Any` and `Optional` from typing:
```python
from typing import Dict, Any, Optional
```
(Currently `from typing import Dict, Any` — add `Optional`.)

Use a forward-reference string annotation `"Optional[Any]"` for `catalog_repo` to avoid
importing `CatalogRepository` at module level (prevents any circular import risk).

Update the class docstring to mention content-source resolution.

**Acceptance criterion addressed:** AC2 (degraded selects from catalog) + AC3 (strict raises).

**Dependency:** Step 2 must be done before testing Step 3, but the code is independent.

---

### Step 4 — Add new test file `tests/unit/core/test_degraded_fallback.py`

Five tests as specified in test_plan.md:
1. Module default is not `"legacy_hardcoded"` (checks source annotation)
2. `resolve_content_source` in degraded mode calls catalog
3. `resolve_content_source` strict+no catalog → `CatalogMissError`
4. `resolve_content_source` non-strict+no catalog → `{}`
5. `CatalogRepository.get_lowest_cost_for_type("items")` returns cheapest-first

**Dependency:** Steps 2 and 3.

---

### Step 5 — Update D02 audit document (`docs/audits/D02_foundation_features.md`)

In section 6.6, add a resolution note below the existing finding text:

```
**Status (updated 2026-06-27):** Resolved by TCK-20260627-P2N-DEGRADED-FALLBACK.
Module-level default changed to `None`; `GracefulDegradationManager.resolve_content_source()`
now selects from catalog in degraded mode and raises `CatalogMissError` in strict mode.
```

---

### Step 6 — Add parity ledger entry to `docs/parity_ledger/infrastructure.yaml`

Add a new entry (next available ID after INFRA-027):

```yaml
- id: INFRA-028
  text: "GracefulDegradationManager.resolve_content_source selects catalog entries in
    degraded mode; raises CatalogMissError in strict mode when catalog is absent."
  status: verified
  priority: P1
  v2_evidence: src/domains/optimization/degradation.py::GracefulDegradationManager.resolve_content_source
  test_path: tests/unit/core/test_degraded_fallback.py::test_resolve_content_source_degraded_uses_catalog
  divergence_note: null
```

## Scope Guards (what NOT to touch)

- Do NOT change the `"legacy_hardcoded"` string value at line 732 of registries.py (only the
  module-level DEFAULT at line 541 changes).
- Do NOT remove the hardcoded fallback maps in `seed_phase1_content` (retirement out of scope).
- Do NOT modify `should_skip_phase`, `update_pressure`, `get_provider_cap`, or `generate_report`
  in `GracefulDegradationManager`.
- Do NOT modify any adapter classes (`CatalogToItemRegistryAdapter`, etc.).
- Do NOT call `load_all()` or any I/O in `get_lowest_cost_for_type()` — it reads already-loaded
  in-memory dicts only.
- Do NOT touch `src/runtime/bootstrap.py`.

## Dependency Map

```
Step 1 (registries default)    — independent
Step 2 (get_lowest_cost)       — independent
Step 3 (resolve_content_source) — depends on Step 2 for full integration
Step 4 (tests)                 — depends on Steps 2 and 3
Step 5 (D02 audit update)      — depends on Steps 1–4 passing
Step 6 (parity ledger)         — depends on Step 4 passing
```

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| `runtime_content_source = "legacy_hardcoded"` no longer the default | Step 1 |
| Degraded mode selects from catalog (lowest-cost) | Steps 2 + 3 |
| Strict mode raises on catalog miss | Step 3 |
| Existing degradation tests pass | Steps 1–3 (no behavior removed) |
| Retirement criteria documented as still-gating | Step 5 (note added) |

## Deviations

None yet. Update this section if implementation differs from plan.
