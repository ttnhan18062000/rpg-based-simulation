---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260607-RUNTIME-CONTENT-MODE
artifact_type: plan
tags: [runtime, content, mode]
---

# Implementation Plan — TCK-20260607-RUNTIME-CONTENT-MODE

## Ticket Correction (Critical)

The ticket says the function is at `src/worldassembly/resolver.py:642`. This is **wrong**.
`seed_phase1_content()` is at `src/core/registries.py:495` and the self-call is at
`src/core/registries.py:642`. `src/worldassembly/resolver.py` is the world module assembly
resolver (already modified by TCK-20260607-RESOLVER-BOUNDARY).

All file changes below use the correct paths.

## Decision: Where RuntimeContentMode Lives

**Decision: `src/core/modes.py` (new file)**

Rationale:
- `seed_phase1_content()` and all adapter classes consuming the enum are in `src/core/registries.py`.
- Placing the enum in `src/worldassembly/modes.py` (ticket's suggestion) would require
  `src/core/` to import from `src/worldassembly/`, inverting the dependency direction
  (worldassembly is higher-level than core).
- `src/core/modes.py` is the architecturally correct location: same package, no circular deps.

## Decision: Enum Values

```python
class RuntimeContentMode(Enum):
    MIGRATION = "migration"   # adapter heuristics active; legacy projection allowed
    V2 = "v2"                 # strict; raises AdapterError on any missing field
```

Exactly as specified in the ticket.

## Decision: AdapterProjectionResult

```python
@dataclass(frozen=True)
class AdapterProjectionResult:
    total_entities: int
    native_resolved: int
    legacy_projected: int
    unresolved: int
    heuristic_details: Dict[str, str]  # entity_id → projection reason
```

Lives in `src/core/registries.py` alongside `seed_phase1_content()`.
Returned only when the catalog path executes (`catalog_repo is not None`).
Legacy hardcoded fallback path returns `None` (no catalog entities to project).
Return type annotation: `Optional[AdapterProjectionResult]`.

For the catalog path, the result is computed post-adapt from dict sizes:
- `total_entities` = sum of all bootstrapped entity counts (items + resources + enemies + recipes + services + regions)
- `native_resolved` = entities that had all required fields (i.e., no heuristic fallback triggered)
- `legacy_projected` = entities that fell through to heuristic branches
- `unresolved` = 0 in MIGRATION mode (errors are raised, so any entity either resolved or raised)
- `heuristic_details` = `{}` for now (per-entity tracking is out of scope per ticket)

Since adapters currently do not expose per-entity projection counts, we instrument them to
return a count tuple `(total, legacy_projected)` from `.adapt()`. This is the minimal change
to the adapter interface — the return type changes from `Dict` to `Tuple[Dict, int]` where
the int is the count of entities that used heuristic fallback.

## Step-by-Step Changes

### Step 1 — Create `src/core/modes.py`

New file. Contents:
```python
from enum import Enum

class RuntimeContentMode(Enum):
    MIGRATION = "migration"
    V2 = "v2"
```

### Step 2 — Update adapter __init__ signatures in `src/core/registries.py`

For `CatalogToItemRegistryAdapter`, `CatalogToServiceRegistryAdapter`,
`CatalogToResourceRegistryAdapter`:

Replace parameter `migration_mode: bool = True` with `mode: RuntimeContentMode = RuntimeContentMode.MIGRATION`.

Replace all internal checks `if not self.migration_mode:` with `if self.mode == RuntimeContentMode.V2:`.

Add import at top: `from src.core.modes import RuntimeContentMode`.

Specific lines:
- `CatalogToItemRegistryAdapter.__init__`: line 205 — `migration_mode: bool = True` → `mode: RuntimeContentMode = RuntimeContentMode.MIGRATION`; store as `self.mode`
- Lines 215, 239: `if not self.migration_mode:` → `if self.mode == RuntimeContentMode.V2:`
- `CatalogToServiceRegistryAdapter.__init__`: line 304 — same change; line 307; line 323
- `CatalogToResourceRegistryAdapter.__init__`: line 368 — same change; line 370; lines 378, 396, 413, 421

### Step 3 — Update adapter `.adapt()` to track heuristic count

Minimal change: add a counter inside each adapter that increments when a heuristic branch
is taken. Return `(result_dict, heuristic_count)` from `.adapt()`. This is internal —
callers inside `seed_phase1_content()` unpack the tuple.

### Step 4 — Update `seed_phase1_content()` in `src/core/registries.py`

4a. Change signature:
```python
def seed_phase1_content(
    catalog_repo: Optional[Any] = _sentinel,
    required: bool = False,
    mode: RuntimeContentMode = RuntimeContentMode.MIGRATION,
) -> Optional[AdapterProjectionResult]:
```

4b. In the catalog path (lines 529–549), update adapter instantiation calls:
```python
items, items_heuristic = CatalogToItemRegistryAdapter(catalog_repo, mode=mode).adapt()
recipes = CatalogToRecipeRegistryAdapter(catalog_repo).adapt()
services, services_heuristic = CatalogToServiceRegistryAdapter(catalog_repo, catalog_mode=True, mode=mode).adapt()
regions = CatalogToRegionRegistryAdapter(catalog_repo).adapt()
resources, resources_heuristic = CatalogToResourceRegistryAdapter(catalog_repo, mode=mode).adapt()
enemies = ArchetypeToEnemyRegistryAdapter(catalog_repo, catalog_mode=True).adapt()
```

4c. Compute and return `AdapterProjectionResult`:
```python
total = len(items) + len(resources) + len(enemies) + len(recipes) + len(services) + len(regions)
legacy_projected = items_heuristic + services_heuristic + resources_heuristic
return AdapterProjectionResult(
    total_entities=total,
    native_resolved=total - legacy_projected,
    legacy_projected=legacy_projected,
    unresolved=0,
    heuristic_details={},
)
```

4d. Legacy hardcoded fallback path (line 551+): return `None` at end.

4e. Add `AdapterProjectionResult` dataclass definition above `seed_phase1_content()`.

### Step 5 — Update module-level self-call at line 642

```python
# Before:
seed_phase1_content()

# After:
seed_phase1_content(mode=RuntimeContentMode.MIGRATION)
```

### Step 6 — Update external callers that pass migration_mode

- `tests/integration/content/test_registry_projection_parity.py:19`:
  `seed_phase1_content(repo, migration_mode=True)` → `seed_phase1_content(repo, mode=RuntimeContentMode.MIGRATION)`
- `tests/unit/core/test_registry_adapters.py:227-264`:
  All `CatalogToItemRegistryAdapter(repo, migration_mode=False)` etc →
  `CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.V2)` etc.

### Step 7 — Add new tests

Add to `tests/unit/core/test_registry_bridge.py` (or new file):
- `test_runtime_content_mode_enum_has_migration_and_v2`
- `test_seed_with_migration_mode_returns_projection_result`
- `test_seed_with_v2_mode_raises_if_unresolved_entities_exist`
- `test_seed_legacy_fallback_returns_none`
- `test_adapter_projection_result_is_frozen_dataclass`

### Step 8 — Run tests

```
pytest tests/unit/core/ tests/integration/content/ -q
```

## Files Changed (corrected from ticket)

| File | Change |
|---|---|
| `src/core/modes.py` | NEW — RuntimeContentMode enum |
| `src/core/registries.py` | Adapter init signatures, adapt() return types, seed_phase1_content signature + return type, AdapterProjectionResult dataclass, line 642 self-call |
| `tests/unit/core/test_registry_bridge.py` | New tests |
| `tests/unit/core/test_registry_adapters.py` | Update migration_mode=False → mode=RuntimeContentMode.V2 |
| `tests/integration/content/test_registry_projection_parity.py` | Update migration_mode=True → mode=RuntimeContentMode.MIGRATION |

NOT changed (ticket's stated files that were wrong):
- `src/worldassembly/resolver.py` — not involved
- `src/worldassembly/modes.py` — not created (use `src/core/modes.py` instead)
- `tests/unit/worldassembly/test_resolver.py` — not involved

## Unresolved Questions

None. All open questions from the ticket have been resolved by investigation:
1. `seed_phase1_content()` currently returns `None` — confirmed.
2. There are 16+ call sites; only 1 (`test_registry_projection_parity.py`) explicitly passes `migration_mode`; 1 passes it directly to adapters (`test_registry_adapters.py`).
3. `RuntimeContentMode` should live in `src/core/modes.py`, not `src/worldassembly/modes.py`.
4. The "adapter heuristic report" = `AdapterProjectionResult` tracking per-adapter heuristic counts.
