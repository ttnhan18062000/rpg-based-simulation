---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP
phase: done
date: 2026-07-06T15:27:41Z
tags: [simulation-quality, world, adventure, bug]
---

# TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP

## Title
`urban_political` has the identical dormant `hometown` resource-opportunity gap as
`simq_routing_test` — currently inert only because its shipped calibration profile keeps
`ENABLE_ADVENTURE_ROUTING` off

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4, cross-world audit)
found that `urban_political` shares both `frontier_village_core` (places `wood_node`/`herb_patch` in
`hometown`) and `hero_adventurers` (spawns all 3 hero-role entities in `hometown`) with
`simq_routing_test` — the exact two modules whose combination produces the "hero permanently stuck
on `defer_with_reason`" failure mode when a hero's `sociability` roll lands under the `FORM_PARTY`
gate (`src/domains/adventure/generator.py:124`) and no resource node's `source_region_tags` covers
`hometown` (`src/world/providers/resources.py:69`).

`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s fix (adding `"hometown"` to
`wood_node`/`herb_patch`'s catalog `source_region_tags` in `data/content/world/resources.yaml`) is a
global, world-agnostic catalog change, so it **already closes the content half of this gap for
`urban_political` too**, as a confirmed side effect (see that ticket's Completion Summary for the
read-only verification performed). What remains unresolved for `urban_political` specifically is the
**profile half**: its shipped SimQ calibration profile does not currently force
`ENABLE_ADVENTURE_ROUTING=ON` (confirmed via `docs/simulation_quality/eval_matrix_results.md`'s
"AGENCY — Cross-World Design Note": `simq_routing_test` is documented as "the one calibration world
that forces `ENABLE_ADVENTURE_ROUTING=ON`"), so `AdventureDecisionPhase` never runs for
`urban_political` today and this gap cannot currently manifest as an observed calibration failure.
It would reproduce `simq_routing_test`'s identical failure mode the moment `urban_political` (or any
future world reusing `hero_adventurers`) enables adventure routing and an unlucky-`sociability` hero
lands in `hometown`.

This ticket is filed as a P2 (dormant, not currently observed failing) tracking item — not a P1/P0
active-failure fix — per the parent ticket's own explicit scope decision to not expand its own scope
to cover this.

## Scope
- Decide, with evidence, whether `urban_political`'s calibration profile should ever force
  `ENABLE_ADVENTURE_ROUTING=ON` (a design/roadmap question — check `docs/simulation_quality/` and any
  `urban_political`-specific archetype docs for whether "routing-capable" was ever intended for this
  world), or whether the dormant risk should simply be explicitly documented as an accepted
  archetype boundary (mirroring the "AGENCY=C is archetype-correct for non-routing worlds" note
  already in `eval_matrix_results.md`).
- If routing is ever enabled for `urban_political` (in this ticket or a future one triggered by that
  design decision), re-run its calibration (seeds 42/123/456) and confirm the now-fixed
  `wood_node`/`herb_patch` `hometown` tags actually prevent the stasis failure mode there too (do not
  assume — verify live, per this ticket family's established precedent).
- If routing is never enabled, close this ticket by adding an explicit "dormant, accepted" note
  to `docs/simulation_quality/eval_matrix_results.md`'s "AGENCY — Cross-World Design Note" section,
  cross-referencing this ticket and `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`, so a
  future reader doesn't have to re-derive this analysis from scratch.

## Out of Scope
- Re-fixing the `wood_node`/`herb_patch` catalog `source_region_tags` — already fixed globally by
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`; do not duplicate that work.
- The broader corpus-wide resource-tag/spawn-region coverage pattern for non-hero roles — tracked
  separately by `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`.
- Changing the `FORM_PARTY` `sociability >= 0.2` gate value — a separate design/balance question.

## Acceptance Criteria
- [x] Explicit decision recorded (with rationale) on whether `urban_political` should ever force
      `ENABLE_ADVENTURE_ROUTING=ON` — **no**, settled by direct precedent (see Completion Summary)
- [ ] ~~If enabled: `urban_political` calibration re-run...~~ — not applicable, routing stays off
- [x] If not enabled: `docs/simulation_quality/eval_matrix_results.md` updated with an explicit
      "dormant, accepted" note for `urban_political`'s `hometown` gap, cross-referencing this ticket
      and the parent content-fix ticket
- [x] `grade_anchors.json` updated if a new `urban_political` calibration run changes any pillar's
      grade — not applicable, no recalibration performed (routing stays off, AGENCY grade unchanged
      at C, confirmed via the existing `test_agency_da_anti_drift_guard` guard test, which already
      passes without modification)

## Related Tickets
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP (parent — filed this ticket; its content fix
  already closes this gap's content half as a side effect; its investigation.md §4(i) is this
  ticket's primary evidence trail)
- TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE — the scoring-formula fix for the same failure mode in
  `simq_routing_test`, for reference on how the failure mode was diagnosed and scored
- TCK-20260627-P0B-URBAN-RESOURCE-NODES — original ticket that placed `wood_node`/`herb_patch` in
  `hometown` via `frontier_village_core.yaml`, for both worlds using that module
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/`. Sequenced FIRST (with the other 3 resource/coverage-gap
  tickets) per that folder's `SEQUENCE.md`, ahead of `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`'s
  2000t extension of `urban_political` — the epic's own scope decision requires this dormant-gap
  disposition to be settled before anchoring `urban_political` at long run

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — "AGENCY — Cross-World Design Note" section
  (documents `simq_routing_test` as the only routing-forced world today)
- `docs/mechanics/adventure_routing_contract.md` — the `defer_with_reason` fallback contract this
  gap interacts with

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP/` (once finalized) —
  investigation.md §4(i) is the direct evidence source for this ticket

## Related Code Areas
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`
- `data/worlds/urban_political/` — world spec/modules and shipped calibration profile
- `data/content/world_modules/hero_adventurers.yaml`, `frontier_village_core.yaml` — shared modules
  causing this gap in both worlds
- `src/domains/optimization/feature_flags.py` — `ENABLE_ADVENTURE_ROUTING` flag default

## Assumptions / Open Questions
- Whether `urban_political` was ever intended to be "routing-capable" is unconfirmed — this ticket's
  first Scope item is to answer that question with evidence before deciding whether to enable the
  flag or document the dormancy as permanent.

## Implementation Notes
The routing-capability question this ticket's Scope item 1 asks was already settled by direct,
on-point precedent — no new human decision was needed:

- `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` ruled `AGENCY=C` in every calibration world except
  `simq_routing_test` is archetype-correct, not a gap — `AdventureDecisionPhase` is opt-in per
  world archetype, not a global default.
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` — the ticket that most directly answered "how do we
  add more AGENCY coverage" — explicitly *considered* `urban_political` as the closest candidate
  (it already has a `hero_guild`-framed population, so it's "not architecturally foreign" to a
  routing framing) and explicitly *rejected* enabling routing on it, choosing instead to author a
  brand-new dedicated world (`hero_guild_routing`). Its own Out of Scope names `urban_political`
  explicitly as a world this decision does not reverse routing for. This is a rejection-with-
  consideration, the strongest form of precedent — not silence or an unexamined default.

Content-fix side effect independently reconfirmed live: `data/content/world/resources.yaml`'s
`wood_node`/`herb_patch` entries both already carry `"hometown"` in `source_region_tags` (landed
globally by `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`, a catalog-wide, not per-world,
change) — so even though routing stays off, if a future ticket ever did reverse the above
precedent, the content half of the original failure mode is already closed.

Added a "Third exception class" paragraph to `docs/simulation_quality/eval_matrix_results.md`'s
"AGENCY — Cross-World Design Note" section (after the `hero_guild_routing` paragraph), matching
that section's existing bold-lead-in/ticket-citation style, cross-referencing this ticket and all
3 precedent tickets. No code, content, profile, or grade-anchor changes — this ticket's entire
scope was documenting an already-settled decision. Confirmed the existing
`test_agency_da_anti_drift_guard` test (added by `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`)
already asserts `urban_political` stays `ENABLE_ADVENTURE_ROUTING` OFF, via
`expected_world_flag_state.json`'s `_meta.agency_da_non_routing_worlds` list — this ticket's
disposition is fully consistent with that existing guard and required no modification to it.

Note for the record: this ticket's realized work (one doc paragraph, zero code/content/test
changes) turned out lighter than a typical `standard`-tier ticket, closer in shape to the
`hotfix`-tier precedent (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) it directly cites — not changing
the ticket's own `Tier` field retroactively, just noting the actual effort for future reference.

## Test Summary
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py
  tests/integration/test_scenario_feature_flag_defaults.py -q` → 100 passed, including
  `test_agency_da_anti_drift_guard` unmodified and still passing.
- `make evaluate` → 610 pillars checked, 0 regressions, 0 missing (expected no-op impact for a
  doc-only change).
- `python3 tools/validate_frontmatter.py docs/simulation_quality/eval_matrix_results.md
  --content-type doc` → pre-existing frontmatter-missing error, confirmed via `git diff` to predate
  this ticket's edit entirely (this file is one of the 12 already tracked by
  `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER`, ticket 5 in this same epic — not this ticket's
  issue to fix).

## Files Changed
- `docs/simulation_quality/eval_matrix_results.md` — new "Third exception class" paragraph in the
  "AGENCY — Cross-World Design Note" section

## Completion Summary
Resolved the routing-capability question via direct precedent rather than a new decision:
`urban_political` will never force `ENABLE_ADVENTURE_ROUTING=ON`, per `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s
archetype-correctness ruling and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s explicit
consideration-and-rejection of `urban_political` as a routing candidate in favor of authoring
`hero_guild_routing` instead. The content half of the original gap
(`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s `wood_node`/`herb_patch` `hometown` tag
fix) already covers `urban_political` as a confirmed side effect of that global catalog change,
independently reconfirmed live here. Documented the full disposition in
`docs/simulation_quality/eval_matrix_results.md` so a future reader doesn't have to re-derive this
analysis from scratch. No code, content, or anchor changes; `make evaluate` confirms 0 regressions.
This closes the second of 4 prerequisite tickets that must land before
`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` extends `urban_political` to 2000t.
