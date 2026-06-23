---
status: open
layer: world
authority: P0
audience: agent
ticket_id: TCK-20260623-FIX-WORLDASSEMBLY
phase: open
date: 2026-06-23
tags: [test-repair, worldassembly, content, validation, P0]
---

# TCK-20260623-FIX-WORLDASSEMBLY

## Title
Fix WorldAssembly content validation cascade (~70 failures)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Two distinct root causes are blocking all world assembly tests (strict world matrix, scenario catalog matrix, multi-pack composition, worldassembly unit tests).

**Root Cause 1 — [CAT-REL-016] river_ford terrain ref:**
`src/worldassembly/resolver.py:712` raises `InvalidWorldSpecError` during `resolver.assemble()` because region `river_ford` references terrain `river` which does not exist in the content catalog. Likely introduced when a content YAML was added/modified during the worldgen epic without registering the `river` terrain entry.

**Root Cause 2 — WorldSpec quest_definitions missing `type` field:**
`WorldSpec.model_validate()` raises `ValidationError: quest_definitions.0.type — Field required`. Test fixtures (and possibly content YAML files) pass quest definition dicts without a `type` field that the Pydantic model now requires. This indicates a recent schema addition to `WorldSpec` or `QuestDefinition` was not back-propagated to test fixtures and content YAML files.

Source: D10 audit F6/F9 partially; root causes confirmed by direct error sampling 2026-06-23.

## Scope
- Identify where `river_ford` region is defined and which content YAML declares it; add missing `river` terrain entry to the catalog, OR remove the reference to `river` if it should not exist
- Identify which Pydantic model added `type` as a required field on quest definitions; determine if `type` should have a default, or if all test fixtures and content YAMLs must be updated to provide it
- Do NOT change existing quest logic or worldassembly resolution logic — this is a content/schema alignment fix only

## Out of Scope
- WorldAssembly logic changes
- Adding new quest types
- Content YAML refactoring beyond the minimal fix

## Acceptance Criteria
- `tests/unit/worldassembly/test_assembly.py` — all 6 tests pass
- `tests/unit/worldassembly/test_perspective_resolution.py` — all 4 tests pass
- `tests/unit/worldassembly/test_quest_merge.py` — all 3 tests pass
- `tests/unit/worldassembly/test_provenance.py` — all 2 tests pass
- `tests/integration/content/test_strict_world_matrix.py` — all 36 parametrized tests pass
- `tests/integration/content/test_swamp_border_pack.py` — all 2 tests pass
- `tests/integration/content_packs/test_multi_pack_composition.py` — all 8 tests pass
- `tests/integration/scenarios/test_scenario_catalog_matrix.py` — all 16 tests pass
- `tests/unit/core/test_catalog_smoke_simulation.py` — passes (quest type field fixed)

## Related Tickets
- D10 audit F6 (content registry drift) — related but separate
- TCK-20260623-FIX-CONTENT-REGISTRY — can run in parallel

## Related Docs
- `docs/audits/D10_test_coverage.md` F6, F9
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/engine/authoritative_pipeline.md`

## Related Code Areas
- `src/worldassembly/resolver.py:712` (assembly validation)
- `src/worldbuilding/schema.py` (WorldSpec, QuestDefinition Pydantic models)
- `data/content/` (YAML files — region/terrain definitions)
- `tests/unit/worldassembly/`
- `tests/integration/content/`

## Assumptions / Open Questions
- Is `river` terrain intentionally absent (river_ford should ref a different terrain), or was it simply not registered?
- Was the `type` field added with `Optional` originally and later changed to required, or was it always required and a fixture never had it?

## Implementation Notes
Investigation order:
1. `graphify query "river_ford terrain"` + read the content YAML that defines river_ford
2. Check `WorldSpec` / `QuestDefinition` Pydantic models for `type` field definition and `default=`
3. Fix content data; update test fixtures that hardcode quest definitions without `type`

## Test Summary
Run: `pytest tests/unit/worldassembly/ tests/integration/content/ tests/integration/content_packs/ tests/integration/scenarios/test_scenario_catalog_matrix.py tests/unit/core/test_catalog_smoke_simulation.py`
Expected: all above pass.

## Files Changed
_To be filled during implementation._

## Completion Summary
_To be filled on completion._
