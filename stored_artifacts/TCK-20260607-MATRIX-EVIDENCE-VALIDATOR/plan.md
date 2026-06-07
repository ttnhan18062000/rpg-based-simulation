# Plan — TCK-20260607-MATRIX-EVIDENCE-VALIDATOR

## Approach

Add `validate_matrix_evidence()` as a standalone function in `src/content/validator.py`, fix 13+ ghost node IDs in `matrix.py`, write 4 new tests in a new evidence test file, add `VALID_TRANSITIONS` guard to the existing matrix test file, and update parity ledger entries INFRA-082, INFRA-094, and INFRA-177.

---

## Ordered Steps

### Step 1 — Audit ghost node IDs in `matrix.py` (no code change yet)

**File:** `src/content/matrix.py`

Read every `evidence_tests` value in `CONTENT_USAGE_MATRIX`. Collect entries that use a `::node_id` suffix. For each, verify that the node ID string (`def <name>` or `class <name>`) actually appears in the referenced file.

Expected findings (confirmed in investigation):

| Matrix key(s) | Current ghost node ID | Correct node ID |
|---|---|---|
| `foundation/traits`, `foundation/skills`, `foundation/archetypes`, `foundation/world_templates`, `foundation/era_templates`, `foundation/biome_templates` | `test_resolvers.py::test_foundation_resolver` | `test_resolvers.py::TestFoundationResolverSingle` |
| `living/base_stats`, `living/size_modifier`, `living/combat_styles`, `living/base_actions`, `living/status_effects`, `living/aging_phases` | `test_resolvers.py::test_living_defaults_resolver` | `test_resolvers.py::TestLivingDefaultsResolver` |
| `social/factions`, `social/roles` | `test_resolvers.py::test_social_defaults_resolver` | `test_resolvers.py::TestSocialDefaultsResolver` |
| `entities/entity_archetypes` | `test_resolvers.py::test_entity_archetype_resolver` | `test_resolvers.py::TestEntityArchetypeResolver` |
| `entities/populations` | `test_resolvers.py::test_population_recipe_resolver` | `test_resolvers.py::TestPopulationRecipeResolver` |
| `social/perspectives`, `social/faction_relationships` | `test_semantics.py::test_perspective_projection` | `test_semantics.py::test_relation_projection_clean` |

Confirm each corrected node ID exists in its file before applying any edit. This audit doubles as the pre-condition for Step 2.

---

### Step 2 — Fix ghost node IDs in `src/content/matrix.py`

**File:** `src/content/matrix.py`

Apply the corrections identified in Step 1. Each fix is a targeted string replacement of the `evidence_tests` value for the affected entry. No structural change to the model or any other field.

Rules:
- Use only `implementation_state` (never `content_maturity`) in any logic.
- Do not alter any field other than `evidence_tests` for affected entries.
- Do not reorder entries.

---

### Step 3 — Implement `validate_matrix_evidence()` in `src/content/validator.py`

**File:** `src/content/validator.py`

Add a new module-level standalone function (not a method of `CatalogValidator`) after the existing `load_all_compositions()` function and before the `CatalogValidator` class definition. This placement mirrors the existing pattern for pure-function utilities in the same file.

Function signature (exact):
```python
def validate_matrix_evidence(matrix: Dict[str, ContentFamilyMatrixEntry]) -> List[str]:
```

Required imports (add to existing import block only what is missing):
- `from pathlib import Path`
- `from src.content.matrix import ContentFamilyMatrixEntry` (confirm whether already imported)

**Logic (in order):**

1. Initialize `violations: List[str] = []`.
2. Locate the project root: `Path(__file__).resolve().parents[2]` (from `src/content/` up two levels).
3. For each `(key, entry)` in `matrix.items()`:
   a. If `entry.evidence_tests` is `None` or empty string:
      - If `entry.implementation_state` in `{"RUNTIME_AUTHORITATIVE", "RESOLVED_PARTIALLY"}`: append violation `"'{key}': state is {state} but evidence_tests is not declared"`.
      - Otherwise: skip (DESIGN_ONLY and others are exempt).
      - `continue`.
   b. Split `entry.evidence_tests` on `,`, strip whitespace from each element.
   c. For each token:
      - Split on `::` — first part is the file path, second part (if present) is the node ID.
      - Resolve file path against project root using `Path`.
      - If file does not exist: append violation `"'{key}': evidence path does not exist: {file_path}"`.
      - If file exists and a node ID suffix is present: read file text, check whether `f"def {node_id}"` or `f"class {node_id}"` appears as a substring. If neither appears: append violation `"'{key}': node ID '{node_id}' not found in {file_path}"`.
4. Return `violations`.

Constraints:
- Do not use `content_maturity` in any conditional.
- Do not raise exceptions on missing files — record violations and continue.
- Do not call `CatalogValidator` or depend on `CatalogRepository`.
- The function must be callable with any `Dict[str, ContentFamilyMatrixEntry]`, including synthetic dicts for unit tests.

---

### Step 4 — Create `tests/unit/content/test_content_usage_evidence.py`

**File:** `tests/unit/content/test_content_usage_evidence.py` (new)

Write exactly 4 tests. Use direct imports (no fixtures). All fake entries use real `ContentFamilyMatrixEntry` constructor calls.

#### Test 1: `test_all_matrix_evidence_paths_exist`
Calls `validate_matrix_evidence(CONTENT_USAGE_MATRIX)` against the real matrix. Asserts `violations == []`. This test will fail if any path is renamed or deleted in the future — that is its purpose.

Pre-condition: Step 2 (ghost node ID corrections) must be complete before this test is written, otherwise it cannot assert `violations == []`.

#### Test 2: `test_missing_evidence_for_runtime_authoritative_is_violation`
Constructs a synthetic `ContentFamilyMatrixEntry` with `implementation_state="RUNTIME_AUTHORITATIVE"` and `evidence_tests=None`. Asserts that `validate_matrix_evidence(fake_matrix)` returns at least one violation whose message references the matrix key.

#### Test 3: `test_missing_evidence_for_design_only_is_not_violation`
Constructs a synthetic entry with `implementation_state="DESIGN_ONLY"` and `evidence_tests=None`. Asserts `violations == []`.

#### Test 4: `test_ghost_node_id_is_violation`
Constructs a synthetic entry with `evidence_tests` pointing to a real file with a `::test_nonexistent_function_zzz` suffix that does not appear in that file. Asserts that the returned violations list contains an entry referencing the bad node ID.

Use `tests/unit/core/test_registry_adapters.py` as the real file (confirmed to exist). The node ID `test_nonexistent_function_zzz` is guaranteed not to appear there.

---

### Step 5 — Add `VALID_TRANSITIONS` and `test_implementation_state_values_are_valid` to `tests/unit/content/test_content_usage_matrix.py`

**File:** `tests/unit/content/test_content_usage_matrix.py`

Append to the bottom of the file (do not insert before any existing test):

```python
VALID_TRANSITIONS = {
    "DESIGN_ONLY":            frozenset({"LOADED_ONLY", "VALIDATED_ONLY"}),
    "LOADED_ONLY":            frozenset({"VALIDATED_ONLY", "RESOLVED_PARTIALLY"}),
    "VALIDATED_ONLY":         frozenset({"RESOLVED_PARTIALLY", "PROJECTED_TO_LEGACY"}),
    "RESOLVED_PARTIALLY":     frozenset({"RUNTIME_AUTHORITATIVE", "PROJECTED_TO_LEGACY"}),
    "PROJECTED_TO_LEGACY":    frozenset({"RUNTIME_AUTHORITATIVE"}),
    "RUNTIME_AUTHORITATIVE":  frozenset(),  # terminal
}


def test_implementation_state_values_are_valid():
    valid_states = set(VALID_TRANSITIONS.keys())
    for key, entry in CONTENT_USAGE_MATRIX.items():
        assert entry.implementation_state in valid_states, (
            f"'{key}' has unknown implementation_state '{entry.implementation_state}'"
        )
```

Note: `VALID_TRANSITIONS` is documentation-as-guard only. It does not enforce transition ordering at runtime; it ensures every declared state is a member of the canonical 6-state enum. No transition-sequence enforcement (out of scope per ticket).

---

### Step 6 — Run tests (scoped)

```bash
pytest tests/unit/content/test_content_usage_matrix.py tests/unit/content/test_content_usage_evidence.py -q
```

All 5 new tests must pass. All existing tests in `test_content_usage_matrix.py` must continue to pass without modification.

If `test_all_matrix_evidence_paths_exist` fails, the failing violation messages identify the specific ghost paths/node IDs still needing correction in `matrix.py`.

Extended regression (run after primary scope passes):
```bash
pytest tests/unit/content/ -q
```

---

### Step 7 — Regenerate matrix report

The test `test_generate_and_save_report` (existing in `test_content_usage_matrix.py`) auto-regenerates `docs/mechanics/content_usage_matrix.md` from the corrected matrix. It will run as part of Step 6. Verify that `docs/mechanics/content_usage_matrix.md` is updated (timestamp or content change). No manual edit needed.

---

### Step 8 — Update parity ledger `docs/parity_ledger/infrastructure.yaml`

Make three changes:

**INFRA-082** (line ~1751 area — "Every checked row names the test path that proves it"):
- Set `test_path: tests/unit/content/test_content_usage_evidence.py::test_all_matrix_evidence_paths_exist`
- Update `v2_evidence` to reference the new validator function.
- Keep `status: verified`.

**INFRA-094** ("CI can fail when a proof path references a missing test file"):
- Set `test_path: tests/unit/content/test_content_usage_evidence.py::test_all_matrix_evidence_paths_exist`
- Keep `status: verified`.

**INFRA-177** (new entry, append after INFRA-176):
```yaml
- id: INFRA-177
  text: >
    validate_matrix_evidence() detects ghost evidence_tests node IDs in
    CONTENT_USAGE_MATRIX — both missing files and ::node_id suffixes that
    do not appear in the referenced file.
  status: verified
  priority: P1
  v2_evidence: >
    src/content/validator.py::validate_matrix_evidence +
    tests/unit/content/test_content_usage_evidence.py
  test_path: tests/unit/content/test_content_usage_evidence.py::test_all_matrix_evidence_paths_exist
  divergence_note: null
```

---

### Step 9 — Finalize ticket and working log

- Update `tickets/inprogress/TCK-20260607-MATRIX-EVIDENCE-VALIDATOR.md`: fill `Files Changed` and `Completion Summary`, set `Status: DONE`.
- Move to `tickets/done/TCK-20260607-MATRIX-EVIDENCE-VALIDATOR.md`.
- Move `staging_artifacts/TCK-20260607-MATRIX-EVIDENCE-VALIDATOR/` to `stored_artifacts/`.
- Append one row to `tickets/working_log.csv`.
- Run cleanup: `rm -rf data/runs/* reports/release_proof/*`.
- Write agent monitoring run entry and at least one event entry to `agent-monitoring/`.

---

## Files Changed (Expected)

| File | Change type |
|---|---|
| `src/content/matrix.py` | Modify — fix ~13 ghost `evidence_tests` node ID suffixes |
| `src/content/validator.py` | Modify — add `validate_matrix_evidence()` standalone function |
| `tests/unit/content/test_content_usage_evidence.py` | Create — 4 new tests |
| `tests/unit/content/test_content_usage_matrix.py` | Modify — append `VALID_TRANSITIONS` dict + `test_implementation_state_values_are_valid()` |
| `docs/parity_ledger/infrastructure.yaml` | Modify — update INFRA-082, INFRA-094, add INFRA-177 |
| `docs/mechanics/content_usage_matrix.md` | Auto-regenerated by existing `test_generate_and_save_report` |

## Deviations from Plan

- Actual ghost node ID count was 18, not ~13. The plan identified 13 from the `::test_function_name` pattern.
  The additional 5 were `test_assembly.py::test_resolved_bundle_includes_compile_context` (4 entities/* entries + defaults),
  where the actual function name is `test_resolved_bundle_includes_compile_context_and_preserves_profiles`.
  All fixed as per plan Step 2 logic — no structural deviation.
- `validate_matrix_evidence()` uses a local import for `CONTENT_USAGE_MATRIX` inside the function body
  (not at module top) to avoid a circular import between `validator.py` and `matrix.py`. This is consistent
  with the existing pattern in `_validate_dead_active_data` which also does a local `from src.content.matrix import ...`.

---

## Unresolved Questions

None. All open questions from the investigation have been decided:

| Q | Decision |
|---|---|
| Q1: `validator.py` or new `matrix_validator.py`? | Add to `validator.py` as a module-level standalone function. Matches `load_all_compositions()` pattern. Split only when file grows further (future ticket). |
| Q2: Return `List[str]` or raise? | Return `List[str]` per ticket AC. Keeps function dependency-light and directly testable. |
| Q3: What counts as valid evidence path? | File path (split on `::`) must exist on disk; if `::node_id` present, `def <node_id>` or `class <node_id>` must appear as substring in file text. |
| Q4: Integrate with `CatalogValidator.validate()`? | No. Keep standalone (Option A). Ticket AC names a standalone function; mixing filesystem checks into the relational validator is out of scope. |
| Q5: Fix ghost node IDs or guard only? | Fix the matrix entries (Step 2) AND add the guard (Steps 3–4). Guard without fixing would require the integration test to assert non-empty violations, defeating its purpose. |

---

## Anti-Drift Hazards (from investigation, included for implementer awareness)

- `validate_matrix_evidence()` must use only `implementation_state`, never `content_maturity`, in all conditionals. The existing `test_yaml_state_comments_are_ignored` and `test_graph_ignores_yaml_comments_explicitly` tests will fail if `STATE:` appears in validator logic.
- Any future rename of `TestFoundationResolverSingle` (or similar classes) in `test_resolvers.py` will cause `test_all_matrix_evidence_paths_exist` to fail — that is the intended guard behavior.
- New `RUNTIME_AUTHORITATIVE` entries added to the matrix without `evidence_tests` will be caught by the existing `test_runtime_authoritative_requires_evidence` (string non-empty) and the new `test_all_matrix_evidence_paths_exist` (path valid). Both must stay green.
