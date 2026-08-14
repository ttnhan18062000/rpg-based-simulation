---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260808-ENTITY-EVENT-LEDGER
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260808-ENTITY-EVENT-LEDGER

## Docs Requiring Update

- `docs/event_ledger/entity.yaml`: the ledger itself (new file, Implement phase)
- `docs/simulation_quality/event_type_coverage.md`: cross-reference pointer (Implement phase)

## Two already-existing, exhaustive source-of-truth docs found — did most of this ticket's enumeration work already

1. **`docs/core/update_intents.md`** ("Entity-level intent taxonomy" table) — a complete, maintained
   enumeration of all 20 fields on `EntityUpdate` (the authoritative durable-state mutation bundle
   per entity), each mapped to its typed sub-intent, file/line, and purpose. This IS the
   authoritative source of truth this ticket needs for "every entity mutation type" — no need to
   re-derive it from scratch by reading `src/core/updates.py` field-by-field.
2. **`docs/simulation_quality/event_type_coverage.md`** — a Certified-Level-1 exhaustive catalog of
   every `event_type` the observability pipeline emits (scored, unscored-intentional, or
   emission-gap), ~95 entries. Covers what's OBSERVED, but is scoped to SimQ-relevant events only —
   does not itself audit "does every entity mutation type have ANY corresponding event."

This ticket's own real, new work: cross-reference these two docs against each other, entry by
entry, to find entity mutation types with NO corresponding event anywhere (not even
unscored-intentional) — a gap neither existing doc audits.

## Methodology correction found mid-investigation

Initial grep for intent-dataclass field names (`attributes_upd`, `biological_upd`, etc.) in
`event_extractor.py` returned zero matches for 8 of 20 mutation types — but this methodology was
initially ambiguous: `event_extractor.py` performs **post-tick state diffing** (confirmed this
session, `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own finding: "the entire
observability pipeline is built on post-tick diffing, not trigger-point emission"), so it reads
**state component field names** (`entity.attributes.strength`, `entity.navigation.position`), not
intent-object field names. Re-verified every candidate against the real `EntityState` component
field names (`src/core/state.py:664-679`: `interaction`, `identity`, `attributes`, `inventory`,
`strategic`, `social`, `biological`, `lifecycle`) before concluding silence — e.g.
`entity.navigation.position` IS read (confirmed, `event_extractor.py:221`, feeds the `movement`
event) even though the `NavigationUpdate` intent's own field name never appears.

## Confirmed silent mutation types (double-verified: intent-field AND state-field grep, both empty)

| Sub-intent | Fields | Verification |
|---|---|---|
| `AttributeUpdate` | STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA deltas | `grep -n "\.attributes\.\|\.strength\b\|\.agility\b" event_extractor.py` — 0 matches |
| `BiologicalUpdate` | sleep debt, hunger, rest pressure, meal/sleep stamps | `grep -n "\.biological\."` — 0 matches |
| `EquipmentUpdate` | slot assignments, durability delta/set | `grep -n "\.equipment\.\|equip_slots\|equipped_"` — 0 matches |
| `StaminaUpdate` | current/max stamina | `grep -n "\.stamina\b\|current_stamina\|max_stamina"` — 0 matches |
| `WoundUpdate` | new wounds, heals, scars | `grep -n "\.wounds\b\|wound_state\|scars"` — 0 matches |
| `TaskUpdate` | work kind, payload | `grep -n "\.task\.\|work_kind"` — 0 matches |

## Confirmed partial mutation types (some fields observed, others not)

| Sub-intent | Observed fields | Silent fields |
|---|---|---|
| `NavigationUpdate` | `position` → `movement` event (event_extractor.py:221) | congestion counters, region ID (`grep -n "congestion\|\.navigation\."` finds only `.navigation.position`) |
| `IdentityUpdate` | `learned_skills`/`traits`/`active_breakthroughs`/`evolution_level` diffs → `skill_unlocked`/`trait_expressed`/`pillar_trait_unlocked`/`level_up` | `role`/`faction` reassignment, recipes, cooldowns — `grep -n "\.role\b\|\.faction\b\|role_set\|faction_set"` — 0 matches |
| `SocialUpdate` | trust (`social_memory_created`), reputation (`reputation_delta`), contracts (`contract_*` events) | familiarity, fear, grudge, nemesis — not confirmed observed by any event in `event_type_coverage.md` |
| `LifecycleUpdate` | death/despawn/spawn → `lifecycle` event (translated to `entity_killed`/passthrough) | age_delta accumulation, heir designation, heirloom transfer — no corresponding event found |
| `InteractionUpdate` | harvest completion → `resource_harvested` | multi-tick `progress_delta` itself — no per-tick progress event |

## Not silent (well-covered, cross-referenced against `event_type_coverage.md` §1)

`CombatUpdate` (extensive: `combat_damage`/`combat_initiated`/`near_death_survival`/`combat_kill`→`entity_killed`/`hazard_drain_applied`/`combat_hard_law_violation`), `QuestUpdate`, `RewardUpdate`
(`xp_granted`), `StrategicUpdate` (extensive: `Strategic*` translated events, `belief_*`, `lead_*`),
`group_id_set` (`group_joined`/`group_expelled`), `self_model_bundle_set` (`self_model_updated`),
`resource_transfers`/`inventory` (indirectly via `shop_transaction`/`trade_executed`/
`quest_reward_dispensed`/`gold_sink_fired`).

`intent_results` and `property_updates` excluded from this audit — the former is explicitly
non-durable feedback (`docs/core/update_intents.md`'s own note: "not applied to durable state"),
the latter is a generic catch-all too broad to meaningfully classify as observed/silent.
