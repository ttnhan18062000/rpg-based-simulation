---
ticket_id: TCK-20260614-WORLDMOD-PARAMS
phase: test_plan
date: 2026-06-15
---

# Test Plan: TCK-20260614-WORLDMOD-PARAMS

## Regression Surface

Changes that could break existing tests:

| Changed artifact | Regression risk | Tests at risk |
|---|---|---|
| `src/worldbuilding/recipe.py` — `count: int` → `Union[int, str]` | Pydantic `ge=0`/`gt=0` validators may reject existing int values if validator logic is altered incorrectly | `tests/unit/worldmodules/test_modules.py`, `tests/integration/worldassembly/test_count_map_assembly.py` |
| `src/worldassembly/resolver.py` — new `AssemblyParameterError` + evaluator call in `assemble()` | Existing modules with `parameters: []` must be unaffected (zero-param fast path) | `tests/integration/worldassembly/test_real_content_world_compositions.py`, `test_real_content_world_modules.py` |
| `src/worldmodules/evaluator.py` — new module | Import-time failures would break resolver imports | All worldassembly integration tests |
| `src/worldmodules/normalizer.py` — add `parameters` field to `NormalizedWorldModule` if missing | Frozen dataclass change could break snapshot tests | `tests/unit/worldmodules/test_modules.py`, `test_real_module_normalized_snapshot.py` |

---

## New Tests Required (per Acceptance Criteria)

### File: `tests/unit/worldmodules/test_parameter_evaluator.py`

#### AC-1: Template substitution + arithmetic → correct count

```
test_evaluate_field_integer_passthrough
    value=9 (plain int), no params → returns 9
    Assert: isinstance(result, int)

test_evaluate_field_simple_substitution
    value="{scale} * 3", resolved_params={"scale": 3} → returns 9
    Assert: result == 9

test_evaluate_field_complex_expression
    value="{base} + {scale} * 2", resolved_params={"base": 1, "scale": 3} → returns 7
    Assert: result == 7

test_evaluate_field_division_truncates
    value="{total} / {parts}", resolved_params={"total": 7, "parts": 2} → returns 3
    Assert: result == 3 (floor, not round)

test_evaluate_field_float_param_in_arithmetic
    value="{rate} * 4", resolved_params={"rate": 2.5} → returns 10
    Assert: result == 10

test_evaluate_field_unary_minus
    value="-{offset} + 5", resolved_params={"offset": 2} → returns 3
    Assert: result == 3
```

#### AC-2: max_value constraint violation raises AssemblyParameterError

```
test_evaluate_raises_on_max_value_exceeded
    param_spec: {name: scale, type: integer, min_value: 1, max_value: 5}
    injected: {scale: 10}
    Assert: raises AssemblyParameterError naming module_id and "scale"
    Assert: "scale" in str(error) and module_id in str(error)

test_evaluate_raises_on_min_value_exceeded
    param_spec: {name: scale, type: integer, min_value: 1, max_value: 5}
    injected: {scale: 0}
    Assert: raises AssemblyParameterError

test_evaluate_raises_on_allowed_values_violation
    param_spec: {name: tier, type: string, allowed_values: ["low","med","high"]}
    injected: {tier: "ultra"}
    Assert: raises AssemblyParameterError
```

#### AC-3: required=True with no value supplied raises AssemblyParameterError

```
test_evaluate_raises_required_param_missing
    param_spec: {name: merchant_count, type: integer, required: True}
    injected: {} (no value, no default)
    Assert: raises AssemblyParameterError naming "merchant_count"

test_evaluate_required_param_satisfied_by_default
    param_spec: {name: scale, type: integer, required: True, default: 2}
    injected: {} (no override)
    Assert: does NOT raise; resolved["scale"] == 2

test_evaluate_required_param_satisfied_by_injected
    param_spec: {name: scale, type: integer, required: True}
    injected: {scale: 4}
    Assert: does NOT raise; resolved["scale"] == 4
```

#### AC-4: Modules with no parameters are unaffected

```
test_evaluate_no_params_returns_empty
    param_specs=[], injected={}
    Assert: evaluate() returns {}

test_evaluate_field_int_no_params_fast_path
    evaluate_field(5, {}) → 5 with no error
    Assert: result == 5; no exception raised
```

#### AC-5: No eval() — expression safety

```
test_evaluate_field_rejects_function_call
    value="{x}.__class__.__name__", resolved_params={"x": 1}
    Assert: raises ValueError (unsafe expression, not AssemblyParameterError)

test_evaluate_field_rejects_name_lookup
    value="os.getenv('SECRET')", resolved_params={}
    Assert: raises ValueError or KeyError (unresolved key, never executes)

test_evaluate_field_rejects_import
    value="__import__('os')", resolved_params={}
    Assert: raises ValueError (unsafe AST node)

test_evaluate_field_rejects_attribute_access
    value="a.b", resolved_params={"a": 1}
    Assert: raises ValueError (unsafe AST node — Attribute node not in allow-list)

test_evaluate_field_valid_parentheses
    value="({scale} + 1) * 2", resolved_params={"scale": 4}
    Assert: result == 10 (parenthesized subexpressions ARE allowed)
```

#### Additional edge cases

```
test_evaluate_field_unresolved_key_raises
    value="{unknown_key} * 2", resolved_params={}
    Assert: raises AssemblyParameterError (or KeyError surfaced as AssemblyParameterError)

test_evaluate_full_ac1_scenario
    param_specs: [{name: scale, type: integer, default: 1, min_value: 1, max_value: 5}]
    injected: {scale: 3}
    recipe field value: "{scale} * 3"
    Assert: evaluate() succeeds; evaluate_field("{scale} * 3", resolved) == 9

test_evaluate_full_ac2_scenario
    Same specs, injected: {scale: 10}
    Assert: evaluate() raises AssemblyParameterError with module_id and "scale"
```

---

### File: `tests/integration/worldassembly/test_real_content_world_compositions.py`

#### Extend existing suite with parametric assembly test

```
test_parametric_module_ref_overrides_count (new test)
    Build a synthetic WorldModuleSpec with:
        parameters: [{name: pop_count, type: integer, default: 2, min_value: 1, max_value: 10}]
        population_recipes: [PopulationRecipeSpec(role=..., count="{pop_count}", faction=..., spawn_region=...)]
    Build a ModuleRefSpec with parameters: {pop_count: 5}
    Assemble via WorldAssemblyResolver
    Assert: resolved PopulationSpec.count == 5

test_parametric_module_ref_default_used_when_not_overridden (new test)
    Same module spec, ModuleRefSpec with parameters: {} (no override)
    Assert: resolved PopulationSpec.count == 2 (default)

test_parametric_module_ref_constraint_violation_raises (new test)
    Same module spec, ModuleRefSpec with parameters: {pop_count: 99} (exceeds max_value=10)
    Assert: raises AssemblyParameterError
```

#### Note on synthetic module injection

These tests must bypass `WorldModuleRepository` file loading and inject the parametric `WorldModuleSpec` directly into a mock/stub repo to avoid requiring new YAML files. Use a minimal in-memory `WorldModuleRepository` subclass or monkeypatch `get_module()`.

---

## Scoped Pytest Commands

Run only the domains touched by this ticket:

```bash
# Unit tests — evaluator (new file)
pytest tests/unit/worldmodules/test_parameter_evaluator.py -v

# Unit tests — existing worldmodules suite (regression guard)
pytest tests/unit/worldmodules/ -v

# Integration tests — world assembly (regression guard + new parametric tests)
pytest tests/integration/worldassembly/ -v

# Full scoped run (all touched domains, excludes slow)
pytest tests/unit/worldmodules/ tests/integration/worldassembly/ -v -m "not slow"
```

Do NOT run the full suite (`pytest tests/`). Scope to the above.

---

## Anti-Drift Guards

These tests protect architectural boundaries that must not regress:

| Guard | What it verifies | Test |
|---|---|---|
| No `eval()` on raw strings | AST-only evaluation; function calls and attribute access are rejected | `test_evaluate_field_rejects_function_call`, `test_evaluate_field_rejects_import`, `test_evaluate_field_rejects_attribute_access` |
| Zero-param fast path | Modules with `parameters: []` incur no evaluation overhead and no exception | `test_evaluate_no_params_returns_empty`, `test_evaluate_field_int_no_params_fast_path` |
| AssemblyParameterError carries module_id and param_name | Error is traceable to exact source | `test_evaluate_raises_on_max_value_exceeded` (assert both fields in error string) |
| Count field result is always `int` | No float leaks into `PopulationSpec.count`/`ResourceNodeSpec.count` which require int | `test_evaluate_field_division_truncates`, `test_evaluate_field_float_param_in_arithmetic` |
| Required param with no value AND no default raises before recipe fields are read | Prevents silent `None` passed to `evaluate_field()` | `test_evaluate_raises_required_param_missing` |
| Existing real-content assembly is unaffected | All current modules have `parameters: []`; assemble() must still pass | `tests/integration/worldassembly/test_real_content_world_compositions.py::test_real_world_compositions_assembly` (existing, must pass unchanged) |

---

## Parity Ledger Entries to Update

After implementation, update `docs/parity_ledger/substrate.yaml`:

1. **SUBSTRATE-NEW-003** — currently covers WORLD-MOD normalization and assembly. Append to `v2_evidence`:
   ```
   + src/worldmodules/evaluator.py (ModuleParameterEvaluator — WORLD-MOD-003 constraint enforcement)
   + src/worldassembly/resolver.py (AssemblyParameterError + evaluate_field call sites in assemble())
   + TCK-20260614-WORLDMOD-PARAMS
   ```
   Update `test_path` to include `tests/unit/worldmodules/test_parameter_evaluator.py`.

2. **Add new entry SUBSTRATE-NEW-005** (append after SUBSTRATE-NEW-004):
   ```yaml
   - id: SUBSTRATE-NEW-005
     text: >
       ModuleParameterEvaluator (WORLD-MOD-003) enforces ModuleParameterSpec constraints
       at assembly time: required params with no value raise AssemblyParameterError,
       allowed_values/min_value/max_value violations raise AssemblyParameterError naming
       module_id and param_name. Recipe count fields declared as "{key} * N" string
       templates are substituted from resolved param values and evaluated via AST-only
       arithmetic (no eval()). Modules with parameters: [] are zero-overhead fast path.
     status: verified
     priority: P1
     legacy_evidence: null
     v2_evidence: >
       src/worldmodules/evaluator.py +
       src/worldassembly/resolver.py (AssemblyParameterError) +
       src/worldbuilding/recipe.py (Union[int, str] count fields) +
       docs/world/modules_contract.md (WORLD-MOD-003)
     proof_type: null
     test_path: tests/unit/worldmodules/test_parameter_evaluator.py
     divergence_note: null
     support_boundary: "WorldModules — world setup preprocessing only, not tick-path."
   ```
