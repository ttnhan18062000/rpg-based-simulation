---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 6: Political Identity & Belonging

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 39, 56, 59, 65.
**Gate:** effectively everything above — the deepest single dependency chain in the whole 65-idea roadmap.
The roadmap explicitly does not recommend starting this milestone early, even speculatively.

## Problem

Four ideas, a strict sequential chain (39 &rarr; 56 &rarr; 59 &rarr; 65): a real path for allegiance to
change, a City that can drift away from its nation without a single triggering event, a person's own bond
to a specific place, and refugees who carry that bond somewhere new. High Direction Fit and Narrative
Generativity scores in the Merit Scorecard, but the least code-validated milestone in the roadmap until this
investigation ran — several real corrections landed here that changed scope, not just risk.

## Scope (not yet broken into child tickets)

1. **Idea 39 — Affiliation's real change path.** Confirmed the entire apply-path already exists and is
   waiting on a single writer (`IdentityUpdate.faction_set`, a fully wired dormant `entity_faction_changed`
   observability event). Real risk: `identity.faction` is read directly by combat/action legality itself
   (`engine/legality.py`, 6 confirmed call sites) — not just diplomatic flavor.
2. **Idea 56 — Drifting Loyalty.** Confirmed genuinely different mechanism kind from idea 39 (continuous
   background pressure vs. discrete event) — stays a separate ticket, sequenced before or alongside idea
   39 so 39's trust gate can read 56's drift signal as an input. Blocked on the same `CultureDeriver`
   substrate as M4's idea 61 and M5's ideas 57/62.
3. **Idea 59 — Home, Exile & Return.** The single largest correction in this whole investigation: its
   central claim (no per-entity place-attachment field exists) was flatly wrong.
   `StrategicComponent.home_region_id` already exists, typed, with a live consumer already wired
   (`RoutineService.evaluate_anchored_behavior()`'s "return home" concern). This ticket is
   populate-an-existing-field, not invent-new-state — materially cheaper than originally scoped.
4. **Idea 65 — Named Refugee Threads.** Folds into idea 59's ticket as extra acceptance criteria (writing
   `home_region_id` at displacement time) rather than a separate ticket, per Shared Implementation
   Opportunities.

## Out of Scope

- Anything from Milestones 1 through 5.
- Wiring `CultureDeriver`/`CulturalBiasApplicator` — the shared blocker idea 56 surfaces, owned wherever
  M4/M5's identical blocker gets resolved, not duplicated here.

## Acceptance Signal

- 3 child tickets, not 4 (59+65 consolidated), landing in the order 39 &rarr; 56 &rarr; 59/65, or with an
  explicit justification for deviating from that order.
- Idea 56 is not built ahead of its `CultureDeriver` dependency clearing.

## Open Questions

- This is the one milestone where "ready to scope in detail" and "ready to build" diverge the most — three
  of its four ideas either depend on a not-yet-wired substrate or on every milestone before it. Worth
  revisiting whether this epic should stay scope-only even longer than the others, pending real evidence
  from M2 and M4/M5's shared blocker resolution.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Cross-Cutting Risk & Blast Radius, Shared Implementation
  Opportunities, Phase Placement & Testing Strategy (`POLITICAL_IDENTITY_ARENA` scenario design)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/plans/rpg_design_roadmap.md`
