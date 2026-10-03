---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY

## The identity rule and change taxonomy

Recorded in full, with reasoning, in the new doc this ticket produced:
`docs/plans/mechanism_identity_and_change_taxonomy.md`. Not duplicated here — see that doc for the
rule statement (§1), the seven-kind change taxonomy (§2), the `depends_on` semantics resolution
(§3), and the full per-mechanism test results (§4).

## Method

For each of the 7 bundled entries named in Scope §3, plus the two special cases
(`action_pacing_readiness`, the falsification test; `combat_resolution`, the multiple-entry-point
test), investigated the real implementing code directly — never assumed a verdict from the
mechanism's own name.

**A methodology note, since it changed mid-investigation.** Three of the seven bundled entries were
first delegated to isolated fork sub-agents for parallel investigation. Two of the three forks
returned content-free replies ("reported above," "the report above stands as final") that did not
actually convey their findings when resumed and asked to restate them — a known, previously-flagged
issue with this fork type, not re-filed as fresh feedback per the once-per-issue rule. Rather than
trust an unverified "SPLIT" claim from the one fork that did relay content (which recommended
splitting all three of its assigned mechanisms — a result the ticket's own Acceptance Criterion #3
explicitly treats with suspicion, since a rule that splits everything is doing no work), all five
remaining mechanisms were investigated directly, by hand, against real code. This caught a real
disagreement: the fork's own unverified claim for `attributes_biology` was SPLIT; direct
verification found no actual state divergence and reversed the verdict to KEEP. The two other
mechanisms it investigated (`buildings_town_services`, `calamities_boss_spawns`) were independently
re-confirmed as real SPLIT candidates, but with more precise reasoning than the fork's own report
in one case (the Church-services dead-facet finding was folded into `town_services`'s own note
rather than treated as its own additional row, per the ticket's own "no forced uniform
granularity" rule).

## Findings requiring correction along the way

**`regional_sovereignty`'s own `implemented_by` binding.** Initially bound to
`RegionalSovereigntyService` (the class whose name matched most directly). Before trusting that
binding, checked its real callers per this epic's own standing discipline — zero, anywhere in
`src/`. The real, live implementation (already investigated at length in the atlas's own card for
this entry) is `FactionInfluenceService`. Corrected before this ticket closed; `RegionalSovereigntyService`'s
own orphan status is flagged (not filed as its own ticket, to keep this ticket's scope bounded).

**Four legitimate pinned-test updates**, each a real, expected consequence of the registry
restructuring, not a gate routed around:
- `test_transitive_dependents_matches_real_data`: 25 → 26 (the new `readiness_speed_scaling`
  mechanism is itself a new direct dependent of `action_pacing_readiness`).
- `test_chart_generator_ancestors_of_produces_a_real_subgraph`: `tactical_decision` no longer
  appears in `combat_resolution`'s own ancestors chart (the edge was removed, §3).
- `test_real_registry_findings_pinned` (state-caller-mismatch check): resolved by fixing the
  `regional_sovereignty` binding above, not by updating the pinned set to accept a wrong finding.
- `test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms`: unmapped set grew by exactly the
  4 new mechanisms that are the "other half" of a split and have no atlas card of their own
  (`regional_trauma`, `calamity_intensity`, `buildings`, `readiness_speed_scaling`) — the mapped
  count of 73 stayed the same, since each split card's own single badge was repointed at whichever
  successor id its own prose actually describes.

## Test Summary

See test_plan.md.

## Files Changed

See ticket body's own Files Changed section.
