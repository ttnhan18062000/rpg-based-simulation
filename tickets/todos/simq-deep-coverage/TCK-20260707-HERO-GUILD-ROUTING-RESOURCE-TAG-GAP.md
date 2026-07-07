---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP
phase: open
date: 2026-07-07
tags: [simulation-quality, world, adventure, resource-registry]
---

# TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP

## Title
`hero_guild_routing` world content gap: `mountain_pass_zone`, `goblin_camp`, and `haunted_battlefield` have no `source_region_tags` coverage in `data/content/world/resources.yaml`

## Status
OPEN

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
- [ ] `mountain_pass_zone`, and any of `goblin_camp`/`haunted_battlefield` confirmed to have a
      resource node physically present, gain `source_region_tags` coverage in
      `data/content/world/resources.yaml`
- [ ] New regression test confirms `ResourceOpportunityProvider.get_opportunities()` returns >=1
      legal opportunity for a hero in each newly-tagged region
- [ ] `hero_guild_routing`'s 3-seed calibration matrix re-run, 0 AGENCY regression confirmed
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions on the full corpus

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
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
