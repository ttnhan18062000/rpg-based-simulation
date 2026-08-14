---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP
phase: done
date: 2026-07-04
tags: [simulation-quality, world, adventure, bug]
---

# TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP

## Title
`simq_routing_test` world content gap: no resource node is tagged for the `hometown` spawn region, so any hero rolling `sociability < 0.2` is permanently stuck

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While investigating `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` (AGENCY=F collapse in
`simq_routing_test` seed456), the investigation traced entity 23's permanent
`defer_with_reason` streak to two combined, independently-confirmed conditions:

1. **World content gap (this ticket's scope)**: `simq_routing_test`'s compiled world has 5
   resource nodes (`herb_patch → (near_forest, moon_cave)`, `wood_node → (near_forest,)`,
   `iron_vein → (old_mine,)`, `silver_vein → ()`, `crystal_outcrop → ()`). **None list `hometown`**
   in `source_region_tags`. All heroes in this world spawn with `navigation.region_id = "hometown"`
   (confirmed for all 30 entities, all 3 seeds — seed-independent). `ResourceOpportunityProvider
   .get_opportunities()` (`src/world/providers/resources.py:69`, `if current_region in
   res_def.source_region_tags:`) therefore **never** returns a `gather_resource` opportunity for
   any hero standing in `hometown`, regardless of seed or entity.
2. **Personality RNG roll (out of scope — not a bug, seed456-specific)**: `FORM_PARTY`
   (`src/domains/adventure/generator.py:124`, `if sociability >= 0.2:`) is the only other route
   family available to a `hometown`-spawned hero (no active needs/perceived weaknesses means
   `RECOVER`/`ASK_INFORMATION` never fire either — `generator.py:97,110`). In seed456, entity 23's
   compiled `sociability = 0.18816...`, just under the `0.2` gate. In seed42/123 the same entity
   rolls `0.534`/`0.407` — comfortably above the gate.

Condition (1) is the one that turns a single below-gate personality roll into a **total, permanent,
whole-run** dead end: with even one `hometown`-tagged resource node, an unlucky-`sociability` hero
would still have `gather_resource` as a fallback route. Without it, `sociability < 0.2` alone is
sufficient to strand a hero for its entire life, in every seed where that roll occurs — this is a
**seed-independent structural fragility** in this world's content, separate from (and not fixed by)
`TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`'s scoring-formula fix (which only bounds the *penalty* for
being stuck — it does not and should not un-stick a legitimately-stuck entity).

## Scope
- Add at least one resource node to `simq_routing_test`'s world content (`data/worlds/
  simq_routing_test/` — compiled via `WorldCompiler.compile()`, source spec/modules TBD by
  investigation) whose `source_region_tags` includes `hometown`, so a hero spawned there always has
  at least one non-`FORM_PARTY` route family available.
- Investigate whether this same gap exists in other calibration worlds that spawn heroes in a
  region not covered by any resource node's `source_region_tags` (a quick audit across
  `data/worlds/*` — not just `simq_routing_test` — before authoring the fix, to avoid a narrow
  point-fix if this is a recurring worldbuilding-authoring gap).
- Re-run `simq_routing_test` calibration for all 3 seeds post-fix and confirm the change doesn't
  regress AGENCY or any other pillar's grade for seed42/123 (which don't rely on this fallback
  today, since their entity 23 rolls above the `FORM_PARTY` gate).

## Out of Scope
- `AgencyScorer`'s stasis-penalty formula (already fixed in `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`)
- Adventure decision logic itself (`AdventureDecisionPhase`/`Generator`/`Service` — confirmed
  correct, not the bug; the fallback-guarantee behavior when `opts` is empty is working exactly as
  designed)
- Changing the `FORM_PARTY` `sociability >= 0.2` gate value itself (a separate design/balance
  question, not a content-authoring gap)

## Acceptance Criteria
- [x] At least one resource node in `simq_routing_test` has `hometown` in its
      `source_region_tags`, confirmed via `WorldCompiler.compile()` inspection
      (both `wood_node` and `herb_patch` fixed; live-verified via
      `CatalogToResourceRegistryAdapter.adapt()` projection, see Implementation Notes)
- [x] A hero spawned in `hometown` with `sociability < 0.2` and no active needs/perceived
      weaknesses now has at least one non-`defer_with_reason` candidate route
      (`gather_resource`) at every tick (confirmed live via seed456's `decision_trace.jsonl`:
      entity 23 selects `gather_resource` at every logged decision tick 0-490, zero
      `defer_with_reason` selections)
- [x] Cross-world audit performed: either confirmed `simq_routing_test`-only, or a broader fix
      applied if the same spawn-region/resource-tag mismatch exists elsewhere (performed in the
      investigation phase; `urban_political` shares the identical dormant hero/hometown gap,
      tracked by `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`; the broader
      non-hero-role pattern is tracked by `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`)
- [x] `simq_routing_test` seed42/123/456 calibrations re-run; no AGENCY (or other pillar)
      regression for seed42/123; seed456's AGENCY grade re-verified against whatever grade the
      scoring-formula fix (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE) left it at (seed42/123: AGENCY
      A/A unchanged, all 9 other pillars unchanged; seed456: AGENCY improved D→A)
- [x] `grade_anchors.json` updated if seed456's AGENCY grade changes as a result of this content fix
      (updated D→A)

## Related Tickets
- TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE (in progress at time of filing) — the scoring-formula
  fix this gap was discovered alongside; that ticket's investigation.md §2.1, §3, and its plan.md's
  Unresolved Question section are the primary evidence trail for this ticket
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP (done) — unrelated crash fix that first allowed
  `simq_routing_test` calibration to run to completion, surfacing both findings
- TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP (open) — follow-up filed for
  `urban_political`'s identical dormant gap, fixed as a side effect of this ticket's global catalog
  edit but not yet exercised by that world's calibration profile
- TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT (open) — follow-up filed for the broader
  corpus-wide pattern (most non-`old_mine`/`near_forest`/`moon_cave` regions similarly uncovered)
- TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP (open) — follow-up filed for an unrelated,
  pre-existing `[CAT-REL-099]` validation failure discovered while independently re-verifying this
  ticket's test results (confirmed via `git stash` bisection to predate this ticket entirely)

## Related Docs
- `docs/mechanics/adventure_routing_contract.md` — documents the `generator.py:164-175`
  empty-candidate-set fallback (`defer_with_reason`) as intended when `opts` is empty; this ticket
  does not change that contract, only the world content that makes the fallback fire unnecessarily
  often for `hometown`-spawned heroes
- `docs/simulation_quality/eval_matrix_results.md` — AC6 section documents the seed456 AGENCY
  finding this gap contributes to

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE/` (once finalized) — investigation and
  plan documenting the discovery of this gap as a byproduct of the stasis-collapse investigation

## Related Code Areas
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`,
  `source_region_tags` gating (line 69)
- `data/worlds/simq_routing_test/` — the world spec/modules to be amended
- `src/domains/adventure/generator.py` — `FORM_PARTY` gate (line 124) and empty-candidate-set
  fallback (lines 164-175), read-only reference, not to be changed by this ticket

## Assumptions / Open Questions
- Whether this is unique to `simq_routing_test` or a broader worldbuilding-authoring convention gap
  across other calibration worlds is unconfirmed — first Scope item requires an audit before
  deciding whether this is a point-fix or a pattern-fix.

## Implementation Notes
- Added `metadata.source_region_tags` to `wood_node` (`["near_forest", "hometown"]`, additive over
  the prior live-projected `("near_forest",)`) and `herb_patch` (`["near_forest", "moon_cave",
  "hometown"]`, additive over `("near_forest", "moon_cave")`) in `data/content/world/resources.yaml`,
  matching `stone_outcrop`'s existing override mechanism exactly. This is the only lever that
  changes gating (`preferred_biomes` is a separate, un-consulted sibling field for these kinds, per
  investigation.md §1a) — a purely additive, global catalog change, not a per-world edit.
- Live-verified catalog pick-up (read-only, in-process, no calibration run needed) via
  `CatalogRepository("data/content").load_all()` → `CatalogToResourceRegistryAdapter(repo).adapt()`:
  `wood_node.source_region_tags == ('near_forest', 'hometown')`,
  `herb_patch.source_region_tags == ('near_forest', 'moon_cave', 'hometown')`. Both prior entries
  (`near_forest`/`moon_cave`) retained.
- Deleted stale `data/calibration/simq_routing_test_seed{42,123,456}_500t/` and re-ran
  `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed {42,123,456} --name
  simq_routing_test` for all 3 seeds. Results (live-verified, not assumed):
  - seed42: AGENCY=A (norm +1.4207), all 9 other pillars match `grade_anchors.json` exactly
    (COMBAT C, ECONOMY C, FACTION C, INFORMATION C, NARRATIVE S, PROGRESSION C, SOCIAL C, WORLD B,
    COGNITION A) — no regression.
  - seed123: AGENCY=A (norm +0.6415), all 9 other pillars match the anchor exactly — no regression.
  - seed456: AGENCY=**A** (norm +0.6415, up from anchored `D`) — matched the plan's "improves"
    branch. Live-inspected `decision_trace.jsonl` for entity 23: at every logged decision tick
    (0, 10, 20, ... 490 — 50 samples across the 500-tick run) the selected route is
    `gather_resource`; zero `defer_with_reason` selections anywhere in the trace. The 491-event
    defer streak documented by `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` is fully interrupted, not
    just shortened. Two other seed456 pillars also shifted by exactly one grade step each as a
    downstream consequence of entity 23's freed decision stream — COGNITION S→A, NARRATIVE A→S —
    both within `test_grade_regression.py`'s ±1-letter anchor band, so neither anchor was re-pinned
    (only `AGENCY` was, per plan.md §4's "single field" instruction).
  - Read-only compile check confirmed `urban_political`'s resolved spec picks up the same catalog
    change automatically (same `hometown`-placed `wood_node`/`herb_patch` nodes, per
    `docs/parity_ledger/town_resource.yaml` TOWN-183) — consistent with the fix being a global,
    world-agnostic catalog change (`ResourceOpportunityProvider.get_opportunities()` gates purely on
    resource kind, no world/module parameter). `urban_political`'s calibration profile/flags were
    not touched (out of scope; tracked by the URBAN-POLITICAL follow-up ticket).
- Updated `tests/simulation_quality/fixtures/grade_anchors.json`'s
  `simq_routing_test_seed456_500t.AGENCY` from `D` to `A` (the only anchor requiring an update,
  confirmed by re-running `test_grade_regression.py` before and after: 1 failure pre-update
  — AGENCY drifted 3 steps outside the ±1 band — 0 failures post-update).
- Appended a new dated status paragraph to `docs/simulation_quality/eval_matrix_results.md`'s AC6
  section ("EXCEPTION CLOSED (grade improved)" branch, since seed456's grade did improve) plus a
  bracketed cross-reference at the end of the "Second exception class" paragraph under "AGENCY —
  Cross-World Design Note". Both prior tickets' history paragraphs preserved unedited.
- Added parity ledger entry `TOWN-188` to `docs/parity_ledger/town_resource.yaml` (confirmed next
  unused ID after `TOWN-187`) and divergence entry `2.27` (Bug Fix class) to
  `docs/guidelines/intentional_divergences.md` (confirmed next unused heading after `2.26`), per
  plan.md's exact drafted content.
- Confirmed cross-references in both already-filed follow-up tickets
  (`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`,
  `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`) — not implemented, out of scope per
  plan.
- **Factual correction to investigation.md §6 (documented here, no separate doc edit needed):** the
  investigation's test-coverage inventory claimed `tests/unit/core/test_registry_bridge.py`
  (~line 355-368) "reads the real `data/content` catalog." On direct inspection, that assertion
  block runs inside `test_registry_bridge_seeding_catalog(mock_catalog_repo)`, which builds a fully
  synthetic `tempfile.TemporaryDirectory()` catalog (only `wood_node`/`iron_vein`, no `herb_patch`,
  no `hometown`) — it does not touch `data/content` at all. The *actual* real-catalog test in that
  test module family is `test_registry_parity.py::test_production_catalog_parity` (uses
  `CatalogRepository("data/content")` directly). Rather than retrofit the synthetic fixture with a
  new `herb_patch`/`hometown` entry (which would only test the generic adapter mechanism, not this
  specific content fix), added a new, separate test function,
  `test_production_catalog_wood_and_herb_cover_hometown`, to `test_registry_bridge.py` (additive —
  no existing test modified) that reads the real `data/content` catalog directly and asserts
  `"hometown"` is present in both kinds' `source_region_tags` alongside their prior tags. This
  satisfies the plan's intent (a `test_registry_bridge.py`-resident, additive `"hometown"`
  assertion) while actually exercising the real fix.
- Pre-existing, unrelated test failures confirmed identical on unmodified code (not caused by this
  ticket, not fixed by it): `tests/unit/world/providers/test_resource_opportunity_provider.py::
  test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village` fails only when run in the
  same session as `test_adapter_heuristic_reporting.py`/others (test-order pollution, reproduces
  identically with `git stash` applied) and is unrelated to `wood_node`/`herb_patch`; and 5 tests in
  `tests/integration/worldassembly/test_e2e_smoke.py` fail with `[CAT-REL-099] Resource
  'stone_outcrop' references non-existent material 'stone'`, reproduced identically on unmodified
  code via `git stash`. Neither is touched or caused by this ticket's change.

## Test Summary
- `pytest tests/unit/strategic/test_opportunities.py tests/unit/core/test_registry_bridge.py
  tests/unit/core/test_registry_parity.py -v` → 17 passed (includes 3 new tests: 2 in
  `test_opportunities.py` — `test_resource_opportunities_hometown_wood_node`,
  `test_resource_opportunities_hometown_herb_patch` — and 1 in `test_registry_bridge.py` —
  `test_production_catalog_wood_and_herb_cover_hometown`).
- `pytest tests/unit/content/test_adapter_heuristic_reporting.py
  tests/integration/content/test_registry_projection_parity.py
  tests/simulation_quality/test_grade_regression.py -v` → 64 passed, 1 skipped.
- `tests/integration/worldassembly/test_e2e_smoke.py` and
  `tests/unit/world/providers/test_resource_opportunity_provider.py` (in combined-session order):
  5 and 1 failures respectively, both confirmed pre-existing/unrelated via `git stash` A/B
  comparison (identical failures on unmodified code) — not a regression from this ticket.
- `make evaluate` (Makefile's `evaluate` target already runs `tools/evaluate_simq.py --dry-run`):
  390 pillars checked, 0 regressions, 0 missing (1 scenario skipped — no calibration data, unrelated
  to this world).
- `data/runs/`, `reports/release_proof/` cleaned per Definition of Done.
- `make knowledge-index-update` run (2 files re-embedded: `eval_matrix_results.md`,
  `intentional_divergences.md`).

## Files Changed
- `data/content/world/resources.yaml` — added `metadata.source_region_tags` to `wood_node` and
  `herb_patch`, additively including `"hometown"`
- `tests/simulation_quality/fixtures/grade_anchors.json` —
  `simq_routing_test_seed456_500t.AGENCY`: `D` → `A`
- `docs/simulation_quality/eval_matrix_results.md` — new dated AC6 status paragraph (EXCEPTION
  CLOSED) + cross-reference note in the "Second exception class" paragraph
- `docs/parity_ledger/town_resource.yaml` — new entry `TOWN-188`
- `docs/guidelines/intentional_divergences.md` — new entry `2.27`
- `tests/unit/core/test_registry_bridge.py` — new test
  `test_production_catalog_wood_and_herb_cover_hometown` (additive)
- `tests/unit/strategic/test_opportunities.py` — new tests
  `test_resource_opportunities_hometown_wood_node`, `test_resource_opportunities_hometown_herb_patch`
  (additive)
- `data/calibration/simq_routing_test_seed{42,123,456}_500t/` — regenerated calibration output
  (not committed as source; regenerated by the calibration commands above)
- Follow-up tickets already filed (pre-existing at start of this implementation session, confirmed
  not modified): `tickets/todos/TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP.md`,
  `tickets/todos/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT.md`

## Completion Summary
Added `"hometown"` additively to `wood_node` and `herb_patch`'s `source_region_tags` in the global
`data/content/world/resources.yaml` catalog, mirroring the `metadata.source_region_tags` override
mechanism `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` used for `stone_outcrop`. Both kinds were
already physically placed in `hometown` by the shared `frontier_village_core` module; only the
catalog-level gating tag that `ResourceOpportunityProvider.get_opportunities()` checks was missing —
a global, catalog-wide, per-kind allowlist with no world/module parameter, confirmed by independent
architecture review to affect every world using these kinds, not just `simq_routing_test`.

Re-ran all 3 `simq_routing_test` calibration seeds live (not assumed): seed42/123 confirmed
unaffected (`AGENCY=A`/`A`, all 9 other pillars unchanged from committed anchors). Seed456's AGENCY
grade improved `D`→`A` (`normalized_score=+0.6415`) — entity 23's 491-event `defer_with_reason`
streak is fully interrupted, not just shortened (verified via `decision_trace.jsonl`: `gather_resource`
selected at every one of 50 logged decision ticks post-fix). This fully closes the AC6 per-seed
exception `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` had to document (that ticket's scoring-formula
fix alone could only bound the *penalty*, not un-stick a legitimately-stuck entity — this ticket's
content fix removes the legitimate stuck-ness itself). `grade_anchors.json`'s AGENCY anchor updated
`D`→`A`; two other seed456 pillars (COGNITION, NARRATIVE) shifted by one grade step each as a
downstream consequence, both within the existing ±1-letter anchor band, so neither anchor was
re-pinned. `eval_matrix_results.md`'s AC6 section and Cross-World Design Note updated with the full
outcome, preserving all prior tickets' history as an append-only record.

Cross-world audit (ticket's own required Scope item) confirmed via live `ResourceRegistry`
inspection across all 10 worlds: only `simq_routing_test` and `urban_political` have hero-role
entities spawned in `hometown` at all (both use the same shared `hero_adventurers` +
`frontier_village_core` modules). `urban_political`'s identical gap is fixed as a side effect of
this same global catalog edit, but remains dormant today (its shipped calibration profile doesn't
force `ENABLE_ADVENTURE_ROUTING=ON`) — filed `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`
to track whether/when that world's profile should be updated to actually exercise it. A much
broader pattern (most non-`old_mine`/`near_forest`/`moon_cave` regions across the whole corpus are
similarly uncovered by any resource node's tags) was also found and filed as
`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` rather than fixed here, since fixing the
entire corpus is out of this ticket's scope.

While independently re-verifying this ticket's test results, found a third, unrelated pre-existing
issue: 5 tests in `tests/integration/worldassembly/test_e2e_smoke.py` fail on unmodified code with
`[CAT-REL-099] Resource 'stone_outcrop' references non-existent material 'stone'` — confirmed via
`git stash` bisection to predate this ticket's changes entirely. Filed
`TCK-20260706-SIMQ-STONE-OUTCROP-MATERIAL-VALIDATION-GAP` to track it separately (out of scope for
a `source_region_tags` content fix).
