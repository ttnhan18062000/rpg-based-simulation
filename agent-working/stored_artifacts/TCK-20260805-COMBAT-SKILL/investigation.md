---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260805-COMBAT-SKILL
artifact_type: investigation
tags: [skills, combat]
---

# Investigation — TCK-20260805-COMBAT-SKILL

## Real Content Grounded

### `docs/mechanics/02_combat_laws.md` (Mechanics Bible ch.2, P0 authoritative)
- **Damage formula** (§1): `Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))` — Fractional Armor
  Mitigation, minimum 1 damage, always cast to `int`.
- **Tactical modifiers** (§2, exact values): High Ground `+0.20` Atk, Flanking `+0.15` Atk,
  Surrounded `+0.25` Atk, Cover `+0.30` Def, Shatter `x1.50` Atk (vs Frozen target), Exhaustion
  `x0.80` Atk (Sleep Debt > 80), Bond Synergy `+0.10` Atk (adjacent ally Familiarity > 0.5).
- **Durability decay** (§3): Attacker `-1.0` `MAIN_HAND`; Defender `-0.5` `HEAD`/`TORSO`/`LEGS`.
- **Kill rewards** (§4): Monster `LVL*10` XP / `LVL*5` gold; Hero `LVL*20` XP / `LVL*50` gold.
  Hero's Journey: Generation 1-3 → rebirth, Generation 4 → permadeath.
- **Wound infliction** (§5): `is_wound = damage > (defender.max_hp * 0.25) and defender.alive`.
  Type SLASH (Hero attacker) / CRUSH (otherwise). Penalty −5 ATK/−5 DEF while active. 30% chance
  to leave a scar on heal (`scar_penalty = wound_penalty * 0.3`).
- **AoE** (§6): primary target 100% skill damage, splash victims 50% of attacker's base ATK, LoS
  blocks splash, no friendly-fire splash.

### `docs/simulation/domains/combat_engagement_contract.md`
- **NOT authoritative** — reads state, returns a typed decision record. Produces a *subjective
  pre-combat assessment* (does not resolve combat outcomes — that's the combat system's job).
- **10 `CombatPosture` values**, escalating: `IGNORE`, `WATCH`, `AVOID`, `PROBE`, `THREATEN`,
  `ENGAGE`, `SKIRMISH`, `CALL_HELP`, `RETREAT`, `PANIC_FLEE`.
- **Entry point**: `CombatEngagementDecisionService.evaluate(actor, target, state)` — stateless,
  deterministic.
- **4-stage sub-service pipeline**: `OpponentPerceptionService` → `SelfCombatEstimateService` →
  `EngagementRiskEvaluator` → `CombatPostureSelector`. Confirmed real files via `ls
  src/domains/combat_engagement/`: `perception.py`, `self_estimate.py`, `risk_evaluator.py`,
  `selector.py` (matching the 4 sub-services 1:1), plus `resolver.py`, `reassessment.py`,
  `learning.py`, `schema.py`, `service.py`.
- **Constraints**: must not import from other domain packages; must not call the Kernel or other
  pipeline phases directly.

### `docs/engine/authoritative_pipeline.md` — real phase grounding
- Phase 10 `action_routing` (`TOWN-149`, `COMB-001`) — **the Sliding State causal rule lives
  here**: "If Actor A kills Target T in this tick, Actor B (later in the queue) will see T as dead
  and cannot receive a kill reward." A skill omitting this would give actively wrong sequencing
  guidance, per the ticket's own explicit warning.
- Phase 11 `position_swaps` (`COMB-028`).
- Phase 13 `combat_engagement` (flag `ENABLE_COMBAT_ENGAGEMENT`).
- Phase 26 `near_death_hardening` (`COMB-121`).

### Real test paths confirmed via `find`
`tests/unit/combat/test_direct_combat_outcomes.py`, `test_combat_rewards.py`,
`test_aoe_splash.py`, `test_engagement_behavior.py`, `test_combat_matrix.py`,
`test_anti_stalemate.py`.

## Scope Decision
One skill, `combat-mechanics`, covering both the deterministic resolution law (damage/tactical
modifiers/durability/wounds/AoE) and the pre-combat assessment domain (`CombatPosture`,
sub-service pipeline) — the ticket's own Scope explicitly requires both, and they're tightly
coupled (assessment feeds resolution via the pipeline).

## Unresolved Questions
None — all cited content verified against 3 real docs and real file/phase names.
