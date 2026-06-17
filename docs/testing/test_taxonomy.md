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
