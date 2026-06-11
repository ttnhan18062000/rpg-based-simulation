---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-MATRIX-EVIDENCE-VALIDATOR
artifact_type: test_plan
tags: [matrix, evidence, validator]
---

# Test Plan — TCK-20260607-MATRIX-EVIDENCE-VALIDATOR

## Regression Surface

The following existing tests must continue to pass without modification:

| Test | File | Why at risk |
|---|---|---|
| `test_matrix_validation_and_states` | `test_content_usage_matrix.py:30` | Touches all matrix entries; state enum must remain stable |
| `test_runtime_authoritative_requires_evidence` | `test_content_usage_matrix.py:138` | Checks `evidence_tests` non-empty; new validator is additive |
| `test_every_family_has_implementation_state` | `test_content_usage_matrix.py:130` | State values must remain in `VALID_IMPLEMENTATION_STATES` |
| `test_family_without_declared_consumer_fails_usage_contract` | `test_content_usage_matrix.py:166` | Must not be broken by any matrix entry corrections |
| `test_living_family_marked_resolved_partially_until_runtime_consumer` | `test_content_usage_matrix.py:201` | Hardcoded state + evidence text assertions for living families |
| `test_yaml_state_comments_are_ignored` | `test_content_usage_matrix.py:118` | Scans `src/` for `STATE:` — new code must not introduce this string in logic |
| `test_graph_ignores_yaml_comments_explicitly` | `test_content_usage_matrix.py:156` | Inspects `CatalogValidator` source — new standalone function must not reference `STATE:` |
| `test_compatibility_family_not_runtime_authoritative` | `test_content_usage_matrix.py:147` | Uses `resolver_component`/`compile_runtime_consumer` — must not be broken by matrix edits |
| `test_matrix_covers_all_content_files` | `test_content_usage_matrix.py:69` | Filesystem scan of `data/content/` vs matrix keys — stable |
| `test_foundation_resolver_fetches_known_ids` | `test_content_usage_matrix.py:211` | End-to-end resolver; not affected by this ticket |
| `test_dead_record_validator_covers_region_concept` | `test_content_usage_matrix.py:250` | `_FAMILY_KEY_OVERRIDES` must remain intact |

---

## New Tests Required (per AC)

### File: `tests/unit/content/test_content_usage_evidence.py` (new)

#### Test 1: `test_all_matrix_evidence_paths_exist`
**AC:** "All current matrix evidence paths exist or the test identifies which ones don't."

```python
def test_all_matrix_evidence_paths_exist():
    from src.content.validator import validate_matrix_evidence
    from src.content.matrix import CONTENT_USAGE_MATRIX
    violations = validate_matrix_evidence(CONTENT_USAGE_MATRIX)
    assert violations == [], (
        f"Matrix evidence violations found:\n" + "\n".join(violations)
    )
```

Pre-conditions: ghost node IDs in `matrix.py` must be corrected before this test can pass (see investigation Q5). Specifically:
- 13+ entries in `CONTENT_USAGE_MATRIX` reference `::test_function_name` suffixes that are actually class names or non-existent functions. These must be corrected to real class or function node IDs before the test is written to assert `violations == []`.
- `social/perspectives` and `social/faction_relationships` reference `test_semantics.py::test_perspective_projection` — this function does not exist; the correct node is `test_semantics.py::test_relation_projection_clean`.

#### Test 2: `test_missing_evidence_for_runtime_authoritative_is_violation`
**AC:** "missing evidence for RUNTIME_AUTHORITATIVE is a violation."

```python
def test_missing_evidence_for_runtime_authoritative_is_violation():
    from src.content.validator import validate_matrix_evidence
    from src.content.matrix import ContentFamilyMatrixEntry
    fake_matrix = {
        "world/fake_runtime": ContentFamilyMatrixEntry(
            file_path="world/fake_runtime.yaml",
            schema_class="FakeDefinition",
            repository_index="fake",
            validator_coverage="None",
            resolver_component="FakeResolver",
            compile_runtime_consumer="FakeRegistry",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests=None,
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="RUNTIME_AUTHORITATIVE",
            content_maturity="REDESIGNED-CORE",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert any("fake_runtime" in v for v in violations), (
        "RUNTIME_AUTHORITATIVE entry with no evidence_tests must produce a violation"
    )
```

#### Test 3: `test_missing_evidence_for_design_only_is_not_violation`
**AC:** "missing evidence for DESIGN_ONLY is not a violation."

```python
def test_missing_evidence_for_design_only_is_not_violation():
    from src.content.validator import validate_matrix_evidence
    from src.content.matrix import ContentFamilyMatrixEntry
    fake_matrix = {
        "simulation_scenarios_fake": ContentFamilyMatrixEntry(
            file_path="simulation_scenarios_fake",
            schema_class=None,
            repository_index="None",
            validator_coverage="None",
            resolver_component="None (Design-Only)",
            compile_runtime_consumer="None (Design-Only)",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests=None,
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="DESIGN_ONLY",
            content_maturity="REDESIGNED-CORE",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert violations == [], (
        "DESIGN_ONLY entry with no evidence_tests must NOT produce a violation"
    )
```

#### Test 4 (recommended addition): `test_ghost_node_id_is_violation`
Not in AC but directly motivated by the audit finding (ghost node IDs in `test_resolvers.py`):

```python
def test_ghost_node_id_is_violation():
    from src.content.validator import validate_matrix_evidence
    from src.content.matrix import ContentFamilyMatrixEntry
    fake_matrix = {
        "world/fake_node": ContentFamilyMatrixEntry(
            file_path="world/buildings.yaml",  # real file
            schema_class="BuildingDefinition",
            repository_index="buildings",
            validator_coverage="None",
            resolver_component="BuildingResolver",
            compile_runtime_consumer="BuildingRegistry",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests="tests/unit/core/test_registry_adapters.py::test_nonexistent_function_zzz",
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="RUNTIME_AUTHORITATIVE",
            content_maturity="REDESIGNED-CORE",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert any("test_nonexistent_function_zzz" in v for v in violations), (
        "A ::node_id suffix that does not appear in the file must produce a violation"
    )
```

---

### File: `tests/unit/content/test_content_usage_matrix.py` (modify existing)

#### Test 5: `test_implementation_state_values_are_valid`
**AC:** "test_implementation_state_values_are_valid() exists in test_content_usage_matrix.py."

Add at the bottom of the file:

```python
VALID_TRANSITIONS = {
    "DESIGN_ONLY":           frozenset({"LOADED_ONLY", "VALIDATED_ONLY"}),
    "LOADED_ONLY":           frozenset({"VALIDATED_ONLY", "RESOLVED_PARTIALLY"}),
    "VALIDATED_ONLY":        frozenset({"RESOLVED_PARTIALLY", "PROJECTED_TO_LEGACY"}),
    "RESOLVED_PARTIALLY":    frozenset({"RUNTIME_AUTHORITATIVE", "PROJECTED_TO_LEGACY"}),
    "PROJECTED_TO_LEGACY":   frozenset({"RUNTIME_AUTHORITATIVE"}),
    "RUNTIME_AUTHORITATIVE": frozenset(),  # terminal
}


def test_implementation_state_values_are_valid():
    valid_states = set(VALID_TRANSITIONS.keys())
    for key, entry in CONTENT_USAGE_MATRIX.items():
        assert entry.implementation_state in valid_states, (
            f"'{key}' has unknown implementation_state '{entry.implementation_state}'"
        )
```

Note: `VALID_TRANSITIONS` is intentionally not enforced as a runtime state machine — it serves as an explicit guard that the declared state is a known member, and documents the intended flow for future readers.

---

## validate_matrix_evidence() — Expected Behavior Contract

```python
def validate_matrix_evidence(matrix: Dict[str, ContentFamilyMatrixEntry]) -> List[str]:
```

| Input condition | Expected output |
|---|---|
| `evidence_tests` is `None` or empty string | Skip (no violation), unless `implementation_state` is `RUNTIME_AUTHORITATIVE` or `RESOLVED_PARTIALLY` |
| `evidence_tests` is `None`, state is `DESIGN_ONLY` | No violation |
| `evidence_tests` is `None`, state is `RUNTIME_AUTHORITATIVE` | Violation: missing required evidence |
| `evidence_tests` contains a valid file path | No violation from path check |
| `evidence_tests` contains a path that does not exist | Violation: ghost path |
| `evidence_tests` contains `file::node_id` where file exists but node absent | Violation: ghost node ID |
| `evidence_tests` is comma-separated list | Each element checked independently |

---

## Scoped Pytest Commands

### Primary scope (this ticket):
```bash
pytest tests/unit/content/test_content_usage_matrix.py tests/unit/content/test_content_usage_evidence.py -q
```

### Extended regression (content + worldassembly domain):
```bash
pytest tests/unit/content/ tests/unit/worldassembly/ tests/unit/content_semantics/ -q
```

### Pre-commit full content check (do not use full suite):
```bash
pytest tests/unit/content/ -q
```

---

## Anti-Drift Test Guards

| Guard | Test | Mechanism |
|---|---|---|
| Ghost evidence paths are caught | `test_all_matrix_evidence_paths_exist` | Calls `validate_matrix_evidence(CONTENT_USAGE_MATRIX)`, asserts `violations == []` — fails immediately if any path is renamed/deleted |
| Ghost node IDs are caught | `test_ghost_node_id_is_violation` | Unit-tests the validator's node-ID-presence check |
| `RUNTIME_AUTHORITATIVE` always has evidence | `test_runtime_authoritative_requires_evidence` (existing) + `test_missing_evidence_for_runtime_authoritative_is_violation` | Dual guard: string non-empty AND path valid |
| `DESIGN_ONLY` exemption preserved | `test_missing_evidence_for_design_only_is_not_violation` | Regression guard for the skip rule |
| State enum membership explicit | `test_implementation_state_values_are_valid` | Uses `VALID_TRANSITIONS` keys as ground truth; any new state must be added there first |
| `content_maturity` not used in logic | `test_yaml_state_comments_are_ignored` + `test_graph_ignores_yaml_comments_explicitly` | Both scan source for policy violations; new validator code must not reference `content_maturity` in conditionals |
| Matrix report stays current | `test_generate_and_save_report` (existing) | Auto-regenerates `docs/mechanics/content_usage_matrix.md` on every test run |
