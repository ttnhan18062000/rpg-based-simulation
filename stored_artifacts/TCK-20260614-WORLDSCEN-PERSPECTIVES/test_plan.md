---
ticket_id: TCK-20260614-WORLDSCEN-PERSPECTIVES
phase: test_plan
date: 2026-06-15
---

# Test Plan: TCK-20260614-WORLDSCEN-PERSPECTIVES
## Wire WorldCompositionSpec.default_perspectives into CompileContext

---

## Regression Surface

The following existing tests are at risk and must remain green after implementation:

| Test | File | Risk |
|---|---|---|
| `test_compile_context_serialization` | `tests/unit/worldassembly/test_assembly.py` | `to_dict()` / `from_dict()` adds `perspectives` key — must handle missing key gracefully |
| `test_structural_world_assembly_resolver` | `tests/unit/worldassembly/test_assembly.py` | Assembly with no `default_perspectives` must still produce valid `CompileContext` |
| `test_resolved_bundle_includes_compile_context_and_preserves_profiles` | `tests/unit/worldassembly/test_assembly.py` | Bundle must still carry correct entity profiles |
| `test_v2_module_resolution_and_heuristics` | `tests/unit/worldassembly/test_assembly.py` | Composition with `default_perspectives: ["hero_view"]` (unknown ID) — currently passes because perspectives are silently ignored. After this ticket, it will raise `ResolverError`. **This test must be updated** to either use a known catalog perspective ID or remove the `default_perspectives` from that composition dict. |
| `test_composition_normalization_shorthand_and_mixed` | `tests/unit/worldassembly/test_assembly.py` | Uses `default_perspectives: ["hero_view"]` in the shorthand dict — tests normalisation only, not assembly. Safe. |
| `test_real_composition_normalization_preserves_perspectives` | `tests/unit/worldassembly/test_assembly.py` | Normalisation-only test, does not call `assemble()`. Safe. |
| `test_real_world_compositions_assembly` | `tests/integration/worldassembly/test_real_content_world_compositions.py` | `frontier_living_world.yaml` has `default_perspectives: ["hero_guild_perspective", "wild_beast_pack_perspective", "goblin_warband_perspective"]` — all three must resolve successfully from catalog |
| `test_cli_resolve_and_compile_integration` | `tests/unit/worldassembly/test_assembly.py` | CLI `handle_resolve` serialises `compile_context.json` via `to_dict()` — `perspectives` key must serialise cleanly |
| `test_scenario_setup_resolver_*` | `tests/integration/scenarios/test_scenario_setup_resolver.py` | `ScenarioSetupResolver` calls `_assembly_resolver.assemble()` — must still work end-to-end |

---

## New Tests Required

**New file:** `tests/unit/worldassembly/test_perspective_resolution.py`

### Test 1 — Known perspective resolves into CompileContext

```
def test_known_perspective_resolves_into_compile_context(repos):
```

- Build a `WorldCompositionSpec` with `default_perspectives=["hero_guild_perspective"]` and a valid module (e.g., `plains_layout + standard_villagers`).
- Call `WorldAssemblyResolver(cat, mod).assemble(composition)`.
- Assert `bundle.compile_context.perspectives` is a dict with key `"hero_guild_perspective"`.
- Assert the value has `chosen_faction == "hero_guild"` and `default_focus == "settlement_survival"`.
- Assert `bundle.compile_context.perspectives["hero_guild_perspective"]` is truthy.

### Test 2 — Unknown perspective ID raises ResolverError

```
def test_unknown_perspective_id_raises_resolver_error(repos):
```

- Build a `WorldCompositionSpec` with `default_perspectives=["nonexistent_perspective_xyz"]`.
- Call `WorldAssemblyResolver(cat, mod).assemble(composition)`.
- Assert `pytest.raises(ResolverError)` and that the error message contains `"nonexistent_perspective_xyz"`.

### Test 3 — Empty default_perspectives produces empty perspectives dict

```
def test_empty_default_perspectives_produces_empty_dict(repos):
```

- Build a `WorldCompositionSpec` with `default_perspectives=[]` (or omit the field entirely).
- Assert `bundle.compile_context.perspectives == {}`.
- Assert assembly completes without error.

### Test 4 — Multiple perspectives resolve correctly

```
def test_multiple_perspectives_all_resolve(repos):
```

- Build a composition with `default_perspectives=["hero_guild_perspective", "goblin_warband_perspective"]`.
- Assert both keys present in `compile_context.perspectives`.
- Assert each value carries the expected `chosen_faction` field from the catalog.

### Test 5 — Perspectives survive to_dict / from_dict round-trip

```
def test_perspectives_survive_serialization_roundtrip(repos):
```

- Assemble with `default_perspectives=["hero_guild_perspective"]`.
- Call `compile_context.to_dict()` → verify `"perspectives"` key present with one entry.
- Call `CompileContext.from_dict(serialized)` → verify `perspectives["hero_guild_perspective"]` round-trips with same `chosen_faction` value.

### Test 6 — CompileContext with no perspectives survives from_dict (backward compat)

```
def test_from_dict_tolerates_missing_perspectives_key():
```

- Build a raw dict (simulating an old serialised context) with `"entities": {}, "buildings": {}, ...` but NO `"perspectives"` key.
- Call `CompileContext.from_dict(raw_dict)`.
- Assert `ctx.perspectives == {}` — no `KeyError`.

### Test 7 — register_perspective method stores resolved def

```
def test_register_perspective_stores_resolved_def():
```

- Instantiate a bare `CompileContext()`.
- Call `ctx.register_perspective("test_persp", {"chosen_faction": "hero_guild", "default_focus": "test", "projected_labels": {}})`.
- Assert `ctx.perspectives["test_persp"]["chosen_faction"] == "hero_guild"`.

### Existing test requiring update — test_v2_module_resolution_and_heuristics

This test at line 529 of `tests/unit/worldassembly/test_assembly.py` uses:
```python
composition = {
    ...
    "default_perspectives": ["hero_view"]
}
```
`"hero_view"` does not exist in the catalog. After this ticket, `assemble()` will raise `ResolverError("perspective", "hero_view")`. The test must be updated: either remove `default_perspectives` from the dict, or change `"hero_view"` to a known catalog ID (`"hero_guild_perspective"`).

---

## Scoped Pytest Commands

Run the new unit test file alone:
```
pytest tests/unit/worldassembly/test_perspective_resolution.py -v
```

Run the full worldassembly unit and integration suites (regression check):
```
pytest tests/unit/worldassembly/ tests/integration/worldassembly/ -v -m "not slow"
```

Run scenario resolver integration tests (validates end-to-end with ScenarioSetupResolver):
```
pytest tests/integration/scenarios/test_scenario_setup_resolver.py -v
```

Full scoped run for the ticket domain:
```
pytest tests/unit/worldassembly/ tests/integration/worldassembly/ tests/integration/scenarios/ tests/unit/content/test_resolvers.py -v -m "not slow"
```

---

## Anti-Drift Guards

1. **Perspectives field must be in `to_dict()` output** — any test that captures `compile_context.to_dict()` and checks for exact key sets must be updated to include `"perspectives"`.
2. **`from_dict()` must use `.get("perspectives", {})`** — never `data["perspectives"]` — to avoid `KeyError` when deserialising context objects serialised before this ticket was implemented.
3. **`test_v2_module_resolution_and_heuristics` must be updated** before marking this ticket done — leaving `"hero_view"` in that composition dict will cause the test to fail with `ResolverError` after implementation.
4. **Do not add a perspectives check to `WorldAssemblyValidator`** — the `ResolverError` raised in `assemble()` is the enforcement point (WORLD-ASM-009). A validator check would duplicate logic and create a divergence risk.
5. **Parity ledger `SUBSTRATE-NEW-004`** must be added to `docs/parity_ledger/substrate.yaml` with `status: verified` only after the new test passes in CI.
