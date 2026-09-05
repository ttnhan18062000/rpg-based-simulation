---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 6: Political Identity & Belonging

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (`tickets/done/` as of
2026-09-06 — all 3 child tickets landed: idea 39
(`TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`), idea 56 (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`),
idea 59/65 (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`) — epic closed)
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

1. **Idea 39 — Affiliation's real change path.** **Landed, 2026-09-06**
   (`TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`): `PartyLifecycleService.check_defection()` is now the
   first real, live producer of `IdentityUpdate.faction_set`, setting a defecting entity's faction to
   `Faction.NEUTRAL` (a NEUTRAL-sentinel design, not rival-faction selection) through the pre-existing
   authoritative apply-path; the previously dormant `entity_faction_changed` observability event now fires
   end-to-end from this real trigger. The combat/action-legality risk this bullet originally flagged
   (`identity.faction` read directly by `engine/legality.py`, 6 confirmed call sites, plus 25 further call
   sites found across `src/`) resolved as a structural consequence of `AuthoritativeApplyPipeline.refine()`'s
   existing `action_routing`-before-`groups` phase order: a same-tick faction change cannot retroactively
   affect a legality decision `action_routing` already made earlier in that same tick, so no
   `engine/legality.py` change was needed. Full contract: `docs/world/affiliation_mutation.md`.
2. **Idea 56 — Drifting Loyalty.** Derives gradual loyalty pressure that may request or influence idea 39's
   mutation. Confirmed genuinely different mechanism kind from idea 39 (continuous background pressure vs.
   discrete event) — stays a separate ticket. **Sequencing corrected, 2026-09-05**: this section previously
   said "sequenced before or alongside idea 39," which contradicted this same doc's own Acceptance Signal
   (`39 → 56 → 59/65`) — flagged by `docs/brainstorm/codex/2026-08-27-core-rpg-feature-review.md`'s "M6 —
   valuable late-game chain, but sequencing text conflicts" section. The single confirmed decision (2026-08-29,
   see References) is idea 39 lands first, establishing the mutation primitive idea 56's signal then
   requests/uses — not before or alongside it. **Not blocked on unbuilt substrate (correction, 2026-09-02 —
   hardening backlog item 3, see
   [`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`](rpg_culture_drift_hardening_plan.md)):**
   `CultureDeriver`/`CulturalBiasApplicator` is real, live, and tested, not dormant — idea 56 needs to be
   scoped as a read-side consumer of `region_cultures`. **Campaign-mode-reachability question answered,
   2026-09-05** (same hardening plan): real but narrow — exactly one corpus profile
   (`campaign_life_arc.yaml`) enables multi-episode Campaign mode, hardcoded to one world, and it is not wired
   into standard CI. Idea 56's own ticket should test against that one real profile directly, not assume
   corpus-wide coverage.
   **Status update, 2026-09-05** (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`): shipped. Reuses the
   already-live `CultureState.faction_conflict_exposure` axis (no new derivation logic) via a new
   `LoyaltyDriftService`, keyed by an entity's *current* region (`entity.navigation.region_id` — real
   and live-populated for every entity today, not `home_region_id`, which is boss-only until idea 59
   lands). Wired as a real, tested, optional `loyalty_pressure` parameter on
   `PartyLifecycleService.effective_defection_threshold()`/`check_defection()`, lowering the grievance
   threshold idea 39's `Faction.NEUTRAL` mutation trigger reads. **Disclosed gap**: the one live
   per-tick caller, `GroupPhase.resolve()`, has no `CampaignState` access (no bridge exists between
   per-tick `AuthoritativeState` and episode-boundary `CampaignState`), so it still supplies only the
   backward-compatible `0.0` default — the signal is real and end-to-end tested via a Culture-Drift
   integration test, but not yet visible in the default single-episode Kernel path. Full contract:
   `docs/world/culture_drift_contract.md`.
3. **Idea 59 — Home, Exile & Return.** The single largest correction in this whole investigation: its
   central claim (no per-entity place-attachment field exists) was flatly wrong.
   `StrategicComponent.home_region_id` already exists, typed, with a live consumer already wired
   (`RoutineService.evaluate_anchored_behavior()`'s "return home" concern). This ticket is
   populate-an-existing-field, not invent-new-state — materially cheaper than originally scoped.
   **Landed, 2026-09-06** (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`): `home_region_id` is now
   populated at birth (`src/world/reproduction_humanoid.py` resolves the spawn region and passes
   it into `EntityGenerator.spawn_humanoid_offspring()`) via the new
   `StrategicUpdate.home_region_id_set` field, whose `StrategicPatch.apply()` resolution is
   deliberately reversed from every other `_set` field: an already-set value always wins over a
   proposed update, so a refugee's original home is never overwritten.
4. **Idea 65 — Named Refugee Threads.** Folds into idea 59's ticket as extra acceptance criteria (writing
   `home_region_id` at displacement time) rather than a separate ticket, per Shared Implementation
   Opportunities. **Landed, 2026-09-06** (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`): new
   `DisplacementService.compute_displacement()` (`src/world/displacement.py`) relocates living
   entities out of any region at or above `calamity_intensity` 0.6 into their lowest-intensity
   adjacent region, carrying `home_region_id` forward via idea 59's mechanism if it was still
   unset. Confirmed end-to-end that `RoutineService.evaluate_anchored_behavior()`'s pre-existing
   "return home" concern correctly targets the displaced entity's original home, not their new
   physical location. Full contract: `docs/world/home_exile_refugee_contract.md`.

## Out of Scope

- Anything from Milestones 1 through 5.
- Building any new Culture Drift derivation/bias-application machinery — confirmed already complete
  elsewhere (see the correction on idea 56 above). Only idea 56's own read-side consumer work belongs here.

## Acceptance Signal

- 3 child tickets, not 4 (59+65 consolidated), landing in the order 39 &rarr; 56 &rarr; 59/65, or with an
  explicit justification for deviating from that order. All 3 landed 2026-09-06, on order.
- Idea 56 is scoped as a read-side `region_cultures` consumer, not deferred waiting on substrate that
  already exists (correction, 2026-09-02).
- **Epic closed, 2026-09-06**: all 4 design ideas (39, 56, 59, 65) landed across the 3 confirmed
  child tickets; `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` moved to `tickets/done/`.

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
- `docs/world/affiliation_mutation.md` — idea 39's landed write-path contract
  (`TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`)
