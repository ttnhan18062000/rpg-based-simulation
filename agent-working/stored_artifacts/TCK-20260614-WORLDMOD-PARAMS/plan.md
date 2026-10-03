---
ticket_id: TCK-20260614-WORLDMOD-PARAMS
phase: plan
date: 2026-06-15
---

# Implementation Plan: TCK-20260614-WORLDMOD-PARAMS
## Parameter expression engine with constraint validation for WorldModuleSpec

---

## Scope Guards (Mandatory — Do Not Violate)

- **No `eval()` on raw strings at any point.** All expression parsing must use `ast.parse()` + `ast.walk()` with an explicit node allow-list.
- **ast.walk safety check**: Any AST node not in `{ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub}` must raise `ValueError("Unsafe expression")` before any value is returned.
- **Touch only**: `src/worldmodules/evaluator.py` (new), `src/worldbuilding/recipe.py`, `src/worldassembly/resolver.py`, `tests/unit/worldmodules/test_parameter_evaluator.py` (new), `tests/integration/worldassembly/test_real_content_world_compositions.py`, `docs/world/modules_contract.md`, `docs/parity_ledger/substrate.yaml`.
- **Do not touch**: `src/quests/`, `src/combat/`, `src/economy/`, `src/strategy/`, `src/simulation/`, or any module outside `worldmodules/`, `worldassembly/`, `worldbuilding/recipe.py`.
- **Zero-param fast path**: Modules with `parameters: []` and `int`-typed count fields must take no evaluation overhead — `evaluate_field()` must return immediately on `isinstance(value, int)`.
- **Numeric count result**: `evaluate_field()` always returns `int` (truncate via `int(...)`, not `round()`). Float leaking into `PopulationSpec.count` / `ResourceNodeSpec.count` is a bug.
- **NormalizedWorldModule.parameters confirmed available**: `src/worldmodules/normalizer.py` L27 declares `parameters: List[ModuleParameterSpec]` and L141 passes it through — no normalizer change needed.
- **Building v1 recipe**: `bld.count` in `BuildingRecipeSpec` exists in schema but is **not used** in the v1 building loop in `assemble()` (L484–506) — each recipe produces exactly one `BuildingSpec` with no count loop. `evaluate_field()` must still be called on `bld.count` for completeness if the field is referenced anywhere, but note it does not drive a range loop in v1 (unlike resources). Do not add a count-loop for buildings in v1 — that would change existing behavior.

---

## Step-by-Step Implementation Order

### STEP 1 — Create `src/worldmodules/evaluator.py`

**Purpose**: Implement `AssemblyParameterError` and `ModuleParameterEvaluator`.

Note: `AssemblyParameterError` is defined in `evaluator.py` (co-located with the evaluator) and re-exported from `src/worldassembly/resolver.py` via import. The ticket scope note says "Define AssemblyParameterError in `src/worldassembly/resolver.py`" — the canonical home is `evaluator.py`; `resolver.py` imports it. This avoids a circular import.

**Contents**:

```
class AssemblyParameterError(ValueError):
    __init__(self, module_id: str, param_name: str, reason: str)
    # message: f"[{module_id}] parameter '{param_name}': {reason}"
    # attributes: self.module_id, self.param_name

class ModuleParameterEvaluator:
    __init__(
        self,
        param_specs: List[ModuleParameterSpec],
        injected: Dict[str, Any],
        module_id: str = "<unknown>"
    ) -> None

    def evaluate(self) -> Dict[str, Any]:
        # 1. Merge: resolved = {spec.name: spec.default for spec in param_specs}
        # 2. resolved.update(injected)
        # 3. For each spec:
        #    a. If required and resolved[spec.name] is None: raise AssemblyParameterError
        #    b. Validate allowed_values membership (skip if None)
        #    c. Validate min_value / max_value bounds (skip if None; only if value is numeric)
        #    d. Raise AssemblyParameterError on any violation with module_id and spec.name
        # 4. Return resolved (concrete typed values only)

    @staticmethod
    def evaluate_field(
        value: Union[int, float, str],
        resolved_params: Dict[str, Any]
    ) -> int:
        # Fast path: isinstance(value, int) → return value immediately
        # String path:
        #   Phase 1 — substitution: replace all {key} patterns from resolved_params
        #     - Use re.sub or str.format_map
        #     - Unresolved key → raise AssemblyParameterError (or KeyError wrapped as such)
        #   Phase 2 — arithmetic evaluation:
        #     - ast.parse(substituted, mode='eval')
        #     - ast.walk() — check every node; allow only:
        #         ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        #         ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub
        #     - Any other node type → raise ValueError("Unsafe expression: ...")
        #     - eval(compile(tree, '<expr>', 'eval')) — safe: tree already verified
        #       (this is safe because we walked and whitelisted every node above)
        #   Phase 3 — coerce: int(result) — truncation, not rounding
        # Return int
```

**Expression grammar** (implemented in `evaluate_field()`):
```
expression  := term (('+' | '-') term)*
term        := factor (('*' | '/') factor)*
factor      := NUMBER | '(' expression ')'
NUMBER      := integer or float literal (post-substitution)
```

Substitution phase replaces all `{key}` tokens with their numeric string representation before AST parsing. Non-numeric param types (string, boolean, enum, id_reference) in arithmetic context raise `AssemblyParameterError` if the resolved value cannot be coerced to a number.

---

### STEP 2 — Modify `src/worldbuilding/recipe.py`

**Purpose**: Allow count fields to carry string templates at YAML load time.

**Changes** (three models):

**`PopulationRecipeSpec`**:
- Change `count: int = Field(..., ge=0, ...)` to `count: Union[int, str] = Field(..., ...)`
- Remove `ge=0` from `Field(...)` (Pydantic `ge` does not apply to `str`)
- Add `@model_validator(mode="after")` that enforces `>= 0` only when `isinstance(self.count, int)`:
  ```python
  @model_validator(mode="after")
  def validate_count(self) -> "PopulationRecipeSpec":
      if isinstance(self.count, int) and self.count < 0:
          raise ValueError("count must be >= 0")
      return self
  ```

**`ResourceRecipeSpec`**:
- Change `count: int = Field(..., gt=0, ...)` to `count: Union[int, str] = Field(..., ...)`
- Add `@model_validator(mode="after")` enforcing `> 0` only when `isinstance(self.count, int)`.

**`BuildingRecipeSpec`**:
- Change `count: int = Field(..., gt=0, ...)` to `count: Union[int, str] = Field(..., ...)`
- Add `@model_validator(mode="after")` enforcing `> 0` only when `isinstance(self.count, int)`.

**Imports to add**: `Union` (already in `typing` import if present; add if not).

**Existing callers of `bld.count`**: The v1 building loop in `assemble()` does NOT use `bld.count` — each recipe produces one `BuildingSpec`. The `WorldTemplateExpander.expand()` in recipe.py uses `bld.count` in `range(bld.count)` (L214) — this is `WorldTemplateSpec.buildings`, not `WorldModuleSpec.building_recipes`. Template expansion uses plain integers; this code path is unaffected because `WorldTemplateSpec.buildings: List[BuildingRecipeSpec]` continues to receive validated integers from template YAML (not module YAML). No change needed to `WorldTemplateExpander`.

---

### STEP 3 — Wire evaluator into `src/worldassembly/resolver.py`

Three sub-steps:

**STEP 3a — Add import**

At the top of `resolver.py`, add:
```python
from src.worldmodules.evaluator import ModuleParameterEvaluator, AssemblyParameterError
```

**STEP 3b — Add constraint validation in `resolve_module_contribution()` (~L670)**

Immediately after the `param_vals is None` guard (L671) and before the region resolution loop (L679), insert:

```python
# Evaluate and validate parameters against declared ModuleParameterSpec constraints
if normalized_module.parameters:
    evaluator = ModuleParameterEvaluator(
        param_specs=list(normalized_module.parameters),
        injected=param_vals,
        module_id=normalized_module.module_id,
    )
    param_vals = evaluator.evaluate()  # returns resolved dict; raises AssemblyParameterError on violation
```

This fires for all modules (v1 recipe and v2 catalog path) and enforces required/constraints before any recipe field is read. Modules with `parameters: []` skip the evaluator body entirely (fast path).

**STEP 3c — Apply `evaluate_field()` in `assemble()` v1 recipe loops**

The three v1 recipe loops run in `assemble()` at L397–506. Wrap count fields before they are passed to Spec constructors:

1. **v1 population loop (~L409)**:
   ```python
   # Before:
   count=pop.count,
   # After:
   count=ModuleParameterEvaluator.evaluate_field(pop.count, param_vals),
   ```
   Also update the provenance `details` dict entry:
   ```python
   # details={"count": pop.count, ...}  →
   details={"count": ModuleParameterEvaluator.evaluate_field(pop.count, param_vals), ...}
   ```

2. **v1 resource loop (~L440–L444)**:
   ```python
   # Before:
   count=res.count,
   # After:
   count=ModuleParameterEvaluator.evaluate_field(res.count, param_vals),
   ```
   Also update provenance details entry.

3. **v1 building loop (~L484–L506)**:
   `bld.count` is in `BuildingRecipeSpec` but the v1 building loop does not pass `count` to `BuildingSpec` constructor (buildings are one-per-recipe). Call `evaluate_field()` defensively to surface any template errors early, but discard the result (it is not passed to `BuildingSpec`). The provenance `details` dict for buildings does not currently include count — no change needed there.

   If future code adds count-loop behavior for v1 buildings, `evaluate_field()` is already called and the result available.

---

### STEP 4 — New unit tests: `tests/unit/worldmodules/test_parameter_evaluator.py`

Create new file. All tests are pure unit tests — no file I/O, no repo access.

**Test groups** (exact test names from test_plan.md):

Group A — `evaluate_field()` arithmetic:
- `test_evaluate_field_integer_passthrough` — plain int 9 → returns 9
- `test_evaluate_field_simple_substitution` — `"{scale} * 3"` with `scale=3` → 9
- `test_evaluate_field_complex_expression` — `"{base} + {scale} * 2"` with `base=1, scale=3` → 7
- `test_evaluate_field_division_truncates` — `"{total} / {parts}"` with `total=7, parts=2` → 3 (int truncation)
- `test_evaluate_field_float_param_in_arithmetic` — `"{rate} * 4"` with `rate=2.5` → 10
- `test_evaluate_field_unary_minus` — `"-{offset} + 5"` with `offset=2` → 3
- `test_evaluate_field_valid_parentheses` — `"({scale} + 1) * 2"` with `scale=4` → 10

Group B — constraint validation raises `AssemblyParameterError`:
- `test_evaluate_raises_on_max_value_exceeded` — scale=10 vs max_value=5; assert module_id and "scale" in error str
- `test_evaluate_raises_on_min_value_exceeded` — scale=0 vs min_value=1
- `test_evaluate_raises_on_allowed_values_violation` — tier="ultra" not in ["low","med","high"]

Group C — required param enforcement:
- `test_evaluate_raises_required_param_missing` — required=True, no default, no injected value
- `test_evaluate_required_param_satisfied_by_default` — required=True, default=2, no override; resolved["scale"]==2
- `test_evaluate_required_param_satisfied_by_injected` — required=True, injected scale=4; no raise

Group D — zero-param fast paths:
- `test_evaluate_no_params_returns_empty` — param_specs=[], injected={} → evaluate() returns {}
- `test_evaluate_field_int_no_params_fast_path` — evaluate_field(5, {}) → 5, no exception

Group E — security / AST safety:
- `test_evaluate_field_rejects_function_call` — `"{x}.__class__.__name__"` → raises ValueError
- `test_evaluate_field_rejects_name_lookup` — `"os.getenv('SECRET')"` → raises (ValueError or KeyError, never executes)
- `test_evaluate_field_rejects_import` — `"__import__('os')"` → raises ValueError (unsafe AST node)
- `test_evaluate_field_rejects_attribute_access` — `"a.b"` with `a=1` → raises ValueError
- `test_evaluate_field_unresolved_key_raises` — `"{unknown_key} * 2"` with empty params → raises AssemblyParameterError or KeyError

Group F — end-to-end AC scenarios:
- `test_evaluate_full_ac1_scenario` — scale spec [min=1,max=5,default=1], injected scale=3, field="{scale}*3" → evaluate_field returns 9
- `test_evaluate_full_ac2_scenario` — same spec, injected scale=10 → evaluate() raises AssemblyParameterError

---

### STEP 5 — Extend integration tests in `tests/integration/worldassembly/test_real_content_world_compositions.py`

**Purpose**: Verify evaluator wires correctly through the full assembly pipeline.

Add three new tests (inject synthetic `WorldModuleSpec` via monkeypatch or in-memory stub repo — no new YAML files):

- `test_parametric_module_ref_overrides_count` — pop_count=5 injected; assert resolved PopulationSpec.count==5
- `test_parametric_module_ref_default_used_when_not_overridden` — no override; assert count==2 (default)
- `test_parametric_module_ref_constraint_violation_raises` — pop_count=99 vs max_value=10; assert raises AssemblyParameterError

Use minimal in-memory `WorldModuleRepository` subclass or `monkeypatch` on `get_module()` to avoid requiring new YAML fixtures.

Also verify existing test `test_real_world_compositions_assembly` (if it exists) still passes unchanged — it is the primary regression guard for the zero-param fast path.

---

### STEP 6 — Update `docs/world/modules_contract.md` WORLD-MOD-003 section

Add a subsection under WORLD-MOD-003 (ModuleParameterSpec) documenting:

1. **Expression Grammar**: The safe arithmetic subset (`+`, `-`, `*`, `/`, numeric literals, `{key}` substitution, parentheses). No function calls, no attribute access, no string concat beyond substitution.
2. **Evaluation Rules**:
   - Substitution phase: all `{key}` tokens replaced with resolved numeric values before AST parse.
   - Evaluation phase: `ast.parse()` + `ast.walk()` with explicit allow-list (no `eval()` on raw strings).
   - Coercion: result always `int` (truncation).
3. **Constraint Enforcement Order**: defaults merged → required check → allowed_values check → min/max check → evaluate_field on count field.
4. **AssemblyParameterError**: carries `module_id` and `param_name`; is a `ValueError` subclass.
5. **Zero-param modules**: `parameters: []` incurs no evaluation overhead.

---

### STEP 7 — Update `docs/parity_ledger/substrate.yaml`

Two changes:

**Change 1** — Update `SUBSTRATE-NEW-003`: Append to `v2_evidence`:
```
+ src/worldmodules/evaluator.py (ModuleParameterEvaluator — WORLD-MOD-003 constraint enforcement)
+ src/worldassembly/resolver.py (AssemblyParameterError + evaluate_field call sites in assemble())
+ TCK-20260614-WORLDMOD-PARAMS
```
Update `test_path` to append `tests/unit/worldmodules/test_parameter_evaluator.py`.

**Change 2** — Add new entry `SUBSTRATE-NEW-005` (append after SUBSTRATE-NEW-004):
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

---

## Dependency Order

```
STEP 1 (evaluator.py)
  └─► STEP 2 (recipe.py Union[int,str])  ← independent of step 1; can run in parallel
        └─► STEP 3a (resolver.py import)
              └─► STEP 3b (resolver.py constraint validation)
                    └─► STEP 3c (resolver.py evaluate_field call sites)
                          └─► STEP 4 (unit tests)
                                └─► STEP 5 (integration tests)
                                      └─► STEP 6 (docs update)
                                            └─► STEP 7 (parity ledger)
```

STEP 1 and STEP 2 are independent and can be done in either order or in parallel.
STEP 3 requires both STEP 1 and STEP 2 to be complete.
STEP 4 requires STEP 1 (can be written before STEP 3 but cannot pass until STEP 3 is wired).
STEP 5 requires STEPs 1–3 to be complete.
STEPs 6–7 are post-implementation documentation and can be done last.

---

## Unresolved Questions

1. **`WorldTemplateExpander` and `bld.count`**: `WorldTemplateExpander.expand()` (recipe.py L214) calls `range(bld.count)` on `BuildingRecipeSpec.count`. After the type change to `Union[int, str]`, if a template YAML ever places a string there, `range()` will raise `TypeError`. Template YAML is a separate path from module YAML — template YAML is not expected to carry parameter templates. Add a runtime guard in `WorldTemplateExpander.expand()` asserting `isinstance(bld.count, int)` before `range(bld.count)`, or add a note to module documentation that `Union[int, str]` in recipe specs is module-YAML-only and template YAML must use integer literals. **Recommendation**: Add the isinstance guard in `WorldTemplateExpander.expand()` for all three count fields (pop.count, res.count, bld.count) to surface the error clearly rather than as a TypeError.

2. **`evaluate_field()` on unresolved key**: The plan specifies this should raise `AssemblyParameterError`, but `evaluate_field()` is a `@staticmethod` with no `module_id` context. Decision needed: either accept a bare `KeyError` (which callers can catch and re-raise as `AssemblyParameterError`), or add an optional `module_id: str = "<unknown>"` parameter to `evaluate_field()`. **Recommendation**: Add optional `module_id` parameter so the error is traceable at the point of failure.

3. **`evaluate_field()` on non-numeric param type in arithmetic**: If a string-type parameter (e.g. `tier="low"`) is substituted into an arithmetic expression, `ast.parse()` will produce a `Constant` with a string value and the BinOp will raise `TypeError` at eval time. The plan should clarify: this TypeError should be caught and re-raised as `ValueError("Non-numeric value in arithmetic expression: ...")`. Confirm this is the desired behavior vs. letting it propagate as TypeError.

4. **Audit of `data/world_modules/` for `required: true` params**: Before merging STEP 3b, confirm no existing YAML module has `required: true` with no default and no injected value — such modules would newly fail assembly after this change. Run `grep -r "required: true" data/world_modules/` before wiring the evaluator call in `resolve_module_contribution()`.
