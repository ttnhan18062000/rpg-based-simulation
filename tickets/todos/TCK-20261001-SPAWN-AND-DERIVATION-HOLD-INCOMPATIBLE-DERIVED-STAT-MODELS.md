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

### 2026-10-02 — PARKED by user direction, with AC1 already discharged

**Parked**, per the user's 2026-10-02 direction to fix only hard RPG bugs, defer balance and feature
work, and complete the registry/rule map/foundation before planning RPG feature implementation. This
is a dormant-path parity gap, not a hard bug (no wrong world truth in corpus play — the derivation
does not run), and AC6's tripwire requirement is what makes waiting safe rather than lucky.

**AC1 is nonetheless discharged** — do not redo it on resume. Full record with every citation
verified at `origin/main` in
`staging_artifacts/TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS/investigation.md`
(retained deliberately while the ticket sits in `todos/`; other parked tickets carry staging artifacts
the same way). Seven of the eight fields turned out to be **already decided** — by the Mechanics Bible
or by `TCK-20260921`'s shipped code — and only `atk_range` was genuinely open:

| field | authority | basis | status |
|---|---|---|---|
| `max_hp` / `atk` / `evasion` | content (profile), via residual base | Bible `01:36,41,43,49-53`; `PROG-127` | settled by #279 |
| `def_stat` | content, via **unclamped** residual | Bible `01:51-53`; `src/core/derived_stats.py:28-33` | settled by #279 |
| `move_cost` | **derivation** — spawn's `10.0` default is the divergence | Bible `01:47` | settled by the Bible |
| `readiness_speed` | **derivation** | Bible `02_combat_laws.md:139-140` | settled by the Bible |
| `tactical_role` | **derivation** | Bible `01:61` | settled by the Bible |
| `atk_range` | **profile is the archetype factor; weapon is an independent factor** | user decision 2026-10-02; CAP-05 | decided |

Three corrections to this ticket's own framing, which the resume should start from:

1. **The `def_stat` drift row is hypothetical — strike it.** `residual_base_terms()` is deliberately
   unclamped and its docstring names this exact `worker def 0 / vitality 5` case; Bible `01:51-53` says
   the residual "may be negative". The `0 → 1` figure describes a clamp-at-zero that **does not exist
   in the code**. The `worker` round-trips exactly today. A future proposal to clamp a residual would
   itself break the round trip `PROG-127` asserts.
2. **`move_cost` is a parity-ledger item, not an `intentional_divergences.md` entry.** Bible `01:47`
   declares the formula, so the derivation is the Bible-conformant path and spawn's default is the
   divergence — activating it moves code *into* parity. A `DEV-` entry would be needed only to keep
   `10.0` *against* the Bible. This resolves the first Assumptions bullet below: the derivation is the
   intended owner.
3. **`readiness_speed` is declared, just not in chapter 01.** The formula
   `max(1.0, 10.0 + (agility - 5) * 1.0)` lives at `02_combat_laws.md:139-140` and
   `attribute_progression_contract.md:141`. Chapter 01 §2's formula block omits `readiness_speed`,
   `atk_range` and `tactical_role` entirely while line 57-58 names three of them as fields spawn and
   derivation must agree on — so §2 cannot currently be read as a statement of the derived set.
   Consolidating it is part of the AC1 record.

**`atk_range` decision (user, 2026-10-02):** the profile's `attack_range` is the archetype factor and
the weapon property is an independent factor, with the combination rule to be written into Bible 01 §2
next to `Move_Cost`. No entity loses declared range. Re-measured independently: **5 of 23 profiles**
(22%) declare non-melee range — `goblin_archer_base` 3, `apprentice_mage_base` 3, `ranger_base` 3,
`spirit_guardian_base` 2, `dragon_champion_base` 3. The plan must still choose between
`max(profile, weapon)` and "weapon overrides when present"; they differ for an archer holding a melee
weapon, and the Bible text must say which.

**AC5 is mostly pre-written:** Bible `01:57-58` already states the activation exit condition. AC5
becomes making that text agree with the table above, not writing a new condition.

**One caution for AC6 on resume:** the tripwire's condition must be "the derivation is reachable **and**
the content-authoritative fields do not round-trip", **not** "AC1 is open". AC1 is now closed on paper
while the drift is still live in code, so an AC1-keyed tripwire would disarm itself at the moment it is
most needed.

Rule-owner positions behind the table (no catalog Rule picks per-field authority, and none should be
written; the ordering is Bible formula → content declaration → derivation, constrained by
PROG-01/CAUSE-01 that a `stats_dirty` trigger is not a cause) are recorded in §2 of the investigation.
`data/content/entities/stat_profiles.yaml` is content data, not the Rule Catalog — "the profile is
wrong" is never a catalog fix.

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
`stat_profile_id` stored at spawn**, not reconstructing it from the residual.

**And reconstruction is a reliability trap, not merely a gap — this is the part to not miss.**
Inverting the residual requires the *spawn-time* attributes, which are not stored. So reconstruction is
**impossible in general, but coincidentally correct for any entity whose attributes have never moved
since spawn** — because then current attributes happen to equal spawn attributes. A reconstruction
helper would therefore **work in short corpus runs and fail silently in long ones**, as soon as a
breakthrough, elder modifier or future allocation touches an attribute. That failure mode passes a
naive test and produces wrong declared-species values later, which is worse than an outright gap.
It is the strongest reason the typed `stat_profile_id` is the only honest answer if anyone needs the
declared value. (Nuance supplied by `world-rule-catalog-design`.)

**Noted as an option, explicitly NOT new scope** for this ticket or the parent. Whoever needs the
declared value should file it.

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
