---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 1: Quick Wins & Housekeeping

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M1-QUICK-WINS` (not yet created — this epic is scope-only,
per `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Rev 60+ (Design Ideas 1, 3, 7, 9, 10, 12, 13, 15-19, 20,
21, 22, 24, 25, 26, 29, 42), cross-checked against Cross-Cutting Risk, Shared Implementation Opportunities,
Phase Placement & Testing Strategy, and `docs/brainstorm/design_merit_scorecard.html`.
**Priority:** P1 — this is the milestone the roadmap itself has zero dependencies on; every other milestone
gates on something upstream of it.

## Problem

20 real, already-investigated gaps sit in the engine today with no design work left to do — half-finished
formulas, orphaned systems with a working consumer already waiting, two confirmed bugs, and five technical
questions that were genuinely unresolved until a follow-up trace answered them directly. None of this needs
new mechanism design; all of it needs someone to actually build the small thing the investigation already
specified. This epic exists to turn "well-understood gap" into "ticketed."

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Prospective child tickets, grouped by shape, not build order
(see Acceptance Signal below for the one real sequencing note):

### A — Governance decision (do this first within M1)

1. **Idea 9 — Decide the eight rollout flags on purpose.** Self-Model, World Emergence, Progression
   Conversion, Combat Engagement, Social Cooperation, Belief Assimilation, Information Intent Execution,
   and Guild Quest Generation are all real, correctly-built, and flag-gated OFF. This ticket is a per-flag
   keep/cut/flip decision, not new code — but M2 onward adds 38 more flagged ideas on top of this precedent,
   so deciding it first, not last, is the point.

### B — Now-resolved technical questions (each needs a real fix or an explicit keep-as-is decision, not just documentation)

2. **Idea 15 — Wound threshold: 25% is the live value, 40% is dead code.** Decide: delete
   `WoundService.should_inflict_wound()`'s unreachable branch, or leave it and correct
   `docs/mechanics/02_combat_laws.md` and `01_entity_anatomy.md`'s cross-reference so the divergence isn't
   re-discovered later.
3. **Idea 17 — Wound/Scar penalty mechanics.** The severity-scaled formula this card originally described
   is dead code; live combat uses a flat `penalty=5.0` for attack/defense only, and no wound has ever
   healed in production (`WoundUpdate.wounds_heal` has zero producers). Two real decisions bundled: wire
   the severity-scaled formula in for real (replacing the flat one), and decide whether healing should ever
   fire, or whether "wounds are permanent until a Scar forms" is the intended design.
4. **Idea 18 — Route/activity kind count.** `docs/mechanics/adventure_routing_contract.md`'s table is stale
   by exactly 3 entries (16 real values, not 13). Doc fix.
5. **Idea 19 — ALLOCATE_AP reachable but never invoked.** A real, unconditional branch exists with two live
   entry points; nothing has ever constructed a payload that reaches it. Decide: wire a real producer, or
   leave it as intentionally-dormant AI-proposal-path scaffolding and document why.

Idea 16 (Ranger doctrine) needs no ticket — already answered by a separate, already-published atlas card
(the "Class" finding); this item is closed by cross-reference.

### C — Wire the real orphans

6. **Idea 1 — Wire the remaining orphans.** Nine originally, now seven after two folded into items 13 and
   (M3's) Reproduction per Shared Implementation Opportunities — see the atlas card for the full checklist.
7. **Idea 3 — Finish `BreakthroughService.apply_bonuses()`.** A literal `pass`; three real breakthroughs
   with real attribute bonuses already sit in the registry, earned but never applied.
8. **Idea 7 — Extend Grief/Nemesis past episode boundaries.** `GriefUrgencyImporter`/`NemesisRelationImporter`
   are real and live, called only from `CampaignOrchestrator._build_initial_state()` — extend the same
   trigger to fire on an in-episode death, not just at Campaign start. **Depth-audit correction:** this idea
   fails on three axes at once, not just the trigger-point gap above — Campaign mode has zero scenario
   content wiring it in anywhere (may only ever run via manual CLI), no SimQ event type exists for it (this
   idea's own success can't be measured once built), and `check_nemesis_promotion()`/`tick_place_attachment()`
   (the functions doing the real work) have zero test coverage. Scope this ticket as "make it reachable,
   measurable, and tested, then extend it" — see Depth Beneath "Done" in the atlas and this idea's own card.
9. **Idea 12 — Wire contradiction detection into the live Leads system.** Skips the flag trap by hanging
   off `BeliefContradictionService` directly — but Phase Placement & Testing Strategy found a sibling
   orphan (`LeadContradictionSystem`) that must be wired in the same ticket, or 3 of 4 lead kinds stay
   permanently unable to resolve via world-state contradiction.
10. **Idea 26 — Expertise Earned Through Living.** `MemoryUpdatePhase` has zero call sites; its consumer
    (`AdventureRouteScorer.score()`) already reads 2 of 10 possible advice values from causal memory that
    never populates. Proposed insertion point (Phase Placement): between `PP-02` and `PP-03`.

### D — Confirmed bugs

11. **Idea 10 — Assign heirs from what already exists.** `heir_entity_id`'s transfer mechanic is fully
    wired and confirmed live; only assignment is missing. `RelationshipService`'s per-pair `SocialBond` data
    is sufficient to pick a default.
12. **Idea 42 — Fix the `town_center` pointer bug.** Deepened past the original finding: two more broken
    consumers found (`FlowFieldService`, a second parallel `town_center` field on the worker-protocol
    dataclass), plus a second, subtler bug in the two consumers that DO have a fallback — both pick one
    arbitrary tile across every town in the world, not the nearest one to the entity asking.

### E — New small mechanisms

13. **Idea 13 — Gate Team-Up/Trade/Paid-Information on affection.** Build this as the shared
    `appraise_contract()` threshold-gate helper Shared Implementation Opportunities identifies — a 6-idea,
    3-milestone cluster (this idea, Conversation, and later M6's ideas 39/40) all converge on the identical
    formula. Building the helper once here means M6 extends it later instead of re-deriving it.
14. **Idea 20 — Life Stages & Rites of Passage.** The consumer (`LifeStageService.get_goal_multipliers()`)
    already runs unflagged inside the Strategic Intelligence Core. What's missing: `identity.life_stage`
    has no writer anywhere — no `life_stage_set` field exists on `IdentityUpdate` today. New typed field +
    apply-path work required before any transition trigger can fire.
15. **Idea 21 — Careers, Apprenticeships & Changing Occupations.** `IdentityUpdate.role_set` already has a
    full live apply path with 12 confirmed consumers (routine, adventure scoring, crafting, combat/rewards,
    movement/spawn priority, legality, military conflict, cooperation, evolution) — the largest confirmed
    blast radius of any Milestone 1 idea. Only the transition trigger is missing.
16. **Idea 22 — Relationship Roles, Not Just Relationship Scores.** `SocialBond` has exactly three fields
    today; adding a role concept is additive. Real risk (Merit Scorecard): a label with no consumer is
    invisible — this codebase has a track record of adding fields nothing ever reads (see idea 8's cognition
    schema). Scope the consumer alongside the field, not as a follow-up.
17. **Idea 29 — Injury That Changes a Life, Not Just a Number.** The Tactical Decision System already
    reacts to raw HP ratio; it never reads structured `WoundState`/`ScarState` data. Wire the real data in.

### F — Scope-ready but with a real upstream blocker (list here for completeness, don't start until noted)

18. **Idea 24 — Personal Economy & Material Ambition.** Wants to attach to `MotivationModel.values`
    (`ValuePreferenceProfile`), which is independently confirmed dead-on-arrival — never populated above
    its 0.5 defaults. Building on top of a dead foundation inherits nothing. **Do not start this ticket
    until that foundation ticket exists and is scoped** (not part of this epic — flag as a dependency to
    resolve first, likely worth its own idea/ticket outside the current 65).
19. **Idea 25 — Secrets, Confidence & Selective Disclosure.** Extends the Information Sourcing/Trust system
    almost exactly, but that whole system is flag-gated OFF (`ENABLE_BELIEF_ASSIMILATION`-adjacent) with a
    documented "flipping the flag alone activates a phase with nothing to process" trap (idea 12's own
    finding). Scope this ticket, but sequence it after whatever ticket actually gets that system live.

## Out of Scope

- Any idea numbered 2, 4-6, 8, 11, 14, 23, 27, 28, 30-41, 43-65 — all belong to Milestones 2 through 6,
  tracked in their own sibling epics per `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`. (Idea 42 is in M1's own scope,
  section D above — deliberately excluded from this range, not an oversight.)
- Actually flipping any of the 8 flags idea 9 evaluates — that's the outcome of item 1's ticket, not a
  decision made in this planning doc.
- Fixing `MotivationModel.values`/`ValuePreferenceProfile`'s dead-on-arrival state (item 18's real
  blocker) — that's a prerequisite this epic surfaces, not a task it owns.

## Acceptance Signal for This Epic (not yet broken into child tickets)

- All 19 prospective tickets above exist in `tickets/` (18, since idea 16 needs none), each referencing this
  epic and its source idea number in the atlas.
- Idea 9's flag-governance ticket lands before any other M1 ticket that adds new flag-gated behavior, per
  the sequencing note in section A.
- Items 24 and 25 (section F) are either explicitly deferred with their blocker ticket referenced, or their
  blocker is resolved first — not silently built on a foundation already known to be broken.
- `docs/brainstorm/rpg_feature_atlas.html`'s own Roadmap section estimate (roughly 18 tickets for this
  milestone) holds, or the discrepancy is explained.

## Open Questions

- Does idea 24's motivation-framework blocker get its own ticket inside this epic, or does it belong to a
  different milestone/epic entirely? Not resolved here — flagged for whoever scopes item 18's child ticket.
- Should idea 13's shared threshold-gate helper be built to already anticipate M6's ideas 39/40 consumers,
  or built minimally for its own three consumers (Team-Up/Trade/Paid-Info) and extended later? Leaning
  toward anticipating it, since the shape is already fully specified in Shared Implementation Opportunities
  — but not decided here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — ideas 1, 3, 7, 9, 10, 12, 13, 15-22, 24-26, 29, 42; Cross-Cutting
  Risk & Blast Radius; Shared Implementation Opportunities; Phase Placement & Testing Strategy
- `docs/brainstorm/design_merit_scorecard.html` — per-idea scores
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, sequencing rules
