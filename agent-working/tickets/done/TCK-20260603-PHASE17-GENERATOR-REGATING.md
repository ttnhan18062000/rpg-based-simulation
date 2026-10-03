---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260603-PHASE17-GENERATOR-REGATING
phase: done
date: 2026-06-03
tags: [phase17, generator, regating]
---

# TCK-20260603-PHASE17-GENERATOR-REGATING

## Title

Phase 17 — Procedural Generator Re-gating

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Refactor the procedural generator to generate against the unified content catalog and resolved artifact contract.

## Scope

- Update generator output to include CompileContext in ResolvedWorldBundle.
- Populate validation_report using WorldValidator.
- Replace hardcoded baseline ids (villagers, monsters, wood, ore, shop, blacksmith, tavern) with dynamic catalog selections or configurable defaults.
- Fix determinism tests to assert stable content fingerprints rather than byte-identical timestamp strings.
- Add a catalog-backed runtime simulation smoke test.

## Out of Scope

- Increasing procedural layout or distribution complexity.
- Modifying compilation phases or rules.

## Acceptance Criteria

- ResolvedWorldBundle includes CompileContext.
- Generated world compiles with CompileContext.
- Baseline content IDs are dynamically validated or resolved from catalog.
- Determinism tests pass without fake timestamp strings.
- Small simulation runs without errors under catalog-backed runtime.

## Related Tickets

- `TCK-20260603-PHASE16-PARITY-TESTS`

## Related Docs

- `world_phases_11_19.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldgeneration/generator.py`
- `tests/unit/worldgeneration/test_generator.py`

## Assumptions / Open Questions

- Catalog repository is fully valid and loaded.

## Implementation Notes

- None

## Test Summary

- Executed `pytest -v tests/unit/worldgeneration/test_generator.py` (All 4 tests passed successfully)
- Executed `pytest tests/unit/worldassembly/` (All 9 tests passed successfully)
- Executed `pytest tests/unit/content_semantics/` (All 4 tests passed successfully)

## Files Changed

- `src/worldgeneration/generator.py`
- `tests/unit/worldgeneration/test_generator.py`
- `src/content_semantics/faction.py`
- `src/content_semantics/role.py`
- `data/world_modules/populations/standard_villagers.yaml`

## Completion Summary

- Refactored the procedural generator to use catalog-valid defender/invader factions (`town_council`/`goblin_warband`), roles, buildings (`shop`, `blacksmith`, `inn`), and resource types.
- Generated compile-time context overrides and validation report metrics inside ResolvedWorldBundle.
- Fixed semantic helpers to use dynamic catalog properties and legacy fallbacks.
- Corrected determinism verification checks and added dynamic catalog simulation kernel smoke test.
