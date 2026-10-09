---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING
phase: done
date: 2026-10-08
tags: [architecture, testing]
---

# TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING

## Title
Fixture guards stop depending on the current release candidate, so registering keys no longer forces a new candidate

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 1 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. Registering keys moved `registry_hash` twice (rc-0006, rc-0007) and each time the pilot and terrainset fixture guards (fresh `export-runtime` of the current rc) broke, forcing a new candidate and re-pointed guards.

## Scope
- Redesign the fixture guards so their substance stays (the committed frontend fixtures equal what the store would
  produce for the slots they claim: same entries, details, file names, PNG bytes) without requiring a candidate on the
  CURRENT registry. Options to weigh and state in plan.md: compare against the stored candidate + its recorded pixel
  hashes and re-derived PNG bytes; or export ignoring only `registry_hash`-derived fields (as icondraft already does).
- Keep a separate, explicit check that a release candidate's registry hash matches the registry when a candidate is
  BUILT (the store's own refusal stays; only the fixture guards stop riding it).
- Mutant proof: a flipped PNG byte, a dropped slot, a changed entry still fail; a registry-only change no longer does.
- Prove it: register a throwaway key in a test catalog and show no fixture guard fails.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Weakening what the fixtures assert about pixels/entries.

## Acceptance Criteria
- [x] Fixture guards survive a registry-only change; still fail on any content change (mutants); store refusal unchanged.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING/ (plan with the planner's approval, investigation, test_plan, mutant_proof)

## Related Code Areas
- tests/visual_assets/test_pilot_fixture.py, test_terrainset_fixture.py, adopted_facts.py, frontend/src/visualAssets/__fixtures__/

## Assumptions / Open Questions
- This changes what a guard checks: plan.md states before/after precisely; planner approves the design before code.

## Implementation Notes
- Probe first: a throwaway key breaks 10 tests; only the pilot and terrainset fixture guards ride the current candidate. Inventory pins stay untouched (deliberate decisions).
- `tests/visual_assets/derived_runtime.py` derives the runtime manifest and files from the stored candidate and artifacts (asserting each PNG decodes to the recorded pixel hash); the two fixture guards use it. Drift guard in `test_derived_runtime.py`; the store's `registry_mismatch` refusal is unchanged.

## Test Summary
- 14 tests in the three files; mutants M1-M8 caught/behaving as stated (a first masked mutation run was discarded and redone). Scoped suites: see the commit report.

## Files Changed
- tests/visual_assets/{derived_runtime,test_derived_runtime,test_pilot_fixture,test_terrainset_fixture}.py, docs/assets/pilot_terrain_key.md, ticket and artifacts.

## Completion Summary
The pilot and terrainset fixture guards no longer ride the current release candidate: registering a key cannot break them and no candidate is needed, while slots, details, hashes and PNG bytes are still asserted; the store's refusal is untouched and a drift guard ties the helper to `export_runtime`.
