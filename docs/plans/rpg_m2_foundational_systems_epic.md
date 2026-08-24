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

Highest-leverage first, per the atlas's own Build Order in-degree ranking — with one explicit tooling-
validation step ahead of the highest-risk content item (see the roadmap's Sequencing rules):

0. **Metamorphic-lab pilot (new, not an atlas idea — a process step).** `src/lab/metamorphic.py` is real
   and CI-tested but has never been run against real content (`data/lab_sessions/` is empty). Before idea
   37's race-relations matrix is validated through it, run one small, low-stakes pilot rule against an
   already-live, already-tuned numeric surface (e.g. `CampService`'s maturity/spawn/raid constants) to
   confirm the tool actually works end-to-end on this codebase's real data shapes. This is a tooling-trust
   step, not a design decision — keep it small and throwaway, not a general lab-adoption ticket.
1. **Idea 43 — Seed `population_cohorts` at world-compile time.** Cited by 5 later ideas; also the single
   highest-uncertainty item in the whole roadmap per Cross-Cutting Risk — the guard it activates has never
   fired against real data in any compiled world.
2. **Idea 14 — Species Classification layer.** Cross-Cutting Risk resolved the prior open question: this
   does NOT duplicate the already-shipped `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY` work — a
   genuinely separate system, safe to ticket as scoped. **Content note:** the obvious anchor for
   `intelligence_tier` (the qualitative `attribute_tendencies.intelligence` field) is a false friend —
   goblin/orc are `medium_low` intelligence but are clearly intended as high-tier per this idea's own
   framing. Use `natural_traits` containing `tool_user` instead (see Content & Balance Requirements in the
   atlas for the full 13-race breakdown). **World-generation note (M8):** `settlement_capacity` doesn't
   exist anywhere at the schema level yet — this ticket needs to add the actual field, not extend one that
   already exists. Read `docs/plans/rpg_m8_world_corpus_generation_epic.md` before scoping this ticket.
3. **Idea 35 — City ownership wiring.** Confirmed wider blast radius than originally scoped: 8 real
   consumer files, not one implementation-time call. **Depth-audit note, corrected after direct
   re-verification:** the sovereignty ownership-flip math this idea wires into is `DEATH_INFLUENCE_SHIFT =
   5.0` per relevant death, conquest at influence ≤ -50.0, liberation at influence ≥ +50.0
   (`src/world/influence.py`) — ±100 is only the influence value's clamp bound, not a trigger, and
   stronghold destruction does NOT trigger liberation (that direction is an unimplemented code comment).
   This already runs in every live sim today with zero balance validation ever — and is the direct cause of
   the atlas's own documented "conquest always shows as Monster Horde" distortion. This ticket should not
   just attribute ownership to the real faction; it inherits an unvalidated numeric surface that a
   metamorphic-lab pass should probably touch too (see Depth Beneath "Done" in the atlas).
4. **Idea 36 — Clan as Faction's shape.** `FactionState`'s shape reused almost verbatim. **Depth-audit
   note:** the Party Formation & Lifecycle precedent this and idea 40 (M4) both cite spans 5 files but has
   exactly 1 test file — budget a review of that existing test's actual coverage before assuming the
   precedent is solid ground to build on.
5. **Idea 48 — Place-type state transitions.** Confirmed cheaper than originally scoped: extends the
   already-live `TransformationService` threshold-table engine rather than building from scratch — but
   also had a real bug in its own first draft (a proposed `.tags` field that doesn't exist at runtime).
6. **Ideas 4, 5, 6, 8, 11 — the "wire an already-built orphan" cluster.** Confirmed NOT one shared
   mechanism (Shared Implementation Opportunities) — five separately-shaped tickets. Idea 5 should
   explicitly reuse the ad-hoc `CapabilityContext` precedent from `TCK-20260811-CAPABILITY-CONFIDENCE-
   ADVENTURE-SCORING` rather than re-deriving it. Idea 8 is a keep/cut decision, not new code.
7. **Ideas 2, 23, 27, 28, 30, 37 — standalone, no cross-idea dependency.** Idea 37 is a textbook orphan
   (plumbing 100% done, lookup table missing) — **and the single highest-risk content decision in the whole
   65-idea roadmap**: its race-relations hostility matrix needs values for up to 156 directed race pairs
   with zero existing signal anywhere to anchor them, feeding directly into already-live combat/legality
   checks. Scope this ticket to include running it through the real (but never-yet-used) metamorphic
   balance lab (`src/lab/metamorphic.py`) before landing, not just a correctness test — see Content &
   Balance Requirements in the atlas. Idea 30 is flagged in Infrastructure Gaps as the one idea in
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
- **The metamorphic-lab pilot (item 0) lands and passes before idea 37's ticket is started, not just before
  it's merged.** Idea 37 is not considered done on a correctness test alone — it needs a real metamorphic-
  rule result (e.g. "increasing a pair's hostility value does not decrease engagement rate between that
  pair") checked into its own ticket, not deferred to a future balance pass.
- Idea 14's `intelligence_tier` assignment uses the `tool_user`-trait anchor, not the qualitative
  intelligence attribute — verifiable directly against the 13-race roster, not left to individual judgment
  at ticket time.

## Open Questions

- Does idea 8's cognition-schema decision block or merely inform idea 22 (M1, Relationship Roles) and idea
  24 (M1, blocked on the separate dead `MotivationModel`)? Not resolved here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Build Order, Cross-Cutting Risk & Blast Radius, Shared
  Implementation Opportunities, Infrastructure Gaps
- `docs/plans/rpg_design_roadmap.md`
