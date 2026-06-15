---
status: done
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-PARAMS
phase: open
date: 2026-06-14
tags: [worldmodules, parameters, expression, validation]
---

# TCK-20260614-WORLDMOD-PARAMS

## Title
Parameter expression engine with constraint validation for WorldModuleSpec

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ModuleParameterSpec` in `src/worldmodules/schema.py` defines `name`, `type`, `default`, `required`, `allowed_values`, `min_value`, `max_value` — a complete parameter contract. However, `WorldAssemblyResolver.resolve_module_contribution()` collects parameter values from `ModuleRefSpec.parameters` and stores them in provenance, but never substitutes them into module recipe field values. Parameters are schema decoration today. This ticket makes them functional: recipe field values like `"{base} + {scale} * 2"` evaluate to real numbers at assembly time.

## Scope
- Implement `ModuleParameterEvaluator` in `src/worldmodules/` (new file `evaluator.py`):
  - Accept a module's declared `parameters: List[ModuleParameterSpec]` and injected values from `ModuleRefSpec.parameters`
  - Fill missing values from `default`; raise `ValueError` for `required` params with no value
  - Support `{key}` substitution for string interpolation and arithmetic expressions: `+`, `-`, `*`, `/`, integer/float literals
  - Use Python `ast.literal_eval` or a safe restricted evaluator — no `eval()` on raw strings
  - Validate injected values against constraints: `allowed_values`, `min_value`, `max_value`; raise `AssemblyParameterError` with module_id and param name on violation
- Call `ModuleParameterEvaluator.evaluate()` inside `WorldAssemblyResolver.resolve_module_contribution()` before recipe fields are used
- Apply evaluated values to recipe count fields (e.g. `PopulationRecipeSpec.count`, `ResourceRecipeSpec.count`) where the YAML value is a string template
- Define `AssemblyParameterError(ValueError)` in `src/worldassembly/resolver.py`

## Out of Scope
- Dynamic Jinja2 templating or arbitrary Python execution
- Parameter inheritance between modules
- GUI or CLI parameter prompting

## Acceptance Criteria
- A module with `parameters: [{name: scale, type: integer, default: 1, min_value: 1, max_value: 5}]` and a recipe field `count: "{scale} * 3"` produces `count=9` when assembled with `parameters: {scale: 3}`
- Assembling with `scale=10` (exceeds max_value=5) raises `AssemblyParameterError` naming the module and parameter
- A `required: true` parameter with no value supplied raises `AssemblyParameterError`
- Modules with no parameters are unaffected (no performance change)
- `ModuleParameterEvaluator` uses no `eval()` — expression parsing is safe

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite — unified schema first)
- TCK-20260614-WORLDGEN-SEED-PARAMS (uses this — seed-based param randomization)
- TCK-20260614-WORLDDAT-NEWMODS (validates this — scalable_bandit_camp module uses params)

## Related Docs
- `docs/world/modules_contract.md` — WORLD-MOD-003 (ModuleParameterSpec)
- `docs/world/assembly_contract.md`

## Related Code Areas
- `src/worldmodules/schema.py` — ModuleParameterSpec (L15), WorldModuleSpec
- `src/worldmodules/evaluator.py` — new file
- `src/worldassembly/resolver.py` — resolve_module_contribution(), WorldAssemblyResolver.__init__()
- `src/worldassembly/schema.py` — ModuleRefSpec.parameters field

## Assumptions / Open Questions
- Recipe fields that are integers today become `Union[int, str]` to support template strings — confirm pydantic model changes needed in `WorldModuleSpec`
- Expression evaluator only handles arithmetic on numeric values; string interpolation (`{key}`) is separate substitution pass before arithmetic evaluation

## Test Summary
- Unit: `tests/unit/worldmodules/test_parameter_evaluator.py` — expression evaluation, constraint validation, required param missing, no-param modules unaffected
- Integration: extend `tests/integration/worldassembly/test_real_content_world_compositions.py` to use a composition with parametric module refs

## Implementation Notes
- `AssemblyParameterError` defined in `src/worldmodules/evaluator.py` (not `resolver.py`) to avoid circular import; imported into `resolver.py`.
- `evaluate_field()` is a `@staticmethod` with optional `module_id` and `field_name` params for error traceability.
- `WorldAssemblyValidator` count field reads wrapped with `evaluate_field(count, {})` so string counts surface as clear `ValueError` during validation, not Pydantic errors.
- `WorldTemplateExpander.expand()` adds `isinstance(count, int)` guards for `res.count` and `bld.count` — template YAML must use integer literals, module YAML may use expressions.
- `PopulationRecipeSpec.count` uses `ge=0` moved to `@model_validator`; `ResourceRecipeSpec.count` and `BuildingRecipeSpec.count` use `gt=0` moved to `@model_validator` — all with `isinstance(self.count, int)` guards.
- v1 population loop: `pop.count` → `evaluate_field(pop.count, param_vals, m_id, "count")`.
- v1 resource loop: `res.count` → `evaluate_field(res.count, param_vals, m_id, "count")`.
- v1 building loop: `evaluate_field(bld.count, param_vals, m_id, "count")` called defensively (result not used in v1 since buildings produce one-per-recipe).

## Files Changed
- `src/worldmodules/evaluator.py` (new)
- `src/worldbuilding/recipe.py` (Union[int, str] count fields + isinstance guards in WorldTemplateExpander)
- `src/worldassembly/resolver.py` (import + resolve_module_contribution constraint validation + evaluate_field call sites + WorldAssemblyValidator wraps)
- `tests/unit/worldmodules/test_parameter_evaluator.py` (new — 22 tests)
- `tests/integration/worldassembly/test_real_content_world_compositions.py` (3 new parametric tests)
- `docs/world/modules_contract.md` (WORLD-MOD-003 expression grammar section)
- `docs/parity_ledger/substrate.yaml` (SUBSTRATE-NEW-003 updated, SUBSTRATE-NEW-005 added)

## Completion Summary
Implemented `ModuleParameterEvaluator` with AST-safe arithmetic expression evaluation, `Union[int, str]` recipe count fields in all three recipe specs, constraint validation wired into `WorldAssemblyResolver.resolve_module_contribution()`, and `isinstance` guards in `WorldTemplateExpander`. 22 unit tests + 3 integration tests pass. SUBSTRATE-NEW-005 added to parity ledger; SUBSTRATE-NEW-003 v2_evidence updated. 1 pre-existing test failure (`test_cli_resolve_and_compile_integration`) confirmed unrelated — `plains_layout` not found in module repo, failed identically on the unmodified branch.
