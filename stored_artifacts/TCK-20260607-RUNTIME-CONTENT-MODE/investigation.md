---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260607-RUNTIME-CONTENT-MODE
artifact_type: investigation
tags: [runtime, content, mode]
---

# Investigation — TCK-20260607-RUNTIME-CONTENT-MODE

## Key Finding

`seed_phase1_content()` lives in `src/core/registries.py` (NOT `src/worldassembly/resolver.py`).
The ticket's statement "line 642 in resolver.py" is inaccurate — the function is at line 495
of `src/core/registries.py`, and the bare module-level self-call is at line 642 of that same
file. The `src/worldassembly/resolver.py` is a different file (world module assembly, already
repaired by TCK-20260607-RESOLVER-BOUNDARY). This is the single most important finding for
the plan — all file paths in the ticket's "Files Changed" section are wrong.

## Actual File Locations

- Function definition: `src/core/registries.py:495`
- Bare self-call at import time: `src/core/registries.py:642`
- Adapter classes using migration_mode: `src/core/registries.py:204-447`
- Test file (existing): `tests/unit/core/test_registry_bridge.py`, `test_registry_adapters.py`, etc.
- New enum target: `src/worldassembly/modes.py` (as specified by ticket — acceptable even though
  the function is in `src/core/`, since modes.py is a shared location; OR better: `src/core/modes.py`)

## Q1: What does migration_mode=True vs False actually change?

Three adapter classes use `migration_mode`:

**CatalogToItemRegistryAdapter (lines 204–262):**
- `migration_mode=True` (MIGRATION): if `use_kind` is missing, infers it from categories
  via heuristics; if `class_fit` is missing, infers from hardcoded item_id maps.
- `migration_mode=False` (V2): raises `AdapterError` for any missing `use_kind` or `class_fit`.

**CatalogToServiceRegistryAdapter (lines 303–343):**
- `migration_mode=True`: if `affordances` is empty, infers from service id/name heuristics.
- `migration_mode=False`: raises `AdapterError` for empty affordances.

**CatalogToResourceRegistryAdapter (lines 367–447):**
- `migration_mode=True`: infers `legacy_id`, `source_region_tags`, `required_tool`,
  `base_difficulty` from hardcoded maps and resource_id patterns.
- `migration_mode=False`: raises `AdapterError` for missing `legacy_id` / source tags;
  `required_tool` defaults to None; `base_difficulty` defaults to 1.

**Summary:** MIGRATION = adapter heuristics active, legacy projection allowed.
V2 = strict mode, raises on any missing field, no heuristic fallback.

## Q2: How many callers of seed_phase1_content()? What do they pass?

Total call sites found: **16** (across src/ and tests/)

| File | Call | migration_mode passed? |
|---|---|---|
| `src/core/registries.py:642` | `seed_phase1_content()` | No — uses bool default True |
| `tests/unit/core/test_registry_bridge.py:25` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_registry_bridge.py:306` | `seed_phase1_content(mock_catalog_repo)` | No |
| `tests/unit/core/test_registry_bridge.py:419` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_registry_bridge.py:450` | `seed_phase1_content(mock_catalog_repo)` | No |
| `tests/unit/core/test_catalog_smoke_simulation.py:15` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_catalog_smoke_simulation.py:81` | `seed_phase1_content(repo)` | No |
| `tests/unit/core/test_hardcoded_regression_guard.py:48` | `seed_phase1_content(catalog_repo=None, required=False)` | No |
| `tests/unit/core/test_registry_parity.py:19` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_registry_parity.py:38` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_registry_parity.py:44` | `seed_phase1_content(repo)` | No |
| `tests/unit/core/test_registry_parity.py:262` | `seed_phase1_content(repo)` | No |
| `tests/unit/core/test_registry_cross_reference.py:10` | `seed_phase1_content(None)` | No |
| `tests/unit/core/test_registry_cross_reference.py:17` | `seed_phase1_content(repo)` | No |
| `tests/unit/core/test_catalog_fallback.py:15,20,30,60` | various | No |
| `tests/integration/content/test_registry_projection_parity.py:19` | `seed_phase1_content(repo, migration_mode=True)` | **YES** — explicit bool |
| `tests/unit/strategic/test_intents.py:8` | `seed_phase1_content()` | No |
| `tests/unit/cognition/test_phase2_knowledge_model_service.py:27` | `seed_phase1_content(None)` | No |
| `tests/unit/worldgeneration/test_generator.py:135,175` | `seed_phase1_content(cat, required=True)` etc | No |
| `tests/unit/core/test_registry_adapters.py:285` | `seed_phase1_content(catalog_repo=None)` | No |

Only **one** site passes `migration_mode` explicitly:
`tests/integration/content/test_registry_projection_parity.py:19` passes `migration_mode=True`.
All others rely on the default. This site must be updated to pass `mode=RuntimeContentMode.MIGRATION`.

Also: `tests/unit/core/test_registry_adapters.py:227-264` passes `migration_mode=False` directly
to adapter constructors (not to `seed_phase1_content`). Those adapter call sites also need updating.

## Q3: Where should RuntimeContentMode enum live?

The ticket specifies `src/worldassembly/modes.py`. However:
- `seed_phase1_content()` is in `src/core/registries.py`
- The adapters are also in `src/core/registries.py`
- `src/worldassembly/` is the world assembly layer; importing from it into `src/core/` would
  create an upward dependency (core → worldassembly), which violates layering.

**Correct location: `src/core/modes.py`** — keeps the enum in the same package as its consumers,
avoids any import circularity, and matches the architecture where `src/core/` is foundational.

The ticket's stated location (`src/worldassembly/modes.py`) is architecturally wrong.
The plan must use `src/core/modes.py` and note this correction.

## Q4: What is the "adapter heuristic report"?

The ticket defines `AdapterProjectionResult` as:
```python
@dataclass(frozen=True)
class AdapterProjectionResult:
    total_entities: int
    native_resolved: int
    legacy_projected: int
    unresolved: int
    heuristic_details: Dict[str, str]  # entity_id → projection reason
```

This is the report of what each adapter actually did — how many entities were resolved
natively from the catalog vs. projected via the migration heuristics vs. left unresolved.
Currently `seed_phase1_content()` returns `None`. The fix changes it to return
`AdapterProjectionResult` populated from counts accumulated during adapter `.adapt()` calls.

`seed_phase1_content()` currently has no sub-return from adapters — adapters return dicts.
So `AdapterProjectionResult` must be computed from the dict sizes + a projection-tracking
mechanism added inside the adapter or post-hoc. The simplest approach (no new heuristics):
compute totals from dict sizes; `heuristic_details` can be an empty dict in MIGRATION mode
with a note, since the ticket says "just capture what already happens" — actual per-entity
tracking would require modifying adapter internals (out of scope for this ticket).

A pragmatic implementation: `AdapterProjectionResult` is computed at `seed_phase1_content()`
level from the returned dicts — total = sum of all bootstrapped entity counts, no per-entity
breakdown in this ticket, `heuristic_details` = `{}` for now.

## Current Return Type of seed_phase1_content()

Annotated as `-> None`. Must change to `-> Optional[AdapterProjectionResult]` where it
returns `None` for the legacy hardcoded fallback path and `AdapterProjectionResult` for
the catalog path (or always returns it for both paths).

## Parity Ledger Findings (substrate.yaml)

Scanned all 200+ entries in `docs/parity_ledger/substrate.yaml`. No entry directly references
`migration_mode`, `seed_phase1_content`, or `AdapterProjectionResult`. The closest relevant
entries are:
- SUB-151: `test_item_registry_not_empty` — item registry non-empty post-seed
- SUB-154: `test_registry_not_empty` — generic registry non-empty guarantee
- SUB-069: Fallback behavior is exercised by real tests (status: verified)

No existing parity entry needs updating for this refactor since the behavioral change is
purely in how the mode is expressed (bool → enum), not in what the simulation computes.
A new parity entry should be added for `AdapterProjectionResult` auditability.

## Conflict Scan

Searched `tickets/inprogress/` and `tickets/done/` for: migration_mode, RuntimeContentMode,
seed_phase1_content, content mode enum.

- TCK-20260607-RESOLVER-BOUNDARY (DONE): touched `src/worldassembly/resolver.py` only.
  No overlap with `src/core/registries.py`. No conflict.
- No other in-progress or done ticket covers `migration_mode` or `seed_phase1_content`.
- No conflict found.
