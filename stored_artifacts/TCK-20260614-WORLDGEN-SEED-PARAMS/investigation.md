# Investigation — TCK-20260614-WORLDGEN-SEED-PARAMS

## Findings

### ProceduralCompositionGenerator.generate() (src/worldgeneration/generator.py)

- Module selection produces `selected_ids: list[str]` in deterministic rank order (score desc, module_id tie-break).
- After selection, `module_refs` is built as a list comprehension with no parameter sampling — all `parameters={}` (empty dict).
- `random` is already imported at the top of the file.

### ModuleParameterSpec (src/worldmodules/schema.py, line 16-43)

Fields relevant to sampling:
- `type: str` — validated to one of: `{"string","integer","float","boolean","enum","id_reference"}`
- `default: Optional[Any]`
- `allowed_values: Optional[List[Any]]`
- `min_value: Optional[Union[int, float]]`
- `max_value: Optional[Union[int, float]]`

Sampling priority:
1. `allowed_values` non-empty → `rng.choice(allowed_values)`
2. `min_value` and `max_value` both present → integer: `rng.randint(int(min), int(max))`; float: `rng.uniform(float(min), float(max))`
3. Else → use `default` unchanged (no rng call)

### ModuleRefSpec (src/worldassembly/schema.py, line 10-18)

- `parameters: Dict[str, Any]` — accepts any key-value dict. This is where sampled values go.

### RNG invariant

- `rng = random.Random(intent.seed)` must be initialized **before** the parameter sampling loop.
- Iteration order: `selected_ids` list order (rank order), then `module.parameters` list order (schema declaration order).
- This guarantees identical call sequence for same seed + same modules.

### Key risk

The existing `WorldProceduralGenerator.generate()` also uses `random.Random(intent.seed)` but that is a separate class — no conflict. `ProceduralCompositionGenerator` does not currently call `random.Random` at all.
