---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT
artifact_type: investigation
tags: [architecture, investigation, schema]
---

# Investigation — TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT

## Method

1. Extracted all 73 mechanism-mapped atlas cards (mechanism id, current `state`/`verified`, badge
   `cls`/`text`, full `desc` prose) from `docs/brainstorm/rpg_feature_atlas.html`'s
   `#card-sections-data` JSON blob, using the existing, already-verified
   `mechanism_atlas_card_mapping.py` mapping. Dumped to a scratch file for review.
2. A forked sub-agent read all 71 non-`camp`/`motivation_doctrine` entries (those two were already
   resolved pre-ticket, see Related Tickets) against the two known caveat shapes -- precondition-gap
   (`camp`'s shape: real code, never triggers in practice) and stale-architecture
   (`motivation_doctrine`'s shape: prose describes code since retired/changed), cross-checking
   candidates against `docs/guidelines/intentional_divergences.md`. Flagged 6 candidates, reported
   the other 65 as read-with-no-issue (full id list below).
3. Every one of the 6 flagged candidates was independently re-verified by direct code read (grep for
   real callers, `git blame` for when code landed, cross-reading the cited divergence-record entry)
   -- the fork's triage was a lead-generation pass, not a source of truth on its own, per this
   ticket's own `code_trace` discipline (every verdict here is a deliberate read, not
   auto-ingested).

## Full "read, no issue" list (65 of 73)

action_pacing_readiness, adventure_routing, belief_cycle, betrayal_siege_war,
breakthrough_bonuses, building_sabotage, campaigns, causal_spatial_memory, chronicle, city, clan,
class_assignment, cognition_capacity_fatigue, combat_resolution, commitment_betrayal,
committed_intentions, conversation, country_lifecycle, crafting, cross_episode_grief_nemesis,
cross_episode_social_consequences, cultural_drift, declared_cognition_schema,
demographic_cohort_cycle, derived_stats, diplomacy, emotion, entity_role, entity_trade,
equipment_scoring, evolution, genetics_aptitude, goal_hierarchy, gods_pantheon_blessings, guilds,
information_trust_deception, interaction_channeling, inventory_trade_conservation,
knowledge_model, movement, opportunity_rumor_seeds, party_formation, perception, personality,
quest_generation_sourcing, race_archetype, race_collective_force, regional_sovereignty,
reputation, ruins_mines_battlefields, self_model, settlement_capacity_axis, skill_unlocks,
social_contracts, social_memory, status_effects, strategic_intelligence_core, succession,
tactical_decision, team_up, temporal_pressure, town_services, world_boss_spawn, world_generation,
xp_leveling

(68 design-idea cards and the 2 no-atlas-card mechanisms, `nest`/`lair`, are out of scope per the
ticket's own Out of Scope section.)

## 6 flagged candidates -- findings and disposition

All 6 turned out to have real, verifiable substance -- none were pure false positives, though
severity and shape varied widely. Every disposition below is `code_trace`, backed by a direct
read cited in the mechanism's own `verified` block (or addendum) in `registries/mechanisms.yaml`.

### 1. `build_diversity` -- stale-architecture, real state correction
Card claimed `state: gap` ("not even a stub", "zero implementing code"). Direct read found
`TCK-20260831-CLASS-TIER-BRANCHING` (`intentional_divergences.md` §2.49 / DEV-006) landed real,
tested class-tier branching infrastructure (`CLASS_TIER_REGISTRY`, `ClassTierService`, a real
`class_id_set` apply-path field) **before** a 2026-09-19 depends-on-edge-resolution comment that
still said "zero implementing code" -- a real, dated methodology miss, not a stale card alone.
`ClassTierService.apply_bonuses()` has a real, live, non-test caller (`rpg_depth.py:368`), so
`orphan` (tried first) was also wrong per `mechanism_state_caller_check.py`'s own
`orphan_with_callers` finding -- corrected to **`partial`**: real, called, wired code that
currently no-ops for every entity, because nothing in `src/` ever sets `class_id_set` to a tier
value during real play (DEV-006's own "Scope note" already said so). `implemented_by` added.
Consumer artifacts (atlas badge, capabilities tier) regenerated via the sanctioned tools.

### 2. `trauma` -- precondition-gap, addendum (state unchanged)
Card's own "Correction, verified directly" paragraph already found `heal_wound()` dead
(zero production callers) but framed it as ordinary dead code. Direct read confirms it is
stronger than that: `heal_wound()`/`get_diagnosis_quality()` were **deleted outright** by a
ratified decision (DEV-005, `TCK-20260824-WOUND-HEALING-DECISION`) -- wounds are declared
**permanent**. The card's own "a Wound heals, it may leave behind a Scar... has a chance to"
framing describes a decision this codebase deliberately reversed, not an open probability.
`ScarState`/`scars_add` remain real, typed, and apply-path-wired but zero-producer -- `orphan`-
shaped, scoped to the Scar half only. `state` unchanged (`done` -- Wound infliction, the
dominant claim, is real and fully exercised). Addendum added citing DEV-005; card desc corrected.

### 3. `combat_engagement` -- internal self-contradiction, addendum (state unchanged)
The card's own desc carries two dated paragraphs that disagree: a 2026-09-15 correction
("nothing downstream ever acts on the result... does not reproduce, read as historical") and the
registry's own `verified` block (2026-09-16/17, "1960 -> 837") which implies a real, current
effect. Direct read resolves the contradiction: `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-
WIRED-TO-EXECUTION` (closed) landed a real per-attack risk gate in `action_router.py` reading
`last_combat_posture`/`last_combat_posture_target` -- the exact mechanism behind the verified
block's own "1960 -> 837" figure. The desc's 2026-09-15 paragraph is now stale, not current.
`PostureIntentResolver.resolve()`'s own `intent`/`strat` output is still discarded
(`intent_results` hardcoded `[]`) -- that specific sub-claim remains true. `state` unchanged
(`done`, correctly verified). Addendum added to the `verified` block; card desc corrected to
note the fix superseded the "nothing consumes this" framing.

### 4. `aging_death` -- stale-architecture (two claims), addendum (state unchanged)
Card claimed `compute_elder_attribute_update()` is "a genuine orphan... only its definition and
its internal self-call... nothing calls it on a live entity," and separately that the `LifeStage`
enum "defaults to ADULT and never transitions." Both are false as of a single commit
(`5993cac368`, 2026-08-31, `TCK-20260824-LIFE-STAGE-TRANSITIONS`) that predates the "genuine
orphan" claim: `LifecycleSystem.resolve_lifecycle()` (this entry's own bound method) both sets
`life_stage_set=target_stage` on a real forward transition into ELDER, and in that same branch
calls `compute_elder_attribute_update()` directly. What remains genuinely open (not resolved
here): whether this transition ever fires at real corpus tick-depths -- the ELDER threshold
(17.28M ticks) sits below the real default death age (20.16M ticks, not the card's stated
"10,000", itself corrected), so it's numerically reachable but far beyond any real corpus run's
tick horizon (1000-5000 ticks), matching this epic's own null-result-horizon caution. `state`
unchanged (`done` -- the entry's dominant OLD_AGE-death claim is independently scenario-verified
and unaffected). Addendum added; card desc corrected (both claims, plus the stale "10,000"
figure).

### 5. `affection_relationship_bonds` -- precondition-gap, addendum (state unchanged)
Card already correctly documented that `place_attachment` (the "affection to a city" sub-feature)
accumulates for real but is never read by any decision logic -- a genuine write-only, zero-effect
field. Confirmed by a direct repo-wide check for any read of `place_attachment` outside its own
writer/apply/serialization chain: none. This entry's own existing `verified` block only covers a
separate binding-ambiguity question (already flagged for the roadmap session, see
`TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`) -- this caveat had no `verified`
citation of its own until now, so it is recorded per AC #2 even though the underlying fact was
already correctly stated in the card. `state` unchanged (`done` -- the dominant claim, personal
sentiment/trust/nemesis tracking, is real with real consumers).

### 6. `attributes_biology` -- stale cross-reference, quick fix (state unchanged)
Card's own closing sentence pointed at "the Emotion card... which found the typed model but it's
orphaned." `emotion` was corrected `orphan -> done` (scenario-verified) on 2026-09-20
(`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`) -- the cross-reference is simply out of
date. Low severity; card desc corrected, no registry change needed (this entry's own claim was
never wrong).

## Verification run after every registry/atlas edit
`registries/mechanisms.yaml` validated clean (`make mechanism-registry-validate`, 93 mechanisms).
`mechanism_atlas_regenerate.py`/`mechanism_capabilities_regenerate.py` ran to sync
`build_diversity`'s badge/tier after its state change (`gap -> partial`) -- each fixed exactly the
one expected card, confirmed by the full `tests/unit/tools/` mechanism suite (257 tests) passing,
including the load-bearing `test_real_atlas_has_no_drift_against_the_real_registry`,
`test_real_capabilities_has_no_drift_against_the_real_registry`,
`test_real_wiring_map_has_no_drift_against_the_real_registry`, and
`test_real_registry_findings_pinned` (the `mechanism_state_caller_check.py` baseline, which
correctly flagged my own first attempt at `build_diversity: orphan` as `orphan_with_callers` --
caught and corrected to `partial` before this ticket closed). `mechanism_prose_field_drift_check.py`
(report-only) ran clean: 0 hits across 93 mechanisms.

Side effect, noted not chased: `implemented_by` coverage moved 76/93 -> 77/93 as a byproduct of
`build_diversity`'s own binding. The closed `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-
EXTENSION` and its replacement `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` both cite
76/93 as of their own 2026-09-23 closure/filing time, accurate at that point -- not retroactively
updated here, since chasing a moving figure across tickets is not this ticket's own job.

## Related Tickets
Same as the ticket's own Related Tickets section -- not duplicated here.
