---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 6: Political Identity & Belonging

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 39, 56, 59, 65.
**Gate:** effectively everything above — the deepest single dependency chain in the whole 65-idea roadmap.
The roadmap explicitly does not recommend starting this milestone early, even speculatively.

## Problem

Four ideas, a strict sequential chain (39 &rarr; 56 &rarr; 59 &rarr; 65): a real path for allegiance to
change, a Place (City or otherwise, now that Idea 66 is promoted — see the parent roadmap) that can drift
away from its nation without a single triggering event, a person's own bond
to a specific place, and refugees who carry that bond somewhere new. High Direction Fit and Narrative
Generativity scores in the Merit Scorecard, but the least code-validated milestone in the roadmap until this
investigation ran — several real corrections landed here that changed scope, not just risk.

**Temporal axis (see the parent roadmap's "Temporal axis" section):** once ticketed, M6 owns the time needed
for affiliation, loyalty, attachment, and refugee identity to change, per the temporal-axis proposal's §13
integration plan. Not resolved or required by this review pass; a forward pointer for whoever scopes these
tickets.

## Scope (not yet broken into child tickets)

**Confirmed single contract** (plan-owner decision, 2026-08-29 — resolves a prior sequencing ambiguity
between "Drifting Loyalty before any affiliation change" and "affiliation primitive first"): idea 39 is not
split into a separate mutation-primitive/voluntary-trigger pair.

1. **Idea 39 — Affiliation's real change path.** Establishes the mutation primitive first. Confirmed the
   entire apply-path already exists and is waiting on a single writer (`IdentityUpdate.faction_set`, a fully
   wired dormant `entity_faction_changed` observability event). Real risk: `identity.faction` is read
   directly by combat/action legality itself (`engine/legality.py`, 6 confirmed call sites) — not just
   diplomatic flavor.
2. **Idea 56 — Drifting Loyalty.** Derives gradual loyalty pressure that may request or influence idea 39's
   mutation. Confirmed genuinely different mechanism kind from idea 39 (continuous background pressure vs.
   discrete event) — stays a separate ticket, sequenced before or alongside idea 39 so 39's trust gate can
   read 56's drift signal as an input. **Not blocked on unbuilt substrate (correction, 2026-09-02 — hardening
   backlog item 3, see
   [`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`](rpg_culture_drift_hardening_plan.md)):**
   `CultureDeriver`/`CulturalBiasApplicator` is real, live, and tested, not dormant — idea 56 needs to be
   scoped as a read-side consumer of `region_cultures`, pending the hardening plan's open Campaign-mode-
   reachability question (does any real corpus world actually run multi-episode Campaign mode today?).
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
- Building any new Culture Drift derivation/bias-application machinery — confirmed already complete
  elsewhere (see the correction on idea 56 above). Only idea 56's own read-side consumer work belongs here.

## Acceptance Signal

- 3 child tickets, not 4 (59+65 consolidated), landing in the order 39 &rarr; 56 &rarr; 59/65, or with an
  explicit justification for deviating from that order.
- Idea 56 is scoped as a read-side `region_cultures` consumer, not deferred waiting on substrate that
  already exists (correction, 2026-09-02).

## Open Questions

- This is the one milestone where "ready to scope in detail" and "ready to build" diverge the most — idea
  56's dependency turned out to already be resolved (2026-09-02 correction), but idea 59/65 still depend on
  every milestone before it. Worth revisiting whether this epic should stay scope-only even longer than the
  others, pending real evidence from M2's own resolution.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Cross-Cutting Risk & Blast Radius, Shared Implementation
  Opportunities, Phase Placement & Testing Strategy (`POLITICAL_IDENTITY_ARENA` scenario design)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Idea 66 promotion, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — single-contract and
  `CultureDeriver` ownership decisions, 2026-08-29
