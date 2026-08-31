---
name: combat-mechanics
description: 'Deterministic combat resolution (damage formula, tactical modifiers) and CombatPosture pre-combat assessment in src/domains/combat_engagement/.'
---

# Combat Mechanics (This Repo)

Sourced from `docs/mechanics/02_combat_laws.md` (Mechanics Bible ch.2, P0 authoritative) and
`docs/simulation/domains/combat_engagement_contract.md`. Covers two distinct layers: the
**pre-combat assessment** (subjective, non-authoritative) and **deterministic resolution**
(authoritative, non-random) — do not conflate them.

## Pre-Combat Assessment vs. Authoritative Resolution — Read This First

`src/domains/combat_engagement/` is explicitly **NOT authoritative** — it reads state and returns
a typed decision record (`CombatEngagementDecisionResult`), it does not resolve combat outcomes.
That's the combat system's job, applied later by the authoritative pipeline. This is the single
easiest thing to get backwards when working in this domain: `CombatEngagementDecisionService`
decides *whether/how an actor wants to engage*, not *what damage gets dealt*.

## `CombatPosture` and the Sub-Service Pipeline

10 posture values, escalating engagement level: `IGNORE`, `WATCH`, `AVOID`, `PROBE`, `THREATEN`,
`ENGAGE`, `SKIRMISH`, `CALL_HELP`, `RETREAT`, `PANIC_FLEE`.

Entry point: `CombatEngagementDecisionService.evaluate(actor, target, state)` — **stateless and
deterministic**: same inputs always produce the same output. Orchestrates 4 sub-services in order:

1. `OpponentPerceptionService` (`perception.py`) — builds `OpponentModel` from the target's
   observable properties.
2. `SelfCombatEstimateService` (`self_estimate.py`) — estimates the actor's own combat capability.
3. `EngagementRiskEvaluator` (`risk_evaluator.py`) — computes a risk ratio from `OpponentModel` vs
   self-estimate.
4. `CombatPostureSelector` (`selector.py`) — selects `CombatPosture` from risk ratio + actor
   personality.

None of these mutate state. `reassessment.py` re-evaluates posture mid-encounter under the same
stateless contract (health drops, reinforcements arrive). `learning.py` produces updated
reputation/learning records **passed to the pipeline for application**, never applied directly.

**Domain isolation constraints**: must not import from other domain packages; must not call the
Kernel or other pipeline phases directly.

## The Deterministic Damage Formula

Source: ch.2 §1. **Fractional Armor Mitigation** — every point of Attack matters, Defense gives
diminishing returns rather than a flat reduction:

```python
Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))
```

Minimum damage on any successful hit: **1**, regardless of Defense. Always cast to `int` after
calculation.

## Tactical Modifiers (§2, exact values)

Applied to base `Atk`/`Def` before damage calculation:

| Modifier | Impact | Condition |
|---|---|---|
| High Ground | `+0.20` Atk | Attacker at higher elevation than target |
| Flanking | `+0.15` Atk | Attacker behind target's current focus |
| Surrounded | `+0.25` Atk | Target surrounded by multiple enemies |
| Cover | `+0.30` Def | Target behind environmental cover relative to attacker |
| Shatter | `x1.50` Atk | Target is currently `Frozen` |
| Exhaustion | `x0.80` Atk | Attacker's Sleep Debt > 80 |
| Bond Synergy | `+0.10` Atk | Adjacent ally has >0.5 Familiarity with attacker |

## Durability, Wounds, Kill Rewards

Source: §3-5.
- **Durability decay** (per engagement): Attacker `-1.0` to `MAIN_HAND`; Defender `-0.5` to
  `HEAD`, `TORSO`, `LEGS`. Broken (0 durability) equipment provides zero stat bonuses.
- **Kill rewards**: Monster target → `LVL*10` XP / `LVL*5` gold. Hero target → `LVL*20` XP /
  `LVL*50` gold. **Hero's Journey**: Generation 1-3 → rebirth (Generation increments) on defeat;
  Generation 4 → permadeath, permanently removed.
- **Wound infliction**: `is_wound = damage > (defender.max_hp * 0.25) and defender.alive`. Type
  `SLASH` for Hero attackers, `CRUSH` otherwise. Severity `damage / defender.max_hp`. Penalty −5
  ATK/−5 DEF while active. On heal: 30% chance of a permanent scar
  (`scar_penalty = wound_penalty * 0.3`).

## Area of Effect (AoE)

Source: §6. Primary target: 100% of calculated skill damage. Splash victims: 50% of the
attacker's base ATK. Splash is blocked by solid walls/terrain (line of sight). Faction allies take
no splash damage from their own teammates.

## The Authoritative Pipeline Phases — and the Sliding State Rule

Source: `docs/engine/authoritative_pipeline.md`. Combat logic executes as specific named phases
inside the 39-phase `AuthoritativeApplyPipeline`, in this fixed order:

| Phase # | Name | What it does | Compliance ID |
|---|---|---|---|
| 12 | `action_routing` | Routes combat/skill/tactical-ability intents through `SimulationDomainLogic` | `TOWN-149`, `COMB-001` |
| 13 | `position_swaps` | Resolves adjacent position exchange contracts and mutual passing | `COMB-028` |
| 15 | `combat_engagement` | Enhanced RPG full combat engagement sequences | flag `ENABLE_COMBAT_ENGAGEMENT` |
| 31 | `near_death_hardening` | Finalizes near-death state and damage-mitigation logic | `COMB-121` |

**Sliding State causal rule** (lives on phase 12, `action_routing`, `src/engine/pipeline_phases/actions.py`):
if Actor A kills Target T in this tick, Actor B — processed **later in the same tick's queue** —
sees T as already dead and **cannot receive a kill reward** for it. This is real, intentional,
order-dependent behavior, not a bug — a skill or debugging session that assumes all actors see a
consistent pre-tick snapshot will draw wrong conclusions about "why didn't B get credit for the
kill."

## Debugging — Real Test Paths

`tests/unit/combat/test_direct_combat_outcomes.py` (damage formula, core resolution),
`test_combat_rewards.py` (kill rewards, Hero's Journey), `test_aoe_splash.py` (AoE logic),
`test_engagement_behavior.py` (pre-combat assessment / `CombatPosture`), `test_combat_matrix.py`,
`test_anti_stalemate.py`.
