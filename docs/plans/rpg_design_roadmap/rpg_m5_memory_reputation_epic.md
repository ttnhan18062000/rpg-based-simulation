---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 5: Memory, Reputation & Legacy

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 53, 54, 55, 57, 58, 60, 62, 63.
**Gate:** M2's idea 36 (Clan) for organization-shaped ideas, M3's idea 32 (Reproduction) for
inheritance-shaped ideas.

## Problem

Reputation, feuds, and recorded history that outlive the person who earned them. The atlas's own
investigation rejected the obvious-looking shortcut here — reusing E43 Social Memory's decay pattern as a
generic propagation engine — since that system decays one entity's own record over time (self-continuity),
not entity-to-entity transfer. What's real instead is two existing choke points every idea in this
milestone converges on.

**Three independent branches** (plan-owner review, 2026-08-29), proceeding in parallel once each branch's
own prerequisites clear rather than as one linear chain: **reputation** (idea 60 before ideas 53/54, per its
own field-shape constraint below); **death and lineage** (ideas 55/58, after Reproduction, heir assignment,
and correct death dispatch exist — see the permadeath repair immediately below); **history and belief**
(idea 62 before idea 57, then idea 63).

**M5 owns the final-permadeath repair** (plan-owner decision, 2026-08-29 — explicitly not part of M1's
in-flight 21-ticket batch, see `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`). Combat already
emits `outcome_kind="PERMADEATH"`, but `LifecycleSystem.resolve_lifecycle()` only deactivates an entity on
`outcome_kind=="KILL"` — a "permadead" entity stays `active=True` and keeps acting. The death-and-lineage
branch above already assumes "correct death dispatch" as a precondition; this repair is what makes that
true. Scope is narrow: recognize the terminal outcome and preserve the intended succession/death
consequences through the existing authoritative pipeline, nothing beyond that.

**Temporal axis (see the parent roadmap's "Temporal axis" section):** once ticketed, M5 owns persistence,
decay, testimony, generational transfer, and historical-memory horizons, per the temporal-axis proposal's
§13 integration plan. Not resolved or required by this review pass; a forward pointer for whoever scopes
these tickets.

**Social/Political mechanics hardening (see the parent roadmap's "Hardening backlog" section, item 1):**
[`docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`](rpg_social_narrative_mechanics_hardening_plan.md)
documents and hardens the `SocialComponent`/`SocialBond`/`RelationshipService` state this milestone's
reputation and history/belief branches both build on — a prerequisite documentation/verification pass these
tickets can cite once scoped, not a substitute for their own investigation.

**Social/Relationship axis (see the parent roadmap's own section, added 2026-09-02):**
[`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`](../../brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md)
is the fuller, temporal-proposal-depth treatment the hardening plan above feeds into — full field inventory,
a real determinism gap (`CanonicalStateHasher` covers only 10 of 15 `SocialComponent` fields), and a
per-idea integration table covering this milestone's own 53-63 range plus idea 67.

**Candidate new idea, added to the atlas 2026-09-02, not yet folded into this milestone's committed scope:**
idea 67, Living Relationship Decay (`docs/brainstorm/rpg_feature_atlas.html#idea-67`,
`docs/brainstorm/rpg_expected_schemas.html#schema-67`) — a passive trust/grudge decay rule for living
entity pairs, distinct from this milestone's idea 55 (inherited feuds, a death-time transfer) and M6's idea
56 (population-scale loyalty). Natural home is here given it targets the same `SocialComponent`/
`RelationshipService` surface this milestone's other ideas already touch, but it is a candidate to review
and schedule, not yet one of the 8 ideas this epic's Scope commits to below.

## Scope (not yet broken into child tickets)

1. **Ideas 55 + 58 — one on-death dispatch hook, two thin handlers.** Both fire at the identical trigger
   moment (death, once `heir_entity_id` resolves) — idea 55 writes a weakened hostility/blocker transfer,
   idea 58 writes a named intention. One ticket, not two.
2. **Idea 53 — Inherited Reputation.** Simpler than originally scoped: no new decay logic needed at all —
   `RelationshipService.process_update()` has no passive decay on `public_reputation` today, so a one-time
   birth-seed write naturally gets swamped by the child's own subsequent deltas.
   **Status update, 2026-09-04:** shipped as `TCK-20260904-INHERITED-REPUTATION-SEED`. Added a pure
   `ReputationService.combine_public_reputation(parent_a, parent_b) -> float` (simple arithmetic mean,
   clamped `[0.0, 2.0]`), wired through `V2EntityBuilder.birth_record()`'s new
   `parent_a_public_reputation`/`parent_b_public_reputation` kwargs — an AND-gate (both parent values
   required, unlike idea 53's genetics-precedent OR-gate) that falls back to the class default `1.0`
   otherwise, since `public_reputation` never has a missing-value case to backfill. Real parent values are
   wired at `HumanoidReproductionService.process_reproduction()`'s call site, through
   `EntityGenerator.spawn_humanoid_offspring()`. The parentless natural-creature/magical-demonic spawn
   paths, `RelationshipService.process_update()`'s decay-free behavior, `regional_reputation`, and
   `ReputationUpdateService`/`PublicReputationProfile` are all untouched, matching this item's own scope.
   Documented in `docs/mechanics/01_entity_anatomy.md` §5 "Reputation Seed" and
   `docs/parity_ledger/social_narrative.yaml` (SOC-267).
3. **Idea 60 — Reputations Are Local.** Its flagged "competing reputation system" risk was independently
   re-checked and downgraded: `PublicReputationProfile`'s only mutator has zero call sites anywhere — dead
   scaffolding, not a live system to reconcile with. **Must still sequence before or alongside idea 53/54**
   — confirmed independently as a real constraint, not just a hedge, since it changes the shape of the same
   field 53/54 write.
   **Status update, 2026-09-04:** shipped as `TCK-20260904-REPUTATION-LOCALITY-SCOPE`, ahead of idea 53
   as sequenced. Added `SocialComponent.regional_reputation: Dict[str, float]` (region-scoped, `[0.0, 2.0]`
   clamp) additive to the retained, unchanged global `public_reputation` scalar, wired through
   `RelationshipService.process_update()` as the sole authoritative writer, with both determinism surfaces
   (`to_canonical_dict()`, `StateFingerprinter`) and an architecture guard test added. This annotation was
   added retroactively by idea 53's own doc-update pass — idea 60's ticket closed without one.
4. **Idea 54 — Guilt by Association.** Gated on M2's idea 36 (Clan) existing as real state.
5. **Idea 57 — The Living Legend Feedback Loop.** Its own original claim ("nothing reads Chronicle's output
   back into anything") was wrong — `CultureDeriver` already does, at region scale, via Cultural Drift.
   Should copy `CultureDeriver`'s aggregation shape rather than invent new event-scoring logic.
6. **Idea 62 — Generations Misremember.** Genuinely distinct from idea 57, not a duplicate — sits upstream
   of both idea 57's and Cultural Drift's consumption of Chronicle's output, as a single transform view.
7. **Idea 63 — Belief Grows Around Real History.** Confirmed a genuine downstream composite, needing both
   idea 36 (Clan, as container) and idea 57 (fame substrate) first — not a thin wrapper on either.

## Out of Scope

- Anything from Milestones 1, 2, 3, 4, or 6.
- Building any new Culture Drift derivation/bias-application machinery — **correction, 2026-09-02**
  (hardening backlog item 3, see
  [`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`](rpg_culture_drift_hardening_plan.md)):
  `CultureDeriver`/`CulturalBiasApplicator` was never actually dormant — it's real, live, and tested. Ideas
  57 and 62 need only their own read-side consumption of `region_cultures`, not a first-time-wiring
  prerequisite owned elsewhere.

## Acceptance Signal

- All 8 ideas land as roughly 6 child tickets per the consolidation above (55+58 as one, the rest
  individually), each citing which choke point (write-side `RelationshipService.process_update()` or
  read-side `SocialAppraisalSystem`) it touches.
- Idea 60 is sequenced before or alongside idea 53/54, not after.
- The final-permadeath repair (a bug, not one of the 8 design ideas) lands before or alongside ideas 55/58,
  since both assume correct death dispatch already exists.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Shared Implementation Opportunities, Cross-Cutting Risk & Blast
  Radius (including the determinism-fingerprint finding on `public_reputation`), Phase Placement & Testing
  Strategy (`LEGACY_PROPAGATION_ARENA` scenario design)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, permadeath ownership, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — branch split and permadeath
  ownership decision, 2026-08-29
