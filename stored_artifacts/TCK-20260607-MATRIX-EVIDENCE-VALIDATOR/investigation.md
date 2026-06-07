# Investigation — TCK-20260607-MATRIX-EVIDENCE-VALIDATOR

## Current Behavior

### CONTENT_USAGE_MATRIX structure
- **File:** `src/content/matrix.py:29`
- `CONTENT_USAGE_MATRIX: Dict[str, ContentFamilyMatrixEntry]` — 37 entries total.
- Key format is `"family/subfamily"` (e.g. `"world/buildings"`, `"foundation/traits"`).

### ContentFamilyMatrixEntry model (`src/content/matrix.py:6–27`)
| Field | Type | Notes |
|---|---|---|
| `file_path` | `str` | Path relative to `data/content/` |
| `schema_class` | `Optional[str]` | Pydantic schema class name |
| `repository_index` | `Optional[str]` | CatalogRepository target field |
| `validator_coverage` | `Optional[str]` | Rule IDs, free text |
| `resolver_component` | `Optional[str]` | Component doing resolution |
| `compile_runtime_consumer` | `Optional[str]` | Consumer component |
| `test_coverage` | `str` | Key test file paths (required) |
| `evidence_tests` | `Optional[str]` | Test node IDs for active flow |
| `resolver_evidence` | `Optional[str]` | Resolver evidence text |
| `runtime_consumer_evidence` | `Optional[str]` | Runtime consumer evidence text |
| `implementation_state` | `str` | Standardized usage state (required) |
| `content_maturity` | `str` | YAML-comment maturity classification (required) |

The model is `frozen=True` (immutable Pydantic). There is **no `v2_evidence` field** — the ticket spec uses `v2_evidence` as shorthand for `evidence_tests`, which is the actual field name.

### implementation_state enum values (verified in tests, `src/content/matrix.py` + `tests/unit/content/test_content_usage_matrix.py:6–13`)
Six valid states:
```
DESIGN_ONLY, LOADED_ONLY, VALIDATED_ONLY, RESOLVED_PARTIALLY, PROJECTED_TO_LEGACY, RUNTIME_AUTHORITATIVE
```
Current distribution: `DESIGN_ONLY=1`, `PROJECTED_TO_LEGACY=2`, `RESOLVED_PARTIALLY=25`, `RUNTIME_AUTHORITATIVE=9`.

### Existing validation touching implementation_state / evidence_tests

**`tests/unit/content/test_content_usage_matrix.py`:**
- `test_matrix_validation_and_states` (line 30) — checks all states are in `VALID_IMPLEMENTATION_STATES`, checks maturity states, checks metadata fields present.
- `test_every_family_has_implementation_state` (line 130) — redundant state membership check.
- `test_runtime_authoritative_requires_evidence` (line 138) — checks that `RUNTIME_AUTHORITATIVE` entries have a non-empty `evidence_tests` string. **Does not verify the path exists on disk.**
- `test_family_without_declared_consumer_fails_usage_contract` (line 166) — checks non-DESIGN_ONLY/PROJECTED_TO_LEGACY have a consumer.
- `VALID_IMPLEMENTATION_STATES` constant (line 6) — already defines all 6 valid states.

**`src/content/validator.py:648`:**
```python
if entry.implementation_state in ("DESIGN_ONLY", "LOADED_ONLY"):
    continue
```
Uses `implementation_state` for dead-record exemption (post-TCK-20260607-VALIDATOR-MATURITY-POLICY fix). No path-existence check anywhere in the file.

---

## What Is Missing

### Gap 1 — No path-existence check for evidence_tests
`evidence_tests` is a free-form string (may contain comma-separated `file::test_node` values). Nothing validates that the paths resolve to real files. The existing `test_runtime_authoritative_requires_evidence` only checks `len(string) > 0`, not filesystem existence.

**Critical finding from audit:** All 37 `evidence_tests` file paths exist on disk. However, 6 entries use `::test_function_name` suffixes that do not match actual function names — they reference pytest node IDs that resolve to **test classes**, not standalone functions:

| Matrix entry | evidence_tests node ID | Actual pytest node |
|---|---|---|
| `foundation/*` (6 entries) | `test_resolvers.py::test_foundation_resolver` | Class: `TestFoundationResolverSingle` etc. |
| `living/*` (6 entries) | `test_resolvers.py::test_living_defaults_resolver` | Class: `TestLivingDefaultsResolver` |
| `social/factions`, `social/roles` | `test_resolvers.py::test_social_defaults_resolver` | Class: `TestSocialDefaultsResolver` |
| `entities/entity_archetypes` | `test_resolvers.py::test_entity_archetype_resolver` | Class: `TestEntityArchetypeResolver` |
| `entities/populations` | `test_resolvers.py::test_population_recipe_resolver` | Class: `TestPopulationRecipeResolver` |
| `social/perspectives`, `social/faction_relationships` | `test_semantics.py::test_perspective_projection` | Does not exist; closest: `test_relation_projection_clean` |

These are **ghost node IDs**: the file exists but `pytest <file>::<node>` would fail or collect zero tests.

### Gap 2 — No state transition guard
There is no test or runtime check verifying that `implementation_state` values belong to the canonical 6-member set using an explicit `VALID_TRANSITIONS` structure. The ticket requires adding `test_implementation_state_values_are_valid()` with a `VALID_TRANSITIONS` dict to make the allowed state set and its terminal/non-terminal structure explicit. This is **documentation-as-guard** — not a runtime state machine.

---

## Mechanics/Engine Constraints

- **Mechanics Bible `docs/mechanics/06_worldbuilding_foundation.md`** — governs content family declarations; `implementation_state` is the canonical gate for when a family enters the runtime pipeline.
- **Engine Contract `docs/engine/kernel.md`** — 6-phase deterministic loop; content families enter at Init phase. Validator integrity is a pre-condition.
- **Content Usage Matrix policy (`src/content/matrix.py:8–12`):** YAML comments (`# STATE: ...`) are human-only; `implementation_state` at the family level is the sole authoritative signal. Any new validator must use `implementation_state`, never `content_maturity`.
- **`docs/mechanics/content_usage_matrix.md`** — auto-generated from `generate_matrix_report()`; will need regeneration after matrix entries are corrected.

---

## Parity Ledger Overlap

Checked `docs/parity_ledger/infrastructure.yaml` (INFRA-001 through INFRA-176):
- **INFRA-094:** "CI can fail when a proof path references a missing test file." — `status: verified`. This entry covers exactly the spirit of this ticket's Fix 1. Its `test_path` is `null` — the behavior is asserted at the audit level, not via an automated test. Adding `validate_matrix_evidence()` creates the missing machine-readable enforcement.
- **INFRA-082:** "Every checked row names the test path that proves it." — `status: verified`. The ghost node ID problem directly undermines this invariant.
- No existing parity entry tracks matrix `evidence_tests` path validity as an automated check.

A new parity entry should be added to `infrastructure.yaml` after implementation:
- `INFRA-177` (next available): "`validate_matrix_evidence()` detects ghost evidence_tests node IDs in CONTENT_USAGE_MATRIX."

---

## Prior Work

| Ticket | Relevance |
|---|---|
| `TCK-20260606-PHASE24-RESOLVER-EVIDENCE` (DONE) | Added `resolver_evidence`/`runtime_consumer_evidence` fields; established `RESOLVED_PARTIALLY` as the correct state for resolver-only families. Produced the current matrix shape under investigation. |
| `TCK-20260607-VALIDATOR-MATURITY-POLICY` (DONE) | Fixed `content_maturity` misuse in validator and tests; established that only `implementation_state` drives logic. **This ticket must not re-introduce `content_maturity` into any conditional.** |
| `TCK-20260523-MUTATION-MATRIX` (DONE, stored_artifacts) | Earlier matrix structure work; established the family key format. |
| `TCK-20260503-INFRA-LEDGER-VALIDATOR` (DONE) | Established parity ledger validation infrastructure; `infrastructure.yaml` format used here. |

---

## Risks and Open Questions

### Q1 — Module placement: `validator.py` or new `matrix_validator.py`?
**Current `src/content/validator.py`** is 667 lines and already imports `CONTENT_USAGE_MATRIX` (line 623). Adding `validate_matrix_evidence()` there keeps related concerns together. However, `CatalogValidator` requires a `CatalogRepository` instance to construct; `validate_matrix_evidence()` needs no repository — it operates purely on the matrix dict and the filesystem. Mixing constructor-requiring and pure-function validators in one file is clean enough given the existing `load_all_compositions()` standalone function pattern in the same file.

**Recommendation:** Add to `src/content/validator.py` as a module-level standalone function, not a method of `CatalogValidator`. This matches the existing `load_all_compositions()` pattern.

If the file grows further, a future ticket can extract to `matrix_validator.py`. Do not pre-emptively split now.

### Q2 — Return violations list or raise?
Existing `CatalogValidator.validate()` returns `List[ValidationIssue]`. The standalone `validate_matrix_evidence()` function should return `List[str]` (violation messages) per the ticket spec — this keeps it dependency-light (no `ValidationIssue` import needed in tests) and consistent with the ticket's AC verbatim. Tests call it directly and assert `violations == []`.

### Q3 — What counts as a valid evidence path?
The `evidence_tests` field may contain:
- A bare file path: `tests/unit/content/test_catalog.py`
- A pytest node ID: `tests/unit/content/test_resolvers.py::test_foundation_resolver`
- A comma-separated list of the above (not currently observed but the field is free-form)

The validator should:
1. Split on comma, strip whitespace.
2. Strip the `::node_id` suffix to get the file path.
3. Check `Path(file_path).exists()` relative to project root.
4. **Separately** check that if a `::node_id` is present, the node ID string actually appears in the file (as `def <name>` or `class <name>`). This catches the ghost-node-ID class vs. function mismatch found during audit.

The second check is the critical addition beyond what the ticket spec literally states — it surfaces the actual defect found.

### Q4 — How does validate_matrix_evidence() interact with CatalogValidator?
`CatalogValidator.validate()` currently runs 14 internal checks. It does not call `validate_matrix_evidence()`. Options:
- **A (preferred):** Keep separate — `validate_matrix_evidence()` is a static-analysis/CI guard, not a runtime catalog check. Tests invoke it directly.
- **B:** Hook it into `CatalogValidator.validate()` and surface results as `ValidationIssue` entries. This is heavier and mixes filesystem checks into the catalog relational validator.

Recommendation: Option A. The ticket AC lists a standalone function; keep it standalone.

### Q5 — Ghost node IDs: fix matrix entries or guard only?
The ticket states: "If many are wrong, the ticket may need to also update matrix entries." All 37 file paths exist — only node ID suffixes are wrong for 13+ entries (classes named as if they were functions, one completely non-existent function name). The validator `test_all_matrix_evidence_paths_exist` will fail if it checks node-ID validity. Implementation must **also fix the stale node IDs** in `matrix.py` as part of this ticket, otherwise the "all pass" test cannot be written.

The correct node IDs to use:
- `test_resolvers.py::TestFoundationResolverSingle` (or just `test_resolvers.py` — the class contains multiple tests)
- `test_resolvers.py::TestLivingDefaultsResolver`
- `test_resolvers.py::TestSocialDefaultsResolver`
- `test_resolvers.py::TestEntityArchetypeResolver`
- `test_resolvers.py::TestPopulationRecipeResolver`
- `test_semantics.py::test_relation_projection_clean` (replaces non-existent `test_perspective_projection`)

---

## Anti-Drift Hazards

1. **Ghost node ID recurrence** — Any rename of a test class or function in `test_resolvers.py` or `test_registry_adapters.py` will silently invalidate `evidence_tests` entries. The new validator test `test_all_matrix_evidence_paths_exist` is the machine-readable guard against this.

2. **content_maturity creep** — `TCK-20260607-VALIDATOR-MATURITY-POLICY` already fixed this once. `validate_matrix_evidence()` must use only `implementation_state`, never `content_maturity`, for all conditional logic.

3. **New families added without evidence** — When a new entry is added to `CONTENT_USAGE_MATRIX` in state `RUNTIME_AUTHORITATIVE` or `RESOLVED_PARTIALLY`, the existing `test_runtime_authoritative_requires_evidence` catches missing `evidence_tests` string. The new validator catches dead file paths. Both must pass.

4. **Matrix report staleness** — `docs/mechanics/content_usage_matrix.md` is auto-generated by `test_generate_and_save_report`. After fixing ghost node IDs in `matrix.py`, that test must be re-run to keep the report current.

5. **INFRA-082/INFRA-094 coverage gap** — These parity entries claim "verified" status but have no `test_path`. A new `INFRA-177` entry with `test_path: tests/unit/content/test_content_usage_evidence.py::test_all_matrix_evidence_paths_exist` closes the gap.
