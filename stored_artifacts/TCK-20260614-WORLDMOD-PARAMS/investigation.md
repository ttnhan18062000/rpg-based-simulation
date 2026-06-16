---
ticket_id: TCK-20260614-WORLDMOD-PARAMS
phase: investigation
date: 2026-06-15
---

# Investigation: TCK-20260614-WORLDMOD-PARAMS

## Current State

### ModuleParameterSpec (file:line)

`src/worldmodules/schema.py:L15–L42`

Frozen Pydantic model (`extra="forbid"`). All fields:

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | `str` (min_length=1) | required | Parameter identifier |
| `type` | `str` | required | Validated against `{"string","integer","float","boolean","enum","id_reference"}` by `@field_validator` |
| `default` | `Optional[Any]` | `None` | If set with `allowed_values`, must appear in that list |
| `required` | `bool` | `False` | Mandatory supply flag |
| `allowed_values` | `Optional[List[Any]]` | `None` | Enumerated constraint |
| `min_value` | `Optional[Union[int, float]]` | `None` | Numeric lower bound |
| `max_value` | `Optional[Union[int, float]]` | `None` | Numeric upper bound |
| `description` | `Optional[str]` | `None` | Human-readable label |

`@model_validator(mode="after")` cross-checks `default` in `allowed_values` if both are set. No min/max cross-validation exists today.

### ModuleRefSpec.parameters (file:line)

`src/worldassembly/schema.py:L17`

```python
parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom parameter override values")
```

Plain `Dict[str, Any]` — no type coercion, no constraint checking at schema construction time. Overrides are caller-supplied raw values.

### Parameter Handling in assemble() (file:line)

`src/worldassembly/resolver.py:L283–L288`

```python
# Inject parameters values into recipes (Basic parameter injection)
param_vals = {p.name: p.default for p in spec.parameters}
param_vals.update(ref.parameters)

# Resolve using component resolvers
contribution = self.resolve_module_contribution(spec, prefix, param_vals)
```

`param_vals` is built correctly: defaults first, then caller overrides. It is passed as the third argument to `resolve_module_contribution()`.

### resolve_module_contribution() — parameter usage (file:line)

`src/worldassembly/resolver.py:L660–L800`

`param_vals` is accepted as the third argument (`param_vals: Dict[str, Any] = None`) and used **only** for provenance recording (`ProvenanceRecord.parameters=param_vals` at lines ~309, ~325, ~393, ~429, ~453, ~479, ~530, ~550). It is **never applied to any recipe field value**. All recipe field reads (`res.count`, `pop.count`, `bld.count`) go directly to the frozen Pydantic model field — no substitution step exists.

### Recipe count fields (file:line)

`src/worldbuilding/recipe.py:L35, L48, L58`

- `PopulationRecipeSpec.count: int` — `ge=0`, strictly typed `int`.
- `ResourceRecipeSpec.count: int` — `gt=0`, strictly typed `int`.
- `BuildingRecipeSpec.count: int` — `gt=0`, strictly typed `int`.

All three are frozen Pydantic models with `extra="forbid"`. A YAML value of `"{merchant_count}"` or `"{base} + {scale} * 2"` would currently fail Pydantic validation at `WorldModuleSpec` construction time because `count` only accepts `int`. This means template strings in YAML cannot even be loaded today — the schema does not yet have `Union[int, str]` for count fields.

### Existing evaluator.py

`ls src/worldmodules/` output: `__pycache__`, `normalizer.py`, `repository.py`, `schema.py`, `utils.py`

**No `evaluator.py` exists.** The file must be created from scratch.

### Where a template string lands today

If a module YAML were written with `count: "{merchant_count}"`, Pydantic would raise `ValidationError` on `ResourceRecipeSpec` (or `PopulationRecipeSpec`/`BuildingRecipeSpec`) because `count` is `int` and the string fails coercion. The template string never reaches `resolve_module_contribution()`. The recipe field type change to `Union[int, str]` is a prerequisite for loading template-bearing modules.

---

## Gap

1. **No `ModuleParameterEvaluator`** — `src/worldmodules/evaluator.py` does not exist.
2. **No `AssemblyParameterError`** — not defined anywhere; must be added to `src/worldassembly/resolver.py`.
3. **No constraint validation** — `min_value`/`max_value`/`allowed_values` on `ModuleParameterSpec` are stored but never enforced against injected values.
4. **No required-param enforcement** — `required: true` parameters are silently satisfied by `None` default today; no `ValueError` is raised.
5. **No expression evaluation** — `param_vals` is assembled but never substituted into recipe field values inside `resolve_module_contribution()`.
6. **Recipe count fields are `int`-only** — `PopulationRecipeSpec.count`, `ResourceRecipeSpec.count`, `BuildingRecipeSpec.count` use strict `int` fields. To accept `"{scale} * 3"` in YAML the field type must become `Union[int, str]`; evaluated value must be an `int` before the frozen Pydantic object is constructed or the recipe field is read.

---

## Key Changes Required

### 1. New file: `src/worldmodules/evaluator.py`

Class `ModuleParameterEvaluator`:

```
__init__(self, param_specs: List[ModuleParameterSpec], injected: Dict[str, Any]) -> None
evaluate(self) -> Dict[str, Any]
    - merge: resolved = {spec.name: spec.default for spec in param_specs}; resolved.update(injected)
    - enforce required: for each spec where required=True and resolved[name] is None → raise AssemblyParameterError
    - validate constraints per spec: allowed_values, min_value, max_value → raise AssemblyParameterError on violation
    - return resolved (concrete typed values only — no template strings remain)
```

Static helper `evaluate_field(value: Union[int, str], resolved_params: Dict[str, Any]) -> int`:
- If `value` is already `int`: return as-is (no-param-module fast path).
- If `value` is `str`: perform `{key}` substitution from `resolved_params`, then evaluate the resulting arithmetic expression using `ast.literal_eval` on a safe parsed form (see Expression Grammar below).
- Return must be `int` (truncate floats if needed; recipe fields require int).

### 2. New exception: `AssemblyParameterError(ValueError)` in `src/worldassembly/resolver.py`

```python
class AssemblyParameterError(ValueError):
    def __init__(self, module_id: str, param_name: str, reason: str):
        super().__init__(f"[{module_id}] parameter '{param_name}': {reason}")
        self.module_id = module_id
        self.param_name = param_name
```

### 3. Call site: `resolve_module_contribution()` — parameter evaluation before recipe field reads

The evaluator plugs in at `src/worldassembly/resolver.py:L670` — the top of `resolve_module_contribution()`, immediately after the `param_vals is None` guard:

```python
# Evaluate and validate parameters (new — replaces raw param_vals pass-through)
from src.worldmodules.evaluator import ModuleParameterEvaluator
evaluator = ModuleParameterEvaluator(
    param_specs=list(normalized_module.parameters),   # from NormalizedWorldModule
    injected=param_vals or {},
    module_id=normalized_module.module_id,
)
resolved_params = evaluator.evaluate()
```

Then every `res.count`, `pop.count`, `bld.count` read in the body of `resolve_module_contribution()` becomes:

```python
from src.worldmodules.evaluator import ModuleParameterEvaluator
count = ModuleParameterEvaluator.evaluate_field(res.count, resolved_params)
```

The exact recipe field read sites in `resolve_module_contribution()` that must be wrapped:
- `L782–L784`: `resource_refs[res_id] = count` (count-map resources) — but these come from `NormalizedWorldModule.resources` which is already `Dict[str, int]`; template strings only appear in `population_recipes`/`resource_recipes`/`building_recipes` (the v1 recipe list fields).
- The v1 recipe fields (`spec.population_recipes`, `spec.resource_recipes`, `spec.building_recipes`) are iterated in `assemble()` at L398–L506, not in `resolve_module_contribution()`. These loops also need `evaluate_field()` wrapping.

**Correction from direct code read**: The v1 recipe loops (`spec.population_recipes`, `spec.resource_recipes`, `spec.building_recipes`) run inside `assemble()` directly (L398–L506), not inside `resolve_module_contribution()`. The correct plug-in points are therefore:
- `assemble()` L409: `count=pop.count` → `count=evaluate_field(pop.count, param_vals)`
- `assemble()` L440–L444`: `count=res.count` → `count=evaluate_field(res.count, param_vals)`
- `assemble()` L492`: `count=bld.count` (implicitly through `bld.building_type`) — building count is in `BuildingRecipeSpec.count`, used only as loop range at L509 in the count-map path.
- `resolve_module_contribution()` (for the v2 population count path): `L768` `count=count` in `PopulationSpec(count=count, ...)` — this count comes from `expanded_archetypes`, not from recipe field directly.

The primary substitution target is therefore the v1 recipe loops in `assemble()`. `resolve_module_contribution()` should also call the evaluator to enforce required/constraint validation even for modules that use v2 catalog refs (no substitution needed, but validation still fires).

### 4. Recipe schema change: `Union[int, str]` for count fields

`src/worldbuilding/recipe.py:L35, L48, L58` — change `count: int` to `count: Union[int, str]` with a note that string values are parameter templates resolved at assembly time. Keep `ge=0` / `gt=0` validator on the int path only (move to `@model_validator` or use `@field_validator` with type branching).

### 5. NormalizedWorldModule — parameters pass-through

`src/worldmodules/normalizer.py` — `NormalizedWorldModule` must expose the `parameters: List[ModuleParameterSpec]` field so `resolve_module_contribution()` can access the declared spec list. Verify this is already present or add it.

---

## Expression Grammar

Safe subset to implement in `evaluator.py` using Python's `ast` module:

```
expression  := term (('+' | '-') term)*
term        := factor (('*' | '/') factor)*
factor      := NUMBER | '(' expression ')'
NUMBER      := integer literal | float literal (after {key} substitution)
```

- **Substitution phase**: Replace all `{key}` patterns with their string-cast numeric value from `resolved_params`. Unresolved keys → `AssemblyParameterError`.
- **Evaluation phase**: Parse substituted string with `ast.parse(expr, mode='eval')`. Walk the AST; allow only `ast.Expression`, `ast.BinOp`, `ast.UnaryOp`, `ast.Constant`, and the operators `Add`, `Sub`, `Mult`, `Div`, `UAdd`, `USub`. Any other node type raises `ValueError("Unsafe expression")`.
- **No `eval()`** on raw strings at any point.
- Result is cast to `int` (truncate, not round) before being used as a recipe count.

This grammar intentionally excludes: function calls, attribute access, subscripts, comparisons, boolean ops, string concatenation, and any name lookup beyond the pre-substituted numeric values.

---

## Risks / Anti-Drift

| Risk | Mitigation |
|---|---|
| Recipe count `Union[int, str]` breaks Pydantic `ge=0`/`gt=0` validators (which require int) | Move bound validation to `@model_validator(mode="after")` with isinstance branch; string fields skip bound check at schema load time |
| `NormalizedWorldModule` does not carry `parameters` field (normalizer strips it) | Verify `normalizer.py` — if `parameters` is not in `NormalizedWorldModule`, add it as `parameters: List[ModuleParameterSpec]` passthrough |
| `evaluate_field()` called on count-map `Dict[str,int]` values (already int, no substitution) | `evaluate_field()` fast-path returns `int` immediately when `isinstance(value, int)` |
| `AssemblyParameterError` raised inside `resolve_module_contribution()` surfaced as generic `ValueError` by callers | Exception is `ValueError` subclass — existing `ValueError` catches in `assemble()` still work; no silent swallowing |
| Integration test `test_real_world_compositions_assembly` breaks if existing modules declare `required: true` params with no default and no injected value | Audit all YAML in `data/world_modules/` for `required: true` params before merging |
| Float result from `/` division coerced to `int` silently truncates | Document truncation behavior; add test with explicit division expression |
| `{key}` substitution on non-numeric param types (e.g. `type: string`) in arithmetic context | Evaluator must type-check resolved value is numeric before substitution into arithmetic expression; raise `AssemblyParameterError` if `type` is not `integer`/`float` and the field is a count |
