---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Motivation Domain Contract

**Source:** `src/domains/motivation/` (service.py, resolver.py, evaluator.py) + `src/world/motivation/pressure_resolver.py`  
**Pipeline phase:** No dedicated phase — runs inline as a scoring utility called by other phases. World-side pressure resolution (`MotivationPressureResolver`) runs upstream before domain phases.  
**Authoritative status:** Pure scoring utility — produces no `EntityUpdate` or `StateUpdate`. All outputs are return values consumed by callers.

---

## Purpose

The motivation domain interprets an entity's **drive profile** and **class doctrine** into concrete scoring inputs used by other domains. It answers two questions:

1. *What does this entity's class naturally prefer or avoid?* (DoctrineResolver)
2. *How strongly does this entity's value profile bias a given route tag set?* (MotivationBiasService)

It also evaluates equipment, skill, role, and quest tag overlap against a stored preference profile (RoleFitEvaluator). None of these produce durable state — they return floats and typed records consumed by callers in the same tick.

---

## Engine Phase

**No dedicated phase.** This domain is a library of scoring utilities:

- `MotivationBiasService.compute_bias_multiplier()` is called inline by the adventure domain during route scoring (Phase 3) and by the cooperation domain during partner-fit scoring.
- `DoctrineResolver.resolve()` is called by the commitment domain to apply class-specific abandonment rules.
- `RoleFitEvaluator` is called by the progression domain's growth gap evaluator to assess what equipment or skills match the entity's role preference.

**World-side backing:** `MotivationPressureResolver` (`src/world/motivation/pressure_resolver.py`) runs **upstream** of all domain phases. It converts catalog `need_profile_id` / `drive_profile_id` into a `MotivationPressureSet` (8 normalized pressure dimensions) and writes the result into entity `need_profile` / `drive_profile` state. That state is what motivation domain services subsequently read.

---

## What It Owns

- **Drive profile interpretation**: translating `need_profile_id` / `drive_profile_id` catalog references into actionable scoring inputs
- **Routing bias multipliers**: the float multiplier returned by `MotivationBiasService` that modulates adventure route scores
- **Doctrine definitions**: the `IdentityDoctrine` records produced by `DoctrineResolver` for warrior, ranger, mage, and the default fallback

The motivation domain does **not** own entity state, the need_profile/drive_profile fields themselves, or any durable record. It is a read-and-compute layer only.

---

## What It Reads

| Field | Source | Purpose |
|---|---|---|
| `entity.identity.class_id` | EntityState | Input to `DoctrineResolver.resolve()` |
| `entity.cognition.motivation.doctrine` | EntityState | `preferred_route_tags`, `avoided_route_tags` read by `MotivationBiasService` |
| `entity.cognition.motivation.values` | EntityState | `survival`, `pride`, `curiosity`, `reward` value profile read by `MotivationBiasService` |
| `entity.cognition.motivation.role_fit_preference` | EntityState | Weapon, armor, skill, party role, quest tag preference maps read by `RoleFitEvaluator` |
| `entity.identity.properties["need_profile_id"]` | Catalog reference | Resolved upstream by `MotivationPressureResolver` |
| `entity.identity.properties["drive_profile_id"]` | Catalog reference | Resolved upstream by `MotivationPressureResolver` |

---

## Three Utility Services

### 1. DoctrineResolver (`resolver.py`)

Maps `class_id` → `IdentityDoctrine`. The doctrine carries four fields:

| Field | Type | Meaning |
|---|---|---|
| `preferred_route_tags` | `dict[str, float]` | Tags that increase bias multiplier |
| `avoided_route_tags` | `dict[str, float]` | Tags that decrease bias multiplier |
| `combat_style_bias` | `dict[str, float]` | Preferred combat approach (consumed by combat domain) |
| `cooperation_bias` | `dict[str, float]` | Solo vs. party preference weights |

**Defined doctrines:**

| Class | Preferred tags | Avoided tags | Cooperation bias |
|---|---|---|---|
| `warrior` | melee +0.5, heavy_armor +0.4, combat +0.3 | ranged −0.5, spells −0.6, flee −0.3 | solo −0.1, party +0.2 |
| `ranger` | ranged +0.6, scouting +0.5, stealth +0.4 | heavy_armor −0.5, melee −0.2 | solo +0.3, party −0.1 |
| `mage` | spells +0.7, intel +0.5, mana +0.4 | heavy_armor −0.7, melee −0.5 | solo 0.0, party +0.3 |
| default | All fields empty | — | neutral |

Case-insensitive match on `class_id`. Unknown class IDs fall through to the default (empty doctrine).

### 2. RoleFitEvaluator (`evaluator.py`)

Computes tag-overlap scores between a `RoleFitPreference` and actual item/skill/role tags. Returns a raw float — higher is a better fit.

| Method | Evaluates |
|---|---|
| `evaluate_weapon(preference, tags)` | Weapon tag overlap against `preference.weapon_tags` |
| `evaluate_armor(preference, tags)` | Armor tag overlap against `preference.armor_tags` |
| `evaluate_skill(preference, tags)` | Skill tag overlap against `preference.skill_tags` |
| `evaluate_party_role(preference, role)` | Single role lookup in `preference.party_role_tags` |
| `evaluate_quest(preference, tags)` | Quest tag overlap against `preference.quest_tags` |

All methods delegate to `evaluate_tags(preference_map, tags)` — a simple sum of matched weights. No minimum clamp; can return 0.0.

### 3. MotivationBiasService (`service.py`)

`compute_bias_multiplier(entity, tags) → float`

Starting from `multiplier = 1.0`, applies two adjustment layers:

**Layer 1 — Doctrine tags:**
```
for tag in tags:
    if tag in preferred_route_tags:  multiplier += preferred_route_tags[tag]
    if tag in avoided_route_tags:    multiplier -= avoided_route_tags[tag]
```

**Layer 2 — Value profile adjustments:**

| Tag set | Value dimension | Adjustment |
|---|---|---|
| `recovery`, `flee`, `caution` | `values.survival` | `+(survival - 0.5) × 0.5` |
| `cooperation`, `help`, `party` | `values.pride` | `-(pride - 0.5) × 0.5` |
| `exploration`, `research`, `intel`, `knowledge` | `values.curiosity` | `+(curiosity - 0.5) × 0.5` |
| `gold`, `chest`, `loot`, `reward` | `values.reward` | `+(reward - 0.5) × 0.5` |

**Floor:** `max(0.1, multiplier)` — the multiplier never goes below 0.1, preventing complete suppression.

---

## World-Side Backing: MotivationPressureResolver

`src/world/motivation/pressure_resolver.py` — runs upstream of all domain phases.

Converts catalog `need_profile_id` and `drive_profile_id` into a `MotivationPressureSet` of 8 normalized dimensions. The resolved pressure set is written into entity `need_profile` / `drive_profile` state, which the motivation domain services subsequently read at scoring time.

This resolver is **not** part of `src/domains/motivation/` — it lives in `src/world/motivation/` and is part of the world-side preparation pipeline. Agents searching for "how motivation pressures are computed" should inspect `src/world/motivation/pressure_resolver.py`, not the domain services.

---

## Decisions Made

**None.** The motivation domain does not select routes, assign projects, or trigger any action. It produces scoring inputs — multipliers, tag-overlap floats, and doctrine records — that calling domains incorporate into their own decision logic.

---

## What It May Mutate

**Nothing.** This domain produces no `EntityUpdate` or `StateUpdate`. All outputs are return values (floats, dataclass instances) held in the calling phase's local scope and consumed within the same tick.

---

## What It Must NOT Mutate

- Entity state of any kind (`identity`, `cognition`, `strategic`, `combat`, `inventory`)
- World state (regions, resources, ecology)
- `need_profile` or `drive_profile` fields (those are written by `MotivationPressureResolver`, not by this domain)
- Any durable record or registry

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Adventure** | `MotivationBiasService.compute_bias_multiplier()` is called during route scoring (Phase 3); the returned multiplier is applied to the adventure score formula |
| **Cooperation** | `MotivationBiasService` is called during partner-fit scoring; `DoctrineResolver` cooperation_bias values inform the cooperation domain's affinity calculation |
| **Commitment** | `DoctrineResolver` outputs inform abandonment rules — class doctrine determines which routes a committed entity may abandon or sustain |
| **Progression** | `RoleFitEvaluator` is called by the growth gap evaluator to assess whether available items or skills match the entity's role-fit preference |
| **World motivation** | `MotivationPressureResolver` (`src/world/motivation/`) runs upstream and populates entity `need_profile` / `drive_profile` — the state this domain reads |

---

## Test Protection

Primary test targets:

```
grep -r "MotivationBiasService\|DoctrineResolver\|RoleFitEvaluator\|pressure_resolver\|MotivationPressureSet" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| DoctrineResolver returns correct doctrine for warrior / ranger / mage | Yes |
| DoctrineResolver unknown class_id → empty default doctrine | Yes |
| MotivationBiasService multiplier floor at 0.1 for high-avoided tag sets | Yes |
| Value profile adjustments move multiplier in correct direction | Yes |
| RoleFitEvaluator returns 0.0 for zero matching tags | Yes |
| MotivationPressureResolver produces normalized 8-dimension set from profile IDs | Yes |

---

## Extension Rules

**To add a new doctrine class:**
Add a new `elif class_id_lower == "<class>"` branch in `DoctrineResolver.resolve()` returning a fully-specified `IdentityDoctrine`. Add a test asserting the correct tags and biases. No mutation pipeline changes required — doctrine is a computed return value.

**To add a new value dimension:**
Extend the `values` model and add a corresponding tag set + adjustment clause in `MotivationBiasService.compute_bias_multiplier()`. Update `MotivationPressureResolver` if the new dimension maps to a pressure input. Add tests.

**To add a new pressure dimension:**
Extend `MotivationPressureSet` in the world-side pressure resolver and update `MotivationPressureResolver` normalization logic. This does not change domain service code unless a new scoring tag is also needed.

**Never add durable writes to this domain.** Motivation is a pure scoring utility. Any behaviour that requires persisting a decision belongs in a different domain with a typed intent path.
