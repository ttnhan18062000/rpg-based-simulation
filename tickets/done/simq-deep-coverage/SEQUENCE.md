# SimQ Deep Coverage — Implementation Sequence

Scoped 2026-07-07 from `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md`
(pre-ticket epic-scoping pass, no code changed) plus the orchestrator's decisions on all 5 of that
investigation's open questions (§5). Parent epic: `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`. This is a
follow-up to `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` (see `tickets/done/simq-corpus-tiers/SEQUENCE.md`
for that epic's own sequencing).

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP | Relocated pre-existing ticket. Must land before ticket 7 anchors `hero_guild_routing` at 1000t — closing its resource-tag gap first avoids anchoring a long-run AGENCY grade against content with a known latent stasis risk (investigation.md §3). |
| 2 | TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP | Relocated pre-existing ticket. Must land before ticket 7 extends `urban_political` to 2000t — the same dormant-gap-before-long-run-anchor rationale as ticket 1. |
| 3 | TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT | Relocated pre-existing ticket. Corpus-wide resource/region coverage audit in the same subsystem as tickets 1-2 and directly relevant to the AGENCY-drift risk ticket 7 is chasing; grouped with 1-2 as a "land before long-run anchoring touches shared worlds" prerequisite. |
| 4 | TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP | Relocated pre-existing ticket. `dungeon_crawl`, `sandbox_world`, and `generated_frontier_3_42` are exactly the worlds carrying (or, for `generated_frontier_3_42`, about to newly carry via ticket 8) this epic's long-run anchors — closing their population-stability test coverage gap first is directly relevant groundwork, grouped with 1-3 as the epic's 4-ticket prerequisite block. |
| 5 | TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER | Relocated pre-existing ticket. Independent doc-hygiene chore with no subject-matter overlap with the corpus/pillar work — can run anytime, including in parallel with tickets 1-4 or 7-10. |
| 6 | TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING | Relocated pre-existing ticket. Independent documentation/traceability chore with zero code/content overlap — can run anytime, including in parallel with anything else in this batch. Note: this new epic's own investigation.md was deliberately written to a pre-ticket working-name folder, then renamed to `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/` once the epic ticket ID existed, and will be preserved to `stored_artifacts/` at epic close, specifically so this citation-rot pattern does not recur. |
| 7 | TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS | New ticket. Hard-depends on tickets 1-4 landing first for the worlds they share (`hero_guild_routing`, `urban_political`, and population-stability coverage relevant to `dungeon_crawl`/`sandbox_world`). Adds the epic's core evidence: 1000t anchors for `unit_selfmodel_pilot`/`unit_faction_tension`/`hero_guild_routing`/`simq_routing_test`, plus 2000t extensions for `unit_faction_tension`/`urban_political`. |
| 8 | TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS | New ticket. Independent of tickets 1-4 (different world, no shared dependency) — can run in parallel with ticket 7. Establishes `generated_frontier_3_42`'s first-ever anchors (it currently has zero, at any tick count), including one long-run tier. |
| 9 | TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC | New ticket. Independent of everything else in this batch (pure documentation of already-completed research) — can run anytime. Sequenced before ticket 10 because ticket 10 cites its output. |
| 10 | TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL | New ticket. Hard-depends on ticket 9 for citation (cites the new §7.5 subsection ticket 9 adds to `quality_scoring_contract.md`). Lowest priority (P2) and narrowest scope in the epic — lands last. |

## Dependency Notes
- Tickets 1-4 form a single prerequisite block: none of them hard-depends on each other, but all
  four must land before ticket 7 touches `hero_guild_routing` or `urban_political`, and are grouped
  together at the front of the sequence for that reason (per investigation.md §5 Q2, decided).
- Tickets 5 and 6 are subject-matter-independent housekeeping — no hard dependency on anything, may
  run in parallel with any other ticket in this batch, including 1-4 or 7-10.
- Ticket 7 hard-depends on 1-4 (worlds shared with `hero_guild_routing`/`urban_political`).
- Ticket 8 has no hard dependency on 1-4 or 7 — `generated_frontier_3_42` is a different world with
  no shared prerequisite.
- Ticket 10 hard-depends on ticket 9 (citation dependency only, not a code dependency).
- No ticket in this batch anchors past 2000 ticks — the epic's explicit user-directed cap. A 5000t+
  tier is out of scope for every ticket in this sequence.
- Per investigation.md §5 Q1, exact seed count per world/tier for ticket 7 is left to that ticket's
  own Plan phase to decide with cost/coverage reasoning — this sequence sets the floor (land 1-4
  first, cap at 2000t) but not the exact anchor grid.
