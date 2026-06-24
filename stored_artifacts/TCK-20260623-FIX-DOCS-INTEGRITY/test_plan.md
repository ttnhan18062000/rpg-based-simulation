# TCK-20260623-FIX-DOCS-INTEGRITY — Test Plan

## Scope

Verify that all 12 failing tests in `tests/docs/`, `tests/integrity/`, and `tests/architecture/` pass after fixes are applied.

The two kernel warmup failures (`test_autonomous_loop_determinism_drift_guard`, `test_resolution_phase_ordering_integrity`) may require additional investigation before they can be fixed; they are included in the target test run but may be deferred to a child ticket if the root cause is deeper than the doc/baseline fixes.

---

## Test Commands

### 1. Full target suite (run after all fixes)

```bash
python3 -m pytest tests/docs/ tests/integrity/ tests/architecture/ -q --tb=short
```

Expected: 0 failures (12 currently failing → 0).

### 2. Focused per-fix validation

#### TYPE A — Missing docs
```bash
python3 -m pytest tests/docs/test_doc_integrity.py tests/docs/test_contributor_guardrails.py tests/integrity/test_doc_guards.py -v --tb=short
```
Expected: `test_manifest_file_existence`, `test_document_structural_compliance`, `test_release_target_binding`, `test_link_integrity`, `test_extension_templates_present`, `test_mandatory_doc_existence` all PASS.

#### TYPE B — Oracle artifacts
```bash
python3 -m pytest tests/integrity/test_parity_guards.py -v --tb=short
```
Expected: `test_oracle_artifact_existence`, `test_oracle_schema_integrity`, `test_critical_parity_scenarios_presence` all PASS.

#### TYPE C — Stale baseline
```bash
python3 -m pytest tests/architecture/test_no_new_hardcoded_gameplay_truth.py -v --tb=short
```
Expected: `test_known_baseline_stale_guard` PASSES. `test_no_new_hardcoded_gameplay_ids_without_migration_map_entry` must still pass (no regression).

#### TYPE D — Import boundary
```bash
python3 -m pytest tests/architecture/test_phase18_import_boundaries.py -v --tb=short
```
Expected: `test_entity_models_do_not_import_domain_services` PASSES.

Verify no runtime breakage from removing the TYPE_CHECKING imports:
```bash
python3 -m pytest tests/core/ -q --tb=short -m "not slow"
```

#### TYPE E — Pipeline ordering contract
```bash
python3 -m pytest tests/integrity/test_logic_guards.py::test_subsystem_order_documentation -v --tb=short
```
Expected: PASSES with updated `required_calls` list referencing `fused_strategic_pass`.

Verify ordering is still enforced (causal law not removed, just renamed):
```bash
python3 -m pytest tests/integrity/test_logic_guards.py -v --tb=short
```

#### TYPE F — Kernel warmup
```bash
python3 -m pytest tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard tests/integrity/test_logic_guards.py::test_resolution_phase_ordering_integrity -v --tb=long
```
Expected: both PASS after warmup fix is applied.

---

## Regression Guards

After all fixes, run the broader integrity + architecture suites to verify no new failures introduced:

```bash
python3 -m pytest tests/integrity/ tests/architecture/ tests/docs/ -q --tb=short
```

Also run the engine tests to confirm pipeline/kernel changes did not break simulation:
```bash
python3 -m pytest tests/engine/ -q --tb=short -m "not slow"
```

---

## Acceptance Criteria Checklist

- [ ] `tests/docs/test_doc_integrity.py` — all 5 tests PASS
- [ ] `tests/docs/test_contributor_guardrails.py::test_extension_templates_present` — PASS
- [ ] `tests/integrity/test_doc_guards.py::test_mandatory_doc_existence` — PASS
- [ ] `tests/integrity/test_parity_guards.py::test_oracle_artifact_existence` — PASS
- [ ] `tests/architecture/test_no_new_hardcoded_gameplay_truth.py::test_known_baseline_stale_guard` — PASS
- [ ] `tests/architecture/test_no_new_hardcoded_gameplay_truth.py::test_no_new_hardcoded_gameplay_ids_without_migration_map_entry` — still PASS (no regression)
- [ ] `tests/architecture/test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services` — PASS
- [ ] `tests/integrity/test_logic_guards.py::test_subsystem_order_documentation` — PASS
- [ ] `tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard` — PASS
- [ ] `tests/integrity/test_logic_guards.py::test_resolution_phase_ordering_integrity` — PASS
- [ ] No new failures in `tests/docs/`, `tests/integrity/`, `tests/architecture/`
- [ ] No regression in `tests/engine/` or `tests/core/`
