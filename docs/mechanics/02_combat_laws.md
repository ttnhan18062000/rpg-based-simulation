---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-09-01
---

# Chapter 2: Combat Laws

This chapter details the mathematical and logical sequence of combat resolution. The simulation follows a deterministic, non-random resolution for all primary attacks.

---

## 1. The Damage Formula
The simulation uses a **Fractional Armor Mitigation** model. This ensures that every point of Attack matters, and Defense provides diminishing returns rather than a flat reduction.

```python
# Raw Core Formula
Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))
```

*   **Minimum Damage**: Every successful hit deals at least **1 damage**, regardless of Defense.
*   **Rounding**: Damage is always cast to an integer (`int`) after calculations.

---

## 2. Tactical Modifiers
Before damage is calculated, the base `Atk` and `Def` values are modified by the tactical context.

| Modifier | Impact | Condition |
| :--- | :--- | :--- |
| **High Ground** | `+0.20` Atk | Attacker is at a higher elevation than the target. |
| **Flanking** | `+0.15` Atk | Attacker is behind the target's current focus. |
| **Surrounded** | `+0.25` Atk | Target is surrounded by multiple enemies. |
| **Cover** | `+0.30` Def | Target is behind environmental cover relative to the attacker. |
| **Shatter** | `x1.50` Atk | Target is currently in the `Frozen` state. |
| **Exhaustion** | `x0.80` Atk | Attacker's `Sleep Debt` is greater than 80. |
| **Bond Synergy** | `+0.10` Atk | Adjacent ally has >0.5 Familiarity with the attacker. |

---

## 3. Durability & Decay
Equipment degrades with every combat engagement. Broken equipment (0 durability) provides **zero** stat bonuses.

*   **Attacker**: `-1.0` durability to the `MAIN_HAND` item.
*   **Defender**: `-0.5` durability to `HEAD`, `TORSO`, and `LEGS` items.

---

## 4. Victory & Rewards
When an entity's HP reaches 0, the resolution system determines the final outcome based on the target's role and lifecycle.

### Kill Rewards
Rewards are granted to the attacker (or their group) based on the target's level (`LVL`).

| Target Role | XP Reward | Gold Reward |
| :--- | :--- | :--- |
| **Monster** | `LVL * 10` | `LVL * 5` |
| **Hero** | `LVL * 20` | `LVL * 50` |

### Death (No Role Is Exempt)
No role is exempt from death. When combat takes a defender to 0 HP the outcome is `KILL` (a lethal attack) or terminal `DEFEAT` (a non-lethal attack, e.g. an opportunity attack); both are recorded by the lifecycle phase as real, final deaths (`death_reason` `COMBAT` / `DEFEAT`, `is_permadeath` set). There is no rebirth, no generation counter and no hero-only exemption: the former "Hero's Journey" rebirth law (generations 1-3 reborn, generation 4 permadeath) was an undeclared resurrection and was retired (`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`, `intentional_divergences.md` §2.63). Continuity after a death is carried by new identities through reproduction, heirs and heirlooms, not by the same entity returning.

---

## 5. Wound Infliction
A **Wound** is inflicted on a surviving defender when a single hit deals damage **strictly greater than 25% of the defender's Max HP**.
```python
is_wound = damage > (defender.max_hp * 0.25) and defender.alive
```
- Wound severity: `severity = min(1.0, damage / defender.max_hp)` (proportional, capped at 1.0).
- Wound type: derived from severity, not attacker role — `CRUSH` if `severity >= 0.8`, `SLASH` if
  `severity >= 0.6`, otherwise `PIERCE` (`WoundService.create_wound`, `src/engine/rpg_depth.py`).
- Wound penalty: severity-scaled, not a flat value — `atk_penalty = int(severity * 3)`,
  `def_penalty = int(severity * 2)`, `speed_penalty = int(severity * 2)`,
  `max_hp_penalty = int(severity * 10)` (applied as long as the wound is active). `atk_penalty`,
  `def_penalty`, and `max_hp_penalty` are subtracted from effective ATK/DEF/Max HP by
  `SkillScalingService.get_effective_stats()`; `speed_penalty` is computed and stored on the wound
  but is **not yet read** by `get_effective_stats()` — no move-cost/speed stat is currently reduced
  by wounds (tracked as a separate follow-up, not a bug in this formula).
- Wound Permanence: Wounds are permanent. No code path currently heals a wound — verified: the
  only production constructor of `WoundUpdate` is `CombatResolutionSystem._get_wound_infliction()`
  (`src/engine/combat.py:605-617`), which always builds `WoundUpdate(wounds_add=[wound])` and never
  populates `wounds_heal` or `scars_add`; `WoundUpdate.wounds_heal`/`scars_add` both default to `[]`
  (`src/core/updates.py:604-609`). A wound's penalty applies for as long as the wound exists on the
  entity. Permanent Scars — a lesser, persistent penalty replacing a healed wound — remain a
  data-model concept only: `scars_add` has zero production producers, and no mechanic currently
  creates a `ScarState` from a healed wound (this remains a settled, open follow-up, not
  implemented by any landed ticket).
- Tactical consequence (`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`): `TacticalDecisionSystem`
  (`src/engine/tactical.py`) reads the structured wound/scar penalty data — never re-deriving it —
  as an additional, independent decision-making signal alongside the existing raw `hp_percent`/
  `hp_ratio` checks:
  - Cover-seeking/retreat gate (`tactical.py:483-494`): an entity whose active wounds sum to
    `WoundService.get_wound_stat_penalties(...)` `>= 9.0` (equivalent to a single wound at
    `severity >= 0.6`) enters the cover-seeking/retreat branch independently of `hp_percent`.
  - The same gate's `hp_percent` threshold (`tactical.py:483-494`) is raised by `0.01` per
    aggregate scar-penalty point (`WoundService.get_scar_stat_penalties(...)` summed), capped at
    `+0.10` — a scarred entity seeks cover/retreats at a durably higher HP than an otherwise
    identical unscarred entity at the same `hp_ratio`.
  - PROTECTOR guard-wounded-ally branch (`tactical.py:542-582`): an ally (or the group leader)
    with combined wound+scar distress `>= 5.0` (equivalent to a single wound at `severity >= 0.4`)
    becomes an additional guard-priority qualifier, alongside the existing `hp_ratio < 0.8`/`< 0.7`
    checks.

---

## 6. Area of Effect (AoE) Logic
For skills with a `splash_radius`:
1.  **Primary Target**: Receives 100% of the calculated skill damage.
2.  **Splash Victims**: All other entities in the radius receive **50%** of the attacker's base ATK as damage.
3.  **Line of Sight**: Splash damage is blocked by solid walls/terrain.
4.  **Friendly Fire**: A splash victim is hit only if the content catalog calls it hostile to the attacker (`content_semantics.faction.are_entities_hostile`, real distance, `combat_engaged=True`) -- the same test the primary-target Friendly-Fire Law below uses. It is not decided by the four-value legacy `Faction` enum, which collapses content factions (`goblin_warband` and `orc_clan` share `MONSTER_HORDE`): same-bucket enemies are splashed, different-bucket allies and neutrals are not (`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`).

---

## 7. Action Legality & the Readiness Gate
Every non-opportunity `ATTACK` requires the attacker's `readiness` to be at **exactly 100.0 or
higher** (`LegalityServiceV2.verify_attack_legality`). Opportunity attacks (triggered by
disengaging while adjacent to a hostile) bypass this specific check.

*   **Consumption**: A successful attack resets readiness by **-100.0** (a full reset). Movement
    does **not** cost readiness (`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`) — it
    costs `stamina` instead (`StaminaComponent.MOVE_COST`, a flat per-move cost, separately
    regenerated by `StaminaService.tick_regen()`). Readiness is a pure attack-eligibility/cooldown
    gate, matching its own documented contract; movement previously also drained it, meaning any
    entity that had to travel to reach a hostile arrived readiness-depleted even with passive
    regeneration active — real corpus re-verification showed this capped the real attack-legal
    rate at ~1.3% even after the fixes below. Removing the double-cost raised it to a real,
    measured 28.5-36.6% on the same live worlds (`dungeon_crawl`/`urban_political`).
*   **Passive Regeneration**: Every tick, an entity below 100.0 readiness regenerates by its own
    `readiness_speed` stat (`CombatComponent.readiness_speed`), capped at 100.0. This closes a gap
    between the documented kernel contract (`docs/engine/contracts/minimal_kernel.md` §5,
    "Readiness Accumulation") and the source: prior to
    `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`, no passive regeneration
    existed anywhere in the pipeline — readiness only ever decreased, and the only restoration
    path was a narrow town-specific REST action (+10.0, `src/engine/town_resolution.py`).
    `readiness_speed` is derived from `agility` in `LevelingService.recalculate_combat_stats()`:
    `readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)`. **10.0/tick is the value at
    reference/baseline agility (`5`), not a universal flat default** — higher agility regenerates
    readiness faster, lower agility slower, floored at 1.0/tick to prevent the gate from ever
    locking permanently (`TCK-20260831-READINESS-SPEED-FORMULA`, `COMB-318`).
*   **Friendly-Fire Law (permission is symmetric, CONFLICT-03)**: whether one party may attack another is a fact about the
    pair and holds in both directions (`LegalityServiceV2._attack_permitted`, `src/engine/legality.py`); an attack the pair does
    not permit is illegal (`ReasonCode.FRIENDLY_FIRE_ILLEGAL`). Permission follows *declared* hostility and missing data declares
    nothing. A faction *declares* data when the catalog has a perspective for it or a relationship row toward the other
    (`_declares`). (1) Both sides declare: legal both ways if either side's `FactionSemanticsService.is_hostile_compat` says
    hostile. (2) Exactly one side declares: that side's verdict decides both directions. (3) Neither declares: the legacy fallback,
    where only a shared legacy faction is illegal. A "contextual threat" (`wild_beast_pack`) differs only in when it *chooses* to
    fight, never in whether it may (decision layer, parked contextual engagement). Hostility for
    `contextual_intruder_groups`-classified relationships (real content: `data/content/social/perspectives.yaml`) resolves from
    real combat-engagement state, not a hardcoded assumption of non-intrusion. See DEV-016.
*   **Species-hostility escalation preserves the law**: `is_hostile_compat` resolves through
    `RelationProjectionService.project_relation()`, whose species-hostility escalation step
    (`src/content_semantics/relation.py`, real content: `data/content/social/species_relations.yaml`)
    can upgrade a projected label toward `enemy`/`threat` using `axes.hostility` for the
    attacker/target species pair, but only ever *upgrades* — it is gated off entirely whenever
    `source_faction_id == target_faction_id`, so a species entry can never make a same-faction
    attack legal, and it is fail-closed on a fixed label ladder
    (`neutral`/`threat`/`intruder`/`enemy`), so an off-ladder perspective-declared label such as
    `ally` or `protected` can never be escalated into hostility. This is what keeps the
    Friendly-Fire Law intact once species-level hostility feeds attack legality
    (`LegalityServiceV2.verify_attack_legality`, `src/engine/legality.py:243`).
*   **Range & LoS**: Attacks additionally require the target within `effective_range` (melee: must
    be exactly adjacent) and unobstructed line of sight.
*   **Unrecoverable-Failure Task Reset**: An `ATTACK` task that fails with
    `ReasonCode.TARGET_INCAPACITATED` (the target died or otherwise became inactive since the
    attack was chosen) resets the entity's task to idle (`ActionRoutingPhase.route()`,
    `src/engine/pipeline_phases/actions.py`), mirroring the file's own established survival-action
    (`EAT`/`REST`/`SLEEP`) success-reset pattern. Without this, the stale `target_id` kept the
    task classified `ENTITY_ACT` with a non-empty payload — which bypasses the scheduler's own
    tactical-brain-cadence gate entirely (that gate only applies when a task's payload is empty)
    — so the same failing attack was re-dispatched every tick readiness recovered from the real
    illegal-target penalty (`-50.0`, ~5 ticks to regen), confirmed via live corpus trace to
    repeat for 180+ real ticks against the same dead target with no natural end
    (`TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`). `OUT_OF_RANGE` is reset the same way
    (`TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`): it was
    once left in place on the reasoning that range may close via a fresh pursuit decision, but the
    held payload is non-empty so no fresh decision ever came, and a melee pair that stayed
    diagonal (Manhattan 2: melee adjacency is orthogonal, world rule MOV-07) re-swung 267 times in
    one run. Clearing it returns the entity to the brain, whose tactical pass pursues whenever an
    attack is not legal. `INSUFFICIENT_READINESS` is deliberately **not** reset: readiness regens
    and the same swing can then land.
    The same law ends a held gathering task: an `INTERACT` on a resource node that is missing or has no
    charges left is reset the same way (see Bible 03 section 3, `TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED`).
*   **Whole-Tile Reach Distance**: positions are whole tiles (world rule MOV-07, Decision 25), and
    every reach check measures one distance: the Manhattan distance between the tiles the two
    positions stand on (`LegalityServiceV2.get_manhattan_dist`, each coordinate read as `int(pos)`,
    as occupancy, terrain and building lookups read it). Attack legality (`verify_attack_legality`)
    and pursuit completion (`MovementCandidateSelector._target_in_attack_reach`) both call it, so
    a pursuer stops exactly when the swing is legal. The long-distance flow-field step toward the
    town centre (`NavigationSystem.get_next_step`) is a one-tile step along the flow vector's
    dominant axis (a tie takes the y axis, as the local step does); it used to add a unit vector
    and leave the entity between tiles, where the truncated legality distance and the float
    pursuit distance disagreed (`TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT`).
*   **An Action Task Does Not Walk**: movement runs on `navigation.target`, whatever the task kind, so an entity that holds an
    action task (`ENTITY_ACT` with a payload: ATTACK, SKILL, INTERACT, HOLD) must not keep walking on a target an earlier
    decision left behind. The ATTACK and SKILL emissions clear the navigation target (`tactical.py`); an entity holding an action
    task is neither offered a move (`MovementCandidateSelector.select`) nor moved (`MovementPhase.route_movement_intent`) unless
    that tick sets a target of its own (`MovementCandidateSelector.holds_action_task`); and live retargeting onto the entity named
    in `payload["target_id"]` applies only to entity-tracking moves (pursuit, intercept, bracketing, kiting, guard), never to an
    action holder (`resolve_live_tracking_target`). Before this an adjacent ATTACK holder was live-retargeted onto its target's
    occupied tile, the refused step fell to the sidestep ladder (`MovementSystem._find_sidestep`) and the attacker stepped off
    adjacency and took an opportunity attack (COMB-009/272). The cost: an attacker whose target steps away no longer closes the gap
    through live tracking; it closes after OUT_OF_RANGE returns it to the brain, which for an idle entity runs once per
    `strategic_intelligence` cadence (10 in the live NORMAL policy, `policy.py:92`).
*   **Withheld-Action Task Reset**: The action router (`ActionRouter.execute_action`,
    `src/engine/domain/action_router.py`) reports `ReasonCode.ACTION_WITHHELD_BY_POSTURE` when its
    combat-posture gate withholds an `ATTACK`/`SKILL` (the attacker's recorded
    `last_combat_posture` toward that exact target is not `engage`/`probe`/`skirmish`/
    `vengeance_engage`; an absent posture, or one recorded for another target, never withholds),
    and `ReasonCode.UNSUPPORTED_ACTION` for an action no handler recognises. Both are
    unrecoverable for the task that carried them, so `ActionRoutingPhase.route()` clears the
    task to idle exactly as it does for `TARGET_INCAPACITATED`, whatever the action kind, and the
    brain re-decides at its next cadence. Previously the gate returned a bare no-op with no
    failure: the task was annotated `outcome: SUCCESS`, kept, and re-dispatched every tick until
    the target died (one entity held ~851 ticks, `frontier_living_world`, seed 42). The task
    annotation also no longer carries the previous tick's `reason`: a `reason` that sits beside an
    `outcome` is an earlier annotation and is dropped before the new one is written
    (`TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS`).
    The gate's policy is unchanged; only its return shape and the resulting annotation.
