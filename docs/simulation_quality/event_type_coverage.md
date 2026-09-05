---
status: authoritative
layer: simulation
authority: P1
audience: developer
last_verified: 2026-08-13
---

# SimQ Event Type Coverage

**See also:** `docs/simulation_quality/extension_points.md` §3 (Recorded events) situates this
table's counts within the full set of extension axes (world breadth/depth, pillars, tuning
config, and more). **`docs/event_ledger/entity.yaml`** (`TCK-20260808-ENTITY-EVENT-LEDGER`) is a
broader, complementary catalog: this doc audits SimQ-scored event coverage; that ledger audits
every `EntityUpdate` durable-state mutation type against whether ANY observability event exists
for it at all, scored or not. It originally found 6 mutation types (attributes, biological,
equipment, stamina, wounds, task) with zero event coverage of any kind. As of 2026-08-08, 5 of
those 6 have real events (`TCK-20260808-ENTITY-{VITALS,ATTRIBUTES,EQUIPMENT,IDENTITY-ROLE-
FACTION}-OBSERVABILITY-GAP`); `task` (`TaskUpdate.work_kind_set`) was investigated and confirmed
deliberately uncovered — see the `deliberately_uncovered` row below, not a residual gap.

**Status:** Certified Level 1 — Authoritative  
**Ticket:** TCK-20260630-SIMQ-TRANSLATE  
**Date:** 2026-06-30  
**Audit base:** calibration runs in `data/calibration/` (sandbox_world seeds 42/137/999 200t, dungeon_crawl 200t, urban_political 200t, wilderness_survival 200t, simq_routing_test 500t)  
**Last updated:** 2026-07-04 (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B — `self_model_phase.py`'s `events=[]` hardcoding fixed, `pipeline.py:152`'s `information_belief` merge-clobber fixed, and `self_model_bundle_set` durable materialization fixed (`SelfModelPatch`, `SUB-374`); `belief_assimilated`'s Branch B path (route-a-new-query off `self_model.knowledge.unknowns`) confirmed reachable end-to-end via a test-scoped cross-tick-boundary test with both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON — see `INFRA-259`/`INFRA-260`. `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped calibration profile, so Branch B contributes 0 to any real calibration_hits count; `belief_assimilated`'s measured `1` remains entirely Branch A. Byte-identical canonical hash confirmed for `urban_political`'s shipped profile with/without the `SelfModelPatch` fix — 0 impact on existing baselines)

**Previously updated:** 2026-07-03 (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER — `pending_information_responses` compile-time plumbing (INFRA-257) + kernel tick-alignment fix (INFRA-258) shipped: `belief_assimilated`/`belief_updated` calibration_hits confirmed == 1 in each of all 7 `urban_political_*` calibration runs through the real `Kernel.tick_once()` live loop (INFORMATION pillar C→B in all 7; COGNITION C→B in 6 of 7, natural `belief_updated` consequence); `dungeon_crawl` spot-check stayed 0 — no leakage. `calamity_spawned`'s tick-gate comparison fix is verified correct by a dedicated unit test, but a one-off diagnostic run (`dungeon_crawl_seed42_5200t`, not anchored) did not naturally produce the event — a separate, pre-existing hero-death-dependent `calamity_intensity` precondition, not fixed by this ticket. `GovernorModeChanged` confirmed firing naturally in existing long-running baselines — infrastructure telemetry, not SimQ-scored)

**Previously updated:** 2026-07-03 (TCK-20260702-SIMQ-UPLIFT2-INFORMATION — `information_source_profiles` compile-time plumbing shipped and recalibrated across all 7 `urban_political_*` runs; `AuthoritativeState.information_source_profiles` now compiles with 2 entries (`town_notice_board`, `traveling_merchant_rumors`) and `ENABLE_BELIEF_ASSIMILATION=ON` is injected, but at that time `belief_assimilated`/`lead_certainty_updated` calibration_hits remained 0 in every run pending this ticket's kernel-fix + trigger-plumbing follow-up)

---

## Summary

| Category | Count | Notes |
|---|---|---|
| scored | 84 | +1 `world_hard_law_violation` (TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP) |
| translation_gap | 0 | — |
| engine_emission_gap | 0 | — |
| no_engine_path | 1 | `camp_constructed` — no dynamic camp construction in simulation; scorer entry is premature |
| p0_a_blocked | 3 | Unchanged — campaign/scenario gate |
| unscored_intentional | 26 | +5 (TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP): `biological_state_changed`, `stamina_changed`, `wound_sustained`, `wound_healed`, `scar_gained`. +1 (TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP): `attribute_changed`. +3 (TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP): `item_equipped`, `item_unequipped`, `equipment_durability_changed`. +4 (TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP): `entity_role_changed`, `entity_faction_changed`, `recipe_learned`, `skill_cooldown_started` — real entity mutations that previously had zero observability event of any kind, not just unscored |
| deliberately_uncovered | 1 | `TaskUpdate.work_kind_set` — investigated and confirmed pure per-tick scheduling plumbing (which verb runs next), not persistent narrative state; an event would be `movement`-class volume with no narrative content. TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP. This is a NEW category, distinct from the others above: a field that was investigated and deliberately judged not worth an event, as opposed to `unscored_intentional` (has an event, just not SimQ-scored) or a genuine gap. |

**Last updated:** 2026-08-08 (`TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP` — see
§5 for `entity_role_changed`/`entity_faction_changed`/`recipe_learned`/`skill_cooldown_started`,
and the new `deliberately_uncovered` category for `TaskUpdate.work_kind_set`)

Previously updated: 2026-08-08 (`TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP` — see §5 for
`item_equipped`/`item_unequipped`/`equipment_durability_changed`); 2026-08-08
(`TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP` — see §5 for `attribute_changed`); 2026-08-08
(`TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP` — see §5 for the 5 vitals events)

**Previously updated:** 2026-08-05 (`TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP` — of the 7 real
`HardLawMonitor` laws, only `LAW-SPAWN-OCCUPANCY` was previously bridged. Added exact-match
`law_id` routing for the other 6: `LAW-HP-NONNEGATIVE`/`LAW-READINESS-NONNEGATIVE` →
`combat_hard_law_violation` (CombatScorer, previously dormant — no real law ever used its
`COMBAT*`-prefix match), `LAW-GOLD-NONNEGATIVE` → `conservation_law_violated` (EconomyScorer,
previously dormant — no real law ever used its `CONSERVATION*`-prefix match),
`LAW-STAMINA-NONNEGATIVE`/`LAW-POSITION-FINITE`/`LAW-OCCUPANCY-COLLISION` → new
`world_hard_law_violation` (WorldDynamicsScorer, no existing generic signal fit these 3). The
`COMBAT*`/`CONSERVATION*` prefix branches were left in place, not repurposed — git history found
no evidence any real law was ever planned under those prefixes, and renaming the 6 real `LAW-*`
laws was out of this ticket's scope.)

**Translation table status:** Complete. All 8 `_TRANSLATE_SIMPLE` entries and the
`_TRANSLATE_CONDITIONAL` entry for `InvariantViolation` (now dispatching all 7 real hard laws, not
just 1) in `quality_hub.py` are correct. No translation table gaps found.

**Remaining gaps:** 0 engine emission gaps. 1 scorer entry has no viable engine path (`camp_constructed` — `StateUpdate` has no `camps_add` field, so no tick-time construction mechanic exists to emit from; see §3.9's `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` note for the narrower, compile-time-only exception).

---

## Classification Definitions

| Classification | Meaning |
|---|---|
| `scored` | Event is emitted by the engine AND reaches the correct scorer(s) via direct match or translation |
| `translation_gap` | Event is emitted but the translation table has a missing or wrong mapping so it never reaches the scorer |
| `engine_emission_gap` | SCORER_REGISTRY entry exists (scorer ready) but the engine does not emit this event type yet |
| `p0_a_blocked` | Scorer entry exists but the event is gated by a feature flag (ENABLE_ADVENTURE_ROUTING) or infrastructure (campaigns/scenario system) that is OFF in all calibration runs |
| `unscored_intentional` | Event is emitted by the engine but is not wired to any scorer — deliberate |

---

## §1 Scored Events

All events below are emitted by the engine and reach at least one pillar scorer, either directly (contract vocabulary already matches) or after `QualityHub._translate()` remaps the engine event_type.

### §1.1 Direct Emission — No Translation Required

| event_type | source | scorers | calibration_hits | notes |
|---|---|---|---|---|
| `demographic_mortality` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | Emitted only on despawn-without-attacker; rare in short runs. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `demographic_birth` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | Emitted on entity spawn; scored via world_dynamics pillar. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `hero_death_unrecorded` | event_shapers (CombatShaper) | NarrativeScorer | 0 | Only for kind="hero" entities. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `combat_damage` | event_shapers (CombatShaper) | CombatScorer | 0 | Light/long-run mode suppresses non-lethal; lethal path hits scorer. `payload.tactical_modifier` (added `TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX`) activates the pillar's own `tactical_variety` signal (+1 per unique modifier), previously permanently dead for lack of a producer — confirmed real in live corpus runs (`STAMINA_EXHAUSTION`), sparse/environment-timing-variable at this corpus scale like `combat_damage` itself. `event_extractor.py`'s own block (which constructs `CombatDamageEvent`) is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `combat_initiated` | event_shapers (CombatShaper) | CombatScorer | 117 | Fires when entity at full HP takes first hit. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `near_death_survival` | event_shapers (CombatShaper) | CombatScorer, ProgressionScorer | 164 | HP crosses below 20% threshold. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `xp_granted` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | Fires on identity.evolution_points delta. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `level_up` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | Direct path; also reachable via `lifecycle` translation. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `route_selected` | event_shapers (StrategyShaper) | AgencyScorer | 20 | Fires when entity.last_routing_family changes. The 20-hit count is from the 2026-07-04 audit base (`simq_routing_test`, `ENABLE_ADVENTURE_ROUTING=ON`); zero in every other calibration world because the flag defaults `OFF`. **Stale as of `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`:** the sole writer of `entity.last_routing_family` (`AdventureDecisionPhase.apply()`) was deleted without a replacement being ported — confirmed via direct source search, no `EntityUpdate.property_updates` writer exists anywhere in `src/domains/adventure/` or `src/ai/goals/adventure_scorer.py`. Fresh re-verification (`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`) confirms `route_selected` now fires **0** times on all 4 of `simq_routing_test_seed{42,456}_500t`/`hero_guild_routing_seed{42,456}_500t` — full AGENCY pillar collapse (grade C), not a partial gap. See `docs/guidelines/intentional_divergences.md` §2.41 (broadened disclosure) and `eval_matrix_results.md`'s 2026-08-13 NOTE blocks. The historical `20` above has not been re-audited against the full corpus and should not be treated as current. This dead-writer gap is shaper-side, not extractor-side — `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source, and shares the identical dead-writer fact. **Superseded again (2026-08-13, `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`):** the write path fix above (§2.41) restored the writer, but a second, independent defect — `AdventureGoalScorer.score()` normalizing against a denominator calibrated for an input the live path never receives — still suppressed `ADVENTURE_ROUTE` from ever winning tier-5 goal competition, so `route_selected` still measured 0 everywhere even with the writer restored. That second defect is now also fixed (`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4`, `src/ai/goals/adventure_scorer.py`, see `docs/mechanics/04_strategic_cognition.md` §6.6). A fresh `calibrate_simq.py` run across all 6 named `_500t` run_keys now measures `route_selected` firing exactly once (nonzero) for `hero_guild_routing_seed42_500t` only (AGENCY grade `B`); the other 5 (`simq_routing_test_seed{42,123,456}_500t`, `hero_guild_routing_seed{123,456}_500t`) still measure 0, unchanged. This is a real, mixed, evidence-grounded outcome, not a full restoration to the historical `20`. |
| `action_executed` | event_shapers (StrategyShaper) | AgencyScorer | 20 | Co-fires with route_selected; same `ENABLE_ADVENTURE_ROUTING` gate. **Stale as of `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`** — same root cause and same 2026-08-13 re-verification as the `route_selected` row above: confirmed 0 hits on all 4 named `_500t` run_keys, not 20. See that row for detail. This dead-writer gap is shaper-side, not extractor-side — `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source, and shares the identical dead-writer fact. **Superseded again (2026-08-13, `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`)** — same tier-5-competition-scale fix and same fresh measurement as the `route_selected` row above: `action_executed` co-fires exactly once (nonzero) for `hero_guild_routing_seed42_500t` only; the other 5 named `_500t` run_keys remain at 0. See that row for detail. |
| `self_model_updated` | event_shapers (StrategyShaper) | CognitionScorer | 0 | Fires on self_model_bundle_set. `self_model_bundle_set` now durably materializes into `EntityState.self_model` via the authoritative apply path (`SelfModelPatch`, `src/engine/patches.py`, 2026-07-04, `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`; see `docs/parity_ledger/substrate.yaml::SUB-374`) — this event itself is read off the `EntityUpdate`, not durable state, so its 0-hit count is unaffected either way; still 0 in every calibration run because `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped profile. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `belief_assimilated` | event_shapers (StrategyShaper) | InformationScorer | 1 | Fires on last_assimilated_tick == prior_state.tick (kernel tick-alignment fix, INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER). `pending_information_responses` compile-time plumbing (INFRA-257) seeds one entry targeting `pop_0` (`bandit_road_danger`, `KNOWN_FACT`) in `urban_political`; confirmed calibration_hits == 1 in each of the 7 `urban_political_*` calibration runs (200t/500t/1000t, seeds 42/123/456) via `calibrate_simq.py` through the real `Kernel.tick_once()` live loop — the seed fires exactly once at the initial compiled state (tick 0), not carried forward by `ApplyPath.apply_generation()` on later ticks. 0 hits in `dungeon_crawl` spot-check (no leakage). INFORMATION pillar grade moved C→B in all 7 `urban_political_*` `grade_anchors.json` entries. Prior to the kernel fix, this measured 0 despite the seed/assimilation mechanism working correctly. **Branch B path (2026-07-04, `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`, `INFRA-259`/`INFRA-260`):** the count above is Branch A only (`pending_information_responses`). Branch B's route-a-new-query path (routed off `self_model.knowledge.unknowns`) is now proven reachable end-to-end via a test-scoped cross-tick-boundary test (`self_model_phase.py`'s `events=[]` fixed, `pipeline.py:152`'s merge-clobber fixed, `self_model_bundle_set` materialization fixed) with both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON — but `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped calibration profile, so Branch B contributes 0 to this event's calibration_hits in any real run. This entry's `1` remains entirely attributable to Branch A. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `belief_updated` | event_shapers (StrategyShaper) | CognitionScorer | 1 | Co-fires with belief_assimilated (same kernel tick-alignment fix, INFRA-258); confirmed calibration_hits == 1 in each of the 7 `urban_political_*` runs. Also scored by CognitionScorer (`belief_active` tag, distinct from InformationScorer) — this natural, plan-anticipated consequence moves the COGNITION pillar grade C→B in 6 of the 7 `urban_political_*` entries (one anchor was already B); within tolerance, confirmed via `make evaluate --dry-run` (0 regressions). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `cooperation_event` | event_shapers (StrategyShaper) | SocialScorer | 1657 | Fires on last_cooperation_decision; 1657 hits in urban_political_seed42_500t with ENABLE_SOCIAL_COOPERATION=ON (TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO). Scored by `SocialScorer` but derived inside `StrategyShaper` (cross-domain colocation, intentional — do not rename to `SocialShaper`). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `resource_harvested` | event_shapers (EconomyShaper) | EconomyScorer | 0 | src_kind=NODE in intent_results. Live derivation moved to `EconomyShaper.shape()` via `run_shadow_shapers()` as of the 2026-08-06 push-shaper cutover (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`); `event_extractor.py`'s own loop is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. Corrected by `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`; remaining stale `source` rows in this table tracked by `TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS`. |
| `item_crafted` | event_shapers (EconomyShaper) | EconomyScorer | 0 | src_kind=CRAFTING. Same 2026-08-06 push-shaper cutover correction as `resource_harvested` above — see that row's note. |
| `shop_transaction` | event_shapers (EconomyShaper) | EconomyScorer | 0 | src_kind=SHOP_BUY or SHOP_SELL. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `trade_executed` | event_shapers (EconomyShaper) | EconomyScorer | 0 | Co-fires with shop_transaction. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `quest_reward_dispensed` | event_shapers (EconomyShaper) | EconomyScorer | 0 | src_kind=QUEST. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `gold_sink_fired` | event_shapers (EconomyShaper) | EconomyScorer | 0 | src_kind in (REPAIR_FEE, SERVICE_FEE, TAX) (archetype-blocked in dungeon_crawl — see eval_matrix_results.md DA note). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `paid_information_transaction` | event_shapers (EconomyShaper) | InformationScorer | 0 | src_kind=INFORMATION_PURCHASE. Requires an active `INFORMATION_SEEKING` project, which only the orphaned `InformationNeedDetector.detect_and_generate()` / `GuildAction.visit()` (zero callers) ever create — still 0 hits post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration. Deferred to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `paid_info_transaction` | event_shapers (EconomyShaper) | EconomyScorer | 0 | Second emit on INFORMATION_PURCHASE (distinct pillar target) — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `conservation_law_verified` | event_shapers (run_shadow_shapers) | EconomyScorer | 0 | tick % 50 + economy events present — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY. Computed directly inside `run_shadow_shapers()` as a cross-shaper aggregation, not any single per-domain shaper class. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `scenario_objective_progressed` | engine/scenario_runtime | NarrativeScorer | 0 | Every tick while objective RUNNING — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `defer_with_reason` | event_shapers (StrategyShaper) | AgencyScorer | 0 | DEFER_WITH_REASON path in phase.py — TCK-20260701-SIMQ-EMIT-AGENCY2. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `route_family_first_use` | event_shapers (StrategyShaper) | AgencyScorer | 0 | First use of a novel routing family per entity per run — TCK-20260701-SIMQ-EMIT-AGENCY2. Gated by the same `ENABLE_ADVENTURE_ROUTING` flag as route_selected/action_executed (defaults `OFF`); 0 in all default-mode worlds (archetype-intentional zero hits — see `eval_matrix_results.md` AGENCY Cross-World Design Note). Originally also 0 in `simq_routing_test_seed42_500t` because that specific calibration artifact predated this emitter (TCK-20260630-SIMQ-ROUTING-TEST ran before TCK-20260701-SIMQ-EMIT-AGENCY2 added it). **That explanation is now superseded, not just outdated:** since `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` deleted the sole `entity.last_routing_family` writer, this event cannot fire in ANY `ENABLE_ADVENTURE_ROUTING=ON` world today regardless of artifact age — confirmed part of the same full AGENCY collapse re-verified by `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` (see `route_selected` row above and `intentional_divergences.md` §2.41). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. **Superseded again (2026-08-13, `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`)** — same tier-5-competition-scale fix and same fresh measurement as the `route_selected` row above: `route_family_first_use` now fires exactly once (nonzero) for `hero_guild_routing_seed42_500t` only; the other 5 named `_500t` run_keys remain at 0. This event is no longer categorically un-fireable in a live `ENABLE_ADVENTURE_ROUTING=ON` world — see that row for the full measured evidence. |
| `commitment_abandoned` | event_shapers (AgencyShaper) | AgencyScorer | 0 | Behavioral classification: abandonment < 3 ticks after start — TCK-20260701-SIMQ-EMIT-AGENCY2. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_agency_active`) rollback path, not the live source. |
| `rejection_cascade_tick` | event_shapers (AgencyShaper) | AgencyScorer | 0 | Population aggregate: > threshold% failed intent rate — TCK-20260701-SIMQ-EMIT-AGENCY2. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_agency_active`) rollback path, not the live source. |
| `lead_certainty_updated` | event_shapers (StrategyShaper) | InformationScorer | 0 | Certainty enum diff per lead per tick — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration — no code path creates the leads whose certainty this would diff; deferred to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `lead_contradiction_resolved` | lead_contradiction.py | InformationScorer | 0 | Co-emitted with belief_contradiction — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap as `lead_certainty_updated` |
| `paid_info_changed_goal` | event_shapers (EconomyShaper) | InformationScorer | 0 | INFORMATION_PURCHASE + project_id change same tick — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap. Scored by `InformationScorer` but derived inside `EconomyShaper` (cross-domain colocation, intentional — do not rename to a `StrategyShaper`/`InformationScorer`-matching name). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `belief_stale` | event_shapers (StrategyShaper) | InformationScorer | 0 | VAGUE/APPROXIMATE lead age > 50 ticks, once per lead per run — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `decision_diverged_by_belief` | event_shapers (StrategyShaper) | InformationScorer | 0 | VAGUE lead + non-information active project — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `decision_divergence_detected` | event_shapers (StrategyShaper) | CognitionScorer | 0 | DANGER concern urgency > 0.7 + non-survival project — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS (archetype-blocked in dungeon_crawl — see eval_matrix_results.md DA note). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `skill_unlocked` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | learned_skills set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `trait_expressed` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | traits set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `pillar_trait_unlocked` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | active_breakthroughs set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `progression_conversion_applied` | event_shapers (ProgressionShaper) | ProgressionScorer | 0 | unspent_ap decrease — TCK-20260701-SIMQ-EMIT-PROGRESSION. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `progression_plateau_detected` | event_shapers (ProgressionShaper) | ProgressionScorer | 18 | XP unchanged for > 50 ticks from run start — TCK-20260701-SIMQ-EMIT-PROGRESSION; calibration_hits updated 2026-07-02 (TCK-20260701-SIMQ-CALIBRATE-REFRESH). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `capability_growth_stalled` | event_extractor | ProgressionScorer | 0 | level/skills/gear/gold all flat for 300+ ticks — TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE, not yet calibrated |
| `life_arc_incoherent` | event_extractor | ProgressionScorer | 0 | generation >= 2 with level <= 1 and zero skills — TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE, not yet calibrated |
| `alliance_proposed` | event_shapers (FactionShaper) | FactionScorer | 0 | NEUTRAL/HOSTILE → ALLIED transition — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `resource_seized` | event_shapers (FactionShaper) | FactionScorer | 0 | territory_add + tension_delta > 0 — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `faction_trajectory_stagnant` | event_shapers (FactionShaper) | FactionScorer | 0 | territory unchanged 300+ ticks despite diplomatic activity — TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY, not yet calibrated |
| `ecology_cycle_completed` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | tick % 200 per region — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `spawn_cadence_fired` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | tick % 50 + non-boss entities_add — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `threat_evolved` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | trauma_score threshold crossing 25/50/75/100 — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `node_recharged` | event_shapers (DeferredInstrumentationShaper) | WorldDynamicsScorer | 0 | remaining_charges 0 → >0 — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. Despite sitting between `threat_evolved` (WorldDynamicsShaper) and `hazard_drain_applied` (CombatShaper) in this table, this row's correct shaper is neither doc-neighbor — derivation lives in `DeferredInstrumentationShaper`. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `hazard_drain_applied` | event_shapers (CombatShaper) | WorldDynamicsScorer | 322 | combat_upd.outcome_kind=="HAZARD". `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `building_sabotaged` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | Emitted on hp_delta < 0 in building_updates (BuildingSabotageSystem.resolve()); 0 hits expected in all current calibration runs because no strategic/goal-selection/quest-reward code anywhere in src/ currently sets task_upd.work_kind_set="SABOTAGE" or payload_set["action"]="SABOTAGE" — confirmed via repo-wide grep (investigation.md Risk #1); this is a genuine engine emission path with no live producer yet, not a translation gap or missing-scorer gap. TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `lead_certainty_changed` | event_shapers (StrategyShaper) | CognitionScorer | 0 | Strategic lead certainty state diff; see §3 note on `lead_certainty_updated`. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `social_memory_created` | event_shapers (SocialShaper) | SocialScorer | 0 | trust_history new entry or delta ≥ 0.3; once per (entity_id, other_entity_id) per run — TCK-20260701-SIMQ-EMIT-SOCIAL-MEM. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_milestone_completed` | event_shapers (SocialShaper) | SocialScorer | 0 | ACTIVE contract at 25%/50%/75% of duration; once per (contract_id, milestone) per run; attributed to source_id — TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `group_joined` | event_shapers (SocialShaper) | SocialScorer | 0 | Entity joins a group. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `group_expelled` | event_shapers (SocialShaper) | SocialScorer | 0 | Entity leaves a group. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `reputation_delta` | event_shapers (SocialShaper) | SocialScorer | 0 | public_reputation delta > 0.05. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_offer_created` | event_shapers (SocialShaper) | SocialScorer | 0 | New contract in OFFERED state. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_offer_accepted` | event_shapers (SocialShaper) | SocialScorer | 0 | OFFERED → ACTIVE transition. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_completed` | event_shapers (SocialShaper) | SocialScorer | 0 | Contract reaches FULFILLED. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_lapsed` | event_shapers (SocialShaper) | SocialScorer | 0 | ACTIVE → EXPIRED. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `contract_expired_offer` | event_shapers (SocialShaper) | SocialScorer | 234 | OFFERED → EXPIRED or contract removed; 234 hits in urban_political_seed42_500t with ENABLE_SOCIAL_COOPERATION=ON (TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `resource_node_depleted` | event_shapers (DeferredInstrumentationShaper) | EconomyScorer | 0 | Node remaining_charges drops to 0. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `region_trauma_delta` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 11 | Non-zero trauma_delta on world_updates. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `region_ownership_changed` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | owner_faction_id_set changes. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `region_transformed` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | kind_set on region update. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `calamity_spawned` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | last_calamity_tick_set == prior_state.tick (kernel tick-alignment fix, INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER) — the tick-comparison bug that made this permanently unreachable through the real `Kernel.tick_once()` loop is fixed and verified correct by a dedicated unit test (`test_calamity_spawned_fires_through_real_tick_once_loop`, which constructs a state meeting CalamityService's spawn gates directly). A one-off diagnostic calibration run (`dungeon_crawl_seed42_5200t`, not added to `grade_anchors.json`) still shows 0 hits: CalamityService additionally requires `calamity_intensity > 0.3` in some region, only raised when a hero-kind entity dies in a `hazard_level > 0.5` region; no hero died in that run's RNG/gameplay. This is a separate, pre-existing content/mechanics precondition, not fixed by the kernel tick-alignment fix — an informational residual gap, not claimed as resolved. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `boss_spawned` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | world-boss-gated: entity kind in (world_boss, ancient_sentinel). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `narrative_milestone` | event_shapers (WorldDynamicsShaper) | NarrativeScorer | 0 | Co-emitted on boss_spawned, war_declared, sovereignty_shift. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `raid_party_spawned` | event_shapers (WorldDynamicsShaper) | WorldDynamicsScorer | 0 | goblin-raider-gated: entity kind == goblin_raider. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `diplomatic_transition` | event_shapers (FactionShaper) | FactionScorer | 29 | Direct emit on faction diplomatic_relations_set change; 29 hits confirmed in all 7 `urban_political_*` calibration runs (200t/500t/1000t, seeds 42/123/456) after `bandit_company`/`town_council` seeded to `initial_tension_level=0.5` via `faction_tension_overrides` (TCK-20260702-SIMQ-UPLIFT2-FACTION); 0 in `dungeon_crawl`/`frontier_extended` (no override declared). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `alliance_accepted` | event_shapers (FactionShaper) | FactionScorer | 0 | Direct emit when new_state == ALLIED. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `territory_ownership_changed` | event_shapers (FactionShaper) | FactionScorer | 0 | faction.territory_add. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `faction_tension_delta` | event_shapers (FactionShaper) | FactionScorer | 0 | Non-zero tension_delta on faction update; still 0 post-TCK-20260702-SIMQ-UPLIFT2-FACTION recalibration — `initial_tension_level` seeding is a compile-time value, not an ongoing per-tick `tension_delta` on a `FactionUpdate`, so this emitter is not exercised by the fix; `diplomatic_transition` (AC-4) is the confirmed non-zero path. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `war_declared` | event_shapers (FactionShaper) | FactionScorer | 0 | WorldEvent category == FACTION_WAR_DECLARED. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `military_conflict_resolved` | event_shapers (FactionShaper) | FactionScorer | 0 | WorldEvent in (TERRITORY_TRANSFERRED, WAR_ENDED_EXHAUSTION). `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_active`) rollback path, not the live source. |
| `world_emergence_event` | event_shapers (WorldDynamicsShaper) | NarrativeScorer | 0 | Every WorldEvent in world_events_add. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `faction_extinct` | event_shapers (DeferredInstrumentationShaper) | FactionScorer | 0 | Faction has no living members; fires only when faction_updates present. Despite the name and `FactionScorer` scoring column, derivation lives in `DeferredInstrumentationShaper`, not `FactionShaper` — do not conflate scorer domain with shaper class. `event_extractor.py`'s own block is now the flag-gated (`_push_shapers_phase2_active`) rollback path, not the live source. |
| `chronicle_entry_created` | campaigns/narrative_ledger, campaigns/orchestrator | NarrativeScorer | 0 | Campaign-gated (see §4) |
| `quest_completed` | campaigns/runner | NarrativeScorer | 0 | Campaign-gated; also reachable via quest_event conditional translation |
| `scenario_objective_completed` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |
| `scenario_stalled` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |

### §1.2 Via `_TRANSLATE_SIMPLE` (one-to-one remaps)

| engine event_type | translation | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `combat_kill` | _TRANSLATE_SIMPLE | `entity_killed` | CombatScorer | 1 |
| `gold_transaction` | _TRANSLATE_SIMPLE | `gold_transferred` | EconomyScorer | 0 |
| `StrategicObjectiveChanged` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicConcernRaised` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicDetourCreated` | _TRANSLATE_SIMPLE | `project_started` | AgencyScorer | 0 |
| `StrategicLeadExhausted` | _TRANSLATE_SIMPLE | `knowledge_default_fallback` | CognitionScorer | 0 |
| `leadership_changed` | _TRANSLATE_SIMPLE | `diplomatic_transition` | FactionScorer | 0 |
| `alliance_formed` | _TRANSLATE_SIMPLE | `alliance_accepted` | FactionScorer | 0 |

### §1.3 Via `_TRANSLATE_CONDITIONAL` (payload-conditional remaps)

| engine event_type | condition | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `quest_event` | payload.status == "started" (default) | `quest_started` | NarrativeScorer | 233 |
| `quest_event` | payload.status == "completed" | `quest_completed` | NarrativeScorer | 0 |
| `quest_event` | payload.status == "failed" | `quest_failed` | NarrativeScorer | 0 |
| `lifecycle` | payload.action == "level_up" | `level_up` | ProgressionScorer | 0 |
| `lifecycle` | payload.action in ("despawn","death") | `entity_killed` | CombatScorer | 0 |
| `lifecycle` | payload.action == "spawn" | passthrough — no translation | none | 0 |
| `StrategicProjectChanged` | "complet" in reason | `project_completed` | AgencyScorer | 0 |
| `StrategicProjectChanged` | "abandon" in reason | `project_abandoned` | AgencyScorer | 0 |
| `StrategicProjectChanged` | default | `project_started` | AgencyScorer | 0 |
| `InvariantViolation` | law_id == "LAW-HP-NONNEGATIVE" or "LAW-READINESS-NONNEGATIVE" | `combat_hard_law_violation` | CombatScorer | 0 |
| `InvariantViolation` | law_id == "LAW-GOLD-NONNEGATIVE" | `conservation_law_violated` | EconomyScorer | 0 |
| `InvariantViolation` | law_id == "LAW-STAMINA-NONNEGATIVE", "LAW-POSITION-FINITE", or "LAW-OCCUPANCY-COLLISION" | `world_hard_law_violation` | WorldDynamicsScorer | 0 |
| `InvariantViolation` | law_id starts with "COMBAT" (no real law uses this prefix — dormant) | `combat_hard_law_violation` | CombatScorer | 0 |
| `InvariantViolation` | law_id starts with "CONSERVATION" (no real law uses this prefix — dormant) | `conservation_law_violated` | EconomyScorer | 0 |
| `InvariantViolation` | law_id starts with "LAW-SPAWN-OCCUPANCY" | `spawn_occupancy_violation` | WorldDynamicsScorer | 0 |
| `InvariantViolation` | other law_id | passthrough — no translation | none | 0 |
| `betrayal_desertion` | payload.faction_id present | `faction_tension_delta` | FactionScorer | 0 |
| `betrayal_desertion` | no faction_id | `contract_lapsed` | SocialScorer | 0 |

---

## §2 Translation Gaps

**None found.** All 8 `_TRANSLATE_SIMPLE` entries and all 5 `_TRANSLATE_CONDITIONAL` entries in `src/simulation_quality/quality_hub.py` are correct and complete as of this audit. Every engine event_type that the translation table touches maps to a valid contract vocabulary type that exists in `SCORER_REGISTRY`.

Test coverage was incomplete for 3 entries (`leadership_changed`, `alliance_formed`, `betrayal_desertion`). Tests were added in `tests/simulation_quality/test_quality_hub_event_translation.py` as part of this ticket.

---

## §3 Engine Emission Gaps

These contract vocabulary types appear in at least one scorer's `EVENT_TYPES` tuple and are therefore registered in `SCORER_REGISTRY`, but the engine never emits them. Scoring infrastructure is ready; upstream emission is deferred to future engine work.

### §3.1 Agency (AgencyScorer)

> All AGENCY pillar events are now emitted. See §1.1 for the 4 events added by TCK-20260701-SIMQ-EMIT-AGENCY2 (`defer_with_reason`, `route_family_first_use`, `commitment_abandoned`, `rejection_cascade_tick`).

### §3.2 Cognition (CognitionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS.

| contract_type | resolved by |
|---|---|
| `decision_divergence_detected` | `event_shapers (StrategyShaper)` — DANGER concern urgency > 0.7 + non-survival project |

### §3.3 Information (InformationScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS.

| contract_type | resolved by |
|---|---|
| `lead_certainty_updated` | `event_shapers (StrategyShaper)` — certainty enum diff per lead per tick |
| `lead_contradiction_resolved` | `lead_contradiction.py` — emitted alongside `belief_contradiction` |
| `paid_info_changed_goal` | `event_shapers (EconomyShaper)` — INFORMATION_PURCHASE intent + project_id change (cross-domain colocation: scored by `InformationScorer`, derived inside `EconomyShaper`) |
| `belief_stale` | `event_shapers (StrategyShaper)` — VAGUE/APPROXIMATE lead age > 50 ticks, once per lead per run |
| `decision_diverged_by_belief` | `event_shapers (StrategyShaper)` — VAGUE lead + non-information active project |

### §3.4 Economy (EconomyScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `paid_info_transaction` | `event_shapers (EconomyShaper)` — second emit on INFORMATION_PURCHASE (distinct from `paid_information_transaction`) |
| `conservation_law_verified` | `event_shapers (run_shadow_shapers)` — tick % 50 guard + economy events present in current tick |

### §3.5 Narrative (NarrativeScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `scenario_objective_progressed` | `scenario_runtime.py` — emitted every tick while objective is RUNNING |

### §3.6 Progression (ProgressionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-PROGRESSION.

| contract_type | resolved by |
|---|---|
| `skill_unlocked` | `event_shapers (ProgressionShaper)` — learned_skills set diff |
| `trait_expressed` | `event_shapers (ProgressionShaper)` — traits set diff |
| `pillar_trait_unlocked` | `event_shapers (ProgressionShaper)` — active_breakthroughs set diff |
| `progression_conversion_applied` | `event_shapers (ProgressionShaper)` — unspent_ap decrease |
| `progression_plateau_detected` | `event_shapers (ProgressionShaper)` — xp_rate_zero + skill_silence signals |

### §3.7 Faction (FactionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `alliance_proposed` | `event_shapers (FactionShaper)` — NEUTRAL/HOSTILE → ALLIED transition detected via prior_state.factions |
| `resource_seized` | `event_shapers (FactionShaper)` — FactionUpdate.territory_add with tension_delta > 0 |

### §3.8 Social (SocialScorer)

All gaps resolved.

| contract_type | resolved by |
|---|---|
| `social_memory_created` | `event_shapers (SocialShaper)` — `trust_history` delta (new entry or Δ ≥ 0.3, once per pair per run). TCK-20260701-SIMQ-EMIT-SOCIAL-MEM. |
| `contract_milestone_completed` | `event_shapers (SocialShaper)` — time-gated: 25%/50%/75% of `(expiry_tick − created_tick)` elapsed for ACTIVE contracts; no schema change needed. Once per `(contract_id, label)` per run, attributed to `source_id`. TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE. |

### §3.9 World Dynamics (WorldDynamicsScorer)

Resolved by TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. One item reclassified as `no_engine_path` (not a wiring gap).

| contract_type | resolved by / notes |
|---|---|
| `ecology_cycle_completed` | `event_shapers (WorldDynamicsShaper)` — tick % 200 per region |
| `spawn_cadence_fired` | `event_shapers (WorldDynamicsShaper)` — tick % 50 + non-boss entities_add |
| `threat_evolved` | `event_shapers (WorldDynamicsShaper)` — trauma_score crossing 25/50/75/100 thresholds |
| `node_recharged` | `event_shapers (DeferredInstrumentationShaper)` — resource_node quantity 0 → >0 (despite sitting alongside the 3 `WorldDynamicsShaper` rows above, this event's derivation lives in `DeferredInstrumentationShaper`, not `WorldDynamicsShaper` — do not assign by proximity) |
| `camp_constructed` | **No engine path.** `StateUpdate` has no `camps_add` field — no dynamic `CampState` construction occurs during simulation ticks; `CampService` only evolves existing camps (maturity, raids). Implementing this event requires adding a tick-time camp placement mechanic first. TCK-20260701-SIMQ-EMIT-CAMP closed. **Update, 2026-09-04 (`TCK-20260904-CAMPSTATE-PLACE-BRIDGE`):** the premise "camps are pre-placed at world generation" was actually false prior to that ticket — zero production `CampState` construction existed anywhere, at world-gen or tick-time. As of that ticket, `WorldCompiler.compile()` CAN construct a `CampState` at world-gen (compile time, not a simulation tick) when content declares the optional, opt-in `PlaceSpec.creature_kind` field — but no real content does so yet, so this row's conclusion (no viable engine path for `camp_constructed` in any real compiled world today) is unchanged. See `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-109` entry for the parity-ledger record of this correction. |

### §3.10 Combat (CombatScorer)

**Newly added 2026-08-09** (`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`) — `combat_resolved`
was a real, undisclosed gap in this section: `CombatScorer.EVENT_TYPES` has carried it since the
pillar's own original design, and `CombatScorer.score()` has always had a real, ready handler
(`+3`, the largest positive weight in the whole COMBAT pillar), but no producer ever existed
anywhere in `src/` — self-disclosed only in `CombatShaper`'s own class docstring, never
cross-referenced into this coverage doc's own §3 audit until now.

| contract_type | resolved by / notes |
|---|---|
| `combat_resolved` | `event_shapers.py`'s `CombatShaper` — fires alongside `combat_engagement_ended` (`TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`) for exactly 2 of its 4 real outcomes: `KILL` and `ESCAPED`, both literal matches for the pillar contract's own wording ("clear winner, loser retreats or dies"). `CAUGHT_FLEEING`/`PURSUIT_ABANDONED` deliberately excluded — neither represents a clear resolution. Real corpus re-verification: fires at real, non-zero volume (1x `dungeon_crawl`, 4x `urban_political`, 2000-tick corpus-default runs), 1:1 correlated with the real `KILL`/`ESCAPED` count in each world, zero leakage into the excluded outcomes. |

---

## §4 P0-A Blocked

Events in `SCORER_REGISTRY` that are not emitted in calibration runs because the subsystem that generates them (campaigns layer, scenario mode) is not active in sandbox_world/dungeon_crawl/wilderness_survival calibration scenarios.

These events DO pass through the translation layer correctly when the subsystem is active and WILL be scored. They are not engine emission gaps — they would appear in full campaign or scenario-mode runs.

| event_type | blocking gate | scorers |
|---|---|---|
| `chronicle_entry_created` | campaigns layer not active in calibration | NarrativeScorer |
| `scenario_objective_completed` | scenario mode not active in calibration | NarrativeScorer |
| `scenario_stalled` | scenario mode not active in calibration | NarrativeScorer |

Note: `boss_spawned` and `raid_party_spawned` are world-infrastructure-gated (require specific entity kinds), but they ARE emitted when those entities spawn. They are classified as `scored` (§1.1) since the engine path exists.

---

## §5 Unscored Intentional

Events emitted by the engine that are deliberately NOT routed to any scorer. No action required.

| event_type | source | reason |
|---|---|---|
| `movement` | MovementEvent | High-volume positional data; not a quality signal |
| `lifecycle` (spawn action) | LifecycleEvent | Spawn passthrough — no quality contract for raw spawn |
| `resource_node_regenerated` | event_shapers (DeferredInstrumentationShaper) | Not a quality signal; node recharge tracked separately |
| `LEGENDARY_ARRIVAL` | LegendaryArrivalEvent | Social consequence event; quality signal not yet defined |
| `KNOWN_TRAITOR_SPOTTED` | KnownTraitorSpottedEvent | Social consequence event; quality signal not yet defined |
| `OLD_DEBT_COLLECTED` | OldDebtCollectedEvent | Social consequence event; quality signal not yet defined |
| `REFINED_UPDATE` | engine/kernel | Kernel internal; pipeline phase marker |
| `GovernorModeChanged` | engine/kernel | Kernel internal; governance state change. Kernel tick-alignment fix (INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER) fixed a comparison bug (`kernel.py:836`) that made this unreachable through the real `Kernel.tick_once()` loop; confirmed firing naturally (63-73 occurrences) in each of the existing `dungeon_crawl_seed{42,123,456}_2000t` / `sandbox_world_seed42_2000t` calibration baselines post-fix. Not scored by any SimQ pillar — infrastructure telemetry only. |
| `TICK_END` | engine/kernel | Kernel internal; tick lifecycle marker |
| `InvariantViolation` (unknown law) | engine/kernel | Falls through conditional translator; unknown law ID has no contract type |
| `belief_contradiction` | engine/pipeline_phases/lead_contradiction | Not yet wired to quality scoring |
| `plan_revision` | campaigns/plan_revision | Campaign planning artifact; not a simulation quality signal |
| `DEFLATION_RISK`, `INFLATION_SPIRAL`, `ECONOMIC_COLLAPSE`, `GOLD_HOARDING` | EconomyHealthMonitor | Defined in events.py but marked deferred — not yet emitted |
| `biological_state_changed` | event_extractor | Hunger/sleep_debt/rest_pressure delta, every tick — high-volume, same class as `movement`. Confirmed firing through a real `Kernel.tick_once()` loop. TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP |
| `stamina_changed` | event_extractor | Stamina delta, every tick — high-volume, same class as `movement`. Confirmed firing through a real `Kernel.tick_once()` loop. TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP |
| `wound_sustained` / `wound_healed` / `scar_gained` | event_extractor | New wound / heal / scar, per real occurrence. Not exercised through a real tick loop this session — combat is corpus-wide gated off (`ENABLE_COMBAT_ENGAGEMENT`); verified instead via real hand-constructed `WoundState`/`ScarState` objects (same precedent as `test_information_intent_execution_fires_through_kernel_tick_once`). TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP |
| `attribute_changed` | event_extractor | Any of the 9 base attributes (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA) delta, per real occurrence — payload carries only the changed fields. Severity direction-based (WARNING on any decline, INFO otherwise), not magnitude-based — no existing numeric "significant attribute change" threshold exists anywhere in the repo. Real, pipeline-wired producer (`src/engine/evolution.py`'s non-hero level-up) confirmed too rare to hit within a real 1500-tick `Kernel.tick_once()` loop on `sandbox_world` (zero HERO-role entities, none leveled up) — verified instead via real hand-constructed `AttributeComponent` objects, same precedent as the wound events above. Two other grep-found `AttributeUpdate` producers (`src/domains/demographics/cohort.py::compute_elder_attribute_update`, `src/actions/attributes.py::AllocateAttributeAction`) are confirmed dead code — zero real callers. TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP |
| `item_equipped` / `item_unequipped` | event_extractor | Per-slot `entity.equipment.slots` delta, per real occurrence — `item_equipped` payload includes `previous_item_id` on a swap. Every producer with real narrative weight (combat durability decay, progression-conversion equip/repair) is gated off corpus-wide (`ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_PROGRESSION_EVOLUTION`); the one live, unconditional producer (`src/engine/evolution.py`'s goblin-kind species-evolution gear grant) requires a goblin-kind entity at evolution level >= 10, confirmed absent from `sandbox_world` (zero goblin-kind entities) within a real 1000-tick `Kernel.tick_once()` loop. Verified via real hand-constructed `EquipmentComponent` objects, same precedent as the wound/attribute events above. TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP |
| `equipment_durability_changed` | event_extractor | Per-slot `entity.equipment.durability` delta, per real occurrence — not per-tick (durability only changes on discrete combat-hit/repair actions). Severity on the field's real 0–100 scale: INFO for a repair/increase or a decrease staying >= 50.0, WARNING for a decrease dropping below 50.0, CRITICAL for a decrease reaching <= 0.0. The 50.0 threshold reuses the same intent already designed into `src/domains/progression/gaps.py`/`src/engine/gold_sink.py` (both compare against 0.5 on a 0-1 scale by mistake — a disclosed, unfixed scale-mismatch bug, see the ticket's own investigation.md), just applied on the field's actual scale. Same reachability/verification story as `item_equipped` above. TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP |
| `entity_role_changed` / `entity_faction_changed` | event_extractor | `entity.identity.role`/`.faction` delta, per real occurrence. Originally wired with zero live producers for either field (future-proof, zero runtime cost when unused), verified via real hand-constructed `IdentityComponent` objects since there was no live trigger of any kind, gated or otherwise, to attempt a real-kernel check against — TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP. Both fields have since gained a real, live producer: `role_set` via `OccupationChangeGoalScorer` (TCK-20260824-OCCUPATION-CHANGE-TRIGGER), and `faction_set` via `PartyLifecycleService.check_defection()` setting a defector's faction to `Faction.NEUTRAL` (TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE, 2026-09-06, `docs/world/affiliation_mutation.md`), each confirmed firing end-to-end through a real Kernel-tick/apply-path sequence in that ticket's own tests. Category placement here (`unscored_intentional`) reflects SimQ-scorer wiring, not producer existence, and is unchanged by either landing — whether real-corpus fire volume warrants scoring is a separate, unresolved question. |
| `recipe_learned` | event_extractor | Per new entry in `entity.identity.known_recipes` (set diff), per real occurrence. Real, unconditional producer (`src/engine/blacksmith.py::BlacksmithSystem.enforce`, wholesale recipe grant on a functional-blacksmith-tile visit with empty `known_recipes` — not feature-flag-gated). Trigger conditions confirmed met in `sandbox_world` (1 blacksmith building, all 18 entities start with empty `known_recipes`), but no entity happened to path onto the blacksmith tile within a real 1500-tick `Kernel.tick_once()` loop — verified instead via real hand-constructed `IdentityComponent` objects. TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP |
| `skill_cooldown_started` | event_extractor | Per new/changed entry in `entity.identity.cooldowns` (skill_id → tick_ready), per real occurrence. Real, action-router-wired producer (`src/engine/domain/skill_actions.py`) with no live AI driver ever selecting the `"SKILL"` action — same reachability class as `execute_allocate_ap`/`execute_repair` in the sibling attributes/equipment tickets. Verified via real hand-constructed `IdentityComponent` objects. TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP |
| `combat_engagement_started` | event_shapers (`CombatShaper`) | High-level combat-lifecycle event, fires alongside the existing `combat_initiated` gate — same tick, same entity pair. `payload.trigger_reason` (`GOAL_ENGAGE` / `OPPORTUNITY_ATTACK`) plus `attacker_snapshot`/`defender_snapshot` (level, hp/max_hp, atk/def, role, faction_id, species_id, bravery, action_style) via the new `_combat_entity_snapshot()` helper, so a later analysis can judge whether a given combat scenario was reasonable. Deliberately additive, not replacing `combat_initiated`. Real, pipeline-wired producer confirmed firing at real, non-zero volume in live corpus re-verification. **Decision (`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`, 2026-08-09): stays unscored, deliberately, not deferred** — it fires on the exact same real gate as the already-scored `combat_initiated` (`combat_active`, +2); promoting it would double-count the identical real-world event under a second event_type, not add new signal. TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY |
| `combat_engagement_ended` | event_shapers (`CombatShaper`) | High-level combat-lifecycle event covering all 4 real ways a combat engagement ends without necessarily continuing: `payload.outcome` = `KILL` (alongside the existing `entity_killed` gate), `CAUGHT_FLEEING` (a real opportunity attack that isn't also a kill — by construction only fires on a hostile's own disengagement movement), `PURSUIT_ABANDONED` (`task.payload_set.reason` in `LEASH_RETURN`/`STALEMATE_BREAK`, read from `e_upd.task` — no `CombatUpdate` present at all for this path), or `ESCAPED` (a new, additive `property_updates["combat_escape"] = "EVASIVE_SUCCESS"` tag written at the source in `src/engine/movement.py`'s real `engaged_hostiles and skip_oa` case — a successful, opportunity-attack-free disengagement previously left zero trace). Carries the same entity snapshot(s) as `combat_engagement_started`. Real, pipeline-wired producer; `PURSUIT_ABANDONED`/`ESCAPED` are narrower real paths, honestly disclosed if not observed at real corpus volume during Test-phase verification. **Decision (`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`, 2026-08-09): the event_type itself stays unscored, but its `KILL`/`ESCAPED` outcomes now also fire the real, scored `combat_resolved` signal (see §3.10) — a deliberate, semantic-mapping decision, not a promotion of `combat_engagement_ended` itself.** TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY |

---

## §6 Maintenance Notes

- When adding a new `event_type` to `event_extractor.py` or any domain emitter, check this table first.
- If the event should be scored, either: (a) use contract vocabulary directly, or (b) add a `_TRANSLATE_SIMPLE` / `_TRANSLATE_CONDITIONAL` entry to `quality_hub.py` and update this table.
- Engine emission gap events (§3) are the primary expansion surface for future SimQ coverage.
- All engine emission gaps are resolved. Only `camp_constructed` (§3.9) has no viable engine path — camps are pre-placed at world generation, not dynamically constructed during simulation.
- Run `make knowledge-index-update` after any change to docs in this directory.
