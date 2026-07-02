---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260701-HAZARD-KIND-RESOLVER-GAP
phase: done
date: 2026-07-01
tags: [world, worldcomposition, hazard, hotfix, regression, testing]
---

# TCK-20260701-HAZARD-KIND-RESOLVER-GAP

## Title
hazard_kind field breaks all worldcomposition.v1 module loading; missing from RegionRecipeSpec and resolver forwarding

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260701-HAZARD-NATIVE-IMMUNITY` (DONE) added `hazard_kind` to `RegionSpec`
(`src/worldbuilding/schema.py:35`) and `RegionState` (`src/core/state.py:243`), and correctly
threaded it through `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:172`,
`hazard_kind=getattr(r_spec, "hazard_kind", "PHYSICAL")`). It also authored
`hazard_kind: "NATURAL_TERRAIN"` on regions in `data/content/world_modules/
wolf_den_near_forest.yaml` and `goblin_camp_conflict.yaml`.

But it missed two spots in the `worldcomposition.v1` module-loading pipeline (a separate path
from direct `worldspec.v1` compilation):

1. **`RegionRecipeSpec`** (`src/worldbuilding/recipe.py:8-16`, `model_config =
   ConfigDict(frozen=True, extra="forbid")`) has no `hazard_kind` field. Any module YAML
   authoring the field fails Pydantic validation outright:
   ```
   Validation failed for module 'wolf_den_near_forest' ... 2 validation errors for WorldModuleSpec
   regions.0.hazard_kind — Extra inputs are not permitted [extra_forbidden]
   regions.1.hazard_kind — Extra inputs are not permitted [extra_forbidden]
   ```
2. **`WorldAssemblyResolver.resolve_module_contribution()`** (`src/worldassembly/resolver.py`,
   the `RegionSpec(...)` construction around line 778) copies `hazard_level=reg.hazard_level`
   but never adds `hazard_kind=...` — so even after fixing #1, every resolved region would
   silently fall back to `RegionSpec`'s default `"PHYSICAL"`, defeating the entire mechanism
   without erroring.

**Impact:** this currently blocks loading for **every** `worldcomposition.v1` module
composition, not just the two modules that author `hazard_kind` — confirmed via
`pytest tests/integration/worldassembly/test_real_content_world_modules.py`, all 5 tests
ERROR in the current working tree, because `WorldModuleRepository.load_all()` has no
per-file error isolation.

**Why this wasn't caught:** `HAZARD-NATIVE-IMMUNITY`'s 11 new unit tests construct
`RegionState`/`EntityState` directly in Python, exercising `calculate_hazard_drain`'s logic
correctly but never exercising the YAML-load → resolve → compile pipeline the real content
changes depend on. The bug was found by `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s attempt-3
investigation, which tried to actually recompile `sandbox_world` and hit the failure directly.

## Scope
1. Add `hazard_kind: Optional[str] = Field("PHYSICAL", description="...")` to
   `RegionRecipeSpec` (`src/worldbuilding/recipe.py`), mirroring `RegionSpec`'s field exactly
   (same default, same semantics).
2. In `WorldAssemblyResolver.resolve_module_contribution()`, add `hazard_kind=getattr(reg,
   "hazard_kind", "PHYSICAL")` to the `RegionSpec(...)` construction, mirroring how
   `hazard_level` is already forwarded on the line above it.
3. Confirm `python3 -m src.worldbuilding.cli resolve sandbox_world` (or the equivalent
   resolve/compile command used elsewhere in this session) now succeeds, and that the
   resolved `wolf_den`/`near_forest` regions carry `hazard_kind: "NATURAL_TERRAIN"` in the
   output.
4. Confirm `tests/integration/worldassembly/test_real_content_world_modules.py` (currently
   5/5 ERROR) passes cleanly again.
5. **Harden against recurrence (explicit user request — this is not optional cleanup):** the
   root cause of this gap was that unit tests validated `calculate_hazard_drain`'s logic via
   direct object construction, never the real YAML-authoring pipeline. Add a **pipeline-level
   regression test** that specifically asserts `hazard_kind` survives module YAML → normalizer
   → `WorldAssemblyResolver.resolve_module_contribution()` → resolved `RegionSpec` unchanged
   for a real module (e.g. `wolf_den_near_forest`), not just that it doesn't error. Place it
   alongside the existing `hazard_level`-forwarding test if one exists (grep first — if
   `hazard_level`'s forwarding has no dedicated test either, note that as a related but
   out-of-scope gap, don't expand scope to backfill it). Also confirm
   `test_real_content_world_modules.py`'s `MODULE_MATRIX` (or equivalent) is part of what a
   content-field-adding ticket's own test_plan.md should be instructed to run — if there's a
   natural place to note this in `docs/testing/v2_test_taxonomy.md` or similar as a process
   guard for future "add a new content field" tickets, add a short note; don't restructure the
   whole test taxonomy doc for this.

## Out of Scope
- Any other content-field gaps not related to `hazard_kind` (this is a targeted fix, not a
  general audit of every field in `RegionRecipeSpec`/`RegionSpec` for drift)
- Re-running `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s recompile/empirical verification — that
  resumes once this hotfix lands, as a separate ticket
- Changing `calculate_hazard_drain`'s logic itself (confirmed correct by two prior
  architecture reviews) — this ticket only fixes the data-plumbing gap upstream of it

## Acceptance Criteria
- [x] `RegionRecipeSpec` has `hazard_kind` field, default `"PHYSICAL"`, matching `RegionSpec`
- [x] `WorldAssemblyResolver.resolve_module_contribution()` forwards `hazard_kind`
- [x] `wolf_den_near_forest`/`goblin_camp_conflict` modules resolve without validation errors
- [x] `tests/integration/worldassembly/test_real_content_world_modules.py` passes (5/5, now 6/6
      with the added regression test)
- [x] New pipeline-level regression test confirms `hazard_kind` round-trips through the real
      module-loading path, not just direct construction
- [x] No regression in existing `worldassembly`/`worldbuilding`/hazard test suites

## Related Tickets
- TCK-20260701-HAZARD-NATIVE-IMMUNITY — source of the gap (done, amended with a transparency
  note pointing here)
- TCK-20260701-SANDBOX-MONSTER-BALANCE — blocked on this hotfix; its attempt-3 investigation
  discovered this gap and is paused pending this fix
- TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC — grandparent context

## Related Docs
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` — original (buggy) implementation
  context
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/investigation.md` — where this gap
  was discovered, with exact error text and blast-radius evidence

## Related Code Areas
- `src/worldbuilding/recipe.py:8-16` — `RegionRecipeSpec`
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver.resolve_module_contribution()`
  (`RegionSpec(...)` construction)
- `src/worldbuilding/schema.py:27-36` — `RegionSpec` (reference only, already correct)
- `src/worldbuilding/compiler.py:165-173` — compile-time threading (reference only, already
  correct)
- `tests/integration/worldassembly/test_real_content_world_modules.py` — currently 5/5 ERROR,
  should pass after this fix

## Assumptions / Open Questions
None — root cause, exact fix locations, and blast radius were all confirmed with direct
command output and test runs during the discovering ticket's investigation. This is a
well-understood, narrow fix.

## Implementation Notes
- **Item 1**: Added `hazard_kind: Optional[str] = Field("PHYSICAL", description="Semantic type
  of this region's passive hazard drain (e.g. 'PHYSICAL', 'NATURAL_TERRAIN', 'TOXIC_GAS').")`
  to `RegionRecipeSpec` (`src/worldbuilding/recipe.py`), copied verbatim from `RegionSpec`
  (`src/worldbuilding/schema.py:35`).
- **Item 2**: In `WorldAssemblyResolver.resolve_module_contribution()`
  (`src/worldassembly/resolver.py`, `RegionSpec(...)` construction ~line 778), added
  `hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL")` immediately after the existing
  `hazard_level=reg.hazard_level` line, mirroring the forwarding pattern exactly.
  - Note: a second, unrelated `RegionSpec(...)` construction exists at
    `src/worldassembly/resolver.py:101` (inside a module-validation dummy-spec builder, not
    `resolve_module_contribution()`). It is out of ticket scope — the ticket's Related Code
    Areas and Scope only name `resolve_module_contribution()` — and was left untouched. It only
    feeds a throwaway validation `WorldSpec`, not the resolved output real content depends on,
    so leaving it defaulting to `"PHYSICAL"` does not reproduce this bug's blast radius.
- **Item 3**: Ran `python3 -m src.worldbuilding.cli resolve sandbox_world` (exact command named
  in the ticket) — succeeded cleanly (no `extra_forbidden`/`hazard_kind` error). Inspected
  `data/worlds/sandbox_world/resolved/world.resolved.yaml`: `wolf_den` and `near_forest`
  regions both carry `hazard_kind: NATURAL_TERRAIN`; `frontier_village` (the module that does
  not author the field) carries `hazard_kind: PHYSICAL` (default).
- **Item 4**: `tests/integration/worldassembly/test_real_content_world_modules.py` — all 5
  pre-existing tests now PASS (previously 5/5 ERROR on `extra_forbidden`).
- **Item 5**: Added a new pipeline-level regression test,
  `test_hazard_kind_survives_module_pipeline`, to
  `tests/integration/worldassembly/test_real_content_world_modules.py` (alongside the other
  `resolve_module_contribution`-exercising tests in that file — there was no separate
  dedicated resolver test file to prefer over it). It exercises the real
  `wolf_den_near_forest` module YAML end-to-end: `WorldModuleRepository` load →
  `WorldModuleAuthoringNormalizer.normalize()` → `WorldAssemblyResolver
  .resolve_module_contribution()` → resolved `RegionSpec.hazard_kind`, asserting
  `"NATURAL_TERRAIN"` for both `near_forest`/`wolf_den`, plus a companion assertion using
  `frontier_village_core` (a module that does *not* author `hazard_kind`) confirming the
  default-forwarding path (`"PHYSICAL"`) also survives the pipeline end-to-end.
  - Searched for an existing dedicated `hazard_level`-forwarding pipeline test: none exists.
    All existing `hazard_level` references in `tests/` construct `RegionRecipeSpec`/
    `RegionState` directly (e.g. `tests/unit/worldassembly/test_archetype_preservation.py:119-120`,
    `tests/unit/worldassembly/test_assembly.py:544`) — none run the real YAML → normalize →
    resolve pipeline for `hazard_level` specifically. Per the ticket's instruction, this is
    noted as a **related but out-of-scope gap**, not backfilled here.
  - Added a short process-guard note to `docs/testing/test_taxonomy.md` (Section 1,
    `worldassembly` marker area — the closest existing doc to the named-but-nonexistent
    `v2_test_taxonomy.md`) explaining that new `worldspec.v1` schema fields must be mirrored
    into `worldcomposition.v1` recipe schemas and forwarded in
    `resolve_module_contribution()`, and that `test_real_content_world_modules.py`'s
    `MODULE_MATRIX` should be part of any content-field ticket's own test plan.

## Test Summary
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py -v` — 6 passed
  (5 pre-existing + 1 new regression test).
- `pytest tests/integration/worldassembly/ -v` — 44 passed, no regression.
- `pytest tests/unit/worldbuilding/ -v` — 92 passed, no regression.
- `pytest tests/unit/worldassembly/ -v` — 48 passed, no regression (covers direct
  `RegionRecipeSpec`/resolver construction call sites).
- Manual verification: `python3 -m src.worldbuilding.cli resolve sandbox_world` succeeds;
  resolved output confirms `hazard_kind: NATURAL_TERRAIN` on `wolf_den`/`near_forest`.

## Parity
No parity ledger entry needed updating. Searched `docs/parity_ledger/` for
`RegionRecipeSpec`/`resolve_module_contribution`/`hazard_kind`: the only `hazard_kind` hits
(`docs/parity_ledger/world_dynamics.yaml` entries around `EnvironmentService
.calculate_hazard_drain`) describe the mechanics-law level (`RegionState.hazard_kind` +
`calculate_hazard_drain`'s exemption logic), which this ticket does not touch and which was
already correctly threaded via `WorldCompiler.compile()` per
`TCK-20260701-HAZARD-NATIVE-IMMUNITY`. The `RegionRecipeSpec`/resolver hits found
(`docs/parity_ledger/substrate.yaml` SUB-367, SUBSTRATE-NEW-009, and the `tags`-forwarding
entry) describe unrelated fields (`service_refs`, `quest_definitions`, `tags`). This ticket is
data-plumbing for an already-verified law, not a new/changed law, so no new entry was added
per the ticket's own Parity phase instruction.

## Files Changed
- `src/worldbuilding/recipe.py` — added `hazard_kind` field to `RegionRecipeSpec`
- `src/worldassembly/resolver.py` — forward `hazard_kind` in
  `resolve_module_contribution()`'s `RegionSpec(...)` construction
- `tests/integration/worldassembly/test_real_content_world_modules.py` — added
  `test_hazard_kind_survives_module_pipeline` regression test
- `docs/testing/test_taxonomy.md` — added process-guard note on content-field additions
  needing both recipe-schema mirroring and resolver forwarding, plus pipeline-test coverage

## Completion Summary
Fixed the two missing `hazard_kind` plumbing spots in the `worldcomposition.v1` module-loading
pipeline that were blocking all module composition loading (`RegionRecipeSpec` had no field at
all under `extra="forbid"`, and the resolver would have silently dropped the value back to
default even after adding the field). Confirmed via direct CLI resolve of `sandbox_world` that
`wolf_den`/`near_forest` now correctly resolve `hazard_kind: NATURAL_TERRAIN`, and that
`test_real_content_world_modules.py` (previously 5/5 ERROR) now passes cleanly (6/6 including
the new regression test). No regressions found across `worldassembly`/`worldbuilding` unit and
integration suites (44 + 92 + 48 passed). Added a pipeline-level regression test and a short
testing-taxonomy process-guard note to prevent recurrence of this class of "field added to one
schema, not mirrored/forwarded in the sibling path" gap.
