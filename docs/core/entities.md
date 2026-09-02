---
status: authoritative
layer: core
authority: P0
audience: developer
last_verified: 2026-09-02
---

# Entities & Factions: The Component-Based Model

In the WorldLoop RPG, every agent (Heroes, Monsters, Shopkeepers, Citizens, Workers, Guards) is
represented by an `EntityState` — a single frozen, composed object, not a shell class wrapping
separate sub-objects. Entities are built from typed, independently-declared **Components**
(each `@dataclass(frozen=True, slots=True)`), the same Component Composition Pattern
`docs/core/state.md` describes for `AuthoritativeState` as a whole.

---

## 1. The EntityState Atom

`EntityState` (`src/core/state.py:723-961`, `@dataclass(frozen=True, slots=True)`) is the real
authoritative entity atom. There is no separate `Entity` shell class — `src/core/` has no
`entities/` subdirectory at all; `EntityState` itself is both the identity and the container for
every component listed below.

### Core Properties
- **`id: int`** (`state.py:726`) — a unique, monotonic integer assigned at creation. See
  "Entity Construction" below for where this actually comes from.
- **`kind: str`** (`state.py:727`) — the archetype string (e.g. `"hero"`).

All `EntityState` mutation flows through the same frozen-state apply path described in
`docs/core/state.md`'s "Frozen Lifecycle" Law — see that doc for the snapshot → deliberation →
refinement → transition sequence via `AuthoritativeState.apply()`. This doc does not repeat that
sequence; it focuses on what an entity *is composed of* and how it is spawned.

---

## 2. Component Composition

`EntityState` composes 16 typed component fields, declared in this order
(`state.py:731-748`):

| Component | Defined In | Key Fields |
| :--- | :--- | :--- |
| **interaction** | `InteractionComponent`, `state.py:401-420` | `target_node_id`, `progress`, `start_tick`, `kind` (`"harvest"`/`"ground_item"`/`"corpse"`/`"chest"`/`"guild"`/`"inn"`/`"tavern"`) |
| **identity** | `IdentityComponent`, `state.py:483-527` | `role`, `faction`, and more — see "Identity" below |
| **attributes** | `AttributeComponent`, `state.py:451-480` | 9 primary stat ints (`strength`, `agility`, `vitality`, `endurance`, `intelligence`, `spirit`, `wisdom`, `perception`, `charisma`) — see `docs/core/attributes_and_classes.md` for the full attribute model |
| **inventory** | `InventoryComponent`, `src/core/models/inventory.py` (imported at `state.py:16`, not defined inline in `state.py`) | `max_slots`, `items`, `gold` |
| **strategic** | `StrategicComponent`, `src/core/strategic.py:382-416` | `home_region_id`, `blockers`, `leads`, `directives`, `projects`, `concerns`, `beliefs`, `profile` (`CognitionProfile`) |
| **social** | `SocialComponent`, `src/core/models/social.py` (imported at `state.py:17`, not defined inline in `state.py`) | trust/familiarity/fear/grudge history, `bonds`, `betrayal_count`, `public_reputation`, `heroism_score`, `notoriety_score` |
| **biological** | `BiologicalComponent`, `state.py:124-147` | `sleep_debt`, `hunger`, `rest_pressure`, `last_meal_tick`, `last_sleep_tick`, `well_rested_until` |
| **lifecycle** | `LifecycleComponent`, `state.py:152-193` | `age_ticks`, `max_age_ticks`, `is_permadeath`, `death_tick`, `death_reason`, `generation`, `heir_entity_id`, `heirlooms`, `parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, `reproduction_cooldowns`, `active`, `genetic_profile` |
| **aptitude** | `AptitudeComponent`, `state.py:529-562` | 9 per-stat growth multipliers — see "Aptitudes" below |
| **combat** | `CombatComponent`, `state.py:305-350` | `hp`, `max_hp`, `atk`, `def_stat`, `speed`, `range`, `evasion`, `tactical_role`, `alive`, `readiness`, `wounds`, `scars`, `status_effects` |
| **equipment** | `EquipmentComponent`, `state.py:706-710` | `slots: Dict[EquipSlot, str \| None]`, `durability: Dict[EquipSlot, float]` |
| **navigation** | `NavigationComponent`, `state.py:368-391` | `position`, `target`, `path`, `movement_mode`, congestion-recovery fields (`wait_count`, `oscillation_count`, `last_position`), leash fields (`home_position`, `leash_radius`) |
| **task** | `TaskComponent`, `state.py:394-398` | `work_kind`, `payload` |
| **stamina** | `StaminaComponent`, `state.py:56-86` | `current`, `max_stamina`, `regen_rate`, `rest_regen_rate`, `exhaustion_threshold`, `exhaustion_penalty` |
| **self_model** | `SelfModelBundle`, `src/core/self_model.py:211-244` (imported at `state.py:19`) | `self_awareness`, `needs`, `capabilities`, `knowledge` — 4 sub-components, each its own `@dataclass(frozen=True, slots=True)` |
| **cognition** | `CognitionModel`, `src/core/cognition.py:548-566` (imported at `state.py:20`) | `subjective`, `memory`, `motivation`, `commitment`, `relationships`, `role_model` |

`self_model` and `cognition` both participate in `EntityState.to_canonical_dict()`
(`state.py:810-811`), so they are canonically hashed durable state, not debug-only scratch data.

### Identity

`IdentityComponent` (`state.py:483-527`) holds an entity's role, faction, and knowledge/growth
state:

- **`role: int`** — an `EntityRole` value (`src/core/enums.py:6-12`): `HERO`, `SHOPKEEPER`,
  `MONSTER`, `CITIZEN`, `WORKER`, `GUARD`.
- **`faction: int`** — a `Faction` value; see "Factions" below.
- **`known_recipes`**, **`craft_target`** — crafting knowledge and current craft target.
- **`evolution_level`**, **`evolution_points`** — evolution progression state.
- **`veterancy_points`**, **`veterancy_rank`** — veterancy progression state.
- **`unspent_ap`** — attribute points available for allocation.
- **`class_id`** — the entity's class (`"NOVICE"` by default); see
  `docs/core/attributes_and_classes.md` for the class model.
- **`learned_skills`**, **`traits`**, **`active_breakthroughs`** — sets of unlocked
  skills/traits/breakthroughs.
- **`cooldowns`** — `skill_id -> tick when ready`.
- **`personality`** — a nested `PersonalityComponent` (`state.py:429-448`): `greed`, `bravery`,
  `sociability`, `industry`.
- **`life_stage`** — a `LifeStage` value (`state.py:423-427`): `CHILD`, `ADULT`, `ELDER`.
- **`group_id`** — the entity's current group/party, if any.
- **`territory_maturity`**, **`properties`** (free-form dict), **`latest_intent_results`** — round
  out the component's remaining real fields.

### Aptitudes

`AptitudeComponent` (`state.py:529-562`) holds 9 per-stat growth multipliers (`str_apt`,
`agi_apt`, `vit_apt`, `end_apt`, `int_apt`, `spi_apt`, `wis_apt`, `per_apt`, `cha_apt`) plus
`learning_rate` and `stamina_efficiency` — **all default to `1.0`**. There is no seed-driven
randomization of these values at entity creation; `EntityGenerator` and `V2EntityBuilder` (see
"Entity Construction" below) assign no aptitude randomization.

The real growth mechanism is `level_up_attributes()`, documented in
`docs/core/attributes_and_classes.md` §3 ("Level-Up Attribute Gains") and §3.5 ("Attribute Decay &
Aptitudes"): on level-up, all 9 primary attributes gain `+2`, modified by Aptitudes and capped — a
favored Aptitude gives `2.0x` training rate and `+2` level-up gain instead of the base rate.

Aptitudes do **not** affect attribute-point (AP) allocation gains. Per
`docs/parity_ledger/progression.yaml::PROG-069` (P0, `divergent`), `execute_allocate_ap`
(`src/engine/domain/core_actions.py`) applies AP spend as a flat delta with no aptitude lookup —
the only code that ever applied an aptitude multiplier to AP allocation
(`AllocateAttributeAction`, `src/actions/attributes.py:39-43`) was dead code, deleted per `DEV-004`
(`docs/guidelines/intentional_divergences.md`).

---

## 3. Factions

`Faction` (`src/core/enums.py:24-28`) is a 4-value `IntEnum`:

| Value | Meaning |
| :--- | :--- |
| `HERO_GUILD = 0` | |
| `MONSTER_HORDE = 1` | |
| `TOWN_COUNCIL = 2` | |
| `NEUTRAL = 3` | |

`IdentityComponent.faction` stores one of these values. `DiplomaticState`
(`src/core/enums.py:14-21`: `NEUTRAL`, `TENSE`, `HOSTILE`, `WAR`, `ALLIED`, `VASSAL`), imported
alongside `Faction` at `state.py:13`, is the real typed relationship state used between factions
(`FactionState.diplomatic_relations`, `state.py:629`).

---

## 4. Entity Construction

Entity IDs come from `EntityGenerator.get_next_id()` (`src/systems/world_systems/generator.py:30-32`)
— a simple monotonic counter (`self._last_id += 1`), used by `spawn_hero` and the monster-spawn
methods on the same class.

Entities are assembled via `V2EntityBuilder` (`src/core/builder.py:79-111`), whose `__init__`
instantiates all 16 components listed in the roster above (`identity`, `inventory`, `combat`,
`navigation`, `strategic`, `social`, `biological`, `lifecycle`, `attributes`, `aptitude`,
`equipment`, `interaction`, `task`, `stamina`, `self_model`, `cognition`).

`AuthoritativeState.__post_init__` (`state.py:1218-1263`) additionally guards `next_entity_id`
against collisions with any pre-existing integer entity keys already present in `entities`.

> [!IMPORTANT]
> All `EntityState` changes must flow through the authoritative apply path described in
> `docs/core/state.md`'s "Frozen Lifecycle" Law. Do not attempt ad-hoc field mutation outside the
> resolution phase.
