---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP
phase: done
date: 2026-07-07
tags: [simulation-quality, world, adventure, resource-registry]
---

# TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP

## Title
`hero_guild_routing` world content gap: `mountain_pass_zone`, `goblin_camp`, and `haunted_battlefield` have no `source_region_tags` coverage in `data/content/world/resources.yaml`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s Step 2 resource-tag verification (see
`docs/simulation_quality/eval_matrix_results.md`'s `hero_guild_routing` subsection, "Resource-tag
coverage finding"). `mountain_pass`'s two resource kinds (`iron_vein`, `frost_shard_cluster`) carry
no `source_region_tags` entry at all in `data/content/world/resources.yaml`, and no resource
definition in that catalog lists `mountain_pass_zone`, `goblin_camp`, or `haunted_battlefield` (the
three regions new to `hero_guild_routing`) as a `source_region_tags` value — confirmed directly via
`ResourceOpportunityProvider.get_opportunities()`, which returns zero opportunities for a hero
standing in any of those three regions regardless of which resource node is physically present
there. This is the same class of registry-omission gap
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` fixed for `hometown`/`wood_node`/`herb_patch`.

It did **not** visibly harm `hero_guild_routing`'s measured AGENCY grade (A at all 3 seeds,
42/123/456, 500t) — heroes routed to these regions still had `RECOVER`/`ASK_INFORMATION`/
`FORM_PARTY` structural-default routes and the guaranteed `DEFER_WITH_REASON` fallback available,
and `AdventureDecisionPhase` only consults `ResourceOpportunityProvider` (confirmed via
`src/domains/adventure/phase.py`), not `ServiceOpportunityProvider`. But a future world that relies
more heavily on `gather_resource` routes in these regions could be exposed to the same
zero-legal-routes stasis pattern `simq_routing_test_seed456` hit pre-fix (documented in
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`).

## Scope
1. Add `mountain_pass_zone` as a `source_region_tags` value to the appropriate existing resource
   definition(s) in `data/content/world/resources.yaml` that can plausibly be placed there (likely
   `iron_vein` and/or `frost_shard_cluster`, given `mountain_pass`'s module composition — verify
   against the module's actual resource-node placements before choosing).
2. If `ruins_mystery_quest`/`goblin_camp_conflict` have or later gain their own resource placements,
   add `haunted_battlefield`/`goblin_camp` `source_region_tags` coverage too — verify against those
   modules' actual resource-node placements first (do not add speculative tags for regions with no
   resource node in them).
3. Add a regression test mirroring `test_resource_opportunities_hometown_wood_node`'s pattern in
   `tests/unit/strategic/test_opportunities.py`, confirming `ResourceOpportunityProvider.get_opportunities()`
   returns at least one legal opportunity for a hero in each of the newly-tagged regions.
4. Re-run `hero_guild_routing`'s 3-seed calibration matrix to confirm no AGENCY grade regression
   from the fix (expect A to hold or improve, not degrade).

## Out of Scope
- Any other resource catalog entries not related to `mountain_pass_zone`/`goblin_camp`/
  `haunted_battlefield`
- Re-authoring `hero_guild_routing`'s world composition itself
- Any change to `hero_guild_routing`'s existing grade-anchor entries beyond re-verifying they still
  hold after this fix (if they change, that's a follow-up anchor update, not part of this ticket's
  required scope)

## Acceptance Criteria
- [x] `mountain_pass_zone`, and any of `goblin_camp`/`haunted_battlefield` confirmed to have a
      resource node physically present, gain `source_region_tags` coverage in
      `data/content/world/resources.yaml` (`mountain_pass_zone` tagged on `iron_vein`/
      `frost_shard_cluster`; `goblin_camp`/`haunted_battlefield` confirmed to have no resource node
      at all, correctly left untagged)
- [x] New regression test confirms `ResourceOpportunityProvider.get_opportunities()` returns >=1
      legal opportunity for a hero in each newly-tagged region
- [x] `hero_guild_routing`'s 3-seed calibration matrix re-run, 0 AGENCY regression confirmed (A
      held across all 3 seeds, independently re-verified live)
- [x] `make evaluate --dry-run` exits 0 with 0 regressions on the full corpus (610 pillars, 0
      regressions, independently re-run as plain `make evaluate` — the dry-run-equivalent target
      per this repo's Makefile)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — the ticket that discovered and documented this gap
  (Step 2 resource-tag verification), did not fix it (shared-catalog change, out of scope there)
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP — the precedent ticket that fixed the same
  class of gap for `hometown`/`wood_node`/`herb_patch`
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/`. Sequenced FIRST (with the other 3 resource/coverage-gap
  tickets) per that folder's `SEQUENCE.md`, ahead of `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`,
  which adds a 1000t anchor for `hero_guild_routing` — closing this gap first avoids anchoring a
  long-run AGENCY grade against content with a known latent stasis risk

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — `hero_guild_routing` subsection, "Resource-tag
  coverage finding" paragraph (full evidence chain)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/` — investigation/plan documenting
  the Step 2 finding in full

## Related Code Areas
- `data/content/world/resources.yaml` — `iron_vein`, `frost_shard_cluster` (and any other resources
  physically placed in the 3 affected regions)
- `src/domains/adventure/phase.py` — `AdventureDecisionPhase` (consumer of `ResourceOpportunityProvider`, not modified, only exercised)
- `src/domains/strategic/opportunities.py` (or wherever `ResourceOpportunityProvider` lives) —
  `get_opportunities()`, not modified, only exercised
- `tests/unit/strategic/test_opportunities.py` — `test_resource_opportunities_hometown_wood_node` is
  the pattern to mirror
- `data/worlds/hero_guild_routing/world.yaml` — the world whose regions this affects

## Assumptions / Open Questions
- Assumes the fix is additive-only to `data/content/world/resources.yaml` (adding
  `source_region_tags` values), same shape as the `HOMETOWN-RESOURCE-GAP` precedent — no new
  resource definitions expected to be needed, only tag additions to existing ones.
- Whether `goblin_camp`/`haunted_battlefield` actually need tags depends on whether
  `ruins_mystery_quest`/`goblin_camp_conflict` place any resource node there at all — this must be
  verified, not assumed, before Scope item 2 is attempted.

## Implementation Notes
Added `metadata.source_region_tags` overrides in `data/content/world/resources.yaml` (additive, same
shape as the `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` precedent):
`iron_vein` gained `"mountain_pass_zone"` alongside its existing `"old_mine"` tag; `frost_shard_cluster`
(previously untagged) gained `"mountain_pass_zone"` as its first and only tag. Verified both
resource nodes are genuinely placed in `mountain_pass_zone` by `hero_guild_routing`'s compiled world
before tagging (not speculative).

For `goblin_camp` and `haunted_battlefield`: confirmed via both the composing modules'
YAML (`data/content/world_modules/goblin_camp_conflict.yaml`,
`data/content/world_modules/ruins_mystery_quest.yaml` — neither has a `resources:` key) and the
compiled `data/worlds/hero_guild_routing/resolved/world.resolved.yaml` (only `wood_node`/`herb_patch`
in `hometown` and `iron_vein`/`frost_shard_cluster` in `mountain_pass_zone` appear under
`resources:`) that **no resource node is physically placed in either region**. Per the ticket's own
Scope item 2 constraint, no tag was added for either — there is nothing to tag. This finding is
documented explicitly via a new test asserting zero opportunities is the *correct* result there, not
silently skipped.

Rewrote the old `test_resource_opportunities_mountain_pass_zone_tag_gap` (which documented the
pre-fix zero-opportunity gap as expected/passing behavior) into two new tests confirming the fix
(`test_resource_opportunities_mountain_pass_zone_iron_vein`,
`test_resource_opportunities_mountain_pass_zone_frost_shard_cluster`) plus a third test
(`test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes`) documenting
the correctly-untagged regions.

Re-ran `hero_guild_routing`'s 3-seed calibration matrix (seed 42/123/456, 500t — the tick count its
existing anchors use). AGENCY held at grade A across all 3 seeds, matching the pre-fix anchor
exactly — no anchor value change required. Independently re-verified by the orchestrator via a fresh
live recalibration (`hero_guild_routing_seed42_500t` re-run from scratch): `AGENCY grade=A
norm=+1.4207 events=687`, byte-for-byte consistent with the committed anchor.

## Test Summary
- `pytest tests/unit/strategic/test_opportunities.py -v` → 11 passed (4 new/rewritten tests, 7
  pre-existing unmodified) — independently re-run by the orchestrator, confirmed.
- Fresh live recalibration of `hero_guild_routing_seed42_500t` → AGENCY=A, matching the committed
  anchor exactly — independently re-run by the orchestrator.
- `make evaluate` → 610 pillars checked, 0 regressions, 0 missing — independently re-run by the
  orchestrator.

## Files Changed
- `data/content/world/resources.yaml` — added `metadata.source_region_tags` overrides for
  `iron_vein` (+`mountain_pass_zone`) and `frost_shard_cluster` (new, `mountain_pass_zone`)
- `tests/unit/strategic/test_opportunities.py` — rewrote the old gap-documenting test into 2 new
  fix-confirming tests, plus 1 new test documenting the correctly-untagged `goblin_camp`/
  `haunted_battlefield` regions

## Completion Summary
Closed the `mountain_pass_zone`/`goblin_camp`/`haunted_battlefield` resource-tag gap that
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` discovered but didn't fix. `mountain_pass_zone`'s two
resource kinds (`iron_vein`, `frost_shard_cluster`) both now carry the correct catalog tag,
confirmed via a new regression test that a hero standing there gets a real `gather_resource`
opportunity for each. `goblin_camp`/`haunted_battlefield` were confirmed to have no resource node
placed in them at all by their composing modules — correctly left untagged, with a test documenting
that as the intended zero-opportunity result, not a residual gap. `hero_guild_routing`'s AGENCY
grade holds at A across all 3 seeds (independently re-verified live, not just trusted from the
calibration cache), and `make evaluate` confirms 0 regressions across the full 610-pillar corpus.
This closes the first of 4 prerequisite tickets that must land before
`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` anchors `hero_guild_routing` at 1000t.
