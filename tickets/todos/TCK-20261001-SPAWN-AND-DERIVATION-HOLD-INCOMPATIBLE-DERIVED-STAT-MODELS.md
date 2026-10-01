---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS
phase: open
date: 2026-10-01
tags: [simulation-quality, progression, combat, architecture]
---

# TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS

## Title
Spawn and the combat-stat derivation hold incompatible models of the derived-stat set, not just of
the base value — so the derivation cannot be safely activated, and "the recalc never fires" is
load-bearing rather than incidental

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found by `rpg-implementer` while implementing
`TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`, by **measuring** that ticket's
plan's value-neutrality claim per-field across three compiled worlds (seed 42) instead of
accepting it. The claim held for `max_hp`/`atk`/`evasion` and **failed for three other derived
fields**. This ticket exists because that is a separate, larger defect than the base-stat erosion,
and because it is the reason the base-stat ticket had to be narrowed.

`LevelingService.recalculate_combat_stats` (`src/progression/leveling.py:76-175`) derives a **set**
of combat stats: `max_hp`, `atk`, `def_stat`, `evasion`, `readiness_speed`, `move_cost`,
`atk_range`, `tactical_role`. The spawn path populates only *some* of these from declared content,
leaves others at component defaults, and sources at least one from a different place entirely than
the derivation does. **The two paths do not model the same thing**, so running the derivation over a
spawned entity silently rewrites fields that spawn had set from content — or had deliberately left
alone.

Measured drift (every entity in `frontier_living_world`, `crowded_frontier`,
`quest_dense_frontier`, seed 42, residual bases computed from spawn `combat` + `attributes`, then
`SkillScalingService.get_effective_stats` diffed per field against the spawn value):

| field | spawn source | derivation source | measured drift |
|---|---|---|---|
| `max_hp`, `atk`, `evasion` | stat profile | base + attributes + gear | **none** (residual reconciles exactly) |
| `move_cost` | **`CombatComponent` default `10.0`** (`src/core/state.py:407`) — spawn never sets it | `10.0 + weight/5 − agility*0.1`, floor `5.0` | `10.0 → 9.5` for **every entity** (2/2, 49/49, 38/38) |
| `atk_range` | stat profile `attack_range` | **main-hand weapon property only**, else `1` | `3 → 1` for the `scout` kind in two worlds |
| `def_stat` | stat profile | base + `int(vitality*0.3)` | `worker` spawns `def 0` at `vitality 5`, so the residual is `-1`; under a clamp-at-zero it becomes `0 → 1` (8 and 11 entities) |
| `readiness_speed`, `tactical_role` | — | — | no drift in these worlds (not proof of none in general) |

**The `atk_range` case is the severe one, and it is wider than the measurement showed.** Five
profiles in `data/content/entities/stat_profiles.yaml` declare a non-melee `attack_range`:
`goblin_archer_base` (3), `apprentice_mage_base` (3), `ranger_base` (3), `spirit_guardian_base` (2),
`dragon_champion_base` (3). Because the derivation sources `atk_range` only from a main-hand weapon
property and otherwise returns `1`, activating the derivation would **silently turn every declared
ranged archetype in the catalog into a melee unit**. The measurement caught two scouts; the catalog
says the blast radius is the whole ranged roster.

**Consequence worth stating plainly: the fact that `stats_dirty` never fires in corpus play is
currently load-bearing, not incidental.** It is the only thing preventing the drifts above. Any
future change that makes the recalculation reachable — including the obvious-looking one of adding a
new trigger — ships a gameplay change unless this ticket lands first. That inverts how the
`STATS-DIRTY-RECALC` ticket originally framed the unreached path: it is not merely a latent defect
waiting to be fixed, it is a latent defect whose *dormancy is load-bearing*.

## Scope
1. Decide, per derived field, which path is authoritative — the declared stat profile or the
   derivation — and record the decision. These are **not** all the same answer: `move_cost` has no
   declared content value at all today, while `atk_range` has one that the derivation ignores.
2. For each field where content is authoritative, make the derivation reproduce the spawned value
   (residual-style base terms, as `STATS-DIRTY-RECALC` does for the first four, or by sourcing the
   declared value directly).
3. For each field where the derivation is authoritative, decide whether spawn should run the
   derivation rather than assigning content values — and declare the resulting value change.
4. `atk_range` specifically: reconcile the profile's `attack_range` with the weapon-property-only
   derivation. A ranged archetype with no main-hand weapon is the case that breaks today.
5. Only once 1-4 hold can the full derivation be safely activated. State that as the exit condition.

## Out of Scope
- The species base-stat erosion for `max_hp`/`atk`/`def_stat`/`evasion` and the permanent-grant
  accumulator — owned by `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`.
- `CoreActions.execute_allocate_ap`'s double-count — dormant by `DEV-004`, which owns it.
- Flipping `ENABLE_PROGRESSION_EVOLUTION`.

## Acceptance Criteria
1. A recorded per-field authority decision for every field `recalculate_combat_stats` returns.
2. A test asserting the derivation reproduces the spawn value for every entity across the three
   corpus worlds, for every field declared content-authoritative — i.e. the generalisation of
   `STATS-DIRTY-RECALC`'s round-trip test from four fields to the whole set.
3. A declared `docs/guidelines/intentional_divergences.md` entry for any field whose value
   intentionally changes, with a rationale class.
4. The ranged-archetype case is covered: a `ranger_base`/`goblin_archer_base` entity does not lose
   its declared range when the derivation runs.
5. The exit condition from Scope 5 is stated explicitly, so a later ticket knows when activation is
   safe.
6. **A guard test or explicit tripwire, not prose.** "`stats_dirty` never firing is load-bearing" is a
   **hazard**, not just a finding: any change that makes `stats_dirty` fire before this ticket lands
   triggers the measured field drift (`move_cost` on every entity; ranged archetypes made melee). A
   test must fail — loudly, naming this ticket — if the trigger set widens or the derivation becomes
   reachable while the per-field authority decisions (AC1) are still open. Required by the rule owner
   as a condition of accepting the interim OWN-01 position on the parent ticket; the prose framing
   alone is insufficient.

## Related Tickets
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` — parent; found during its
  implementation and narrowed because of this. Its `investigation.md` §2 establishes the
  spawn-is-final-value-vs-derivation-is-base-term mismatch that this ticket generalises.
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — prior investigation of the
  same code path from the reachability angle.

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` §2 — the derived-stat formulas of record
- `docs/world_rules/foundations/state-ownership.md` — OWN-01 (:23, ACCEPT), OWN-03; the
  single-writer/materialised-derivation basis
- `docs/guidelines/intentional_divergences.md` — where any declared value change lands

## Related Stored Artifacts
`stored_artifacts/TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS/investigation.md`
(§§2, 7) once that ticket closes.

## Related Code Areas
- `src/progression/leveling.py:76-175` (`recalculate_combat_stats`, all derived fields)
- `src/engine/rpg_depth.py:342-356` (`SkillScalingService.get_effective_stats`)
- `src/entities/contract_builder.py` / `src/core/builder.py` (spawn assignment of combat stats)
- `src/core/state.py:407` (`CombatComponent.move_cost` default)
- `data/content/entities/stat_profiles.yaml` (`attack_range` declarations)
- `src/engine/apply.py:595-623` (`stats_dirty` trigger set and call site)

## Assumptions / Open Questions
- Whether `move_cost` is *meant* to be content-declarable at all is open — no profile declares it
  today, so the derivation may simply be its only intended owner, making the `10.0 → 9.5` shift a
  latent correction rather than a regression. Not assumed either way.
- `readiness_speed` and `tactical_role` showed no drift in three worlds. That is **not** evidence
  they cannot drift — `tactical_role` has hysteresis logic (`leveling.py:166-175`) whose behaviour
  under a first-ever recalc has not been measured.
- Whether any live entity actually spawns as a ranged archetype in the three corpus worlds is **not
  measured**; the catalog declares five, which is sufficient to block activation regardless.

## Implementation Notes

### 2026-10-01 — Provenance narrowing introduced by the parent ticket's residual base (rule owner)

Recorded here at `world-rule-catalog-design`'s request, because it is a consequence of the parent
ticket that this ticket inherits rather than a defect in either.

The parent ticket's stored base is **`declared profile value − attribute contribution at spawn`**, not
the declared value itself. Combined with two existing facts — entities carry **no `stat_profile_id`
pointer** (`EntityState` has only `kind`; the resolved contract computes `archetype_id`/`species_id`
and discards both), and **attributes change after spawn** — the consequence is:

> **Once an entity's attributes move, its declared species stat is no longer recoverable from entity
> state.** The residual plus current attributes reconstructs the *current* derived value, not the
> original declared one.

**This is not a rule violation.** It is a **narrowing of what the base can answer**, and it is the
honest cost of the residual shape (which is itself required — see the parent's `investigation.md` §2;
storing the declared value directly would inflate every entity). Rated accordingly: a documented
limitation, not a defect.

**If anything needs "what was this entity's declared species stat?"** — the de-hero inventory's
"re-ground capability on real state" is the live candidate — **the clean answer is a typed
`stat_profile_id` stored at spawn**, not reconstructing it from the residual. Reconstruction would
require inverting the formula against *spawn-time* attributes that are themselves no longer stored, so
it is not merely awkward but impossible in general.

**Noted as an option, explicitly NOT new scope** for this ticket or the parent. Whoever needs the
declared value should file it.

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
