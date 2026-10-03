---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE
artifact_type: investigation
tags: [quests, strategy, world-evolution, pressure]
---

# Investigation — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

## Current Behavior

`QuestGenerator` (`src/quests/generator.py`) is confirmed **still static-template, hero-level-only**
as of 2026-07-04. Re-verified directly against source:

- `TEMPLATES` is a fixed `List[QuestTemplate]` class attribute (6 entries) keyed only by
  `(min_level, max_level)` bands: `q_slime_cull`/`q_wood_survey` (1–5/1–8), `q_wolf_hunt`/`q_herb_gather`
  (6–12/4–10), `q_bandit_bounty`/`q_camp_liberate` (11–100/15–100).
- `generate(seed, level, tick, existing_ids)` filters `TEMPLATES` by level band and dedupes against
  `existing_ids`, then does `rng.choice(Domain.QUEST, tick, level, candidates)` — a uniform,
  stateless, deterministic pick from whatever survives the level filter. No world-state parameter
  exists in the signature at all.
- Reward/goal scaling (`scale_factor`, `scaled_goal/xp/gold`) is purely a function of `level` vs.
  `template.min_level` — no pressure input there either.

**Single live call site**: `src/town/guild.py::GuildAction.visit()` →
`QuestGenerator.generate_quests(seed=state.tick + entity.id, level=entity.identity.evolution_level,
tick=state.tick, building_id=1000, count=1)`. `GuildAction.visit` already has `state:
AuthoritativeState` in scope and already reads `state.resource_nodes` for the (separate) leads
logic — extending it to also read `state.regions` for quest generation is a natural, local change,
not a new architectural seam.

**Dead sibling code (do not confuse with the above)**: A second, unrelated `QuestGenerator` class
exists at `src/systems/world_systems/quest_generator.py` (re-exported via
`src/systems/quest_generator.py`), with a `generate_for_entity(entity, state)` method that *does*
already read `state.regions[...].stability`, `Faction.MONSTER` ownership, and
`state.global_resources`. **Grep confirms zero call sites** for `generate_for_entity` anywhere in
`src/` or `tests/` — this is unused/orphaned code, not a wired precedent. It should not be treated
as prior art to build on, and this ticket's scope (per its own "Related Code Areas") is
unambiguously `src/quests/generator.py`, not this file. Worth flagging to the human/reviewer since
it's easy to edit the wrong file.

**A third, already-wired, already-pressure-driven quest pipeline exists and is out of scope**:
`QuestOpportunity` (`src/core/models/quests.py`) + `state.quest_registry` + `QuestOpportunityGenerator`
(`src/domains/world_emergence/services.py`) + `QuestOpportunityRewardSystem`
(`src/engine/pipeline_phases/quest_opportunity_rewards.py`). This system already converts
`WorldEvent(RESOURCE_DEPLETED)` and high-severity `WorldEvent(ENTITY_DEATH/CAMP_RAID)` into
`QuestOpportunity` records added to `state.quest_registry` via `WorldEmergencePhase.execute()` →
`update.quest_registry_add`, applied authoritatively in `src/engine/apply.py:317-320`, scored by
`AdventureRouteScorer` (`src/domains/adventure/scoring.py`) for route selection, and paid out by
`QuestOpportunityRewardSystem.enforce()`. **This is a fully separate quest content model** from the
`QuestState`/`QuestTemplate`/Guild-project model this ticket targets — different dataclass
(`QuestOpportunity` vs `QuestState`), different registry (`state.quest_registry` vs
`entity.strategic.projects`), different consumption path (route scoring vs Guild NPC visit).
The ticket's premise ("signals already exist, just not wired to quests") is **only true for the
Guild/`QuestTemplate` path** — it is not true for the adventure-opportunity path, which has been
pressure-driven since TCK-20260619-E23A/E23C. This is not a blocker (the ticket explicitly scopes to
`src/quests/generator.py` and explicitly excludes "the broader quest activation precondition chain"
and "`ResourceOpportunityProvider` itself"), but the overlap was not previously documented and
should be named explicitly in the ticket/plan so a future reader doesn't conflate the two systems or
try to merge them (see Risks below).

There is also a fourth, apparently-abandoned scaffold: `DynamicQuestSeedService.generate()`
(`src/domains/world_emergence/services.py`) produces `QuestSeed` records
(`src/domains/world_emergence/schema.py`) that are attached to `WorldEmergenceResult.quest_seeds` in
`WorldEmergencePhase.execute()` step 5 — but `result.quest_seeds` is **never read anywhere** after
that assignment (grepped; no consumer in `src/` or `tests/`). This looks like an earlier,
never-finished attempt at pressure→quest wiring that was superseded by the `QuestOpportunity` path.
Not this ticket's job to fix, but worth a one-line note in the plan so it isn't mistaken for a
currently-working mechanism.

## Mechanics/Engine Constraints

**Where the three pressure signals actually live, confirmed by direct read of `src/core/state.py`:**

| Signal | Field | Type | Durable? |
|---|---|---|---|
| Regional trauma | `RegionState.trauma_score` (`src/core/state.py:246`) | `float`, persistent "scar" value | Yes — durable field, part of `to_canonical_dict()` |
| Threat/hazard level | `RegionState.hazard_level` (`:242`) and `RegionState.retaliation_pressure` (`:247`) | `float` 0–1 (hazard), short-term monster response (retaliation) | Yes — both durable fields |
| Resource scarcity | **Not a durable per-region scalar.** Must be derived at read-time from `state.resource_nodes: Dict[int, ResourceNodeState]` (`:905`), specifically `remaining_charges / max_charges` for nodes matching the entity's region via `ResourceRegistry.get(node.kind).source_region_tags` (same pattern `ResourceOpportunityProvider.get_opportunities()` already uses at `src/world/providers/resources.py:53-72`) | Node fields are durable; the ratio is a cheap derived read, not new state |

All three are genuinely available today — not just described in docs. `docs/mechanics/05_world_evolution.md` §2 ("Regional Trauma & Hazards") documents the trauma/hazard formulas correctly and matches `RegionalPressureModel.evaluate()`'s use of `reg_state.trauma_score` and `reg_state.hazard_level` (`src/domains/world_emergence/models.py:76-79`).

**Important correction to the ticket's own citation**: `docs/mechanics/03_economic_laws.md` has **no
"§resource pressure" section at all** (grepped — zero hits for "pressure" or "scarcity" in that
file; the only trauma-adjacent line is a shop-pricing surcharge note). The actual resource-scarcity
formula (`ScarcityModel.evaluate()`: `scarcity = min(1.0, harv*0.08 + depl*0.25)`) lives in
`src/domains/world_emergence/models.py` and is documented in
`docs/simulation/domains/world_emergence_contract.md` (Step 3), not in the Mechanics Bible. This
ticket's AC4 ("cross-referenced correctly for the signal formulas actually used") therefore cannot
be satisfied by citing `03_economic_laws.md` §resource pressure as originally written — planning
should either (a) cite `world_emergence_contract.md` for the *existing* `ScarcityModel` formula (if
reused) or, more likely given the "derive from resource_nodes directly" recommendation below, (b)
document the *new*, simpler node-charge-ratio formula QuestGenerator will actually use, in whichever
doc is authoritative for it (`05_world_evolution.md` §3 "Ecology & Replenishment" is the closest
existing home for resource-node charge/respawn mechanics).

**A critical wiring constraint**: `RegionalPressure`/`ResourceScarcitySignal`/`WorldEmergenceResult`
(the "official" Phase 8 pressure models, `ScarcityModel`/`RegionalPressureModel`) are **ephemeral**
— computed once per `WorldEmergencePhase.execute()` call from a 100-tick rolling window of
`recent_events`, and **not stored anywhere in `AuthoritativeState`** (confirmed: no
`regional_pressures`/`scarcity_signals`/`world_emergence_result` field exists in `state.py`).
`GuildAction.visit()` runs in a different phase/call context and has no access to that phase's
`WorldEventAggregator` window or `recent_events`. **Recommendation: QuestGenerator/GuildAction should
read the three signals directly from durable state** (`region.trauma_score`, `region.hazard_level`,
node-charge ratios) rather than trying to reuse `ScarcityModel`/`RegionalPressureModel`, which are
not reachable from the Guild call site without a much larger plumbing change (passing
`WorldEmergenceResult` through to `GuildAction`, which is out of scope and would duplicate work
already flagged as a non-goal). This keeps the fix local and consistent with how
`ResourceOpportunityProvider` already does it (reads `state.resource_nodes` directly, no phase-8
dependency).

## Parity Ledger Overlap

`docs/parity_ledger/strategic_cognition.yaml` already carries 5 relevant **P0** entries for
`QuestGenerator`'s current behavior, all `status: verified` or `legacy_verified`, all with
`test_path: null` (pre-existing gap, not caused by this ticket, but must not be made worse):

- `STRAT-154` — `test_generate_quest_returns_quest`
- `STRAT-155` — `test_generate_quest_respects_level` (`legacy_verified`)
- `STRAT-156` — `test_generate_quest_skips_duplicate`
- `STRAT-157` — `test_generate_quest_gold_scales_with_level` (`legacy_verified`)
- `STRAT-158` — `test_generate_explore_quest`

None of these currently point at a real `test_path`. When this ticket lands, per the Authoritative
Mechanics Rule ("if logic changes, update the corresponding doc AND the parity ledger entry ... in
the same session"), these 5 entries should be updated with real `test_path` values pointing at the
(surviving, renamed-if-needed) tests in `tests/unit/quest/test_quest_generation.py`, plus at least
one new `P1` entry added for the new pressure-driven-selection behavior itself (currently no entry
covers it — it's a net-new capability, not a divergence).

`docs/parity_ledger/progression.yaml` carries the quest **reward** parity chain
(`TCK-20260619-E23C-QUEST-REWARDS`) — that's the `QuestOpportunity`/`quest_registry` reward path
(out of scope, confirmed above as a separate system) and needs no changes here.

## Prior Work

- `TCK-20260619-E23A` / `E23C` (referenced via parity ledger and `tests/unit/quest/test_quest_generation.py`
  docstrings) built the `QuestOpportunity` pressure-driven pipeline — architecturally the closest
  prior art for "how do we turn a `WorldEvent`/pressure signal into quest content deterministically,"
  even though it targets a different registry. Its `objective_chain`/`reward_spec` typed-string
  pattern and strict determinism tests (`test_quest_generation_determinism` in the same file, same
  name collision as the `QuestGenerator`-level determinism test — both exist, in different test
  classes/functions, confirmed no actual name clash breaks pytest since both are top-level functions
  in the same file — **this needs a rename check**, see Anti-Drift Hazards) are a good style
  reference for the new weighting logic's own determinism tests.
- `TCK-20260628-E21E-CROSS-REGION-PRESSURE` added `RegionalPressureModel.propagate_cross_region()` —
  demonstrates the established pattern for adding pressure-consuming logic without touching the
  `RegionState`/`ResourceNodeState` schemas, and is a good template for "read existing durable
  fields, don't add new durable state" scoping.
- `docs/plans/idea_pressure_propagation_economy.md` explicitly flags pressure-signal routing as
  higher-risk/needs-care territory in general (cited in user's own memory as "pressure propagation is
  HIGH RISK before E33") — this ticket is a narrow, local consumer (read-only from `QuestGenerator`'s
  perspective) and does not touch the propagation model itself, so it sits outside that risk zone,
  but the plan should say so explicitly to preempt scope creep into touching
  `RegionalPressureModel`/`ScarcityModel` themselves (which the ticket's Out-of-Scope already
  forbids for `ResourceOpportunityProvider`, and should be read as forbidding for the Phase-8 models
  too, by the same logic).

## Risks and Open Questions

- **UQ-1 (from ticket, requires human/planning decision, not resolvable by re-reading source):**
  Probabilistic weighted-random selection vs. deterministic highest-pressure-match. Both are
  achievable without breaking determinism (see below) — this is a *design* choice (variety vs.
  predictability of quest content), not a technical constraint. Recommend **deterministic weighted
  random** (weights derived from pressure profile, drawn via the existing seeded
  `DeterministicRNG.choice`-style mechanism) as the best fit for this codebase because: (a) the
  existing `generate()` already uses `rng.choice` for uniform selection among level-band survivors —
  switching to *weighted* choice via the same seeded RNG is a minimal, idiomatic delta, not a new
  determinism model; (b) pure highest-pressure-match risks quest content going stale/repetitive
  whenever one pressure kind dominates for many consecutive ticks (e.g. a region stuck in high
  trauma always produces the same HUNT template), which cuts against the ticket's own
  NARRATIVE/PROGRESSION-richness motivation. This is a recommendation, not a unilateral resolution —
  flagging for the plan/ticket owner to confirm before implementation, since it does affect
  acceptance-test shape (a "highest match wins" test asserts an exact template; a "weighted random"
  test must assert distributional shift, e.g. over N draws, matching-kind templates are selected
  more often than baseline).
- **Two-systems risk**: since `QuestOpportunity`/`quest_registry` is *also* a pressure-driven quest
  mechanism, a future reader (or SimQ scorer) could reasonably ask "why are there two independent
  pressure-driven quest systems." Recommend the plan/ticket explicitly states these serve different
  layers (Guild-assigned leveled projects vs. world-triggered adventure opportunities) rather than
  silently coexisting — this satisfies the "no important decision left undocumented" Definition of
  Done bar.
- **Empty/degenerate region data**: `tests/unit/world/test_guild_pipeline.py::test_guild_visit_quests`
  constructs `AuthoritativeState(tick=1, seed=42, entities={99: entity})` with **no `regions` dict
  entry at all** and no `entity.navigation.region_id` set. Any new region-lookup logic in
  `GuildAction`/`QuestGenerator` must default gracefully (empty pressure profile → uniform weights,
  matching current behavior) rather than raising `KeyError` — this is the mechanism by which the
  ticket's own AC3 ("existing hero-level gating behavior unchanged for neutral-pressure scenarios")
  gets satisfied structurally, not just asserted.
- **Signature change ripples**: `QuestGenerator.generate()` and `.generate_quests()` are `@staticmethod`
  with positional/keyword params consumed only by `GuildAction.visit()` and
  `tests/unit/quest/test_quest_generation.py`. Adding a new parameter (e.g. `pressure_profile: Optional[...] = None`
  with a safe default) keeps both call sites source-compatible; changing existing parameter order
  would not.

## Anti-Drift Hazards

- Do not edit `src/systems/world_systems/quest_generator.py` believing it's the live path — it is
  dead code (zero call sites for `generate_for_entity`). Confirm via `grep -rn "generate_for_entity"`
  before touching it.
- Do not attempt to make `QuestGenerator` consume `WorldEmergenceResult`/`ScarcityModel`/
  `RegionalPressureModel` directly — those are ephemeral, phase-scoped, and not reachable from
  `GuildAction.visit()`'s call context without material new plumbing that is out of this ticket's
  scope.
- Do not touch `src/domains/world_emergence/services.py::DynamicQuestSeedService` or its `QuestSeed`
  output — it looks related (also produces "quest" content from pressure) but is dead/unconsumed and
  is not part of this ticket's scope.
- Do not touch `state.quest_registry` / `QuestOpportunity` / `QuestOpportunityRewardSystem` — that is
  the separate, already-pressure-driven system; ticket's Out of Scope already forbids touching the
  activation chain in `intelligence.py`, and by the same reasoning the `quest_registry` path should
  not be touched either (confirmed `intelligence.py` has zero quest-specific logic — it only handles
  generic `ProjectState`/`ObjectiveState` lifecycle, so "already fixed for P1-B" refers to
  project-activation preconditions generically, not anything quest-template-specific).
- `test_quest_generation_determinism` exists as **two different functions with the same name** in
  `tests/unit/quest/test_quest_generation.py` — one at the top (line 11, tests `QuestGenerator.generate`)
  and one later (line 106, tests `QuestOpportunityGenerator.from_resource_depleted`). Python allows
  this (later definition shadows earlier one at module scope) but `pytest` will only collect/run the
  **second** definition under that name — the first one is currently masked. This is a pre-existing
  test-file defect, not introduced by this ticket, but implementation must be aware the first
  `test_quest_generation_determinism` (for `QuestGenerator.generate`) **is not actually executed
  today**. Flag for the implementer: either rename on touch (e.g.
  `test_quest_generator_determinism` for the first one) to restore its coverage, or explicitly note
  in the ticket that fixing this pre-existing masking is in-scope since this ticket depends on that
  exact determinism guarantee continuing to hold.
