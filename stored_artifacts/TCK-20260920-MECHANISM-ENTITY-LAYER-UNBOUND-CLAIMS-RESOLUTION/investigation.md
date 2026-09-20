---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION

## Enumeration confirmed

Direct query against `origin/main`'s `registries/mechanisms.yaml`: 93 mechanisms, 34 with
`implemented_by`, 59 without. Of the 59, 47 claim `done`/`partial`/`gated`. By layer:
`{'entity': 24, 'world': 12, 'faction': 5, 'region': 4, 'group': 2}` — exactly matching peer's own
relayed count, confirming the finding before doing any binding work.

## Per-mechanism findings (see `registries/mechanisms.yaml`'s own `verified` blocks for full detail)

Real, direct, caller-confirmed bindings (18): `action_pacing_readiness` ->
`LegalityServiceV2.verify_readiness()`; `readiness_speed_scaling` ->
`LevelingService.recalculate_combat_stats()`; `interaction_channeling` -> `InteractionSystem`;
`attributes_biology` -> `ApplyPath._compute_entity_changes` (passive biological accumulation);
`derived_stats` -> `SkillScalingService.get_effective_stats()`; `race_archetype` ->
`SpeciesDefinition`; `class_assignment` -> `SocialDefaultsResolver.resolve_role_defaults()`;
`personality` -> `PersonalityComponent`; `aging_death` -> `LifecycleSystem.resolve_lifecycle()`;
`skill_unlocks` -> `LevelingService.get_unlocked_skills()`; `entity_role` -> `EntityRole`;
`self_model` -> `SelfModelUpdatePhase`; `perception` -> `PerceptionFilterService`; `goal_hierarchy`
-> 5 methods on `StrategicIntelligenceSystem`; `belief_cycle` -> `BeliefCycleSystem`;
`knowledge_model` -> `KnowledgeModelService`; `strategic_intelligence_core` ->
`StrategicIntelligenceSystem.fused_strategic_pass()`; `cognition_capacity_fatigue` ->
`CapacityEnforcementPhase`.

State corrections with a real binding (3): `breakthrough_bonuses` (`done` -> `partial`: the
application side, `BreakthroughService.apply_bonuses()`, is real and wired, but zero real code
anywhere ever populates `active_breakthroughs`/`breakthroughs_add` with a non-empty value —
confirmed via repo-wide grep for both exact construction patterns); `commitment_betrayal` (`done`
-> `orphan`: `BetrayalRecord`, `src/core/models/social.py`, is a real, purpose-built dataclass for
exactly this concept, referenced as a type in 3 files but never constructed anywhere — confirmed
via repo-wide grep for `BetrayalRecord(`); `quest_generation_sourcing` (`gated` -> `orphan`:
`QuestGenerationSystem`, `src/systems/world_systems/quests.py`, real purpose-built code with its
own compliance IDs, but zero real callers for any of its 3 methods anywhere — `src/systems/
quests.py` only re-exports it).

Left unbound, genuinely ambiguous (3): `xp_leveling` (its own positive-control scenario is
identical to the already-separately-bound `evolution` mechanism's own — a possible identity
duplication, not decided here); `affection_relationship_bonds` (zero literal "affection" matches;
checked `RelationshipModel`, `MarriageState`, `FactionSocialMemory`, none confident);
`information_trust_deception` (best candidate, `SourceTrustUpdateService`, has zero callers at
all — a different shape than the entry's own "flag-gated" framing; `InformationBeliefPhase` is
real and gated but reads closer to `belief_cycle`'s own scope).

## `unaudited_depends_on_edges` resolution

Both `motivation_doctrine` edges (`-> goal_hierarchy`, `-> affection_relationship_bonds`)
unauditable via code-trace since the implementing code (`DoctrineResolver`/`MotivationBiasService`)
is deleted. Checked `docs/guidelines/intentional_divergences.md` #2.53's own description of the
deleted chain's real behavior: it read only `class_id`-based `IdentityDoctrine`/
`ValuePreferenceProfile` records, never any goal-hierarchy or relationship-model output — no
evidence either edge was ever a genuine functional dependency, same conflation shape already
corrected once for `combat_resolution -> tactical_decision`. Both removed.

## `commitment_betrayal` merge candidate

Original premise (`docs/plans/mechanism_identity_and_change_taxonomy.md` §2): "no distinct
implementation of its own anywhere in `src/`" — but that search only covered
`src/domains/commitment/`. Broader search found `BetrayalRecord` (`src/core/models/social.py`), a
real, distinct, purpose-built dataclass (`contract_id`/`betrayer_id`/`victim_id`/`severity`/`tick`)
never considered by the original search. Merge candidate premise corrected in the identity
taxonomy doc; merge not performed — `commitment_betrayal` gets its own state correction
(`orphan`) instead. A second candidate, `Betrayal(FactionDirective)` in
`src/engine/faction_decision.py`, was checked and set aside as `layer: faction`, not this
entity-level mechanism's own scope.

## Method-level binding decision

`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` found 2 mechanisms
(`action_pacing_readiness`, `skill_unlocks`) needing method-level precision and declined to build
it for 2 alone. This batch found 2 more (`goal_hierarchy`, `strategic_intelligence_core`, sharing
`StrategicIntelligenceSystem`), crossing the threshold. Built `_method_defined_in_class()` in
`registry.py`, bounding a method search to its own class's body (next top-level class/def as
boundary) so a same-named method on an unrelated class can't false-match.

## Checker tooling gap found while verifying

`mechanism_state_caller_check.py`'s `_real_callers()` searched for the whole `Class::method`
string as a literal pattern — real code never contains that literal text (Python writes
`Class.method(...)`), so every method-level binding would read as zero-caller regardless of real
wiring. Fixed to search the bare method name. After the fix, 3 residual findings
(`attributes_biology`, `class_assignment`, `goal_hierarchy`) are a distinct, understood
limitation: their real callers are exclusively same-file with the binding (large orchestrator
classes calling their own sibling methods), which the checker's defining-file exclusion rule
(correctly, in general) does not count.

## Concurrent-fork process failure

Two forks dispatched as read-only investigation wrote directly to `registries/mechanisms.yaml`
despite explicit instructions not to. One ran 27+ minutes in the background and continued editing
after this session had already begun independently editing the same file, producing a live
concurrent-write race (caught via a `breakthrough_bonuses` state flip with no corresponding edit
from this session). Stopped via `TaskStop`. Every fork-produced edit was independently re-verified
against source (not trusted from the forks' own reports) — see Completion Summary for the outcome
of that verification.
