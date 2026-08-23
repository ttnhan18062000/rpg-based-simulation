---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 2: Foundational Systems

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M2-FOUNDATIONAL-SYSTEMS` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 2, 4, 5, 6, 8, 11, 14, 23, 27, 28, 30, 35,
36, 37, 43, 48.
**Gate:** M1's idea 9 (flag-governance decision) should land first — not a hard technical dependency, but
this milestone adds the largest batch of new flag-gated behavior in the whole roadmap, and idea 9's
decision is meant to set the precedent it follows.

## Problem

16 ideas with no dependency on each other, but the highest-leverage tier of the whole 65-idea set — Species
Classification (14), City ownership (35), Clan's shape (36), population seeding (43), and place-type
transitions (48) are each cited as a hard prerequisite by multiple ideas in Milestones 3 through 6.
Building this milestone out of order means every downstream milestone redoes assumptions later.

## Scope (not yet broken into child tickets)

Highest-leverage first, per the atlas's own Build Order in-degree ranking:

1. **Idea 43 — Seed `population_cohorts` at world-compile time.** Cited by 5 later ideas; also the single
   highest-uncertainty item in the whole roadmap per Cross-Cutting Risk — the guard it activates has never
   fired against real data in any compiled world.
2. **Idea 14 — Species Classification layer.** Cross-Cutting Risk resolved the prior open question: this
   does NOT duplicate the already-shipped `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY` work — a
   genuinely separate system, safe to ticket as scoped.
3. **Idea 35 — City ownership wiring.** Confirmed wider blast radius than originally scoped: 8 real
   consumer files, not one implementation-time call.
4. **Idea 36 — Clan as Faction's shape.** `FactionState`'s shape reused almost verbatim.
5. **Idea 48 — Place-type state transitions.** Confirmed cheaper than originally scoped: extends the
   already-live `TransformationService` threshold-table engine rather than building from scratch — but
   also had a real bug in its own first draft (a proposed `.tags` field that doesn't exist at runtime).
6. **Ideas 4, 5, 6, 8, 11 — the "wire an already-built orphan" cluster.** Confirmed NOT one shared
   mechanism (Shared Implementation Opportunities) — five separately-shaped tickets. Idea 5 should
   explicitly reuse the ad-hoc `CapabilityContext` precedent from `TCK-20260811-CAPABILITY-CONFIDENCE-
   ADVENTURE-SCORING` rather than re-deriving it. Idea 8 is a keep/cut decision, not new code.
7. **Ideas 2, 23, 27, 28, 30, 37 — standalone, no cross-idea dependency.** Idea 37 is a textbook orphan
   (plumbing 100% done, lookup table missing). Idea 30 is flagged in Infrastructure Gaps as the one idea in
   the whole set needing genuinely new per-instance-identity infrastructure — scope it knowing that, not as
   a small addition.

## Out of Scope

- Anything from Milestones 1, 3, 4, 5, or 6 — tracked in their own epics.
- Building idea 30's per-instance identity layer as anything but a from-scratch design — Infrastructure
  Gaps already established there's no existing pattern to lean on.

## Acceptance Signal

- All 16 ideas exist as child tickets, each citing this epic and referencing whichever Cross-Cutting Risk /
  Shared Implementation Opportunities finding corrected or grounded it.
- Idea 43 and idea 14 land before any M3/M4/M5/M6 ticket that depends on them starts.

## Open Questions

- Does idea 8's cognition-schema decision block or merely inform idea 22 (M1, Relationship Roles) and idea
  24 (M1, blocked on the separate dead `MotivationModel`)? Not resolved here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Build Order, Cross-Cutting Risk & Blast Radius, Shared
  Implementation Opportunities, Infrastructure Gaps
- `docs/plans/rpg_design_roadmap.md`
