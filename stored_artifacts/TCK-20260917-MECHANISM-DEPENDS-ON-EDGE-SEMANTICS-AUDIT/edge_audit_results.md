---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
artifact_type: investigation
tags: [architecture, schema]
---

# Full per-edge audit results — TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT

All 70 edges audited by hand (not by the dispatched fork — see Provenance below), applying the
registry's own stated `depends_on` test: does the dependent mechanism's own real code produce a
meaningful result without the dependency's own state/output already existing, independent of which
mechanism's code calls the other. **Tally: 21 KEEP / 32 REMOVE / 17 UNCLASSIFIABLE.**

## Provenance — why this was audited by hand, not by the dispatched fork

A fork was dispatched to do the per-edge code lookup (the mechanical, well-specified part of this
task). It returned a bare tally with no per-edge evidence on its first completion. Re-requested with
an explicit output-shape specification (one line per edge, verdict + real file/function citation);
its second completion asserted *"the full 70-line verdict table has already been delivered in my
previous reply"* — no such content had ever reached this session. Both completions produced only a
terse task-notification summary. This is the fourth occurrence of this failure shape in this session
(per peer review from `rpg-feature-planning`), and the second occurrence is qualitatively worse than
a bare empty return: it asserts delivery of content that was never delivered, which defeats
re-request as a recovery strategy. Per a pre-decided cutoff (agreed before either retry, to avoid an
unbounded retry loop against a component that had already failed twice that day), the audit was
redone entirely by hand rather than bounced a third time. This trail was passed to
`agent-working-design`'s pending fork-reliability detection ticket.

## Method note: grep vs. graphify

Per a live question from peer review, tool choice was tracked per edge. **Plain grep for the
mechanism's literal id/class name was sufficient for the large majority of edges** (state names and
class names generally matched well enough for `grep -rn` to find the real implementation). `graphify
query` was decisive in at least 3 concrete cases where a literal-name grep found nothing and graphify
surfaced the real code via a fuzzy/AST match:

- `regional_trauma` — grep for `regional_trauma`/`RegionalTrauma` found nothing; `graphify query
  "trauma"` surfaced `TraumaRegionConcernBridge` (`src/domains/world_emergence/services.py`), whose
  real state field is `RegionState.trauma_score` — word-order reversed from the mechanism id (Trauma
  *Region* vs *Regional* Trauma), exactly the naming-drift class grep misses.
- `ruins_mines_battlefields` — grep found nothing; `graphify query "battlefield"` surfaced
  `create_battlefield_scar()` (`src/world/consequences.py`) as the closest candidate (ultimately
  still marked UNCLASSIFIABLE below — confidence in the mapping was too low to force a verdict, not
  because the search itself failed).
- `party_formation` / `city` / `class_assignment` — graphify's broader traversal surfaced adjacent
  real code (`party.py`, `settlement_personality.py`) that helped narrow the search even where the
  final mapping stayed uncertain.

Where grep failed and graphify also failed or returned an unconvincing match (e.g. `country_lifecycle`,
`nest`, `settlement_capacity_axis`, `goal_hierarchy`), the edge is recorded UNCLASSIFIABLE rather than
forcing a verdict from a low-confidence identification. This is a real, if informal, measurement: for
this specific audit, grep was sufficient for most edges but graphify's AST/fuzzy matching resolved a
handful of genuine naming-drift misses that would otherwise have gone unclassified or, worse, wrongly
verified against the wrong code.

## Full verdict table

Format: `dependent → dependency | VERDICT | evidence`

### KEEP (21)

1. `combat_resolution → status_effects` | KEEP | `src/engine/combat.py:84` — `resolve_attack` reads
   `defender.combat.status_effects` directly (`frozen` check multiplies `atk_mult` by 1.5).
2. `combat_resolution → entity_role` | KEEP | `src/engine/combat.py:136` — reads
   `defender.identity.role` directly to gate `is_lethal` (HERO permadeath exemption).
3. `combat_engagement → personality` | KEEP | `src/domains/combat_engagement/risk_evaluator.py:41,82,98`
   — reads `actor.identity.personality` traits directly into `personality_bias`.
4. `derived_stats → attributes_biology` | KEEP | `src/progression/leveling.py:76-103` —
   `recalculate_combat_stats` reads `attributes.vitality/strength/endurance/agility` directly.
5. `succession → aging_death` | KEEP | `src/systems/lifecycle_systems/lifecycle.py:137-206` —
   `resolve_lifecycle` detects `is_dead` then triggers `_select_default_heir` succession logic.
6. `adventure_routing → entity_role` | KEEP | `src/domains/adventure/scoring.py:194,199,206,229,456`
   — reads `entity.identity.role` extensively.
7. `adventure_routing → personality` | KEEP | `src/domains/adventure/scoring.py:122` — reads
   `entity.identity.personality` directly.
8. `adventure_routing → diplomacy` | KEEP | `src/domains/adventure/scoring.py:202` — reads
   `fs.diplomatic_relations` directly.
9. `strategic_intelligence_core → belief_cycle` | KEEP | `src/systems/strategic_systems/intelligence.py:93,436,448`
   — imports and calls `BeliefCycleSystem.process_observation()`/`apply_contradiction()`, consuming
   their return values in its own decision logic.
10. `party_formation → movement` | KEEP | `src/systems/social_systems/party.py:115-116` — reads
    `target.navigation.position` directly.
11. `cross_episode_social_consequences → social_memory` | KEEP | `src/systems/social_systems/consequence_events.py:82-111`
    — `evaluate_social_consequence` reads `campaign_state.social_memories`/`faction_social_memories`
    directly.
12. `fame → campaigns` | KEEP | `src/domains/fame/exporter.py:83` — reads
    `campaign_state.entity_fame.get(entity_id)` (prior state) as an input to its own carry-forward.
13. `fidelity_drift → campaigns` | KEEP | `src/domains/fidelity/exporter.py:78` — reads
    `campaign_state.historical_drift.get(entry_id)` (prior state) as an input to its own drift calc.
14. `belief_institution → campaigns` | KEEP | `src/domains/belief_institution/exporter.py:94` — reads
    `campaign_state.belief_institutions.get(...)` (prior state) as an input.
15. `world_boss_spawn → regional_trauma` | KEEP | `src/world/boss.py:101,227` — reads
    `region.trauma_score >= BOSS_SPAWN_TRAUMA_THRESHOLD` directly as a spawn gate.
16. `camp → regional_trauma` | KEEP | `src/world/camp.py:44` — reads `region.trauma_score > 50.0`
    directly.
17. `equipment_scoring → inventory_trade_conservation` | KEEP | `src/core/equipment.py:211-216` —
    `auto_equip` iterates `entity.inventory.items` directly.
18. `crafting → inventory_trade_conservation` | KEEP | `src/systems/economy_systems/crafting.py:37-56`
    — reads `entity.inventory.items`/`max_slots` directly for craft-eligibility.
19. `town_services → buildings` | KEEP | `src/town/shop.py:22,74`, `src/town/blacksmith.py:19` —
    read `state.buildings.values()` filtering on `b.functional` directly.
20. `building_sabotage → buildings` | KEEP | `src/engine/sabotage.py:62-65` — directly reads/mutates
    `building.hp`.
21. `regional_sovereignty → world_generation` | KEEP | `src/world/influence.py` — `process_influence_shift`
    reads `state.regions[r_id]` (owner_faction_id/influence), state that only exists because
    world_generation created it. Weaker than the others on this list (a foundational "world must
    exist" prerequisite shared by nearly every region-based mechanism, not a mechanism-specific
    dynamic read) — kept rather than forced to REMOVE because the code-read criterion is still
    literally satisfied, but flagged here as the least clean-cut KEEP in this set.

### REMOVE (32)

1. `combat_resolution → combat_engagement` | REMOVE | `src/engine/combat.py:129-243` (`resolve_attack`)
   never reads combat_engagement state; `apply_combat_learning` (combat_engagement's own learning
   update, `src/domains/combat_engagement/learning_outcome.py`) is called AFTER `resolve_attack`
   using ITS output (`src/engine/domain/combat_actions.py:133-134`) — the real data flow runs the
   opposite direction from the declared edge.
2. `combat_resolution → skill_unlocks` | REMOVE | `resolve_skill_usage` (`src/engine/combat.py:256-325`)
   never reads `learned_skills`; the unlock gate lives entirely in the caller,
   `SkillActions.execute_skill` (`src/engine/domain/skill_actions.py:37-42`), before combat
   resolution is ever invoked — same shape as the already-confirmed `tactical_decision` correction.
3. `tactical_decision → action_pacing_readiness` | REMOVE | `src/engine/tactical.py` has zero
   readiness references.
4. `combat_engagement → action_pacing_readiness` | REMOVE | zero readiness references anywhere in
   `src/domains/combat_engagement/*.py`.
5. `movement → action_pacing_readiness` | REMOVE | `src/engine/movement.py` and
   `src/engine/domain/movement_actions.py` have zero readiness references; the gate is the caller
   (`LegalityServiceV2.verify_movement_legality`, `src/engine/legality.py:154-182`, and the generic
   `action_router.py:39` check) — movement's own `resolve_move` computes position purely from
   distance/speed, independent of readiness.
6. `readiness_speed_scaling → action_pacing_readiness` | REMOVE | its own formula
   (`src/progression/leveling.py:102`, `readiness_speed = f(agility)`) computes a rate coefficient
   from `attributes.agility` only — it never reads the current readiness value itself.
7. `interaction_channeling → action_pacing_readiness` | REMOVE | `execute_interact`
   (`src/engine/domain/core_actions.py:586+`) only WRITES `readiness_delta` as an output cost, never
   reads readiness as an input.
8. `entity_trade → action_pacing_readiness` | REMOVE | `execute_trade`
   (`src/engine/domain/core_actions.py:220+`) only writes `readiness_delta`, same pattern.
9. `team_up → action_pacing_readiness` | REMOVE | `execute_team_up`
   (`src/engine/domain/core_actions.py:147-215`) only writes `readiness_delta`, same pattern.
10. `xp_leveling → combat_resolution` | REMOVE | `src/progression/leveling.py` never references
    `CombatResolutionSystem`/`resolve_attack`; XP is a generic currency fed through a shared
    `ResourceTransferIntent` pipeline that combat is just one producer of, not a combat-specific
    coupling.
11. `breakthrough_bonuses → xp_leveling` | REMOVE | `BreakthroughService.apply_bonuses`
    (`src/progression/breakthroughs.py`, itself commented "Placeholder registry for Phase 8
    recovery") takes a pre-decided `breakthrough_ids` set as a parameter; no code path was found
    anywhere that derives that set from xp/level state.
12. `self_model → perception` | REMOVE | `src/cognition/self_model_phase.py`/`src/core/self_model.py`
    never import from `src.domains.perception`; the `perceived_condition/weaknesses/strengths`
    fields are self_model's own internal self-assessment vocabulary (health/stamina/equipment
    introspection) — a naming coincidence with `perception`'s `PerceivedEntity` types, not a real
    functional link.
13. `self_model → trauma` | REMOVE | zero trauma/wound references anywhere in the same two files.
14. `perception → cognition_capacity_fatigue` | REMOVE | `PerceptionBudget.max_perceived`
    (`src/domains/perception/filter.py:29-31`) is a hardcoded default (`10`), never derived from
    fatigue state; `phase.py:22` constructs it with that static default.
15. `emotion → tactical_decision` | REMOVE | `src/domains/emotion/emotion_service.py` has zero
    tactical/`TacticalDecisionSystem` references.
16. `affection_relationship_bonds → interaction_channeling` | REMOVE |
    `src/systems/social_systems/relationships.py` only tracks bond state passively
    (sentiment/familiarity/`last_interaction_tick`); never calls into interaction_channeling's own
    action-execution code.
17. `belief_cycle → self_model` | REMOVE | `src/systems/strategic_systems/belief.py` has zero
    self_model references.
18. `causal_spatial_memory → belief_cycle` | REMOVE | `src/domains/memory/phase.py`
    (`MemoryUpdatePhase`) has zero belief/`BeliefEntry` references.
19. `adventure_routing → motivation_doctrine` | REMOVE | zero motivation/doctrine references in
    `src/domains/adventure/{service,scoring,mapper}.py`.
20. `adventure_routing → cognition_capacity_fatigue` | REMOVE | zero fatigue references in the same
    three files.
21. `reputation → affection_relationship_bonds` | REMOVE | `src/systems/social_systems/reputation.py`
    has zero bond/familiarity/sentiment references.
22. `cross_episode_grief_nemesis → campaigns` | REMOVE |
    `GriefUrgencyImporter.apply()`/`build_strategic_update()`
    (`src/domains/campaigns/grief_urgency.py`) take pre-built `GriefUrgencyModifier`/`NemesisRelation`
    value objects as parameters; `CampaignOrchestrator` (`orchestrator.py:336,357`) reads
    `CampaignState` and constructs those objects BEFORE calling in — grief_urgency's own code never
    reads `CampaignState` directly.
23. `regional_trauma → betrayal_siege_war` | REMOVE | `region.trauma_score`'s own update logic
    (`src/world/consequences.py:42` decay, `src/engine/apply_plan.py:230` building-death trigger)
    never references siege_state; `src/engine/military_conflict.py` (the real
    `betrayal_siege_war` implementation) never touches trauma or buildings.
24. `buildings → city` | REMOVE | `src/town/buildings.py` has zero city references.
25. `town_services → city` | REMOVE | `src/town/{shop,blacksmith,town_navigation}.py` reference
    individual buildings, never a "city" concept.
26. `clan → betrayal_siege_war` | REMOVE | `src/systems/social_systems/clan_lifecycle.py` has zero
    siege/WAR references.
27. `evolution → derived_stats` | REMOVE | `src/engine/evolution.py` never calls
    `LevelingService.recalculate_combat_stats` or reads any attribute-derived combat stat; only uses
    `get_xp_required`/`get_unlocked_skills`.
28. `regional_sovereignty → betrayal_siege_war` | REMOVE | `src/world/influence.py`
    (`FactionInfluenceService.process_influence_shift`) has zero siege references; influence shifts
    are computed purely from `recent_deaths`, independent of active siege state.
29. `demographic_cohort_cycle → regional_trauma` | REMOVE | `src/domains/demographics/cohort.py`
    (`DemographicCycleService`) has zero trauma references.
30. `calamity_intensity → regional_sovereignty` | REMOVE | `src/world/calamity.py` has zero
    `owner_faction_id`/`influence` references.
31. `resource_harvesting → inventory_trade_conservation` | REMOVE |
    `src/systems/world_systems/harvesting.py` (`HarvestSystem`) has zero inventory references at
    all — it emits its own output independent of inventory state, mirroring the
    combat_resolution/skill_unlocks caller-side-only pattern.
32. `demographic_cohort_cycle → regional_sovereignty` | REMOVE | same file
    (`src/domains/demographics/cohort.py`) has zero `owner_faction_id`/`influence` references either
    — this was a **both-implemented_by-bound edge** (highest evidence tier available), and it still
    fails the test cleanly.

### UNCLASSIFIABLE (17) — no distinguishable real implementation located for at least one side
after a genuine grep + graphify search attempt; recorded rather than forced

1. `conversation → action_pacing_readiness` | searched TALK/dialogue/conversation keywords across
   `src/engine/` and `src/systems/` — no distinguishable "conversation" implementation exists
   separate from the generic `execute_interact` (already separately attributed to
   `interaction_channeling`). Consistent with its own `state: gap`.
2. `class_assignment → race_archetype` | grep for `ClassAssignmentService`/`assign_class` and
   `RaceArchetype`/`RACE_ARCHETYPE`, plus `graphify query "class assignment archetype"` — all
   inconclusive; no confident, distinguishable implementation for either side.
3. `build_diversity → class_assignment` | depends on locating `class_assignment` first (above);
   same result.
4. `trauma → combat_resolution` | no per-entity "trauma" state field exists in `src/core/state.py`
   (only `RegionState.trauma_score`, which is regional, and `WoundState`, which is physical
   SLASH/CRUSH/PIERCE/BURN injury, not clearly psychological trauma) — searched grep and
   `graphify query "psychological trauma entity"` without a confident match.
5. `self_model → trauma`'s companion investigation (above) directly informs this: same
   unlocatable dependency.
6. `motivation_doctrine → goal_hierarchy` | `MotivationModel` (`src/core/cognition.py:419-438`) is a
   pure dataclass with only `to_canonical_dict` — no computational logic to check. Its own docstring
   states the `doctrine`/`values` fields were already formally retired as dead code
   (`TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT`, "confirmed dead, never read") — worth its
   own flag, separate from this audit (see Implementation Notes).
7. `motivation_doctrine → affection_relationship_bonds` | same underlying cause as above.
8. `commitment_betrayal → combat_resolution` | no distinct `commitment_betrayal` implementation
   located separate from `commitment_pressure_consequences`'s own 4 bound files — the "betrayer"
   reputation label both mechanisms would plausibly touch is set inside
   `src/domains/commitment/reputation.py:21`, itself one of `commitment_pressure_consequences`'s own
   files, making it impossible to attribute a read to a genuinely separate `commitment_betrayal`
   module.
9. `goal_hierarchy → belief_cycle` | `goal_hierarchy`'s own implementation could not be located —
   grep for class names and `graphify query "goal hierarchy"` (which surfaced only
   `.claude/skills/cognition-strategy/SKILL.md` doc nodes, not code) both inconclusive.
10. `goal_hierarchy → reputation` | same underlying cause.
11. `committed_intentions → goal_hierarchy` | `CommitmentModel` (`src/core/cognition.py:465-477`) is
    also a pure dataclass (only `to_canonical_dict`) — no computation to check, and `goal_hierarchy`
    itself is unlocatable per above.
12. `country_lifecycle → betrayal_siege_war` | no implementation found anywhere for
    `country_lifecycle` (grep for `CountryLifecycle`/`Country` class names, and broader search under
    `src/world/`, `src/domains/` — all empty).
13. `city → regional_sovereignty` | no distinct "city" aggregate implementation found (checked
    `src/town/*.py`, `graphify query "city settlement"` — drifted to unrelated
    `SettlementPersonalityService`/campaign nodes).
14. `ruins_mines_battlefields → regional_trauma` | `graphify query "battlefield"` surfaced
    `create_battlefield_scar()` (`src/world/consequences.py:58-77`) as the closest candidate, but
    confidence this is genuinely the "ruins/mines/battlefields" mechanism (rather than an unrelated
    death-scar decay marker) was too low to force a verdict either way — the function itself doesn't
    reference `trauma_score`, but the mapping itself is unconfirmed.
15. `ruins_mines_battlefields → regional_sovereignty` | same low-confidence mapping issue.
16. `nest → camp` | no implementation found anywhere for "nest" as a mechanism (searched
    `class Nest`).
17. `settlement_capacity_axis → race_archetype` | depends on `race_archetype`, which is itself
    unlocatable per #2 above.

## Priority-shift measurement (Acceptance Criteria #3)

Re-ran `tools/mechanism_registry/generate_mechanism_priority_view.py` against the registry before
and after the 32 removals (before = `git show HEAD:registries/mechanisms.yaml` at the commit prior
to this ticket's own edit). **The shift is large, not negligible:**

| Mechanism | Priority before → after | Dependents before → after |
|---|---|---|
| `movement` | 75 → 25 | 15 → 5 |
| `personality` | 75 → 10 | 15 → 2 |
| `entity_role` | 70 → 25 | 14 → 5 |
| `betrayal_siege_war` | 42 → 3 | 14 → 1 |
| `status_effects` | 70 → 20 | 14 → 4 |
| `belief_cycle` | 30 → 20 | 6 → 4 |
| `interaction_channeling` | 30 → (dropped off top-N) | 6 → 0 |
| `cognition_capacity_fatigue` | 45 → (dropped off top-N) | 9 → 0 |
| `perception` | 40 → (dropped off top-N) | 8 → 0 |
| `trauma` | 40 → (dropped off top-N) | 8 → 0 |
| `goal_hierarchy` | 15 → 10 | 3 → 2 |
| `reputation` | 12 → 9 | 4 → 3 |
| `affection_relationship_bonds` | 25 → 5 | 5 → 1 |
| `attributes_biology` | 10 → 5 | 2 → 1 |
| `campaigns` | 4 → 3 | 4 → 3 |
| `world_generation` | 8 → 3 | 8 → 3 |
| `inventory_trade_conservation` | 3 → 2 | 3 → 2 |

`betrayal_siege_war` alone dropped from the 5th-highest derived priority in the registry to
effectively off the list (14 dependents → 1) — it was almost entirely propped up by edges that did
not survive this audit (`regional_trauma`, `regional_sovereignty`, `clan`, `country_lifecycle`
[UNCLASSIFIABLE, not removed but also not confirmed], `demographic_cohort_cycle` indirectly). Several
mechanisms that were previously buried below the view's cutoff now surface
(`adventure_routing`, `belief_institution`, `breakthrough_bonuses`, `build_diversity`,
`building_sabotage`) because the mechanisms that had been artificially inflating the ranking above
them lost their unearned priority. This confirms the ticket's own motivating concern: **the "what to
fix next" ranking this registry exists to produce was measuring something other than real blast
radius** for a substantial fraction of the registry before this audit.
