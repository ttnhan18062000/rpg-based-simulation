---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-MATRIX-EVIDENCE-VALIDATOR
phase: done
date: 2026-06-07
tags: [matrix, evidence, validator]
---

# TCK-20260607-MATRIX-EVIDENCE-VALIDATOR

## Title
Add ContentUsageEvidenceValidator and state transition guards

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`CONTENT_USAGE_MATRIX` entries carry `v2_evidence` strings (paths to test files) but nothing
validates that those paths actually exist. When a test is renamed or deleted, the matrix
silently points to ghost evidence. There are also no formal rules governing valid
`implementation_state` transitions — a family can move from `DESIGN_ONLY` to
`RUNTIME_AUTHORITATIVE` without passing through required intermediate states.

## Scope

### Fix 1 — `ContentUsageEvidenceValidator`

Create a new function or class in `src/content/validator.py` (or a new module
`src/content/matrix_validator.py` if the file is already large):

```python
def validate_matrix_evidence(matrix: Dict[str, ContentFamilyMatrixEntry]) -> List[str]:
    """
    Check that every v2_evidence string in the matrix resolves to a real test path.
    Returns a list of violation messages (empty = valid).
    """
```

- Parse each `entry.v2_evidence` as a file path (relative to project root)
- If path does not exist → violation
- If path is `None` or empty string → skip (no evidence declared, that's allowed for DESIGN_ONLY)
- If entry is `RUNTIME_AUTHORITATIVE` or `RESOLVED_PARTIALLY` and evidence is missing → violation

Add a corresponding test:
```
tests/unit/content/test_content_usage_evidence.py
```
Tests to add:
```python
- test_all_matrix_evidence_paths_exist
  → calls validate_matrix_evidence(CONTENT_USAGE_MATRIX), asserts violations == []
- test_missing_evidence_for_runtime_authoritative_is_violation
- test_missing_evidence_for_design_only_is_not_violation
```

### Fix 2 — State transition guards

Add to `tests/unit/content/test_content_usage_matrix.py`:

```python
VALID_TRANSITIONS = {
    "DESIGN_ONLY":          frozenset({"LOADED_ONLY", "VALIDATED_ONLY"}),
    "LOADED_ONLY":          frozenset({"VALIDATED_ONLY", "RESOLVED_PARTIALLY"}),
    "VALIDATED_ONLY":       frozenset({"RESOLVED_PARTIALLY", "PROJECTED_TO_LEGACY"}),
    "RESOLVED_PARTIALLY":   frozenset({"RUNTIME_AUTHORITATIVE", "PROJECTED_TO_LEGACY"}),
    "PROJECTED_TO_LEGACY":  frozenset({"RUNTIME_AUTHORITATIVE"}),
    "RUNTIME_AUTHORITATIVE": frozenset(),  # terminal
}
```

Add:
```python
def test_implementation_state_values_are_valid():
    valid_states = set(VALID_TRANSITIONS.keys())
    for key, entry in CONTENT_USAGE_MATRIX.items():
        assert entry.implementation_state in valid_states, \
            f"'{key}' has unknown implementation_state '{entry.implementation_state}'"
```

Note: The transition graph is documentation/guard only — it does not prevent arbitrary
state changes in YAML; it merely validates that the current state is a known enum member.

## Out of Scope
- Do not enforce sequential transition order (families can skip states in the initial authoring pass)
- Do not add a state machine runtime to `ContentFamilyMatrixEntry`
- Do not validate `resolver_component` or `compile_runtime_consumer` beyond existing tests

## Acceptance Criteria
- [ ] `validate_matrix_evidence()` (or equivalent) exists in `src/content/`
- [ ] `tests/unit/content/test_content_usage_evidence.py` exists with at least 3 tests
- [ ] All current matrix evidence paths exist or the test identifies which ones don't
- [ ] `test_implementation_state_values_are_valid()` exists in `test_content_usage_matrix.py`
- [ ] All states in CONTENT_USAGE_MATRIX are known enum members

## Related Tickets
(none)

## Related Docs
- `docs/parity_ledger/substrate.yaml`
- `world_phase_20_28_repair_remaining.md` R6.1, R6.2

## Related Code Areas
- `src/content/validator.py` or new `src/content/matrix_validator.py`
- `src/content/content_usage_matrix.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `tests/unit/content/test_content_usage_evidence.py` (new)

## Assumptions / Open Questions
- Do any current `v2_evidence` strings point to real test paths? Must check before writing the "all pass" test.
- If most evidence paths are invalid, the P0 action is to fix the matrix entries, not skip the validator.

## Implementation Notes
Investigation confirmed 13 ghost node IDs across 6 entry groups in matrix.py:
- foundation/* (6 entries): `test_foundation_resolver` → `TestFoundationResolverSingle`
- living/* (6 entries): `test_living_defaults_resolver` → `TestLivingDefaultsResolver`
- social/roles, social/factions: `test_social_defaults_resolver` → `TestSocialDefaultsResolver`
- social/perspectives, social/faction_relationships: `test_perspective_projection` → `test_relation_projection_clean`
- entities/populations: `test_population_recipe_resolver` → `TestPopulationRecipeResolver`
- entities/entity_archetypes: `test_entity_archetype_resolver` → `TestEntityArchetypeResolver`
- entities/stat_profiles, combat_profiles, inventory_profiles, skill_profiles, defaults (5 entries): `test_resolved_bundle_includes_compile_context` → `test_resolved_bundle_includes_compile_context_and_preserves_profiles`

All ghost node IDs fixed. `validate_matrix_evidence()` implemented as a module-level standalone function in validator.py after `load_all_compositions()`. Returns `List[str]` violations. Uses `implementation_state` only (never `content_maturity`). No circular import: `CONTENT_USAGE_MATRIX` imported locally inside function.

`VALID_TRANSITIONS` dict and `test_implementation_state_values_are_valid()` appended to test_content_usage_matrix.py.

## Test Summary
```
pytest tests/unit/content/test_content_usage_matrix.py tests/unit/content/test_content_usage_evidence.py -q
```

## Files Changed
- `src/content/matrix.py` — Fixed 18 ghost `evidence_tests` node ID suffixes across 6 entry groups
- `src/content/validator.py` — Added `validate_matrix_evidence()` standalone function
- `tests/unit/content/test_content_usage_evidence.py` — New file, 4 tests
- `tests/unit/content/test_content_usage_matrix.py` — Appended `VALID_TRANSITIONS` + `test_implementation_state_values_are_valid()`
- `docs/parity_ledger/infrastructure.yaml` — Updated INFRA-082, INFRA-094; added INFRA-177
- `docs/mechanics/content_usage_matrix.md` — Auto-regenerated by `test_generate_and_save_report`

## Completion Summary
Fixed 18 ghost node ID suffixes in `CONTENT_USAGE_MATRIX` across 6 resolver class groups and 1 assembly test rename. Implemented `validate_matrix_evidence()` as a pure standalone function in `validator.py` that checks file existence and `def`/`class` node ID presence for every `evidence_tests` token. Added 4 new tests in `test_content_usage_evidence.py` (integration guard, RUNTIME_AUTHORITATIVE violation, DESIGN_ONLY exemption, ghost node ID detection). Added `VALID_TRANSITIONS` dict + `test_implementation_state_values_are_valid()` to existing matrix test file. Updated parity ledger: INFRA-082 v2_evidence + test_path, INFRA-094 test_path, new INFRA-177. All 149 content unit tests pass (22 pass in scoped run).
