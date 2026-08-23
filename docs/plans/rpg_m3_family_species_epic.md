---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 3: Family, Species & the Adult Life

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M3-FAMILY-SPECIES` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 31, 32, 33, 34, 38.
**Gate:** hard dependency on M2's idea 14 (Species Classification) and idea 43 (population seeding) — both
confirmed as real blockers, not soft preferences, in Cross-Cutting Risk.

## Problem

The reproduction/marriage/coming-of-age arc — the first milestone that gives an entity a real life path
instead of a fixed stat block. Highest Direction Fit and Narrative Generativity scores of any cluster in
`docs/brainstorm/design_merit_scorecard.html` (idea 34 scores 5/5 on both), and the deepest internal
sequencing of any milestone this size.

## Scope (not yet broken into child tickets)

Build order within the milestone, confirmed by Phase Placement & Testing Strategy:

1. **Idea 34 — Coming of Age.** The single most depended-on idea in the entire late-game chain (Leverage
   5/5). Fires alongside M1's idea 20 (Life Stages) and needs idea 32's birth record to exist first.
2. **Idea 33 — Marriage.** The first genuine two-party propose/accept handshake anywhere in the codebase —
   fits Contracts' existing offer/accept shape better than a new phase.
3. **Idea 31 — Personal Dependents & Responsibility.** Small, well-precedented — gives `heir_entity_id`'s
   real write-path a reason to fire.
4. **Idea 32 — Reproduction.** Splits three ways by species (natural creatures reuse Camp's maturity
   mechanic, magical/demonic beings reuse the calamity substrate, human/humanoid needs a genuinely new
   cadence-gated sub-phase). The single highest-cost, highest-risk idea in the whole 65-idea set per the
   Merit Scorecard (Efficiency 1/5, Risk-Adjusted Cost 1/5) — explicitly not a "quick" milestone item
   despite M3's small idea count.
5. **Idea 38 — Close the reproduction population-pressure feedback loop.** Depends on idea 32 landing
   first; the signal it nudges doesn't exist without M2's idea 43 either.

## Out of Scope

- Anything from Milestones 1, 2, 4, 5, or 6.
- Any inheritance/legacy mechanic building on top of idea 32's birth records (ideas 53, 55, 58 — M5).

## Acceptance Signal

- All 5 ideas exist as child tickets in the build order above.
- Idea 32's population-growth risk (explicitly named in its own atlas card and independently in Cross-
  Cutting Risk) has an owner and a concrete mitigation before this milestone ships, not just a flag.

## Open Questions

- Idea 32's Merit Scorecard cost/risk profile (the worst in the set on both axes) may argue for splitting
  it into its own smaller epic rather than one child ticket among five — not decided here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Cross-Cutting Risk & Blast Radius, Phase Placement & Testing
  Strategy (`LINEAGE_ARENA` scenario design + explicit long-run-cost caveat for population-pressure
  convergence)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/plans/rpg_design_roadmap.md`
