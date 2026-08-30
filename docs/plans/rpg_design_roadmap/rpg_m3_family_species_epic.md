---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 3: Family, Species & the Adult Life

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M3-FAMILY-SPECIES` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 31, 32, 33, 34, 38.
**Gate:** hard dependency on M2's idea 14 (Species Classification) and idea 43 (population seeding) — both
confirmed as real blockers, not soft preferences, in Cross-Cutting Risk.

## Problem

The reproduction/marriage/coming-of-age arc — the first milestone that gives an entity a real life path
instead of a fixed stat block. Highest Direction Fit and Narrative Generativity scores of any cluster in
`docs/brainstorm/design_merit_scorecard.html` (idea 34 scores 5/5 on both), and the deepest internal
sequencing of any milestone this size.

## Scope (not yet broken into child tickets)

**Build order (revised, plan-owner decision 2026-08-29): Marriage is decoupled from Reproduction.** Idea 33
is no longer a gate — it proceeds independently once its own proposal-lifecycle prerequisites clear. Order:

1. **Idea 32 — Reproduction.** Splits three ways by species (natural creatures reuse Camp's maturity
   mechanic, magical/demonic beings reuse the calamity substrate, human/humanoid needs a genuinely new
   cadence-gated sub-phase). The single highest-cost, highest-risk idea in the whole 65-idea set per the
   Merit Scorecard (Efficiency 1/5, Risk-Adjusted Cost 1/5) — explicitly not a "quick" milestone item
   despite M3's small idea count. **Content note:** the population-pressure gate has a real, concrete
   numeric anchor already coded (`migration_threshold: float = 0.7` in `demographics/cohort.py`) — the best
   candidate in the whole roadmap for the real (never-yet-used) metamorphic balance lab once the
   births-don't-feed-back-into-the-gating-signal gap this card names is closed. Birth cooldowns and the
   genetic-inheritance multiplier range have no comparable existing anchor. **World-generation note (M8):**
   this idea cannot be corpus-tested in any real profile today, for two stacked reasons — `population_cohorts`
   is unseeded everywhere (same root cause as M2's idea 43), and no reproduction/capacity-gating mechanism
   exists in code at all. Sequence any real corpus-testing work for this idea strictly after idea 43 (M2)
   and this ticket itself both ship — see `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md`.
2. **Idea 38 — Close the reproduction population-pressure feedback loop.** Depends on idea 32 landing
   first, immediately after or atomically with it; the signal it nudges doesn't exist without M2's idea 43
   either. The acceptance text forbids exposing repeatable births before this loop can incorporate them into
   the aggregate pressure signal.
3. **Idea 31 — Personal Dependents & Responsibility.** Small, well-precedented — gives `heir_entity_id`'s
   real write-path a reason to fire.
4. **Idea 34 — Coming of Age.** The single most depended-on idea in the entire late-game chain (Leverage
   5/5). Fires alongside M1's idea 20 (Life Stages) and needs idea 32's birth record to exist first — this
   plan must not place Coming of Age before that birth record. **Content note:** the personality/occupation/
   regional-need archetype-choice weighting has no existing numeric precedent — a free judgment call. Guard
   the known convergence-risk bug class this card itself flags (children in the same regional shortage all
   converging on one occupation) with a metamorphic rule: increasing the regional-need weight should push
   the distribution, not collapse its variance to zero.

**Idea 33 — Marriage (independent).** The first genuine two-party propose/accept handshake anywhere in the
codebase — fits Contracts' existing offer/accept shape better than a new phase. May be ticketed and built in
parallel with 32/38/31/34 once its own prerequisites clear; it is no longer a precondition for Reproduction.
This milestone also owns concrete human/species lifecycle durations and fantasy-year aging once the
temporal-axis calendar authority is settled (see the parent roadmap's "Temporal axis" section) — no numeric
threshold here is changed by this review pass.

## Out of Scope

- Anything from Milestones 1, 2, 4, 5, or 6.
- Any inheritance/legacy mechanic building on top of idea 32's birth records (ideas 53, 55, 58 — M5).

## Acceptance Signal

- All 5 ideas exist as child tickets in the build order above.
- Idea 32's population-growth risk (explicitly named in its own atlas card and independently in Cross-
  Cutting Risk) has an owner and a concrete mitigation before this milestone ships, not just a flag.
- **The individual-births-don't-feed-back-into-the-aggregate-signal gap (idea 32's own card, idea 38) is
  closed and a real metamorphic-lab result exists** for "increasing population-pressure threshold should not
  increase birth rate" before this milestone is considered balanced, not just functionally correct. Reuses
  the M2 pilot's proven lab setup rather than validating the tool a second time.
- Idea 34's archetype-choice weighting has a metamorphic check in place against the convergence-risk bug
  class its own card names — not just a manual spot-check at review time.

## Open Questions

- Idea 32's Merit Scorecard cost/risk profile (the worst in the set on both axes) may argue for splitting
  it into its own smaller epic rather than one child ticket among five — not decided here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Cross-Cutting Risk & Blast Radius, Phase Placement & Testing
  Strategy (`LINEAGE_ARENA` scenario design + explicit long-run-cost caveat for population-pressure
  convergence)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — Marriage/Reproduction
  decoupling decision, 2026-08-29
