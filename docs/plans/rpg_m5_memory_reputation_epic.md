---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 5: Memory, Reputation & Legacy

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 53, 54, 55, 57, 58, 60, 62, 63.
**Gate:** M2's idea 36 (Clan) for organization-shaped ideas, M3's idea 32 (Reproduction) for
inheritance-shaped ideas.

## Problem

Reputation, feuds, and recorded history that outlive the person who earned them. The atlas's own
investigation rejected the obvious-looking shortcut here — reusing E43 Social Memory's decay pattern as a
generic propagation engine — since that system decays one entity's own record over time (self-continuity),
not entity-to-entity transfer. What's real instead is two existing choke points every idea in this
milestone converges on.

## Scope (not yet broken into child tickets)

1. **Ideas 55 + 58 — one on-death dispatch hook, two thin handlers.** Both fire at the identical trigger
   moment (death, once `heir_entity_id` resolves) — idea 55 writes a weakened hostility/blocker transfer,
   idea 58 writes a named intention. One ticket, not two.
2. **Idea 53 — Inherited Reputation.** Simpler than originally scoped: no new decay logic needed at all —
   `RelationshipService.process_update()` has no passive decay on `public_reputation` today, so a one-time
   birth-seed write naturally gets swamped by the child's own subsequent deltas.
3. **Idea 60 — Reputations Are Local.** Its flagged "competing reputation system" risk was independently
   re-checked and downgraded: `PublicReputationProfile`'s only mutator has zero call sites anywhere — dead
   scaffolding, not a live system to reconcile with. **Must still sequence before or alongside idea 53/54**
   — confirmed independently as a real constraint, not just a hedge, since it changes the shape of the same
   field 53/54 write.
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
- Wiring `CultureDeriver`/`CulturalBiasApplicator` for the first time — a prerequisite this epic's ideas 57
  and 62 surface, shared with M4's idea 61 and M6's idea 56 (see parent roadmap's "Known open items"), not
  owned by any single ticket inside this epic.

## Acceptance Signal

- All 8 ideas land as roughly 6 child tickets per the consolidation above (55+58 as one, the rest
  individually), each citing which choke point (write-side `RelationshipService.process_update()` or
  read-side `SocialAppraisalSystem`) it touches.
- Idea 60 is sequenced before or alongside idea 53/54, not after.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Shared Implementation Opportunities, Cross-Cutting Risk & Blast
  Radius (including the determinism-fingerprint finding on `public_reputation`), Phase Placement & Testing
  Strategy (`LEGACY_PROPAGATION_ARENA` scenario design)
- `docs/plans/rpg_design_roadmap.md`
