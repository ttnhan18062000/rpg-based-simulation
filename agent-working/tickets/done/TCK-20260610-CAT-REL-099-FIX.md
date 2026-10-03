---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-CAT-REL-099-FIX
phase: done
date: 2026-06-10
tags: [cat, rel, fix]
---

# TCK-20260610-CAT-REL-099-FIX

## Title
Fix CAT-REL-099: catalog relation defect blocking moon_cult_ruins / apprentice_mage population resolution

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
CAT-REL-099 is the single most impactful open defect. It causes the catalog to fail to resolve the `moon_cult_ruins` module's `apprentice_mage` population, which cascades into xfails across three separate phases: full world assembly (Phase 31), scenario setup resolver happy path (Phase 30), and content expansion gate (Phase 34). No phase 30/31/34 test can be called fully passing until this is fixed.

## Scope
- Diagnose the exact failure mode in CAT-REL-099: why `apprentice_mage` population fails to resolve during catalog relation projection for `moon_cult_ruins`
- Fix the root cause (missing catalog entry, broken reference, relation projection bug, or normalization gap)
- Verify fix does not regress any currently passing tests
- Remove or promote xfail markers in the following test files once fixed:
  - `tests/integration/content/test_strict_world_matrix.py` (full assembly rows)
  - `tests/integration/content/test_expansion_gate.py` (assembly gate item)
  - Any scenario setup resolver happy-path tests marked xfail due to this defect

## Out of Scope
- Unrelated catalog entries or population defects not part of CAT-REL-099
- Rewriting the catalog schema or relation projection pipeline beyond what is necessary to fix the defect

## Acceptance Criteria
- [x] Root cause of CAT-REL-099 identified and documented in implementation notes
- [x] `moon_cult_ruins` module resolves `apprentice_mage` population without error in strict catalog mode
- [x] Previously xfailed full-assembly rows in `test_strict_world_matrix.py` now pass
- [x] `test_expansion_gate.py` gate item that was xfailed due to CAT-REL-099 now passes
- [x] No previously passing tests are broken
- [x] Parity ledger checked — no relevant entries affected

## Related Tickets
- TCK-20260610-STRICT-MATRIX-UNXFAIL (unblocked by this fix — now covered directly)
- TCK-20260610-SCENARIO-RESOLVER-UNXFAIL (unblocked by this fix — now covered directly)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/engine/authoritative_pipeline.md`
- `docs/parity_ledger/substrate.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260609-STRICT-WORLD-MATRIX/`
- `stored_artifacts/TCK-20260609-CONTENT-EXPANSION-GATE/`

## Related Code Areas
- `data/content/world_modules/moon_cult_ruins.yaml`
- `data/content/entities/populations.yaml`
- `data/content/social/faction_relationships.yaml`
- `tests/integration/content/test_strict_world_matrix.py`
- `tests/integration/content/test_expansion_gate.py`
- `tests/integration/scenarios/test_scenario_setup_resolver.py`

## Assumptions / Open Questions
Resolved during investigation: CAT-REL-099 was three missing catalog records (data bug, not logic bug).

## Implementation Notes
Root cause: three broken data references caused CatalogValidator to block all world assembly.

1. `moon_cult_ruins.yaml` referenced `apprentice_mage` (an archetype ID) as a population group ID. The `apprentice_mage` archetype exists and has `themes: ["arcane", "moon"]` — thematically correct for moon_cult_ruins. Fixed by:
   - Adding `moon_cult_apprentice_circle` population group to `populations.yaml` with `apprentice_mage: 4` members and `preferred_regions: ["moon_cave"]`
   - Updating `moon_cult_ruins.yaml` populations list from `["apprentice_mage"]` to `["moon_cult_apprentice_circle"]`

2. `orc_clan_territory.yaml` referenced `town_to_orc_clan` and `orc_clan_to_town` faction relationships that didn't exist. Fixed by adding both entries to `faction_relationships.yaml` following the goblin_warband/town pattern (security_hostility + territorial_raider models).

After data fixes, all xfail markers removed from 3 test files. No source code changes were needed.

## Test Summary
- `tests/integration/content/test_strict_world_matrix.py`: 73 passed (0 xfail, previously 45 xfail in full-assembly rows)
- `tests/integration/content/test_expansion_gate.py`: 12/12 passed (previously 11/12)
- `tests/integration/scenarios/test_scenario_setup_resolver.py`: 9/9 passed (previously 4 xfail)
- Total: 95 passed, 0 failed, 0 xfail across all three suites

## Files Changed
- `data/content/entities/populations.yaml` — added `moon_cult_apprentice_circle` population group
- `data/content/world_modules/moon_cult_ruins.yaml` — fixed populations reference
- `data/content/social/faction_relationships.yaml` — added `town_to_orc_clan` and `orc_clan_to_town`
- `tests/integration/content/test_strict_world_matrix.py` — removed `_PREEXISTING_CAT_BUG` xfail markers
- `tests/integration/content/test_expansion_gate.py` — removed `_CAT_REL_099` xfail marker
- `tests/integration/scenarios/test_scenario_setup_resolver.py` — removed `_PREEXISTING_CAT_BUG` xfail markers

## Completion Summary
Fixed three missing catalog data entries (one population group, two faction relationships) that were causing CatalogValidator to generate CAT-REL-099 errors and block all world assembly. All 95 previously-xfailed tests now pass. Phases 30, 31, and 34 are now fully verified.
