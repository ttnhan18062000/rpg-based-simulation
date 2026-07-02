---
status: active
layer: testing
authority: P1
audience: developer
---

# Test Taxonomy and Proof Standards

To ensure the engine is truthful and deterministic, all tests in the `tests/parity/` suite must adhere to this taxonomy.

## 1. Taxonomy Markers

### `legacy_characterization`
- **Purpose**: To document and freeze the current behavior of the legacy `src`.
- **Standard**: These tests should ideally run against the original `src` modules or use frozen output data (Oracles) to define the "Legacy Truth".

### `v2_contract`
- **Purpose**: To define the behavior of engine components where no legacy parity is required (e.g., new engine substrate, improved observability).
- **Standard**: Should focus on idempotency, immutability, and deterministic state transitions.

### `differential`
- **Purpose**: To prove bit-identical or semantic parity between `src` and `src`.
- **Standard**: Must use the same seeds and configurations. These are the strongest proof of parity.

### `intentional_divergence`
- **Purpose**: To explicitly document where current behavior *must* differ from legacy (e.g., fixing a legacy non-deterministic bug).
- **Standard**: Must assert the difference. Requires an `id` argument (e.g., `@pytest.mark.intentional_divergence(id="COMB-001")`) mapping to the Parity Ledger.

### `regression`
- **Purpose**: To prevent the return of bugs identified during the hardening process.
- **Standard**: Must include a comment or link to the original ticket/issue.

### `certification`
- **Purpose**: High-level "Smoke Tests" that verify the engine can complete a full tick/run without crashing or drifting.
- **Standard**: Runs long scenarios with randomized seeds.

### `worldassembly`
- **Purpose**: Tests that own the world module assembly, composition spec loading, region/faction/population merging, provenance manifest generation, and CompileContext serialization.
- **Location**: `tests/unit/worldassembly/`, `tests/integration/worldassembly/`
- **Ownership boundary**: These tests own the behaviors listed below. The strict world matrix suite **must not** duplicate them.

| Owned behavior | Test file |
|---|---|
| Region merge / duplicate collision | `test_assembly.py` |
| WorldSpec structural correctness | `test_assembly.py` |
| Deterministic provenance manifests | `test_provenance.py` |
| CompileContext serialization | `test_resolver.py` |
| Archetype metadata preservation | `test_archetype_preservation.py` |
| Real module catalog loads | `test_real_content_world_modules.py` |
| Real composition load/normalize | `test_real_content_world_compositions.py` |
| Module normalization snapshot | `test_real_module_normalized_snapshot.py` |

**Strict matrix tests** may verify scenario-specific assembly constraints (e.g., per-scenario region counts, population distributions) but must not re-assert basic "assembly produces a valid WorldSpec" or "catalog loads without error."

**Process guard — adding a new content field to a `worldspec.v1` schema (e.g. `RegionSpec`):**
When a field is added to a `worldspec.v1` schema class, it must also be added to the
corresponding `worldcomposition.v1` recipe schema (`src/worldbuilding/recipe.py`) and forwarded
in `WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py`) — these
are two separate, easy-to-miss authoring paths. Unit tests that construct schema objects directly
(e.g. `RegionState(...)`, `RegionSpec(...)`) do **not** exercise this gap; only a real
module-loading pipeline test does (module YAML → `WorldModuleAuthoringNormalizer.normalize()` →
`WorldAssemblyResolver.resolve_module_contribution()` → resolved spec, as in
`test_real_content_world_modules.py::test_hazard_kind_survives_module_pipeline`). A ticket that
adds a content field should run `tests/integration/worldassembly/test_real_content_world_modules.py`
(the `MODULE_MATRIX` covers all real `data/content/world_modules/*.yaml` files) as part of its own
test plan, not just its new unit tests. See TCK-20260701-HAZARD-KIND-RESOLVER-GAP for the
incident this guards against.

## 2. Enforcement
All tests in `tests/parity/` are subject to automated collection-time enforcement. A test will NOT run unless it has at least one of these markers.

## 3. How to Mark a Test
```python
import pytest

@pytest.mark.differential
def test_movement_parity():
    ...

@pytest.mark.intentional_divergence(id="SUB-042")
def test_improved_determinism():
    ...
```

---

## 4. Performance Test Authoring

Performance tests live in `tests/perf/` and use the `perf_budget` fixture (defined in `tests/perf/conftest.py`).  The fixture enforces budgets declared in `perf_baselines.json` at the repo root.  See also `docs/engine/performance_contract.md` §3.2 for measurement methodology and hardware class definitions.

### 4.1 Adding a new performance test

1. Write the test function in `tests/perf/`, accepting `perf_budget` as a parameter.
2. **Before running the test**, add a baseline entry to `perf_baselines.json`.  The fixture calls `pytest.fail` (not skip) if no entry exists — this is intentional to force authors to declare a budget up-front.
3. Obtain a starting budget by running:
   ```
   make perf-measure
   ```
   `perf_guard.py` will print a proposed JSON entry.  Copy it into `perf_baselines.json`, fill in `rationale` and `updated_by` (your ticket ID), and commit the baseline alongside the test.

**Minimal test structure:**

```python
import time
import pytest

def test_my_operation_perf(perf_budget):
    rss_before = perf_budget.snapshot_rss()
    t0 = time.perf_counter()

    result = my_expensive_operation()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    rss_delta_kb = perf_budget.snapshot_rss() - rss_before
    perf_budget.assert_within_budget(elapsed_ms, rss_delta_kb)
```

### 4.2 Updating after an intentional performance change

If a code change legitimately increases (or decreases) cost:

1. Land the code change.
2. Run `make perf-measure` — review the proposed diff on stdout.
3. Update the relevant `perf_baselines.json` entries: set `time_ms` / `memory_kb` to the new measured values, update `rationale`, set `updated_by` to your ticket ID, and set `updated_at` to today's date.
4. Commit `perf_baselines.json` in the same commit as the code change.

**Do not** commit a new baseline without a rationale explaining why the budget changed.

### 4.3 Tolerance bands

| `tolerance_pct` | When to use |
|---|---|
| 20 | Deterministic, CPU-bound operations — tight gate |
| 50 | Moderate noise (I/O, allocator variance) |
| 100 | High VM or scheduler noise; wide gate preferred over flaky test |

Use the narrowest band that avoids false positives on Class B hardware (shared VM, `PERF_HARDWARE_CLASS=B`).

### 4.4 Hardware class (`PERF_HARDWARE_CLASS`)

Override the hardware class via environment variable:

```
PERF_HARDWARE_CLASS=A python3 -m pytest tests/perf/
```

| Class | Description |
|---|---|
| A | Dedicated CI / bare-metal |
| B | Shared VM (default) |
| C | Laptop / dev workstation |

In the current pass, hardware class is **informational only** — it is recorded in `perf_baselines.json` entries and printed by `perf_guard.py`, but does not modify the effective tolerance band.  Per-class tolerance multipliers will be added when CI hardware is classified (see `docs/engine/performance_contract.md` §4.2).
