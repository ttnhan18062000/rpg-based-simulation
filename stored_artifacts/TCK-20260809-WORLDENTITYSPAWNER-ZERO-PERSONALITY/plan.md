---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY

## Chosen approach
Thread the seed `CatalogScenarioStateBuilder.build()` already accepts (`seed: int = 42`) down
through `WorldEntitySpawner.spawn_from_context()` → `ArchetypeEntityFactory.build_entity()` (and
the legacy-guard path), reusing this session's own already-shipped, data-driven bravery-bias/
ActionStyle mechanism — extracted into a new shared module first to avoid a backward architecture
dependency (see investigation.md).

## Step 1: extract shared personality-bias helpers (pure refactor, no behavior change)
Move `_PERSONALITY_BIAS_FALLBACK`, `_personality_bias_cache`, `_load_personality_bias_config()`,
`get_bravery_bias()`, `get_action_style_for_bravery()` from `src/worldbuilding/compiler.py` into
a new `src/content_semantics/personality.py`, matching this repo's own established precedent for
cross-cutting semantic helpers (`content_semantics/faction.py`, `relation.py`, `role.py`).
`compiler.py` imports the 3 public functions from the new module instead of defining them —
zero behavior change to its own already-verified, already-shipped callers.

## Step 2: seed personality/ActionStyle in `ArchetypeEntityFactory.build_entity()`
Add `seed: int = 42` parameter (default matches `CatalogScenarioStateBuilder`'s own existing
default exactly — backward-compatible for all 12 existing direct-call tests). Compute
`PersonalityComponent` via `DeterministicRNG(seed)`, using the exact same `Domain.WORLD`/
`sub_id` convention `WorldCompiler.compile()` already uses (10=greed, 11=bravery, 12=sociability,
13=industry), bias bravery via `get_bravery_bias(contract.faction_id)`, clamp to `[0.0, 1.0]`.
Set `action_style=get_action_style_for_bravery(bravery)` in the existing `.combat(...)` builder
call. Add `.identity(personality=personality)` to the existing `.identity(...)` call.

## Step 3: thread the seed through `WorldEntitySpawner`
Add `seed: int = 42` to `spawn_from_context()`'s own signature, pass through `_spawn_one()` →
`_spawn_archetype_native()` → `self._factory.build_entity(entity_id, contract, spawn, seed)`.
Also apply the identical personality/ActionStyle logic in `_spawn_legacy_guard()` (its own
`V2EntityBuilder` chain), so both real construction branches get real personality, not just the
archetype-native one.

## Step 4: wire `CatalogScenarioStateBuilder`'s own already-existing seed through
`self._spawner.spawn_from_context(setup.world_bundle.compile_context, self._catalog, seed=seed)`
— a 1-line change, since the seed parameter already exists on `build()`.

## Step 5: correct `docs/world/assembly_contract.md`'s own now-inaccurate "no randomness" claim.

## Rejected alternatives
- **Import `compiler.py`'s helpers directly into `archetype_factory.py`**: rejected —
  architecturally backward (a foundational `entities/` module depending on a specific
  `worldbuilding` compiler), and `src/content_semantics/` is this repo's own established, correct
  home for exactly this kind of shared helper.
- **Duplicate the bias logic in `archetype_factory.py`**: rejected — real drift risk (2 copies of
  the same bias table diverging over time), no benefit over a shared module.
- **Generate a fresh random seed per spawn instead of threading one through**: rejected — would
  violate the real, existing determinism contract this whole subsystem is built around
  (`docs/world/assembly_contract.md`'s own "bit-identical given the same inputs" guarantee) — the
  fix must remain deterministic given (CompileContext, base_entity_id, seed), not become
  non-deterministic.

## Verification plan
- Real unit tests for the new `src/content_semantics/personality.py` module's own public API
  (mirroring the sibling tests already added for `compiler.py`'s own version this session).
- Real tests confirming `ArchetypeEntityFactory.build_entity()` now produces non-zero,
  faction-correlated personality and non-default `action_style`.
- Real tests confirming determinism is preserved: same `(entity_id, contract, spawn, seed)` →
  bit-identical personality across repeated calls.
- Full existing scoped test suite re-run unmodified (`tests/unit/entities/`,
  `tests/integration/entities/`, `tests/integration/worldassembly/`,
  `tests/unit/certification/`, `tests/integration/certification/`) to confirm zero regressions.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms zero-current-impact finding | Confirmed still accurate — this ticket's own fix doesn't change which real pipeline calls this path |
| Real fix lands: entities get real, race-correlated personality | Done — steps 1-4 |
| Scoped pytest passes | Done |
