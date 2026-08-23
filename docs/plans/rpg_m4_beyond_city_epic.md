---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 4: Beyond the City & the Layer Model

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M4-BEYOND-CITY` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 40, 41, 44, 45, 46, 47, 49, 50, 51, 52, 61,
64.
**Gate:** M2's idea 35 (City ownership), idea 36 (Clan's shape), and idea 48 (place-type transitions).

## Problem

The settlement-capacity tier below City (Camp, Nest, Lair), plus the rest of the layer-model wiring theme —
where places stop being static and start having texture. 12 ideas, the most internally clustered milestone
in the roadmap: Shared Implementation Opportunities found real consolidation across most of it.

## Scope (not yet broken into child tickets)

1. **Ideas 44 + 45 + 46 — Settlement population/identity, consolidated.** Confirmed real: collapses to
   roughly 2 tickets, not 3 — one `CampService` extension covers Camp seeding/texture and Nest as a variant
   swapping the raid branch for a spread branch.
2. **Idea 47 — Lair.** Confirmed a genuinely separate ticket, correctly NOT a Camp variant — but its real
   precedent is Boss's entity-anchor idempotency pattern (`boss_region_id`), not Camp's shape, a correction
   from the original card.
3. **Idea 61 — Settlements Develop Personalities.** Re-scoped by a real correction: its original cited
   precedent (idea 48) was wrong; the actual live match is Culture Drift's `CultureDeriver`/
   `CulturalBiasApplicator` — which has zero live callers anywhere. **This idea is blocked until that
   substrate is wired**, the same blocker three other clusters across this roadmap share (see
   `docs/plans/rpg_design_roadmap.md`'s "Known open items").
4. **Ideas 49 + 50 — Ambition/expansion, small shared helper only.** Both gate on "does this entity
   possess/consume material X" — worth one shared predicate, not a ticket merge. Idea 49 also carries a
   real naming-collision footgun: two unrelated classes both named `RecipeRegistry`.
5. **Ideas 51 + 52 — consolidated into one ticket.** Idea 52 confirmed pure wiring on top of idea 51's
   EXPAND directive, not a separate mechanism.
6. **Idea 40 — Clan lifecycle.** Real correction found in Phase Placement: `party_lifecycle.py`'s SOC-228
   doesn't fire on death as originally assumed — which would have silently killed cross-generational Clans
   if built as first scoped.
7. **Idea 64 — The Empty Chair.** Confirmed genuinely unrelated to idea 40 (correctly not forced into a
   cluster) — the real remaining half after heir-assignment split off to M1's idea 10. No code precedent
   anywhere for the economic-vacancy signal it needs.
8. **Idea 41 — Information hubs.** Confirmed standalone, no cluster overlap — still gated behind
   `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_INFORMATION_INTENT_EXECUTION`, both OFF by default.

## Out of Scope

- Anything from Milestones 1, 2, 3, 5, or 6.
- Wiring `CultureDeriver`/`CulturalBiasApplicator` itself — that's a prerequisite this epic surfaces (for
  idea 61), owned by whichever ticket resolves the cross-milestone blocker named in the parent roadmap, not
  built speculatively inside this epic.

## Acceptance Signal

- Consolidation findings above are reflected in the actual child-ticket count (roughly 9 tickets for 12
  ideas, per the atlas's own Roadmap estimate) — not silently reverted to 1:1 ticket-per-idea.
- Idea 61 stays explicitly blocked/deferred until its substrate dependency is resolved, not built against
  the wrong precedent it originally cited.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Shared Implementation Opportunities, Cross-Cutting Risk & Blast
  Radius, Phase Placement & Testing Strategy (`SETTLEMENT_TIER_ARENA`, `AMBITION_LOOP_ARENA`,
  `CLAN_LIFECYCLE_ARENA`, `EMPTY_CHAIR_ARENA` scenario designs)
- `docs/plans/rpg_design_roadmap.md`
