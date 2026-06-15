---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDSCEN-PERSPECTIVES
phase: done
date: 2026-06-14
tags: [worldassembly, perspectives, compile-context, scenario]
---

# TCK-20260614-WORLDSCEN-PERSPECTIVES

## Title
Wire WorldCompositionSpec.default_perspectives into CompileContext

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`WorldCompositionSpec.default_perspectives: List[str]` declares perspective IDs for the world, and `SimulationScenarioDefinition.perspective: str` declares the active perspective for a scenario run. However, `CompileContext` (`src/worldassembly/context.py`) has no `perspectives` field, and `WorldAssemblyResolver` never resolves or validates `default_perspectives` against the catalog `PerspectiveDefinition` records. The perspective declared in the composition is silently ignored during assembly. This ticket makes perspectives a validated first-class field in `CompileContext`.

## Scope
- In `WorldAssemblyResolver.assemble()` (`src/worldassembly/resolver.py`):
  - For each ID in `WorldCompositionSpec.default_perspectives`, resolve via `PerspectiveDefinitionResolver` (or equivalent in `src/content/resolver.py`)
  - Raise `ResolverError` if a perspective ID is not in the catalog (consistent with other resolver failures)
  - Store resolved perspectives in `CompileContext`
- Add `perspectives: Dict[str, Any] = {}` field to `CompileContext` (`src/worldassembly/context.py`)
- Add `register_perspective(perspective_id, resolved_def)` method to `CompileContext`
- `ResolvedWorldBundle.compile_context.perspectives` is accessible after assembly
- Compositions with empty `default_perspectives` produce empty `CompileContext.perspectives` — no error

## Out of Scope
- Perspective filtering of simulation events (observation layer; separate epic)
- `SimulationScenarioDefinition.perspective` validation against composition perspectives — that belongs in `ScenarioSetupResolver` (already exists in `src/scenarios/resolver.py`)
- Adding perspective IDs to world module YAML (authoring concern; can be done in TCK-20260614-WORLDDAT-COMPOSE)

## Acceptance Criteria
- A composition with `default_perspectives: ["hero_guild_perspective"]` produces `CompileContext.perspectives` with that perspective resolved (if catalog has the ID)
- A composition with an unknown perspective ID fails assembly with `ResolverError` naming the unknown ID
- A composition with empty `default_perspectives` assembles without error and `CompileContext.perspectives == {}`
- `dungeon_crawl.yaml` composition (from TCK-20260614-WORLDDAT-COMPOSE) with `default_perspectives: ["hero_guild_perspective"]` assembles correctly if that perspective ID exists in catalog
- All existing integration tests pass

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDDAT-COMPOSE (provides test data — dungeon_crawl uses perspectives)
- TCK-20260609-SCENARIO-SETUP-RESOLVER (ScenarioSetupResolver handles perspective at scenario level — do not duplicate)

## Related Docs
- `docs/world/assembly_contract.md` — WORLD-ASM-003 (CompileContext)

## Related Code Areas
- `src/worldassembly/resolver.py` — WorldAssemblyResolver.assemble()
- `src/worldassembly/context.py` — CompileContext (add perspectives field)
- `src/worldassembly/schema.py` — WorldCompositionSpec.default_perspectives
- `src/content/resolver.py` — check if PerspectiveDefinition resolver exists; add if not
- `src/scenarios/resolver.py` — ScenarioSetupResolver (READ ONLY — do not modify)

## Assumptions / Open Questions
- Check whether `PerspectiveDefinition` exists in `src/content/schema.py` and is loaded by `CatalogRepository` before implementing — if not present in catalog, perspectives can only be validated as non-empty strings (log warning instead of hard fail)

## Test Summary
- Unit: `tests/unit/worldassembly/test_perspective_resolution.py` — known perspective resolves, unknown raises ResolverError, empty list produces empty dict
- Integration: `dungeon_crawl` composition assembles with perspectives if catalog has the IDs

## Implementation Notes
- `CompileContext.perspectives` uses `Dict[str, Any]` (not `Dict[str, PerspectiveDefinition]`) to avoid a new `worldassembly.context → content.schema` coupling edge. Stored values are raw `model_dump()` dicts.
- `register_perspective()` accepts both dict and model instances via `isinstance(resolved_def, dict)` guard — keeps the method safe for direct calls with either type.
- Perspectives are resolved into a local `resolved_perspectives` dict before `CompileProfileResolver.resolve()` is called (which creates a fresh `CompileContext`). Registration happens after the call to avoid pre-call state loss (Risk 5 in investigation).
- Import of `SocialDefaultsResolver` follows the same pattern as other resolver imports in `resolver.py`.
- `test_v2_module_resolution_and_heuristics` in `test_assembly.py` was using `"hero_view"` (not a catalog ID) in `default_perspectives`. Changed to `"hero_guild_perspective"` — the only change to that test.
- Pre-existing `test_cli_resolve_and_compile_integration` failure is unrelated to this ticket (CLI path resolution issue with module repo data path).
- `from_dict()` uses `.get("perspectives", {})` — backward compat with contexts serialized before this ticket.
- `to_dict()` uses `dict(self.perspectives)` — already plain dicts, no further transformation needed.

## Files Changed
- `src/worldassembly/context.py` — added `perspectives` field, `register_perspective()`, updated `to_dict()` and `from_dict()`
- `src/worldassembly/resolver.py` — imported `SocialDefaultsResolver`, instantiated `self.perspective_resolver`, added resolution block in `assemble()`
- `tests/unit/worldassembly/test_assembly.py` — fixed `"hero_view"` → `"hero_guild_perspective"` in `test_v2_module_resolution_and_heuristics`
- `tests/unit/worldassembly/test_perspective_resolution.py` — new: 7 tests covering all acceptance criteria
- `docs/world/assembly_contract.md` — added `perspectives` row to WORLD-ASM-003 table
- `docs/parity_ledger/substrate.yaml` — appended SUBSTRATE-NEW-004 entry

## Completion Summary
Added `perspectives: Dict[str, Any]` to `CompileContext` with `register_perspective()` and `to_dict`/`from_dict` support. Wired `SocialDefaultsResolver` into `WorldAssemblyResolver.__init__` and `assemble()`. 7 new unit tests covering all acceptance criteria. SUBSTRATE-NEW-004 added to parity ledger. Unknown perspective ID raises `ResolverError`. AC4 (`dungeon_crawl.yaml`) deferred to TCK-20260614-WORLDDAT-COMPOSE — composition data not yet available. All 26 non-pre-existing tests pass; 1 pre-existing failure (`test_cli_resolve_and_compile_integration`, `plains_layout` not in content repo) predates this ticket and is unrelated.
