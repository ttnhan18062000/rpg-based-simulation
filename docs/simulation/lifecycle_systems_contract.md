---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-09-28
---

# Lifecycle Systems Contract

**Source:** `src/systems/lifecycle_systems/lifecycle.py`, `src/engine/apply.py` (`ApplyPath._compute_entity_changes`, passive branch), `src/systems/lifecycle_systems/genetics.py`
**Related docs:** [docs/mechanics/01_entity_anatomy.md](../mechanics/01_entity_anatomy.md) (P0 mechanics law parent), [docs/simulation/domains/adventure_contract.md](domains/adventure_contract.md) (biological pressure → routing)

---

## Purpose

Lifecycle systems govern the biological layer of entity existence: aging and death transitions, ongoing biological pressure accumulation, and innate genetic traits that modify attribute scaling. This is distinct from the progression layer (`src/progression/`) which handles XP, leveling, and skill advancement.

---

## Lifecycle — `lifecycle.py`

### Entity lifecycle states

Entities have two lifecycle flags rather than a state enum:
- `entity.lifecycle.active` — whether the entity is alive and simulation-active
- `entity.lifecycle.is_permadeath_set` — whether the entity has died (cannot be revived)

An inactive entity (`active=False`) is removed from tick processing. Death is permanent.

### Death triggers

`LifecycleSystem.resolve_lifecycle()` detects deaths each tick:

| Trigger | Condition | death_reason |
|---|---|---|
| Old age | `age_ticks >= max_age_ticks` | "OLD_AGE" |
| Combat death | EntityUpdate with `combat.outcome_kind == "KILL"` | "COMBAT" |
| Terminal defeat | EntityUpdate with `combat.outcome_kind == "DEFEAT"` (non-lethal zeroing) | "DEFEAT" |
| Hazard death | EntityUpdate with `combat.outcome_kind == "HAZARD"` and `combat.alive_set is False` (regional hazard drain itself took HP to 0, no terminal combat outcome already held the slot) | "HAZARD" |
| Passive biological death | persisted `lifecycle.passive_death_cause` (written by the passive drain on the tick HP reached zero) | `"STARVATION"` / `"SLEEP_DEPRIVATION"` |

Same-tick attribution (Mechanics Bible 01 §4): the first cause in phase order whose own effect reached 0 HP
wins -- `WorldDynamicsSystem` never overwrites a terminal combat outcome (`TERMINAL_COMBAT_OUTCOME_KINDS`) and
carries the drain independently in `CombatUpdate.hazard_damage`.

The DEFEAT, HAZARD and passive branches share one idempotency guard: an entity that already carries a
`death_reason` or `is_permadeath` is never classified by them again (a cross-tick property, not branch
ordering). They read persisted typed facts only -- never `hunger`/`sleep_debt` thresholds or role
(LIMIT-04). **Declared precedence: hunger outranks sleep debt as a recorded cause of death** when both
thresholds hold on the fatal tick; this is a declared rule, not derived from the damage magnitudes.
A passive cause is cleared once a different `death_reason` is recorded (it is never reported for that
entity). `resolve_lifecycle` is the sole authority for HP-death deactivation, exactly as for old age.

On death:
1. `active = False`
2. `is_permadeath_set = True`
3. `death_tick_set = state.tick`
4. `death_reason_set` populated
5. Succession processing (if `heir_entity_id` is set)
6. Influence shift processing (via `FactionInfluenceService.process_influence_shift()`)
7. Conquest lifecycle evaluation (stronghold spawn/removal)

### Declared authority for `lifecycle.active` (TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE)

Two writers touch `entity.lifecycle.active` each tick: `resolve_lifecycle`'s OLD_AGE branch above,
and `ApplyPath._compute_entity_changes`'s passive branch (`src/engine/apply.py:94-110`), which
increments `age_ticks` and recomputes `active` every `is_life_due` tick as part of the same passive
decay pass that also drains HP from hunger/sleep-debt. Before this ticket, the passive branch
independently computed `active=(new_hp > 0 and new_age < life.max_age_ticks)`, so on the exact tick
an entity's `age_ticks` first reached `max_age_ticks`, the passive branch deactivated it a tick
*before* `resolve_lifecycle` (which runs against the pre-tick snapshot) ever got a chance to record
`death_reason="OLD_AGE"` — and once `active` was `False`, `resolve_lifecycle`'s own
`if not entity.lifecycle.active: continue` guard skipped the entity forever, so the death was never
observed and no lineage consequence ever dispatched.

**Resolution rule: `resolve_lifecycle` is the sole declared authority for old-age AND HP-death
deactivation** (the HP half completed by TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER,
`intentional_divergences.md` §2.61). The passive branch's formula is now
`active=(life.active or (new_hp > 0 and new_age < life.max_age_ticks and no death record))` — it never
deactivates; its only `active` write is the construction-time `initial_active=False` spawn
reactivation, which must exclude zero-HP and already-dead entities (a bare
`life.active or new_age < max_age` is True for every dead young entity and would resurrect each
corpse). Deactivation of an aged-out or HP-zero entity is `resolve_lifecycle`'s job alone, one kernel
step later. This is a real, documented, determinism-visible one-tick shift in when an
old-age death is recorded — see `docs/guidelines/intentional_divergences.md` §2.59. When
`life.active` is already `False` (a dead entity, or an `initial_active=False` construction-time
spawn that has not yet been reactivated), the formula reduces to exactly the pre-fix expression, so
that path is unchanged.

### Succession and heirlooms

If `entity.lifecycle.heir_entity_id` is set, the deceased entity's inventory and designated heirlooms transfer to the heir via `ResourceTransferIntent` (source_kind="CHEST"). This is a transactional transfer — if the heir's inventory is full, the transfer may partially fail per the atomic conservation law.

The deceased entity's `inventory.items` is normalized to `list` before combining with the
heirloom stacks (`list(entity.inventory.items) + heirloom_stacks`) — `items` is a `list` on a
live/authoritative entity but a `tuple` when the entity passed in is a `to_readonly()` view
(`src/core/state.py`'s immutability optimization); concatenating a tuple with a list raises
`TypeError` (fixed by `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`, a pre-existing
bug from 2026-05-18 only newly exposed by increased death frequency post-navigation-fix).

### Engine phase

`LifecycleSystem.resolve_lifecycle()` runs inside the authoritative apply pipeline. It receives the `StateUpdate` from workers and returns a refined `StateUpdate` with death processing added.

---

## Biological — `ApplyPath._compute_entity_changes` (`src/engine/apply.py`)

Biological pressure accumulation runs inline in the authoritative apply path's passive branch,
gated by cadence (`is_bio_due`), not as a separate system module. **Corrected 2026-09-11**: this
section previously described `BiologicalSystem.update()` (`src/systems/lifecycle_systems/
biological.py`), a parallel implementation that was never wired into the pipeline and has been
deleted as confirmed dead code (`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`) — its
decay rates and thresholds had drifted from the real live values below, so the two were never
interchangeable.

### Applies to

All entity kinds with `entity.lifecycle.active` true (or due for a lifecycle tick) — `biological`
is a default-populated component on every `EntityState`, and `_compute_entity_changes` applies no
kind filter. This is broader than the deleted `BiologicalSystem.update()`'s HERO/VILLAGER-only
gate; monsters and NPCs do accrue hunger/sleep-debt pressure in the live implementation.

### Biological pressure rates

Per Mechanics Bible [`01_entity_anatomy.md` §4](../mechanics/01_entity_anatomy.md#4-biological-laws-decay--needs)
(bit-identical parity, authoritative):

| Pressure | Rate (per tick, cadence-scaled) | Damage condition |
|---|---|---|
| Hunger | `+0.1 * cadence.biological` | `hunger >= 95.0` → HP −2 per lifecycle tick (starvation) |
| Sleep debt | `+0.05 * cadence.biological` | `sleep_debt >= 98.0` → HP −1 per lifecycle tick (exhaustion) |

Both pressures accumulate monotonically until the entity eats (resets hunger) or rests (resets sleep_debt). There is no passive decay of the pressures themselves — only of HP once a threshold is crossed.

**Passive HP death (TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER):** when this
passive HP loss drives `combat.hp` from positive to 0 the writer records
`lifecycle.passive_death_cause` (`STARVATION` if `hunger >= 95`, else `SLEEP_DEPRIVATION`) and
`passive_death_cause_tick`, and leaves `lifecycle.active` untouched. `resolve_lifecycle` reads the
cause on the next kernel step (refine runs before apply within a tick) and records the death with its
full succession dispatch. The cause is only written for an entity with no `death_reason` or
`is_permadeath`, and is cleared if another death is recorded first.

### Output

Folded directly into the same `StateUpdate`/entity `changes` dict `_compute_entity_changes`
produces for the tick — not a separate `EntityUpdate`. HP loss is applied via the same function's
lifecycle/health-decay branch (`combat.hp_delta` equivalent), gated by `is_life_due` cadence.

### Connection to need interpretation

High biological pressure → `src/cognition/need_interpretation.py` interprets the biological state into prioritized need signals. The motivation domain reads those signals to generate survival route biases (rest, gather food). See [docs/cognition/need_interpretation_contract.md](../cognition/need_interpretation_contract.md).

---

## Genetics — `genetics.py`

Compliance IDs: LEG-RPG-144, LEG-RPG-145

### GeneticProfile data model

```python
GeneticProfile:
    strength_mult: float      # 0.8 to 1.3
    agility_mult: float       # 0.8 to 1.3
    intelligence_mult: float  # 0.8 to 1.3
    wisdom_mult: float        # 0.8 to 1.3
    constitution_mult: float  # 0.8 to 1.3
    charisma_mult: float      # 0.8 to 1.3
```

All multipliers range 0.8–1.3. A multiplier of 1.0 is neutral. 1.3 means the entity has a 30% genetic advantage in that attribute.

### Assignment at spawn

`GeneticsSystem.generate_profile_from_seed(seed: int) -> GeneticProfile`

Seed is derived from the entity's spawn parameters. Uses MD5 hash of the seed string, extracting 6 two-byte hex offsets to generate 6 multipliers deterministically. Identical seeds produce identical profiles.

Genetic profiles are **permanent** — they do not change during simulation (no evolution or mutation during a run).

### Effect on attributes

`GeneticsSystem.apply_genetic_profile(base_stats, profile) -> effective_stats`

`effective_stat = base_stat × genetic_multiplier` per attribute. Effective stats (not base stats) are used in all downstream calculations: combat, skill scaling, progression.

### Assignment via parent combination (inheritance)

`GeneticsSystem.combine_profiles(parent_a: GeneticProfile, parent_b: GeneticProfile, *,
combat_lean: bool, seed: int) -> GeneticProfile`

A second, coexisting construction-time assignment mechanism (alongside `generate_profile_from_seed()`
above), for human/humanoid reproduction (idea 32). Per attribute: convex-combine the two parents'
multipliers (average), convex-blend that average with a `generate_profile_from_seed(seed)`
perturbation draw (0.6/0.4 weighting), then — only when `combat_lean` is `True` and the attribute
is `strength_mult`/`agility_mult`/`constitution_mult` — pull the blended value 35% of the remaining
distance toward the 1.3 ceiling. Every step is a convex combination of values already in
`[0.8, 1.3]`, or an explicit `min`/`max` clamp, so the result stays in range by construction —
satisfying Extension rule #2 below without an `intentional_divergences.md` entry.

`combat_lean` is `True` only when both parents' `IdentityComponent.role == EntityRole.HERO`; any
other parent-role pairing (civilian `CITIZEN`/`SHOPKEEPER`, `WORKER`/`GUARD`, or a mismatch
between them) falls through to the same neutral default — this is the general fallthrough, not a
rule scoped to `CITIZEN`/`SHOPKEEPER` alone.

`V2EntityBuilder.birth_record()` (`src/core/builder.py`) is this method's first real, live,
non-test caller: passing `parent_a_genetic_profile`/`parent_b_genetic_profile`/`parent_a_role`/
`parent_b_role` triggers `combine_profiles()` and writes the combined profile onto the new
entity's `LifecycleComponent.genetic_profile` via `LifecycleUpdate.genetic_profile_set` →
`LifecyclePatch.apply()` — the same authoritative write path as every other `LifecycleComponent`
field, never a direct mutation. The natural-creature and magical/demonic parentless spawn paths
never pass parent profiles, so `genetic_profile` stays `None` for those entities.

### Skill scaling by genetics

`SkillScalingSystem.compute_skill_power()` applies effective stats to skill power formulas:

| Skill type | Formula |
|---|---|
| PHYSICAL | `base × (1 + primary_stat / 100)` |
| MAGICAL | `base × (1 + primary_stat / 80 + secondary_stat / 200)` |
| ELEMENTAL | `base × (1 + primary_stat / 90) × 1.1` |
| HYBRID | `base × (1 + (primary + secondary) / 150)` |

---

## Genetics vs evolution boundary

| Layer | File | Scope |
|---|---|---|
| **Genetics** | `src/systems/lifecycle_systems/genetics.py` | Innate talent multipliers assigned at spawn; permanent |
| **Evolution** | `src/progression/evolution.py` | Permanent stat changes from milestone accomplishments (e.g., defeating 100 enemies unlocks an ATK bonus); applied via the progression system |

Genetics is a starting condition; evolution is earned progression. Both modify effective stats, but through different mechanisms and at different lifecycle points.

---

## Regression tests

- `tests/integration/world/test_long_run_stability.py` — death detection, succession, permadeath flag, influence shift on death
- `tests/integration/kernel/test_long_run_determinism.py` — hunger/sleep accumulation rates, HP damage at thresholds
- `tests/unit/worldgeneration/test_generator.py` — deterministic profile generation, multiplier range 0.8–1.3, skill power formulas

---

## Extension rules

1. To add a new biological pressure type (e.g., thirst): add a field to `BiologicalUpdate`, add accumulation logic in `BiologicalSystem.update()`, add a damage condition, add need interpretation handling in `src/cognition/need_interpretation.py`. Applies to HERO and VILLAGER kinds only unless explicitly extended.
2. To add a new genetic trait: extend `GeneticProfile` with a new multiplier field (default 1.0), extend `generate_profile_from_seed()` to compute it from the hash, extend `apply_genetic_profile()` to apply it. Multiplier range must stay 0.8–1.3 unless the trait is intentionally extreme (document in intentional_divergences.md).
3. To add a new death trigger: add detection logic in `LifecycleSystem.resolve_lifecycle()` with a new `death_reason` string. Always process succession and influence shifts on death regardless of reason.
4. Biological pressure accumulation must remain deterministic — never introduce randomness into hunger/sleep rates.
