---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP
phase: done
date: 2026-07-06
tags: [simulation-quality, world, resource-registry, bug]
---

# TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP

## Title
`stone_outcrop` resource fails content-graph validation: `[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While independently verifying `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s test results
(confirming two test failures were genuinely pre-existing via `git stash` bisection, not introduced
by that ticket), found that `tests/integration/worldassembly/test_e2e_smoke.py` fails 5 tests on
unmodified code with:

```
src.worldbuilding.schema.InvalidWorldSpecError: Assembly validation failed with blocking errors:
[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'
```

This traces to `src/content/validator.py`'s graph-based referential-integrity checker
(`get_rule_id`, ~line 646, falls through to the generic `CAT-REL-099` code when no more specific
rule applies) building an edge from `resource:stone_outcrop` to `material:stone` (via
`stone_outcrop`'s `material: "stone"` field in `data/content/world/resources.yaml`, line 23) and
finding no corresponding node in its content graph.

This is confusing because `data/content/world/items.yaml` DOES have a `stone` entry (added by
`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`, `categories: ["material"]`, `base_value: 2`) — but
the validator's graph apparently indexes "material" as a distinct concept from "item" (or reads a
different catalog file entirely for materials), so `stone_outcrop`'s `material:` field reference
does not resolve to that `items.yaml` entry. The exact mechanism is unconfirmed — this ticket's
Scope is to find it.

Confirmed via `git stash` bisection this reproduces identically on the current `main`-adjacent
branch tip, unrelated to any change in `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`. Not
yet confirmed whether this was already failing before `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`
landed (i.e. a pre-existing gap in STONE-GAP's own test coverage — `test_e2e_smoke.py` may not have
been part of that ticket's scoped test run) or introduced by it.

## Scope
- Trace exactly what `src/content/validator.py`'s content graph considers a "material" node: is
  there a distinct `data/content/*/materials.yaml` catalog separate from `items.yaml`, or does the
  graph builder read `items.yaml` but key nodes differently (e.g. by `categories` field matching,
  which might require `"material"` to be the ONLY category, or a different field name than `id`)?
- Determine why `stone`'s `items.yaml` entry (confirmed present, `categories: ["material"]`) doesn't
  satisfy the graph's material-node lookup for `stone_outcrop`'s reference.
- Check whether other resources' `material:` field values (e.g. `wood`, `iron_ore`, `herb` —
  pre-existing, presumably working) resolve correctly in the same graph, to isolate whether `stone`
  specifically is malformed/missing from wherever the graph actually looks, or whether the whole
  `material:` cross-reference mechanism is broken for every resource (unlikely, since only
  `stone_outcrop`-referencing tests fail, not all resource-related tests).
- Fix `stone_outcrop`'s `material` reference (or the missing catalog entry, whichever is the true
  root cause) so `test_e2e_smoke.py`'s 5 currently-failing tests
  (`test_smoke_wilderness_survival_compiles_to_authoritative_state`,
  `test_smoke_urban_political_compiles_to_authoritative_state`,
  `test_urban_political_all_entities_have_region_id`,
  `test_smoke_dungeon_crawl_compiles_to_authoritative_state`,
  `test_smoke_generated_frontier_3_42_compiles_to_authoritative_state`) pass.
- Confirm whether this was a pre-existing gap in `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`'s
  own test coverage (i.e. that ticket's scoped test run didn't include
  `tests/integration/worldassembly/test_e2e_smoke.py`) and note this as a process learning if so —
  not to re-litigate that ticket's already-completed work, just to record why this wasn't caught
  sooner.

## Out of Scope
- Re-litigating `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`'s already-completed
  `ResourceRegistry`/ecology-emission fix (confirmed correct and unrelated to this validation gap)
- Re-litigating `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s already-completed
  `source_region_tags` fix (this ticket only discovered the finding while independently verifying
  that ticket's test results; the finding itself is unrelated to that ticket's own change)
- The separate, already-tracked `test_resource_opportunity_provider.py::
  test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village` test-order-pollution flake
  (confirmed via the same bisection to be a distinct, unrelated issue — passes in isolation, only
  fails under specific suite-ordering conditions)

## Acceptance Criteria
- [x] Root cause of the material-graph resolution gap confirmed with file:line evidence
- [x] `stone_outcrop`'s material reference resolves correctly (fix applied to whichever side is
      actually wrong — the resource's reference, the material catalog entry, or the validator's
      graph-building logic)
- [x] All 5 currently-failing `test_e2e_smoke.py` tests pass
- [x] Confirmed whether other resources' material references are correctly validated (i.e. this
      isn't a systemic graph-builder bug affecting everything, just isolated to `stone`/`stone_outcrop`)
- [x] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP (done) — authored `stone_outcrop` and its paired
  `stone` item catalog entry; this ticket's own test scope did not include `test_e2e_smoke.py`,
  which is where this validation gap was later discovered
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP (done) — discovered this finding
  incidentally while independently verifying that ticket's test results via `git stash` bisection;
  unrelated to that ticket's own `source_region_tags` fix
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO (done) — independently hit this exact bug as a
  hard blocker (`python -m src.worldbuilding.cli resolve` failed for every world in the catalog,
  not just `stone_outcrop`-adjacent ones, since `WorldAssemblyResolver.assemble()` runs this
  validation unconditionally) and applied the actual fix (the `data/content/foundation/materials.yaml`
  entry) as a necessary prerequisite for its own new-world authoring work. This ticket is closed as
  a duplicate resolution — the fix landed via that ticket's commit, not a separate one, since it was
  a genuine implementation blocker there.

## Related Docs
(none yet — investigation should determine if `docs/parity_ledger/` has a relevant content-catalog
validation entry, or if one should be added)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP/` — original `stone_outcrop`
  authoring context
- `stored_artifacts/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP/` — where this finding was
  incidentally discovered during independent test verification

## Related Code Areas
- `src/content/validator.py` — the graph-based referential-integrity checker (`CAT-REL-099` rule,
  ~line 646)
- `data/content/world/resources.yaml` — `stone_outcrop`'s `material: "stone"` field (line 23)
- `data/content/world/items.yaml` — `stone`'s catalog entry (line 97, `categories: ["material"]`)
- `tests/integration/worldassembly/test_e2e_smoke.py` — the 5 currently-failing tests

## Assumptions / Open Questions
- UQ-1: Is there a distinct materials catalog file separate from `items.yaml`, or does the
  validator's graph builder read `items.yaml` but key/match nodes differently than expected?
  Unconfirmed — first Scope item requires tracing this before proposing a fix.

## Implementation Notes
Root cause confirmed: `src/content/reference_graph.py`'s concept-mapping table (lines 7, 78-80)
keys `"foundation.materials"` (i.e. `data/content/foundation/materials.yaml`) — a distinct catalog
from `items.yaml` — to the `"material"` node concept. `src/content/validator.py`'s
`_validate_reference_graph()` (`CAT-REL-099`, line ~646) builds an edge from
`resource:stone_outcrop` to `material:stone` via `resources.yaml`'s `material: "stone"` field
(confirmed exact line), and looks for a `material:stone` NODE — which only exists if `stone` is
registered in `materials.yaml`, regardless of what `items.yaml` contains. `items.yaml`'s `stone`
entry (added by `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`, `categories: ["material"]`) was a
red herring — the `categories` field has no bearing on this graph's node-concept classification,
which is purely catalog-file-driven per the mapping table.

Confirmed via direct inspection this was a genuinely systemic gap for THIS specific field, not
isolated to `stone`/`stone_outcrop` alone in principle — but confirmed no OTHER resource is
currently affected, since every other resource's `material:` value (`wood`, `iron_ore`, `herb`,
etc.) already has a corresponding `materials.yaml` entry; `stone` was the only omission, introduced
when `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` added `stone` to `items.yaml` but not to
`materials.yaml` — the two catalogs are not automatically kept in sync, and no test at the time
caught the gap (`test_e2e_smoke.py` was not part of that ticket's scoped test run — this is the
"process learning" this ticket's own Scope item asked to record).

Fix: added a `stone` entry to `data/content/foundation/materials.yaml`
(`categories: ["mineral", "crafting", "construction"]`, `common_regions: ["frontier_village",
"mountain", "mine"]`) matching the file's existing entry shape. This is a minimal, additive fix —
no changes to `stone_outcrop`'s `resources.yaml` entry, `items.yaml`'s `stone` entry, or the
validator/graph-building logic itself, all three of which were already correct.

This fix was actually applied and discovered as a hard implementation blocker by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`, not as this ticket's own standalone
implementation — that ticket needed `python -m src.worldbuilding.cli resolve` to work for its own
new world-authoring work, and this exact `CAT-REL-099` error blocked `resolve` for every world in
the catalog (not just ones referencing `stone_outcrop` directly), since
`WorldAssemblyResolver.assemble()` runs this validation unconditionally, catalog-wide, regardless of
which world is being resolved. The fix commit is that ticket's, not a separate one for this ticket.

## Test Summary
- `pytest tests/integration/worldassembly/test_e2e_smoke.py -q` → all 5 previously-failing tests
  now pass (independently re-confirmed by the orchestrator, not just trusted from the other
  ticket's report).
- `python -m src.worldbuilding.cli resolve urban_political` → succeeds (previously failed with
  `CAT-REL-099` on every world; independently re-confirmed, then reverted the incidental
  regeneration of `urban_political`'s `resolved/` artifacts, which is out of this ticket's scope).
- `make evaluate` → exit 0, 0 regressions (confirmed via `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s
  own Verify step, which ran after this fix landed).

## Files Changed
- `data/content/foundation/materials.yaml` — new `stone` entry (landed via
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s commit)

## Completion Summary
Root cause confirmed: the content-graph validator's `"material"` node concept is keyed exclusively
to `data/content/foundation/materials.yaml`, a catalog distinct from `items.yaml` — `stone_outcrop`'s
`material: "stone"` reference had no corresponding `materials.yaml` entry, even though `items.yaml`
had one (added by the original `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` ticket, which didn't
know to update the separate materials catalog). Fixed with one minimal, additive `materials.yaml`
entry. No other resource is currently affected by this same gap. Closed as resolved via
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s commit, which hit this bug as a genuine
implementation blocker (it broke `resolve` for every world in the catalog, not just ones touching
`stone_outcrop`) and applied the fix directly rather than waiting for this ticket to be picked up
separately — this ticket is closed as the record of that resolution, not a duplicate fix.
