---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS
date: 2026-09-06
---

# Investigation: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS

## Current Behavior (file:line refs)
All 5 blockers re-confirmed cleared, and all 5 real mechanisms re-verified directly (not inherited
from the ticket text blindly):

- **Idea 60**: `SocialComponent.regional_reputation: Dict[str, float]` (`src/core/models/social.py:48`),
  region-keyed, already included in `AuthoritativeState.to_canonical_dict()`'s hash
  (`src/core/state.py:912`) and `StateFingerprinter` (per M5's own ticket). `frontier_extended`
  world confirmed registered (`config/simulation_quality/corpus_registry.yaml:56-68`, 3 seeds, 200t).
- **Idea 32+43**: `demographic_birth` real event type (`src/simulation_quality/scorers/
  world_dynamics.py:28,155`). `PopulationCohort.migration_threshold: float = 0.7`
  (`src/domains/demographics/cohort.py:53`), consumed by `src/world/camp.py:127` and
  `src/world/reproduction_humanoid.py:70`. Genetic inheritance multiplier confirmed `[0.8, 1.3]`
  (`src/systems/lifecycle_systems/genetics.py:81-120`). `frontier_living_world` confirmed registered.
- **Idea 51/52**: `EXPAND_TERRITORY` is a real `directive_kind` constant
  (`src/engine/faction_constants.py:11`), population-pressure-gated territorial expansion
  (`src/engine/faction_decision.py:118,174-189` — "mean `compute_regional_scarcity()` over
  `fs.territory` > 0.7"). `frontier_marches` confirmed registered.
- **Idea 65**: `StrategicComponent.home_region_id: Optional[str]` (`src/core/strategic.py:414`),
  `DisplacementService.compute_displacement()` (`src/world/displacement.py:21,33`). `crowded_frontier`
  confirmed registered (6 factions per its own `description:` field).
- **Idea 54**: `SocialAppraisalSystem.appraise_contract()`'s clan-trust blend confirmed real
  (`src/systems/social_systems/appraisal.py:55-69`, `CLAN_INFLUENCE_WEIGHT=0.2`). `ClanState`
  schema confirmed (`src/core/state.py:757-773`: `member_entity_ids`, `clan_reputation: float = 1.0`).
  `ClanLifecycleService.find_clan_id_for_entity()` (`clan_lifecycle.py:41-51`) is an O(n_clans)
  reverse lookup by `member_entity_ids` membership.

## Correction — idea 54's real "witnessed betrayal" trigger is party-defection, not contract-betrayal
`CLAN_REPUTATION_MISCONDUCT_DELTA = -0.25` (`clan_lifecycle.py:32`) has exactly 2 write sites:
1. `src/engine/pipeline_phases/groups.py:163-169` — inside `GroupPhase.resolve()`'s real,
   live, per-tick party-defection trigger (`PartyLifecycleService.check_defection()`, fires when
   `len(group.grievance_log) >= effective_defection_threshold(group)`, baseline threshold 3).
   **This is the real, live-reachable path through a genuine `Kernel.tick_once()` run.**
2. `src/systems/social_systems/contracts.py:280-291` — explicitly self-documented as **NOT wired to
   any live pipeline phase**: "`process_active_contracts()`, the only production caller of
   `resolve_contract_outcome()`, never passes `betrayal=True`/`betrayer_id` ... reachable only from
   direct unit tests until a future ticket wires a real betrayal trigger." This is the exact,
   already-disclosed M5 pipeline-reachability gap (`TCK-20260904-CLAN-REPUTATION-ASSOCIATION`'s own
   Completion Summary).

The ticket's own scope text ("one member of Clan A commits a witnessed betrayal") most naturally
reads as the contract-betrayal path, but that path cannot be exercised through a real `Kernel.tick_once()`
run at all — only the party-defection path can. Corrected the corpus proof to exercise the real,
live path (defection) instead of fabricating a Kernel-driven trigger for a path that is provably
dead in production. `resolve_contract_outcome`'s own dead path is unaffected and untouched by this
ticket (already disclosed elsewhere; not this ticket's job to fix).

## No existing corpus world has real `ClanState` content
Confirmed via grep: zero `data/worlds/*/world.yaml` files contain `clans:`/`clan_id`/`ClanState`
content. Several worlds (`crowded_frontier`, `frontier_marches`) reference an "orc_clan" FACTION by
name — a naming coincidence, not the `ClanState` game mechanic. `ClanState` is exercised today only
via direct hand-built unit/integration tests (`tests/unit/social/test_clan_appraisal.py`,
`test_contract_lifecycle.py`) — no registered corpus world has ever carried real Clan content.

Per this ticket's own Assumptions section ("confirm no existing world already fits this shape before
authoring one") — none does. Building a full new registered corpus world (world.yaml authoring,
profile registration, corpus_registry.yaml entry, compilation validation) is a materially larger
undertaking than the other 4 sub-tests in this same ticket (each reuses an existing world) and is not
warranted for one sub-item of an otherwise same-sized 5-part ticket. Following this same M9 batch's
own already-established precedent (tickets 1/2/3, all used a hand-built `AuthoritativeState` +
`Kernel.tick_once()` deterministic proof instead of forcing corpus-world/emergent-play evidence when
impractical or when no real corpus world had the needed shape) — idea 54's proof uses a Unit-tier
SimQ corpus test (`corpus_tier_taxonomy.md`'s Unit tier explicitly allows synthetic content) with a
hand-seeded `AuthoritativeState` carrying 2 real `ClanState` clans (4 members each), driven through
real `Kernel.tick_once()` calls to exercise the real defection->clan_reputation_delta pipeline path,
then a direct `appraise_contract()` pure-function call for the stranger-trust assertion.

## Docs Requiring Update
None. All 5 sub-tests exercise already-shipped, already-documented mechanisms with no behavior
change — test-only ticket.

## Parity Ledger Overlap
None affected — no `src/` production code changes, `behavior_changed=false`. SOC-268 (idea 54's own
parity entry) already documents the `CLAN_INFLUENCE_WEIGHT`/pipeline-reachability facts this ticket
re-confirms; unaffected by this ticket.

## Prior Work
- `tests/unit/social/test_clan_appraisal.py`, `test_contract_lifecycle.py` — existing Clan/contract
  pure-function test precedent (structural template for idea 54's `appraise_contract()` assertion).
- `tests/simulation_quality/test_age_tier_transitions_corpus.py` (M9 ticket 2) — the real, established
  hand-built-`AuthoritativeState`-through-`Kernel.tick_once()` Unit-tier corpus-proof template this
  ticket's own idea-54 sub-test follows.

## Risks and Open Questions
None outstanding.

## Anti-Drift Hazards
- Do not build a full new registered corpus world for idea 54 — a hand-scripted Unit-tier proof is
  the scope-appropriate, precedented choice.
- Do not exercise the disclosed-dead `resolve_contract_outcome(betrayal=True)` path as if it were
  live — use the real, live party-defection trigger instead.
- Do not duplicate `test_clan_appraisal.py`'s own existing pure-function coverage — this ticket's
  value-add is the SimQ-corpus-framed, end-to-end-through-a-real-Kernel-tick angle.
