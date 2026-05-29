# Source Inventory — Implemented Entity Actions and Action-Related Aspects

## Inventory verdict

The engine already has **many action mechanics**, but they are **not cleanly unified**.

There are three different action surfaces:

| Surface                    | Meaning                                                             | Status                                                                      |
| -------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Runtime routed actions** | Payload actions handled by `ActionRouter`                           | Real runtime path                                                           |
| **Domain/system actions**  | Movement, interaction, blacksmith/shop/guild systems                | Real mechanics, but not always routed as direct actions                     |
| **Wrapper/test actions**   | `BlacksmithAction`, `ShopAction`, `GuildAction`, `HomeAction`, etc. | Useful, but do not assume they are all part of the main runtime action loop |
| **Phase 3 Subjective Routing**| Route candidate evaluation, imperfect personality-biased scoring, strategic mapping, and resolution to first intent | Fully implemented in `src/domains/adventure/` with 33 TDD/perf tests passing |
| **Phase 4 Combat Cognition**| Subjective target estimate, self capability estimate, risk evaluations, combat postures selection (`PROBE`, `AVOID`, `RETREAT`, `ENGAGE`, etc.), mid-combat reassessment, and capacity-limited combat memory updates | Fully implemented in `src/domains/combat_engagement/` with 36 TDD/perf tests passing |
| **Phase 5 Belief loop**| Subjective queries, candidate routers, response normalizers, personal knowledge/unknowns assimilation under memory limits, belief observations verification & contradiction disproofs, slow gradual clamping source-trust adjustments, and adventure route-scorer impact bridging | Fully implemented in `src/domains/information/` with 25 TDD/perf tests passing |
| **Phase 10 Optimization & Rollout**| Feature flag controls, rollout profile budgets, dirty entity/region work scheduling, provider scoped query enforcement, cache & invalidation strategies, trace volume governor, memory/capacity limits, graceful degradation, developer diagnostics, and rollout gate script | Fully implemented in `src/domains/optimization/` and verified with comprehensive TDD & certification tests |
| **Phase 11 Cognition Restructure** | Hierarchical restructure of cognitive state into Subjective, Memory, Motivation, Commitment, and Relationship sub-models | [INVESTIGATING] Documented hierarchy schemas and migration boundaries |

 The uncomfortable truth: **the engine has action capability, but not yet a clean adventure action model**. You have mechanics for fighting, moving, crafting, buying, selling, resting, looting, training, recruiting, and interacting. But there is no single canonical “adventurer action vocabulary” yet.

---

# 1. Implemented entity model

`EntityState` is already rich. An entity is not just position + HP. It includes identity, inventory, strategy, social state, biological state, lifecycle, aptitude, combat, equipment, navigation, task, stamina, and interaction components.

## Main implemented entity aspects

| Aspect      | Implemented fields / behavior                                                               |
| ----------- | ------------------------------------------------------------------------------------------- |
| Identity    | role, faction, class, level/evolution, recipes, traits, cooldowns, personality              |
| Attributes  | strength, agility, vitality, endurance, intelligence, spirit, wisdom, perception, charisma  |
| Aptitude    | learning rate, stamina efficiency, stat aptitudes                                           |
| Combat      | HP, max HP, attack, defense, speed, range, evasion, readiness, wounds, scars, tactical role |
| Equipment   | slots and durability                                                                        |
| Inventory   | items, gold, capacity/weight logic through inventory services                               |
| Navigation  | position, target, path, movement mode, failure reason, leash/home/region                    |
| Stamina     | current/max stamina, regen, attack/move/harvest/skill costs                                 |
| Biological  | sleep debt, hunger, rest pressure, meal/sleep timestamps                                    |
| Lifecycle   | active/dead state, death reason, age, generation/heir fields                                |
| Interaction | target node, progress, start tick                                                           |
| Strategic   | projects, objectives, blockers, leads, concerns, directives, hypotheses, contracts          |
| Social      | trust/bonds/contracts/reputation-like state                                                 |
| Task        | current work kind and payload                                                               |

The canonical export also exposes strategic projects, directives, blockers, leads, concerns, social trust, combat state, biological state, lifecycle, and navigation state. That means the data exists for scenario diagnostics.

---

# 2. Implemented runtime action router

The main direct runtime action surface is `ActionRouter.route_action`.

It routes these payload action strings:

```text
SLEEP
EAT
REST
RECRUIT
ALLOCATE_AP
TRAIN
REPAIR
INTERACT
ATTACK
SKILL
AOE_ATTACK
```

`ActionRouter` first checks entity readiness through legality validation, then delegates to the correct action handler.

## Critical mismatch

The `ActionType` enum only defines:

```text
REST
MOVE
INTERACT
ATTACK
SKILL
```

But `ActionRouter` handles many more raw string actions like `SLEEP`, `EAT`, `RECRUIT`, `ALLOCATE_AP`, `TRAIN`, `REPAIR`, and `AOE_ATTACK`.

That is schema drift. You need one canonical action vocabulary.

---

# 3. Implemented action catalog

## 3.1 Survival / body actions

Implemented through `CoreActions.execute_survival`.

| Action  | Current behavior                                         |
| ------- | -------------------------------------------------------- |
| `SLEEP` | reduces sleep debt and rest pressure; consumes readiness |
| `EAT`   | reduces hunger; records last meal tick                   |
| `REST`  | reduces rest pressure                                    |

These are routed directly by `ActionRouter`.

### Current limitation

These are body-maintenance actions, not full adventure recovery yet. There is no strong adventure loop like:

```text
wounded -> retreat -> heal -> reassess readiness -> retry easier/harder objective
```

The pieces exist, but the closed loop is not mature.

---

## 3.2 Progression actions

## `ALLOCATE_AP`

Implemented in `CoreActions.execute_allocate_ap`.

Current routed version supports:

| Attribute | Effect                             |
| --------- | ---------------------------------- |
| strength  | increases strength and attack      |
| vitality  | increases vitality, max HP, and HP |

But there is also a separate `AllocateAttributeAction` wrapper that supports a broader attribute set through aptitude mapping.

### Problem

There are two allocation implementations with different capability breadth.

That is not harmless duplication. It can create false test confidence.

---

## `TRAIN`

Implemented in `CoreActions.execute_train`.

It requires `skill_id`, charges 50 gold through a `ResourceTransferIntent`, and removes capability blockers for that skill.

### Verified Bug

This is a **verified bug** in the codebase. 

- **Source:** Both `CoreActions.execute_train` ([core_actions.py:L199](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/domain/core_actions.py#L199)) and `ClassHallAction.train` ([class_hall.py:L33](file:///home/vboxuser/Work/rpg-based-simulation/src/town/class_hall.py#L33)) set:
  ```python
  identity_upd=IdentityUpdate(recipes_learned=[skill_id])
  ```
- **Result:** In `IdentityPatch.apply` ([patches.py:L194](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/patches.py#L194)), this maps strictly to `known_recipes` (crafting).
- **The Failure:** `SkillActions.execute_skill` ([skill_actions.py:L40](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/domain/skill_actions.py#L40)) checks against `entity.identity.learned_skills` and fails with `SKILL_NOT_LEARNED`.
- **Verdict:** Training fails to unlock skill usage because the skill is stored in `known_recipes` instead of `learned_skills`.

---

## `REPAIR`

Implemented in `CoreActions.execute_repair`.

It checks equipment durability, computes gold cost, and emits a repair transfer from `BLACKSMITH` with an `EquipmentUpdate`.

This is useful for adventure loops, especially after combat or dungeon runs.

---

# 4. Combat actions

## 4.1 Normal attack

`CombatActions.execute_attack` is implemented and routed directly by `ATTACK`.

It does:

| Step                                                             | Behavior |
| ---------------------------------------------------------------- | -------- |
| validates target exists                                          |          |
| checks attack legality                                           |          |
| resolves attack via `CombatResolutionSystem`                     |          |
| applies attacker readiness/equipment/resource transfer           |          |
| evaluates hunt quest victory                                     |          |
| applies defender combat/wound/social/strategic/lifecycle updates |          |
| handles group betrayal case                                      |          |
| drains stamina                                                   |          |

Combat resolution includes positional and state modifiers such as high ground, flanking, surrounded, cover, frozen/exhaustion/stamina, bond synergy, and then applies damage, kill reward, XP/gold transfer, durability damage, wounds, social grudges, and strategic/social consequences.

## 4.2 Skill action

`SkillActions.execute_skill` is implemented and routed directly by `SKILL`.

It checks:

| Check                              | Behavior |
| ---------------------------------- | -------- |
| `skill_id` exists                  |          |
| skill is in `learned_skills`       |          |
| cooldown                           |          |
| stamina                            |          |
| target exists and is alive         |          |
| then resolves skill damage/effects |          |

## 4.3 AOE attack

`AoeActions.execute_aoe_attack` is implemented and routed by `AOE_ATTACK`.

It uses target position and radius, resolves affected entities, applies updates, checks kill quest progress, and drains stamina.

---

# 5. Movement and tactical actions

## 5.1 Direct movement

`SimulationDomainLogic.execute_move` delegates movement to `MovementActions.execute_move`.

`MovementActions.execute_move` calls `MovementSystem.resolve_move` and evaluates exploration quests after movement.

## 5.2 Movement resolution

`MovementSystem.resolve_move` is detailed.

It handles:

| Aspect                                    | Behavior |
| ----------------------------------------- | -------- |
| dead entity check                         |          |
| pathing/cache                             |          |
| weather/aura/movement mode cost modifiers |          |
| legality and occupancy                    |          |
| sidestep / yielding                       |          |
| reroute / replan                          |          |
| opportunity attack on disengagement       |          |
| terrain cost                              |          |
| readiness and stamina drain               |          |
| navigation update                         |          |

## 5.3 Tactical decision layer

`TacticalDecisionSystem` is large and already tries to choose local behavior based on emotion, hostile awareness, leash, project objective, group behavior, target selection, anti-stalemate, cover, retreat, bracketing, guarding, intercepting, chokepoints, kiting, skills, attacks, and pursuit.

This is one of the stronger implemented areas.

### Current limitation

Tactical behavior is more mature than strategic adventure behavior. The entity can fight/move tactically, but it still lacks complete high-level adventure routes like:

```text
choose quest
prepare supplies
ask information
upgrade gear
form party
enter dungeon
return and convert rewards
```

---

# 6. Interaction, harvesting, looting

## 6.1 Generic interaction

`INTERACT` is routed by `ActionRouter` into `CoreActions.execute_interact`.

It sets the target and advances interaction progress.

## 6.2 Harvest start action

`HarvestAction.start_harvest` exists.

It validates:

| Check                         |
| ----------------------------- |
| node exists                   |
| node has remaining charges    |
| cooldown <= 0                 |
| entity is within 1.5 distance |

Then it starts an interaction channel with target node and harvest metadata.

## 6.3 Loot start action

`LootAction.start_loot` exists.

It validates:

| Check                                  |
| -------------------------------------- |
| target exists as ground item or corpse |
| entity is within 1.5 distance          |

Then it starts an interaction channel.

## 6.4 Interaction completion

`InteractionSystem.enforce` handles channeling laws and completion.

It resets interaction on movement, target switch, or damage; advances progress; detects resource node, ground item, corpse, or chest; and on completion emits `ResourceTransferIntent` from `NODE`, `GROUND_ITEM`, `CORPSE`, or `CHEST`.

### Important distinction

Harvest and loot are not direct `ActionRouter` strings. They are interaction-start wrappers plus the interaction enforcement system.

For adventure design, you should treat them as implemented mechanics, but not yet cleanly part of the canonical routed action vocabulary.

---

# 7. Town, service, and economy actions

## 7.1 Blacksmith crafting

There are two relevant blacksmith surfaces.

### `BlacksmithService.craft_item`

It validates:

| Check                        |
| ---------------------------- |
| functional blacksmith nearby |
| distance <= 2                |
| recipe exists                |
| materials exist              |
| gold is enough               |

Then it emits a craft `ResourceTransferIntent` that removes materials, adds crafted item, and charges gold.

### `BlacksmithSystem.enforce`

This is deeper and more engine-like. It includes recipe definitions, recipe learning when visiting a blacksmith, craft target handling, known recipe check, material/gold blockers, and successful crafting transfer.

This matters because adventure crafting already has a mechanical foundation.

### Missing adventure behavior

There is still no clean high-level action like:

```text
ASK_BLACKSMITH_FOR_UPGRADE
REQUEST_RECIPE_FOR_CLASS
CRAFT_BEST_AFFORDABLE_ITEM
```

The mechanics exist, but the adventure-facing intent layer is missing.

---

## 7.2 Shop buy/sell

`ShopService.buy_item` and `ShopService.sell_item` exist.

Buy validates functional shop proximity, item registry, dynamic price, enough gold, and inventory capacity, then emits `SHOP_BUY`.

Sell validates item ownership and shop proximity, then emits `SHOP_SELL`.

There is also `ShopSystem.enforce`, which validates shop prices against truth, rejects stale/exploit price attempts, auto-sells materials/junk when entity is on shop tile, and includes trauma-based price effects.

### Missing adventure behavior

There is no clear high-level routed action like:

```text
BUY_FOOD
BUY_POTION
BUY_UPGRADE
SELL_LOOT
COMPARE_EQUIPMENT_BEFORE_BUY
```

The transaction mechanics exist, but the adventurer decision layer is still underbuilt.

---

## 7.3 Guild visit / intel

`GuildAction.visit` exists.

It scans resource nodes and adds vague `LeadState` entries, especially around iron nodes, and can generate quest projects if strategic capacity allows.

This is important for adventure information flow.

### Current limitation

It is still simple. It creates raw leads from world state. It is not yet a rich information economy with guide/guild/traveler differences, source trust, price-for-information, false rumors, and contradiction loops.

---

## 7.4 Home actions

`HomeAction.rest` and `HomeAction.upgrade` exist.

Rest reduces sleep debt. Upgrade charges gold and resolves maintenance blockers.

## 7.5 Home storage

`HomeStorageService.deposit` and `withdraw` exist near town center.

They validate proximity and item availability, then emit deposit/withdraw transfer intents.

## 7.6 Inn rest

`InnAction.rest` exists.

It costs 10 gold, clears sleep debt, reduces hunger, and grants `well_rested_until`.

## 7.7 Town navigation

`TownNavigation` can find the nearest service and check town radius.

---

# 8. Social, group, and recruitment actions

## 8.1 Recruit

`RECRUIT` is routed by `ActionRouter`.

`CoreActions.execute_recruit` does:

| Step                                                                                       | Behavior |
| ------------------------------------------------------------------------------------------ | -------- |
| finds target                                                                               |          |
| creates temporary recruitment contract                                                     |          |
| calls `SocialAppraisalSystem.appraise_contract`                                            |          |
| if accepted, creates `ContractState`, group ID, payout transfer, strategic contract update |          |
| if rejected, records rejection / social update                                             |          |

This is a real social-action bridge.

### Current limitation

Recruitment exists, but broader party-adventure behavior is not yet complete:

```text
form party because objective too hard
evaluate class compatibility
split loot
coordinate dungeon route
maintain cohesion
handle betrayal/abandonment
```

The engine has some group records and tactical group behavior, but not the full adventure-party loop.

---

# 9. Building / sabotage action

`SabotageAction.apply` exists.

It validates building existence, functioning state, and distance, then applies damage based on entity attack.

This is implemented, but for the current narrowed adventure scope, sabotage is probably not a priority unless you want monster camps, enemy structures, or faction conflict.

---

# 10. Quest-related actions and effects

Quest systems exist around:

| System                          | Behavior |
| ------------------------------- | -------- |
| exploration quest evaluation    |          |
| combat victory quest evaluation |          |
| quest resolution enforcement    |          |
| quest generation                |          |

Movement evaluates exploration quest progress after movement.

Combat evaluates hunt quest victory after kills.

Quest resolution/generation systems exist, but the action vocabulary still lacks a clean adventure route like:

```text
BROWSE_QUESTS
ACCEPT_QUEST
REJECT_QUEST
ABANDON_QUEST
TURN_IN_QUEST
```

That matters. For an adventure-first engine, quest actions should be first-class.

---

# 11. Strategic / cognitive action selection

## 11.1 Goal registry

The implemented goal framework has:

| Class          | Purpose                         |
| -------------- | ------------------------------- |
| `GoalScore`    | scored candidate goal           |
| `GoalScorer`   | interface                       |
| `GoalRegistry` | registers and evaluates scorers |

Current registered/basic scorers include:

| Scorer          | Purpose                                            |
| --------------- | -------------------------------------------------- |
| `HarvestScorer` | harvest utility                                    |
| `SleepScorer`   | fatigue/sleep utility                              |
| `EatScorer`     | hunger utility                                     |
| `SocialScorer`  | placeholder social utility                         |
| `TownScorer`    | return town based on needs, full inventory, low HP |

## Verified Bug: TownScorer fails to create project

This is a **verified bug** in the codebase.

- **Source:** `TownScorer.score` ([scorers.py:L97](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/scorers.py#L97)) returns a `GoalScore` with `target_pos=state.town_center`, but **`target_id` is None**.
- **Result:** In `StrategicIntelligenceSystem.evaluate_strategic_intent` ([intelligence.py:L1171](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py#L1171)), any goal score with `target_id is None` is skipped:
  ```python
  if g_score.utility < 20.0 or g_score.target_id is None:
      continue
  ```
- **Verdict:** Because `target_id` is never set, the town-return goal score is discarded on every strategic update, meaning `town_return` projects are never created. This fundamentally breaks the leave-town/return-town adventure loop.

---

# 12. Strategic projects, blockers, leads, concerns

The entity strategic state already supports:

| Strategic item   | Purpose |
| ---------------- | ------- |
| projects         |         |
| blockers         |         |
| leads            |         |
| directives       |         |
| concerns         |         |
| candidate zones  |         |
| hypotheses       |         |
| source trust     |         |
| contracts        |         |
| turning points   |         |
| boredom/overload |         |

`StrategicUpdate` supports adding/removing/updating all of these.

`StrategicIntelligenceSystem.evaluate_strategic_intent` evaluates goal scores, applies modifiers, filters low scores, requires a target, builds an objective/project, and evaluates project switching.

### Good

The strategic substrate is real.

### Bad

The current goal/action set is not adventure-complete. It does not yet express enough of:

```text
choose quest
prepare for quest
upgrade equipment
seek information
research unknown location
form party
buy supplies
repair gear because of upcoming risk
return to town as adventure closure
escalate to harder content
```

---

# 13. Resource transfer and update model

The engine uses `ResourceTransferIntent` as the key lawful transaction mechanism.

It can carry:

| Transfer aspect                                                                    |
| ---------------------------------------------------------------------------------- |
| source ID/kind                                                                     |
| items added/removed                                                                |
| gold delta / gold cost                                                             |
| price multiplier                                                                   |
| XP reward                                                                          |
| transfer kind                                                                      |
| group requirement                                                                  |
| contingent biological/attribute/identity/combat/strategic/equipment/reward updates |

`EntityUpdate` can mutate almost every entity aspect: position, readiness, resource transfers, identity, attributes, inventory, strategic, biological, social, quest, reward, lifecycle, combat, equipment, navigation, task, and stamina.

This is good. The law-enforcement substrate is strong enough for adventure simulation.

---

# 14. Implemented action aspects by category

## A. Body / survival

| Implemented                | Missing / weak for adventure                                        |
| -------------------------- | ------------------------------------------------------------------- |
| sleep, eat, rest           | heal action, potion use, condition recovery, camp/rest outside town |
| hunger/sleep/rest pressure | full survival-to-adventure readiness loop                           |
| inn rest                   | smarter choice of inn/home/rest/camp                                |

## B. Movement / navigation

| Implemented                         | Missing / weak                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------------- |
| move resolution                     |                                                                                           |
| pathing/reroute                     |                                                                                           |
| sidestep/yield                      |                                                                                           |
| opportunity attack                  |                                                                                           |
| terrain/readiness/stamina cost      |                                                                                           |
| movement modes                      |                                                                                           |
| tactical retreat/pursuit/reposition | high-level expedition route planning, return-home loop reliability, party travel cohesion |

## C. Combat

| Implemented           | Missing / weak                                                                                             |
| --------------------- | ---------------------------------------------------------------------------------------------------------- |
| attack                |                                                                                                            |
| skill                 |                                                                                                            |
| AOE                   |                                                                                                            |
| damage modifiers      |                                                                                                            |
| wounds/scars          |                                                                                                            |
| kill rewards          |                                                                                                            |
| durability decay      |                                                                                                            |
| grudge/bond updates   |                                                                                                            |
| quest kill evaluation | adventure-level encounter selection, threat avoidance from memory, class-specific combat strategy maturity |

## D. Interaction / resource acquisition

| Implemented                       | Missing / weak                                                                               |
| --------------------------------- | -------------------------------------------------------------------------------------------- |
| interact                          |                                                                                              |
| harvest start                     |                                                                                              |
| loot start                        |                                                                                              |
| channeling completion             |                                                                                              |
| node/ground/corpse/chest transfer | clean direct action names for harvest/loot/open chest/gather; deeper tool/skill requirements |

## E. Economy

| Implemented              | Missing / weak                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| shop buy                 |                                                                                            |
| shop sell                |                                                                                            |
| dynamic price            |                                                                                            |
| stale price rejection    |                                                                                            |
| trauma price factor      |                                                                                            |
| storage deposit/withdraw | intentional adventurer buying: food, potion, gear, upgrade comparison, sell loot after run |

## F. Crafting / blacksmith

| Implemented                         | Missing / weak                                                                                                                                       |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| recipe registry                     |                                                                                                                                                      |
| known recipe check                  |                                                                                                                                                      |
| material/gold check                 |                                                                                                                                                      |
| crafting transfer                   |                                                                                                                                                      |
| recipe learning on blacksmith visit |                                                                                                                                                      |
| repair                              | ask blacksmith for recommended upgrade, class-fit item selection, material source inquiry, prerequisite planning from recipe to adventure objectives |

## G. Progression

| Implemented                          | Missing / weak                                                                               |
| ------------------------------------ | -------------------------------------------------------------------------------------------- |
| AP allocation                        |                                                                                              |
| training                             |                                                                                              |
| level progression service            |                                                                                              |
| skill registry                       |                                                                                              |
| equipment ranking/auto-equip service | training likely writes wrong field; no full “I need stronger skill/gear for next quest” loop |

## H. Social / party

| Implemented                     | Missing / weak                                                                                                    |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| recruit                         |                                                                                                                   |
| contract appraisal              |                                                                                                                   |
| contract creation               |                                                                                                                   |
| group record                    |                                                                                                                   |
| betrayal/grudge hooks in combat | full party adventure loop, class compatibility, reward split, escort behavior, trust-based future party selection |

## I. Information / guild / knowledge

| Implemented                    | Missing / weak                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| guild visit creates leads      |                                                                                                                      |
| belief system exists           |                                                                                                                      |
| source trust exists            |                                                                                                                      |
| strategic leads/blockers exist | ask guide/traveler/merchant, paid info, partial/wrong info, contradiction-driven route change, knowledge-gap project |

## J. Quest

| Implemented                         | Missing / weak                                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------------------- |
| explore quest evaluation            |                                                                                             |
| hunt victory evaluation             |                                                                                             |
| quest generation/resolution systems | first-class browse/accept/reject/abandon/turn-in quest actions; risk/reward quest selection |

## K. World/building

| Implemented                                      | Missing / weak                                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| sabotage building                                |                                                                                                            |
| camps/boss/calamity/world pressure systems exist |                                                                                                            |
| regional trauma affects some systems             | direct adventurer response to world threat, region threat escalation loop, quest pressure from world state |

---

# 15. What is implemented but not properly unified

## 15.1 Action vocabulary is fragmented

You currently have:

```text
ActionType enum
ActionRouter strings
ActionProposal verb
TaskComponent.work_kind
Town wrapper actions
System enforce actions
Strategic project/objective kinds
```

These are not yet one coherent action model.

That is the biggest structural problem.

## 15.2 Runtime router is narrower than available mechanics

`ActionRouter` does not directly route many important adventure actions:

```text
BUY
SELL
CRAFT
HARVEST
LOOT
OPEN_CHEST
VISIT_GUILD
REST_IN_INN
DEPOSIT
WITHDRAW
SABOTAGE
ACCEPT_QUEST
TURN_IN_QUEST
ASK_INFO
FORM_PARTY_BY_OBJECTIVE
```

Some of these exist through wrappers/systems, but not as a unified direct action surface.

## 15.3 Goal system is much narrower than action mechanics

The entity can mechanically do more than it can strategically decide to do.

Current goal scorers mostly cover:

```text
harvest
sleep
eat
social
town_return
```

That is not enough for adventure RPG behavior.

## 15.4 Training does not unlock skill usage (VERIFIED BUG)

Training writes `recipes_learned` (which updates crafting recipes), while skill execution checks `learned_skills`. They do not intersect. This is a verified bug and must be fixed.

## 15.5 Return-to-town is strategically broken (VERIFIED BUG)

`TownScorer` returns only `target_pos` and omits `target_id`. Because strategic project creation filters out scores where `target_id is None`, return-to-town projects are never active, breaking the loop:

```text
leave town -> adventure -> return town -> recover/sell/upgrade -> next adventure
```

This is a verified bug in `scorers.py` and `intelligence.py`.

---

# 16. Missing adventure-critical action intents

These are not necessarily absent as mechanics, but they are missing or weak as **clear adventure action intents**.

## Immediate missing canonical action intents

```text
INSPECT_SELF
INSPECT_EQUIPMENT
CHOOSE_QUEST
ACCEPT_QUEST
REJECT_QUEST
ABANDON_QUEST
TURN_IN_QUEST

BUY_SUPPLY
BUY_EQUIPMENT
SELL_LOOT
EQUIP_BEST_ITEM
REPAIR_GEAR

ASK_BLACKSMITH_UPGRADE
ASK_INFORMATION
PAY_FOR_INFORMATION
RESEARCH_LOCATION
SCOUT_LOCATION

HARVEST_RESOURCE
LOOT_TARGET
OPEN_CHEST

FORM_PARTY
REQUEST_ESCORT
LEAVE_PARTY
SPLIT_REWARD

RETREAT_TO_TOWN
RECOVER_IN_TOWN
PREPARE_FOR_ADVENTURE
ESCALATE_TO_HARDER_OBJECTIVE
```

Do not implement all blindly. But these are the missing action vocabulary for your narrowed adventure-only scope.

---

# 17. Priority Plan

## Mindset / assumption to change

Stop saying “the action exists” just because a helper class or service exists.

Use this stricter rule:

```text
An action is truly implemented only if:
1. the entity can decide to do it,
2. it can be routed/executed consistently,
3. legality/resource laws are enforced,
4. the result updates state,
5. future cognition can observe the result.
```

By that standard, many mechanics exist, but many adventure actions are not fully integrated yet.

## Immediate actions

1. Build a canonical action matrix with these columns:

```text
Action name
Current implementation path
Routed by ActionRouter?
Used by strategic goal?
Uses ResourceTransferIntent?
Updates cognition/memory?
Needed for adventure loop?
Status: complete / partial / wrapper only / missing
```

2. Fix obvious inconsistencies first:

```text
TRAIN writes recipes_learned but SKILL checks learned_skills
TownScorer target_pos vs target_id strategic filter
ActionType enum vs ActionRouter strings
Allocate AP duplicated behavior
```

3. Define the adventure action vocabulary before adding new features.

Start with:

```text
prepare
move
fight
flee
interact
harvest
loot
buy
sell
repair
rest
eat
sleep
train
craft
ask_info
accept_quest
turn_in_quest
return_town
form_party
```

4. Map each current implemented mechanic into that vocabulary.

## What to stop

Stop treating wrappers, systems, and router actions as the same thing.

They are not the same.

Also stop adding new story scenarios until you know exactly which actions are:

```text
fully runnable
partially runnable
only test wrappers
not routed
not strategically selectable
```

## Consequence if ignored

You will design adventure campaigns that the engine cannot actually execute end-to-end.

The failure will look like this:

```text
rich scenario design
rich entity state
many action helpers
but no clean route from strategic intent to executable action
```

That is how a simulation becomes impressive on paper and broken in runs.

---

# 18. Phase 2: Bottom-Up Entity Self Model

To solve the mismatch between raw entity parameters and high-level strategic reasoning, Phase 2 implements a bottom-up self-assessment and interpretation layer. This provides entities with subjective self-awareness, need prioritization, capability estimation, and personal knowledge retention, completely decoupled from action execution.

## 18.1 Architecture and Design Rationale

Unlike brittle top-down components like an "AdventureReadinessComponent" (which would hardcode transient tactical assumptions), Phase 2 implements a pure **bottom-up interpretation layer**. 

```mermaid
graph TD
    RawState["Raw EntityState Components (HP, Inventory, Hunger)"] --> SelfAssess["SelfAssessmentService"]
    SelfAssess --> SelfAwareness["SelfAwarenessComponent"]
    SelfAwareness --> NeedInterpret["NeedInterpretationService"]
    NeedInterpret --> NeedComponent["NeedInterpretationComponent"]
    
    SelfModelBundle["SelfModelBundle"]
    SelfAwareness --> SelfModelBundle
    NeedComponent --> SelfModelBundle
    
    CapabilityContext["CapabilityContext (Scoped Request)"] --> CapEstimate["CapabilityEstimateService"]
    CapEstimate --> CapComponent["CapabilityEstimateComponent"]
    CapComponent --> SelfModelBundle
    
    InfoEvent["InformationResponse Event"] --> KnowModel["KnowledgeModelService"]
    KnowModel --> KnowComponent["KnowledgeModelComponent"]
    KnowComponent --> SelfModelBundle
```

All self-model data is kept inside `SelfModelBundle` as a single top-level field on `EntityState`. Since this is derived state, it is excluded from the authoritative canonical state hash, but remains included in serializations for debugging and inspection.

## 18.2 Schema Components

### 18.2.1 SelfAwarenessComponent
Converts raw physical states into subjective wellness assessments:
* **Perceived Condition**: Rounded float metrics tracking HP percentage (`"health"`), stamina percentage (`"stamina"`), slots utilized percentage (`"carrying_load"`), and gear health (`"gear_quality"`).
* **Perceived Weaknesses**: Tuple of detected vulnerabilities (e.g. `"low_health"`, `"low_stamina"`, `"hunger_pressure"`, `"weak_weapon"`).
* **Confidence & Stress Levels**: Composite scores computed from physical status and severity of weaknesses.

### 18.2.2 NeedInterpretationComponent
Maps self-awareness into active desires and a single dominant need:
* **Healing**: Becomes critical when health is severely low, dominating all other desires.
* **Survival (Food, Rest)**: Outranks all growth needs under stress.
* **Growth (Gold, Equipment, Information)**: Active during stable conditions but deflated under vulnerability.

### 18.2.3 CapabilityEstimateComponent
Generates scoped capability estimates (0.0 to 1.0) for potential actions. To avoid expensive O(N) world-scans, estimates are strictly requested through a `CapabilityContext`:
* **Combat**: Compares entity stats (atk, defense, hp) vs expected enemy levels.
* **Gathering/Crafting**: Verifies tool requirements, recipe availability, gold, and component inventories.

### 18.2.4 KnowledgeModelComponent
Stores what the entity explicitly has learned (KnowledgeFacts) or knows it doesn't know (UnknownFacts).
* **Information Opacity**: Preservation of uncertainty is guaranteed — hidden world truth is never leaked; providers only return low-certainty "LeadState" facts.

## 18.3 SelfModelUpdatePhase & Performance Skip

Updates are orchestrated efficiently via the `SelfModelUpdatePhase.run` loop. A high-performance dirty-check ensures that Need Interpretation and Capability Estimation are skipped entirely if no raw stats changed and no information events were assimilated, executing in **under 5 microseconds** for clean ticks.


# 22. Phase 6: Bounded Progression, Equipment, and Reward Conversion Architecture

To bridge the gap between raw combat rewards and long-term capability growth, Phase 6 implements a subjective meaning interpretation, growth gap detection, and options-scoring decision loop. Decisions are successfully resolved and mapped into standard non-mutative authoritative proposed updates.

## 22.1 Architecture and Workflow

```mermaid
graph TD
    RawState["Raw EntityState Components (Gold, Inventory, Durability)"] --> PossessionService["PossessionUnderstandingService"]
    PossessionService --> PossessionComponent["PossessionUnderstandingComponent"]
    
    PossessionComponent --> GapsEvaluator["GrowthGapEvaluator"]
    GapsEvaluator --> GapsReport["GrowthGapReport"]
    
    EventLedger["Event-Driven RewardLedgerComponent"] --> RewardInterp["RewardInterpretationService"]
    GapsReport --> RewardInterp
    
    RewardInterp --> OptionGen["ConversionOptionGenerator"]
    OptionGen --> DecisionService["ConversionDecisionService (Scoring + Personality Bias)"]
    
    DecisionService --> Result["ProgressionDecisionResult"]
    Result --> IntentResolver["ConversionIntentResolver"]
    IntentResolver --> proposedUpdates["Executable proposed updates (TaskUpdate, EquipmentUpdate, IdentityUpdate)"]
```

## 22.2 Component Specifications

### 22.2.1 PossessionUnderstandingComponent & Service
Translates inventory items subjectively against active recipes and equipment power comparisons to assign keep, sell, craft, or equip priorities.
* Keeps active recipe components (`iron_ore`, `wolf_fang`) instead of selling them.
* Recognizes rare unknown clues (`ancient_fragment`) as items to store and ask guides about instead of discarding.

### 22.2.2 GrowthGapEvaluator & Report
Identifies active weaknesses and needs across weapon potency, critical gear repairs, recipe components, gold reserves, and level AP upgrades. Determines the dominant gap (e.g. prioritizes critical repairs over minor weapon upgrades).

### 22.2.3 RewardLedgerComponent & Service
Provides an event-driven, capacity-bounded list (capped at 20 entries) of recent XP, gold, or item gains, bypassing full-state reconstructs and ensuring high execution leanness.

### 22.2.4 RewardInterpretationService
Translates recent reward gains against active growth gaps to formulate subjectively useful meaning records (e.g. interprets a gold gain as a blacksmith repair opportunity under a critical durability gap).

### 22.2.5 ConversionDecisionService & Personality Scoring
Generates conversion options and applies personality traits (`greed`, `industry`, `caution`) to choose final choices:
* **Caution**: Prefers blacksmith repair tasks and supplies.
* **Greed**: Favors selling loot and saving gold.
* **Industry**: Directs towards keeping materials and active crafting.

### 22.2.6 ConversionIntentResolver & ProgressionConversionPhase
Translates decisions to standard executable intents (e.g. `BLACKSMITH_REPAIR` task payload, main-hand equipment updates, or unspent AP delta decrease). The phase runs fully bounded behind a feature flag and executes in **1.9 ms for 100+ entities** (under the 5ms gate budget).


## Section 23: Phase 7 — Party / Social Cooperation Architecture

Phase 7 adds strategic, social cooperation and party dynamics to the simulation. It establishes a dedicated Cooperation Domain under the immutable boundary pattern. Entities evaluate their capability-derived help needs, query spatial or highly trusted partner candidates, score candidate fit with private trust, grudges, alignment, and capability indicators, select cooperation postures, and bridge those decisions into executable contract intents or tactical overrides.

### 23.1 Core Components

* **CooperationPosture**: Formally typed social orientations:
  - `SOLO`: Process objective entirely independently.
  - `REQUEST_HELP`: Seek assistance from a trusted peer.
  - `HIRE_SUPPORT`: Pay a commercial hireling or guild worker.
  - `DEFER_NO_PARTNER`: Delay strategic progress due to high risk and lack of suitable allies.
  - `JOIN_COOP`: Accept and join an existing party or contract.
  - `ABANDON_COOP`: Deliberately break alignment and leave the party.

* **HelpNeedEvaluator**: Evaluates high combat risk, near-death history, critical HP levels, unexplored regions, or excessive carrying loads to establish typed `HelpNeed` records (`combat_support_needed`, `healer_needed`, `guide_needed`, `carry_support_needed`).

* **PartnerCandidateProvider**: Restricts scan space to nearby entities (within a spatial radius) or highly trusted strategic allies (trust > 0.7) to guarantee low latency. It implements a cheap bounding box filter before evaluating full spatial distances.

* **PartnerFitEvaluator**: Computes fit score by incorporating baseline trust (including bonds), applying grudge/nemesis penalties, assessing role compatibility (e.g. VANGUARD fits combat need), evaluating objective alignment (e.g. sharing identical current objective targets), and penalizing commercial costs against gold reserves.

* **CooperationDecisionService**: Translates help needs and candidate fit reports into a definitive posture and choice of partner, returning a trace record and lists of rejected partners with reasons.

* **CooperationIntentBridge**: Bridges strategic cooperation decisions into actionable, typed updates (such as `StrategicUpdate` with new contracts or `SocialUpdate` updating trust/fatigue).

* **PartyObjectiveAlignmentService & PartyCohesionService**: Evaluates structural cohesion of active groups, identifying when objective changes or trust decay signals member abandonment or leader loss, updating social trust deltas accordingly.

* **CooperationLearningService**: Adapts future posture decisions based on past cooperation outcomes (e.g. memory of betrayal decreases partner trust).

* **CooperationPhase**: Orchestrator of the cooperation tick sequence, operating inside the `AuthoritativeApplyPipeline` with strict execution bounding (< 25.0ms for 100+ entities).

### 23.2 Architecture Data Flow

```mermaid
graph TD
    EntityState["EntityState Components (HP, Social, Strategic)"] --> NeedsEval["HelpNeedEvaluator"]
    NeedsEval --> HelpNeeds["HelpNeeds (combat, healing, guide)"]
    
    HelpNeeds --> Providers["PartnerCandidateProvider (spatial & trust filter)"]
    Providers --> Candidates["Candidate List"]
    
    Candidates --> FitEval["PartnerFitEvaluator (trust, grudge, role, alignment)"]
    FitEval --> FitReports["PartnerFitReports"]
    
    FitReports --> DecisionService["CooperationDecisionService"]
    DecisionService --> Decision["CooperationDecision (posture, partner, rejects)"]
    
    Decision --> IntentBridge["CooperationIntentBridge"]
    IntentBridge --> StateUpdate["StateUpdate / Intents / Blockers"]
```


## Section 24: Phase 8 — World Emergence / Population-Level Consequences

Phase 8 introduces macro environmental feedback loops. Entity actions (such as deaths, resource gathering, and combat wins) are aggregated into dynamic regional, resource, and service pressures. These world pressures, in turn, are bridged back to subjective entity-level observations, dynamically driving future routing and progression choices.

### 24.1 Core Components

* **WorldEventAggregator**: Bounded window aggregator that compiles raw simulation event streams (deaths, harvest events, etc.) inside a 100-tick sliding window, preventing expensive $O(N)$ historical scans.
* **RegionalPressureModel**: Evaluates regional danger (based on entity death events and quest failures) and wild camp escalation levels, mapping aggregate metrics to a standardized $[0.0, 1.0]$ range.
* **ScarcityModel**: Evaluates resource exhaustion patterns per region (e.g. rapid node depletion events) to determine raw material scarcity coefficients.
* **WorldOpportunityPressureService**: Translates regional danger and resource shortages into dynamic opportunity pressures (`clear_threat`, `gather_resource`, `camp_clear`).
* **DynamicQuestSeedService & RumorSeedService**: Generates deterministic quest seeds (difficulty and gold reward hints mapped to pressure intensity) and low-certainty rumor seeds for travelers.
* **ServiceStatePressureModel**: Computes town service strains (e.g. blacksmith material shortage derived from iron ore scarcity).
* **WorldToEntitySignalBridge**: Projects macro world pressures onto local entity observations based on spatial proximity or hometown association, bridging danger levels into subjective route adjustments (e.g. `force_route_reevaluation`).
* **WorldEmergencePhase**: Orchestrates the entire evaluation loop inside the authoritative simulation pipeline, safely avoiding raw mutable state changes and maintaining a strict performance budget ($< 5.0\text{ms}$ for $100+$ entities).

### 24.2 Architecture Data Flow

```mermaid
graph TD
    WorldEvents["Raw Simulation Events (deaths, harvests, etc.)"] --> EventAgg["WorldEventAggregator (sliding window)"]
    EventAgg --> RegionalModel["RegionalPressureModel (danger, camp)"]
    EventAgg --> ScarcityModel["ScarcityModel (resource depletion)"]
    
    RegionalModel & ScarcityModel --> OppService["WorldOpportunityPressureService"]
    OppService --> QuestService["DynamicQuestSeedService (quest seeds)"]
    
    RegionalModel & ScarcityModel --> RumorService["RumorSeedService (rumor seeds)"]
    RegionalModel & ScarcityModel --> ServiceModel["ServiceStatePressureModel (service pressures)"]
    
    QuestService & RumorService & ServiceModel --> SignalBridge["WorldToEntitySignalBridge (spatial exposure)"]
    SignalBridge --> EntityState["Subjective Entity Updates (force route reevaluation, signals)"]
```

## Section 25: Phase 9 — Long-Run Life-Arc Campaigns Architecture

Phase 9 establishes the campaign verification system for long-run simulation runs. It provides structural validation of entity lives rather than raw tick transitions, ensuring the RPG simulation generates coherent individual lifespans, behavioral adaptability based on historical events, route diversity, and strict compliance with simulation boundaries (preventing post-death actions or hidden information leaks).

### 25.1 Core Modules and Architecture

* **CampaignSpec (`schema.py` & `spec.py`)**: Data-driven specification loaded from YAML/JSON files, allowing reproducible runs across seeds. It specifies expected actor behaviors, target life arc families, world pressures, semantic budget limits, and forbidden behaviors.
* **CampaignRunner (`runner.py`)**: Orchestrator wrapping the simulation Kernel. It sets up actors, executes a long-run simulation loop, captures entity events, intercepts simulation state transitions, and feeds the resulting trace to semantic analyzers.
* **LifeArcClassifier (`classifier.py`)**: Evaluates entity life traces against deterministic criteria to classify them into distinct archetypal life arcs:
  - `cautious_growth`: Entity recovers at inns or accepts easy quests after experiencing combat losses.
  - `craft_growth`: Entity learns recipes and crafts items to improve capability.
  - `info_growth`: Entity gathers rumors, scouts unknown zones, and routes around obstacles.
  - `party_growth`: Entity forms social contracts and tactical groups.
  - `risky_growth`: Entity takes high combat risks and wins high-difficulty encounters.
  - `failed_adventurer`: Entity suffers death after making traceable tactical choices.
  - `stagnant`: Entity fails to achieve progression or remains trapped in loop patterns.
* **BehaviorChangeProofDetector (`behavior_change.py`)**: Verifies temporal causal proofs, ensuring that actions in later phases are causally shifted based on cognitive events in earlier phases (e.g. combat loss leading to danger avoidance, upgrading after acquiring crafting ingredients).
* **RouteDiversityAnalyzer (`diversity.py`)**: Computes entropy metrics, unique path ratios, and trait correlations to detect behavioral collapse or stagnation across the population.
* **ForbiddenBehaviorDetector (`forbidden.py`)**: Scans event logs to enforce absolute rule verification, instantly identifying post-death actions, actions utilizing hidden/omniscient world knowledge, or infinite stuck looping.
* **CampaignScorecardEvaluator (`scorecard.py`)**: Combines classification, behavior proofs, diversity metrics, and forbidden logs to issue a final verdict (`pass` or `fail`).
* **CampaignReportGenerator (`reports.py`)**: Formulates comprehensive markdown and JSON analysis outputs for continuous validation and continuous integration verification.

### 25.2 Architecture Data Flow

```mermaid
graph TD
    SpecFile["Campaign Specification (YAML)"] --> SpecLoader["CampaignSpecLoader"]
    SpecLoader --> Runner["CampaignRunner"]
    
    Runner --> KernelLoop["Kernel Tick Loop (17-Phase Authoritative Pipeline)"]
    KernelLoop --> EventStream["Campaign Events Trace"]
    
    EventStream --> Classifier["LifeArcClassifier (cautious, craft, stagnant, death)"]
    EventStream --> ChangeDetector["BehaviorChangeProofDetector (avoidance, route shifts)"]
    EventStream --> Diversity["RouteDiversityAnalyzer (entropy, trait correlation)"]
    EventStream --> Forbidden["ForbiddenBehaviorDetector (post-death, omniscient leak)"]
    
    Classifier & ChangeDetector & Diversity & Forbidden --> Scorecard["CampaignScorecardEvaluator"]
    Scorecard --> Reports["CampaignReportGenerator (JSON & Markdown summaries)"]
```


## Section 26: Phase 11 — Cognition Hierarchy Restructure

Phase 11 introduces a structured, nested hierarchy for the entity's cognitive components, refactoring them from flat fields (such as `SelfModelBundle`) into a organized `CognitionModel` top-level attribute. This restructure supports deterministic serialization, strict modular boundaries, and backward-compatible accessors to avoid breaking active loops during transition.

### 26.1 Core Sub-Models and Architecture

* **CognitionModel**: The central top-level cognitive record containing:
  - `subjective`: Holds perception, subjective self-awareness, knowledge model facts, risk beliefs, temporal models, and short-term emotional states.
  - `memory`: Contains historical causal, spatial, combat, habit, and social memories.
  - `motivation`: Encapsulates long-term biases, identity doctrines, values, and role preference profiles.
  - `commitment`: Stores promises, quest obligations, and party commitments.
  - `relationships`: Tracks private trust, public reputation, and betrayal records.

* **Compatibility Accessors**: Lightweight functions mapping old paths (e.g. `entity.self_model`) directly to new sub-paths (e.g. `entity.cognition.subjective.self`) to prevent compiler failures and support gradual migration.

* **Import Boundaries**: Architecture guardrails ensuring that cognitive schema dataclasses under `src/core/` are pure immutable data models and do not import any domain or tactical systems.


## Section 27: Phase 12 — Perception / Attention Domain

Phase 12 prevents entity omniscience by forcing entities to filter, prioritize, and rank candidate world signals through salience, attention focus, and capacity bounds before their strategic or tactical systems can execute.

### 27.1 Core Components

* **PerceptionModel**: The structured container under `cognition.subjective.perception` storing:
  - `attention_focus`: Dynamic bias tags.
  - `perceived_entities`, `perceived_resources`, `perceived_services`, `perceived_threats`, `perceived_opportunities`: Bounded dictionaries containing perceived records with rounded subjective salience scores.
  - `ignored_signals`: High-salience elements dropped due to capacity limitations.

* **AttentionFocusService**: Determines dynamic biases based on dominant need (e.g. mapping `"healing"` need to `"healing_resource"`, `"healer"`, `"safe_place"` tags) and active projects.

* **SignalSalienceEvaluator**: Ranks raw candidates combining base relevance, focus tag match bonuses, fear-scaled threats, curiosity-scaled novelty, and a distance decay factor.

* **PerceptionFilterService**: Enforces a strict perception budget (e.g., maximum of 10 perceived objects), mapping signals into structured typed records.

* **PerceptionUpdatePhase**: The authoritative pipeline update loop orchestrator driving perception sweeps for active entities.




## Section 28: Phase 13 — Temporal / Causal / Spatial Memory Domain

Phase 13 establishes history continuity across time, place, and cause by enabling entities to analyze past failure causes, compute dynamic time-related pressure urgencies, and map regional danger familiarity logs.

### 28.1 Core Components

* **TemporalModel**: Nested under `cognition.subjective.time` storing `DeadlineEntry`, `CooldownEntry`, `StalenessEntry`, and `DelayRiskEntry` metrics to represent dynamic temporal limits.
* **CausalMemory**: Bounded container under `cognition.memory.causal` storing `CausalMemoryEntry` records which represent subjective attribution analysis and future plans after failed events (such as combat losses or failed search actions).
* **SpatialMemory**: Nested under `cognition.memory.spatial` keeping `RegionVisitMemory`, `RouteMemory`, `ResourceSiteMemory`, and `FailedSearchMemory` records detailing regional safety/danger logs and familiarity deltas.

* **TemporalPressureService**: Processes active deadlines, cooldowns, and stale items to derive urgency factors (0.0 to 1.0) dynamically.
* **CausalAttributionService**: Attributes specific causes (such as low health or damaged weapons) and lists of recommendations after simulation failure triggers.
* **SpatialMemoryUpdateService**: Increments visit counts and maps hazard safety variables.
* **MemoryUpdatePhase**: Integrates temporal calculations and attribution updates inside the authoritative tick sequence.


## Section 29: Phase 14 — Motivation / Doctrine / Role-Fit Domain

Phase 14 prevents entities from converging on identical strategic decisions by introducing long-term identity preference profiles, class-specific doctrines, weapon/armor role evaluations, and value-based cognitive biases.


### 29.1 Core Components

* **IdentityDoctrine**: Stored under `cognition.motivation.doctrine`, defining class preferred/avoided tags, combat biases, and cooperation preferences.
* **ValuePreferenceProfile**: Nested under `cognition.motivation.values` storing survival, reward, knowledge, loyalty, pride, curiosity, and caution parameters.
* **RoleFitPreference**: Nested under `cognition.motivation.role_fit` holding specific weapon, armor, skill, party role, and quest tags mapping.


* **DoctrineResolver**: Yields class preference profiles based on actor types (`warrior` -> prefers melee/heavy armor; `ranger` -> prefers ranged/scouting; `mage` -> prefers spells/intel).
* **RoleFitEvaluator**: Computes suitability scores for equipment, skills, party roles, and quests against structural doctrine preferences.
* **MotivationBiasService**: Applies cognitive values and doctrine preferences as stable multiplier modifiers for strategic route evaluation.


## Section 30: Phase 15 — Commitment / Obligation / Reputation Domain

Phase 15 makes accepted commitments (escort quests, lone contracts, group duties) and public reputation affect entity behavior, preventing immediate greedy route switches and establishing clear social consequences for betrayal.

### 30.1 Core Components

* **CommitmentEntry**: Stored under `cognition.commitment.active_commitments` detailing quest/contract obligation parameters (id, strength, deadline_tick, created_tick).
* **PublicReputationProfile**: Stored under `cognition.relationships.public_reputation` representing public labels (reliable, heroic, betrayer) and witnessed event logs.


* **CommitmentPressureService**: Computes pressure (0.0 to 1.0) to hold or fulfill active commitments, scaled down under critical health scenarios.
* **AbandonmentEvaluator**: Distinguishes valid survival choices from greedy betrayal during combat.
* **ReputationUpdateService**: Processes witnessed events to incrementally evolve public labels.
* **CommitmentReputationRouteImpact**: Applies commitment route boosts and reputation penalties (e.g. Fit score penalties for betrayers) as scoring modifiers.


## Section 31: Phase 16 — Emotion / Recovery / Habit / Opportunity Cost Domain

Phase 16 integrates short-term emotional biases, recovery states, learned habits, and explicit trade-off reasoning into entities to make them less robotic and more realistic.

### 31.1 Core Components

* **EmotionalModel**: Stored under `cognition.subjective.emotion` containing short-term emotional variables (fear, confidence, frustration, curiosity, satisfaction, panic, boredom).
* **RecoveryState**: Stored under `cognition.subjective.self.recovery` detailing recovery metrics (recent_near_death, confidence_loss, retry_readiness, recovery_until_tick, trauma_tags).
* **HabitMemory**: Stored under `cognition.memory.habit` keeping a map of action success and failure patterns.


* **EmotionUpdateService**: Adjusts active emotional metrics based on combat, goals, and exploration outcomes.
* **RecoveryReadinessService**: Evaluates whether an entity is ready to retry a challenge or must recover first.
* **HabitBiasService**: Scales route scores based on past successful/failed habit patterns.
* **OpportunityCostEvaluator**: Computes trade-off costs to prevent poor strategic decisions.


## Section 32: Phase 17 — Derived Views / Decision Trace Contract

Phase 17 standardizes complex strategic and tactical transparency by defining purely computed derived views (no core state storage) and a unified, validated decision-tracing pipeline to ensure every entity behavior is fully debuggable from perception to outcome.

### 32.1 Core Components


* **DerivedReadinessView**: Represents computed transient metrics (score, confidence, blocking/supporting factors, and source aspects) built on the fly for combat, adventure, and recovery.
* **DecisionTrace**: A structured trace record capturing what was noticed, known, needed, believed, considered, selected, and expected for any major cognitive domain decision.
* **DecisionTraceValidator**: Strictly validates structural completeness of emitted traces based on OFF, WARN, and STRICT modes.
* **CausalityChainReporter**: Compiles sequential links connecting perceived signals, decisions, action intents, and authoritative outcomes.


## Section 33: Phase 18 — Migration / Integration / Architecture Guardrails

Phase 18 establishes strict architectural boundaries, static linting safety checks, and formal deprecation plans to guarantee long-term maintainability of the `CognitionModel` nested mind hierarchy.

### 33.1 Core Components

* **Import Boundary Guard**: Static analysis test ensuring that core dataclass models (`src/core/`) never import downstream business or domain services.
* **Cognition Migration Linter**: Validates whitelisted flat aspects on `EntityState`, rejecting any unauthorized flat aspect pollution outside whitelisted caches or whitelisted standard components.
* **Domain Ownership Map**: Formally documents the binding between dynamic cognition sub-models and authoritative package directories.
* **Deprecation Guide**: Registers whitelisted backward-compatibility accessors and timelines for path removals in the upcoming releases.





