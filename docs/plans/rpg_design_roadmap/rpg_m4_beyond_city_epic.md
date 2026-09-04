---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 4: Beyond the City & the Layer Model

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M4-BEYOND-CITY` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Design Ideas 40, 41, 44, 45, 46, 47, 49, 50, 51, 52, 61,
64.
**Gate:** M2's idea 35 (City ownership), idea 36 (Clan's shape), and idea 48 (place-type transitions).

## Problem

The settlement-capacity tier below City (Camp, Nest, Lair), plus the rest of the layer-model wiring theme —
where places stop being static and start having texture. 12 ideas, the most internally clustered milestone
in the roadmap: Shared Implementation Opportunities found real consolidation across most of it.

**Three branches with different gating** (plan-owner review, 2026-08-29): **place-shaped ecology and
settlements** (ideas 44-47, 61) satisfy Idea 66's gate first if it's promoted (it is — see the parent
roadmap), otherwise the accepted replacement Place boundary must be resolved first; **material exploration
and national expansion** (ideas 49-52) apply the Idea 66 gate only to outcomes that authoritatively use
Place identity/containment, at ticket scope, not milestone-wide; **institutions and economic signals**
(ideas 40, 41, 64) keep their own Clan-lifecycle, information-activation, and vacancy-signal prerequisites
and are not blocked on Idea 66 at all.

**Correction, 2026-09-02 (hardening backlog item 3 — see
[`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`](rpg_culture_drift_hardening_plan.md)):**
`CultureDeriver`/`CulturalBiasApplicator` is NOT a dormant substrate needing activation — direct
investigation confirmed it's complete, live, tested (`docs/world/culture_drift_contract.md`:
`AUTHORITATIVE`, E62A-E62C), and has a real live call site
(`src/domains/campaigns/orchestrator.py:226-230`). The earlier "M4 owns activation" framing below is
superseded. The real, narrower scope: that call site only fires at multi-episode Campaign episode
boundaries, so idea 61 (and M5's 57/62, M6's 56) most likely need only a read-side consumer of the real,
populated `region_cultures: Dict[str, CultureCarryForward]` state — see the hardening plan doc for the
open Campaign-mode-reachability question this still needs answered.

**Temporal axis (see the parent roadmap's "Temporal axis" section):** once ticketed, M4 owns seasonal
settlement, economy, vacancy, apprenticeship, and travel cadence, per the temporal-axis proposal's §13
integration plan. Not resolved or required by this review pass; a forward pointer for whoever scopes these
tickets.

## Scope (not yet broken into child tickets)

1. **Ideas 44 + 45 + 46 — Settlement population/identity, consolidated.** Confirmed real: collapses to
   roughly 2 tickets, not 3 — one `CampService` extension covers Camp seeding/texture and Nest as a variant
   swapping the raid branch for a spread branch. **Content note:** idea 44's own city/camp/nest heuristic
   doesn't fully reproduce itself against real race data (goblin has `social_humanoid`, contradicting the
   card's claim) and leaves 5 of the 13 real races unclassified — resolve that judgment call before ticketing,
   not during. 45/46's Camp features (totem, stockpile, palisade) reuse real, already-tuned constants
   (`RAID_MATURITY_THRESHOLD`, spawn cap, raid cost) for the mechanism but still need new, unanchored
   magnitudes for the features themselves — see Content & Balance Requirements in the atlas.
   **Status update, 2026-09-04:** the classification-and-CampService half of this item has shipped as
   `TCK-20260904-CAMP-NEST-CLASSIFICATION` — the goblin `social_humanoid` contradiction is resolved
   (the real discriminator is `drive_profile == "opportunistic_raider"`, not `social_humanoid`) and all
   5 previously-unclassified races got an explicit disposition (wolf/spider/troll/slime → Nest;
   undead/spirit → Excluded/no-fit; dragonkin → Excluded/Lair-adjacent), documented in
   `docs/mechanics/05_world_evolution.md` §6. `CampService` gained a flag-gated (`ENABLE_CAMP_NEST_SPREAD`,
   default OFF) Nest-spread fork reusing the raid branch's timing/cost, plus provisional
   (unpopulated-by-production-code) `totem_tier`/`stockpile`/`palisade_integrity` typed fields on
   `CampState`/`CampUpdate`. The world-generation gap below remains fully open — that ticket explicitly
   did not construct or seed any `CampState`, and feature magnitudes/accrual logic for
   totem/stockpile/palisade are still undefined, left to a follow-on ticket
   (`TCK-20260904-CAMPSTATE-PLACE-BRIDGE` covers the world-gen wiring half).
   **World-generation note (M8) — closed, 2026-09-04, by `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`.**
   The original note below ("`CampState` is never constructed in production anywhere... needs a new
   `WorldModuleSpec` field plus a new `WorldCompiler` step") is now stale — idea 66's `Place` hierarchy
   already gave `WorldCompiler.compile()` a generic insertion point for `kind=CAMP`/`kind=NEST`
   `PlaceState` construction, and the bridge ticket closed the remaining gap with only a narrow, additive
   change: an optional `creature_kind: Optional[str]` field on `PlaceRecipeSpec`/`PlaceSpec` (CAMP/NEST-
   scoped, `None` by default) plus a branch inside the *existing* Place-construction loop that builds a
   companion `CampState`, keyed by the same `place_id`, when that field is set. No new `WorldModuleSpec`
   field and no new `WorldCompiler` step were needed. The bridge is opt-in and inert for all content on
   disk today (including `hero_guild_routing`'s `goblin_camp_place`) — migrating real content to set
   `creature_kind` remains a separate, deliberately-deferred future step. See
   `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` item 2 (updated in the same
   ticket) for the as-built framing. Good news from the same epic: 3 of the 6 real test-corpus profiles
   already have City+hostile-camp content coexisting, so testing this needs zero new corpus authoring
   once real content opts in.
2. **Idea 47 — Lair.** Confirmed a genuinely separate ticket, correctly NOT a Camp variant — but its real
   precedent is Boss's entity-anchor idempotency pattern (`boss_region_id`), not Camp's shape, a correction
   from the original card. **Depth-audit note:** boss-spawn logic itself has zero dedicated test files
   ("boss" appears in none of them) — this ticket is extending an untested precedent, budget test-writing
   for the base mechanism, not just the extension.
   **Status update, 2026-09-04:** shipped as `TCK-20260904-LAIR-ENTITY-ANCHOR`. `BossService` gained a new
   `check_for_lair_spawn` method (`src/world/boss.py`), a direct sibling of `check_for_boss_spawn`,
   generalizing the same entity-property idempotency pattern from per-`region_id` keying
   (`boss_region_id`) to per-`place_id` keying (`identity.properties["lair_place_id"]`), so multiple
   LAIR-kind Places in one Region each get an independent spawn slot. **Option A chosen:**
   `PlaceState.occupant_entity_id` stays write-never — the lock lives entirely on the occupant entity's
   properties, not on the Place, so no new `PlaceUpdate`/apply-path plumbing was added. Wired into
   `WorldDynamicsSystem.resolve_dynamics` reusing the existing `cadence.boss_spawn` gate and
   `state.maturity`/`region.trauma_score` thresholds unchanged — no new cadence or trigger condition.
   Occupants spawn with `kind="dragonkin"`, which required extending
   `src/observability/event_extractor.py`'s `spawn_cadence_fired` exclusion tuple and `_BOSS_KINDS`
   frozenset (rollback-path lists only) so Lair spawns are correctly excluded from cadence-spawn
   misclassification and emit `boss_spawned`. The depth-audit note above is now partially addressed:
   `test_world_dynamics.py` gained 4 new Lair-spawn tests (fill/idempotency/multi-Place/no-dissolution)
   alongside the original boss idempotency test, though `check_for_boss_spawn` itself still has no
   dedicated test file of its own. Content is a synthetic fixture only
   (`test_lair_kind_place_compiles_via_worldcompiler`) — no real corpus world has LAIR-kind content yet,
   matching the CAMPSTATE-PLACE-BRIDGE precedent's own deferred-content discipline. Lair
   dissolution/transformation on occupant death (idea 48, place-type transitions) remains explicitly
   deferred and un-ticketed, guarded by a new negative test proving this ticket's code never mutates
   `PlaceState.kind`/`prior_kind`/`transformed_tick`.
3. **Idea 61 — Settlements Develop Personalities.** Re-scoped by a real correction: its original cited
   precedent (idea 48) was wrong; the actual live match is Culture Drift's `CultureDeriver`/
   `CulturalBiasApplicator`. **Not blocked** (correction, 2026-09-02, see the Problem section above) — the
   substrate is real, live, and tested; this idea needs to be scoped as a read-side consumer of
   `region_cultures`, with the Campaign-mode-reachability question (does any real corpus world actually run
   multi-episode?) answered before treating it as trivially unblocked in practice.
   **Status update, 2026-09-04:** shipped as `TCK-20260904-SETTLEMENT-CULTURE-READ`. The
   Campaign-mode-reachability question is answered: no corpus world runs multi-episode Campaign mode
   today. Scoped the read-side consumer to Region granularity (`RegionState.id`/`.name` —
   `PlaceState` still has no name/identity field): a new pure `SettlementPersonalityService.describe()`
   (`src/domains/culture/settlement_personality.py`, reuses `CulturalBiasApplicator.compute_culture_delta`
   unchanged), a new read-only `CampaignOrchestrator.describe_settlement_personality(region_id)` method,
   and a new `GET /api/v1/campaigns/{campaign_id}/regions/{region_id}/personality` REST endpoint with a
   shaped Pydantic presenter. The deeper reachability blocker this correction named —
   `CampaignOrchestrator._build_initial_state()` never carrying Region/Place data into per-episode
   `AuthoritativeState` — is real, confirmed independent of idea 66, and tracked by a new ticket,
   `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`, filed rather than fixed inline.
4. **Ideas 49 + 50 — Ambition/expansion, small shared helper only.** Both gate on "does this entity
   possess/consume material X" — worth one shared predicate, not a ticket merge. Idea 49 also carries a
   real naming-collision footgun: two unrelated classes both named `RecipeRegistry`.
5. **Ideas 51 + 52 — consolidated into one ticket.** Idea 52 confirmed pure wiring on top of idea 51's
   EXPAND directive, not a separate mechanism.
   **Status update, 2026-09-04:** shipped as `TCK-20260904-FACTION-EXPAND-DIRECTIVE`. Added
   `EXPAND_TERRITORY` as a 4th `FactionDirective` kind (`src/engine/faction_decision.py`), gated on
   mean `compute_regional_scarcity()` > `0.7` over a faction's `fs.territory` (population density
   from `compute_population_density()` folds into `priority` scaling only, never the gate — it has
   no existing gate precedent elsewhere in the codebase). Target resolution is deliberately narrow:
   the lowest-id faction-less region only (`RegionState.owner_faction_id is None`, sorted for
   determinism) — explicitly not Camp/Nest-as-conquest-target and not idea 35's City-ownership
   (still design-only, no implementation ticket exists yet). The directive threads same-tick through
   `WorldDynamicsSystem.resolve_dynamics()` into `CampService.process_camps()` (both gained a new
   trailing-optional `faction_directives` param, verified backward-compatible against all 33 real
   call sites), where a matching directive additively boosts a camp's maturity growth by
   `EXPAND_TERRITORY_MATURITY_BOOST` (`1.0`). This consumption path is real and unit-tested but
   currently has zero observable effect in any real compiled world — `state.camps` is `{}`
   everywhere since no world content sets `creature_kind` yet, the same content-authoring gap
   `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` already disclosed for item 1 above. The material-possession
   predicate (item 4's shared helper) was deliberately not consulted — population-pressure alone is
   the hard gate, per this ticket's own investigation. This closes the 6th and final ticket in the
   `m4-place-material-expansion` batch; real, disclosed follow-up work remains open and not yet
   ticketed — a `CampService` content-authoring bridge for Camp/Nest, a recipe-catalog namespace
   bridge for item 4's `RecipeRegistry` naming collision, and roughly 44 stale parity test-path
   citations surfaced across this batch — plus one already-filed ticket,
   `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY` (from item 3 above). This is the 5th of 8 scope items
   above to get a "Status update" (items 1-5 now all shipped at least one ticket; item 1's world-
   generation content-authoring half remains explicitly open per its own note) — items 6 (Clan
   lifecycle), 7 (The Empty Chair), and 8 (Information hubs) remain fully unticketed. This epic is
   not complete.
6. **Idea 40 — Clan lifecycle.** Real correction found in Phase Placement: `party_lifecycle.py`'s SOC-228
   doesn't fire on death as originally assumed — which would have silently killed cross-generational Clans
   if built as first scoped. **Depth-audit note:** the Party Formation & Lifecycle precedent this idea (and
   M2's idea 36) reuses spans 5 files but has exactly 1 test file — see Depth Beneath "Done" in the atlas.
   **Candidate new idea, added to the atlas 2026-09-02, not yet in this ticket's scope:** idea 68,
   Inter-Clan Relations (`docs/brainstorm/rpg_feature_atlas.html#idea-68`,
   `docs/brainstorm/rpg_expected_schemas.html#schema-68`) — Clan-to-Clan relationship state reusing idea
   37's race-relations pattern one layer up, and the missing external driver for `ClanState.tension_level`
   (real field, M2's idea 36, but nothing outside a Clan currently pushes it). Distinct from idea 40's own
   internal lifecycle scope (joining/leaving/succession) — a candidate for its own ticket once M2's idea 36
   lands as real state, not part of idea 40's scope itself.
7. **Idea 64 — The Empty Chair.** Confirmed genuinely unrelated to idea 40 (correctly not forced into a
   cluster) — the real remaining half after heir-assignment split off to M1's idea 10. No code precedent
   anywhere for the economic-vacancy signal it needs.
8. **Idea 41 — Information hubs.** Confirmed standalone, no cluster overlap — still gated behind
   `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_INFORMATION_INTENT_EXECUTION`, both OFF by default.

## Out of Scope

- Anything from Milestones 1, 2, 3, 5, or 6.
- **Superseded, 2026-09-02:** wiring `CultureDeriver`/`CulturalBiasApplicator` for the first time — the
  2026-08-29 update below assumed this was needed; it is not (see Problem above). No first-time-wiring
  ticket belongs in this epic's scope; only idea 61's own read-side consumer work does.
- ~~**Update, 2026-08-29:** wiring `CultureDeriver`/`CulturalBiasApplicator` for the first time is now IN
  scope for this epic (see Problem above) rather than out of it — M4 is its assigned owner, shared with M5's
  ideas 57/62 and M6's idea 56 as consumers. Scope it as its own small prerequisite ticket inside this epic,
  landed before or alongside idea 61, not built speculatively ahead of idea 61 needing it.~~

## Acceptance Signal

- Consolidation findings above are reflected in the actual child-ticket count (roughly 9 tickets for 12
  ideas, per the atlas's own Roadmap estimate) — not silently reverted to 1:1 ticket-per-idea.
- Idea 61 is scoped as a read-side consumer of `region_cultures`, not built against the wrong precedent it
  originally cited, and not treated as blocked on unbuilt substrate that already exists (correction,
  2026-09-02).

## References

- `docs/brainstorm/rpg_feature_atlas.html` — Shared Implementation Opportunities, Cross-Cutting Risk & Blast
  Radius, Phase Placement & Testing Strategy (`SETTLEMENT_TIER_ARENA`, `AMBITION_LOOP_ARENA`,
  `CLAN_LIFECYCLE_ARENA`, `EMPTY_CHAIR_ARENA` scenario designs)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Idea 66 gate, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — branch split and
  `CultureDeriver` ownership decision, 2026-08-29
