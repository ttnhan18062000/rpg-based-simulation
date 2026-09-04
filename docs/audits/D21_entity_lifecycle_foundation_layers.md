---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, documentation]
---

# D21 — Entity Lifecycle Foundation Layers

**Ticket:** TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
**Date:** 2026-08-08

## Purpose

The simulation's core design intent is goal-driven, cognition-based entities exploring a
non-hardcoded, personality/RNG-biased route toward power — not a scripted path per entity. Within
that intent, some layers are foundational (every entity touches them: staying alive, moving,
fighting, growing, eventually dying) and some are inherently complex, dependent on the foundation
working first (economy, social cooperation, and quest narrative only make sense once entities
reliably survive, act, and grow). This document audits the real, current state of the
**foundational layers only** — before any further ECONOMY/SOCIAL/NARRATIVE_QUEST investment —
so that decision is made from evidence, not assumption.

It answers two *different* questions that are easy to conflate:

1. **Is the event wired to reach a scorer?** (`docs/simulation_quality/event_type_coverage.md`'s
   own question — audited independently, Certified Level 1, last verified 2026-07-04 and
   incrementally updated through 2026-08-08.)
2. **Does the event actually fire, at meaningful volume, in real gameplay?** (this session's own
   real kernel-level finding — a different question the coverage audit doesn't and isn't meant to
   answer.)

The central finding of this document: **the answer to (1) is excellent across the board — 0 real
translation or emission gaps.** The answer to (2) is mostly also yes, with **one significant real
exception: `GROWTH_PROGRESSION`**, where 5 of 6 positive-signal event types are correctly wired but
essentially never fire in practice. **Update 2026-08-08**: follow-up investigation split this into
2 real, distinct causes rather than one — see `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`
(a real, fixable gate: skill/AP/attribute/evolution progress is blocked behind `level_up`, which
itself rarely fires) and the confirmed-no-producer finding below (`trait_expressed`/
`pillar_trait_unlocked` have no real gate to open at all — a missing mechanic, not a blocked one).
`item_equipped`'s own dormancy has a 3rd, still-open thread
(`TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`).

## Summary table

| Bucket | Wired to scorer? | Fires at real volume? | Status |
|---|---|---|---|
| `VITALS` | Yes | Yes — every populated world | Solid |
| `EXPLORATION` | Yes | Yes — every populated world with resources | Solid |
| `GROWTH_PROGRESSION` | Yes (all 15 event types) | **No — only `xp_granted` in practice** | **Real gap, open** |
| `COMBAT` | Yes | Yes — via the real dominant path, not the obvious one | Solid, but read carefully (see below) |
| `STRATEGY_COGNITION` (baseline) | Yes | Yes — flag-free baseline runs by default | Solid |
| `CONCLUSION_DEMOGRAPHIC` | Yes | Yes — one of the most reliably-touched buckets | Solid |
| `IDENTITY` | Field exists, no producer | Never — structurally impossible | Hard ceiling, not a bug to fix casually |

`ECONOMY`, `SOCIAL`, `NARRATIVE_QUEST` are intentionally **out of scope** for this document — per
the design priority this doc exists to support, they are not audited here.

---

## VITALS

**Real trigger events:** `biological_state_changed`, `stamina_changed`, `wound_sustained`,
`wound_healed`, `scar_gained` (`config/simulation_quality/entity_lifecycle_weights.yaml`).

**Status: solid.** These fire for every entity in every populated world — the most basic "is this
entity alive and simulated" signal. All 5 events were confirmed to have real observability
coverage as of `TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP` (previously some had zero event
coverage of any kind; now all 5 do).

## EXPLORATION

**Real trigger events:** `movement`, `resource_harvested`.

**Status: solid.** Movement is the most basic real activity in the engine and fires continuously;
resource harvesting fires in any world with resource nodes and a population that pursues them
(the default AI behavior, no flags required).

## GROWTH_PROGRESSION — the one real open gap

**Real trigger events (15):** `attribute_changed`, `xp_granted`, `level_up`, `skill_unlocked`,
`trait_expressed`, `pillar_trait_unlocked`, `recipe_learned`, `skill_cooldown_started`,
`item_equipped`, `item_unequipped`, `equipment_durability_changed`,
`progression_conversion_applied`, `capability_growth_stalled`, `life_arc_incoherent`,
`progression_plateau_detected`.

**Wired to scorer?** Yes, all 15 — `event_type_coverage.md` shows 0 real emission or translation
gaps anywhere in the corpus.

**Fires at real volume?** **No, for 5 of the 6 positive-signal events.** This session's own direct
kernel-level probe (`TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`) found only
`xp_granted` fires in real 2000-tick runs across the corpus — `level_up`, `skill_unlocked`,
`recipe_learned`, `item_equipped`, `attribute_changed`, `trait_expressed` were all confirmed zero.
Meanwhile the two negative/silence-signal events —`capability_growth_stalled` and
`progression_plateau_detected` — fire **13-21x more often** than real growth activity.

**Real `PROGRESSION` scoring weights** (`config/simulation_quality/scoring_weights.yaml`), quoted
in full because the magnitudes are the evidentiary point:

```yaml
pillar_trait_milestone: 75.0    # never fires in practice
level_milestone: 40.0            # never fires in practice
skill_growth: 25.0               # never fires in practice
soft_skill_evolution: 20.0       # never fires in practice
survival_experience: 15.0        # rarely fires
xp_active: 5.0                   # the one real, reachable positive signal
xp_plateau: -8.0
capability_growth_stalled: -10.0 # fires 13-21x more than growth
progression_frozen: -10.0
trait_system_silent: -10.0
skill_system_silent: -5.0
level_cap_reached: -1.0
all_level_1: -30.0
life_arc_incoherent: -15.0
genetic_determinism_active: 10.0
```

The pillar's own design clearly intends a rich, multi-source growth signal (75/40/25/20/15-point
positives) — but real gameplay only ever reaches the weakest one (`xp_active: +5`), while every
silence/stall penalty fires freely. This is why population-level `growth_trajectory` is negative
in every real corpus world checked, even after the one real structural bug in this area
(an orphaned kill-reward, `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE`) was
already fixed. **Root cause, confirmed real, not fixed here**: kill rate via the real dominant
combat path is too low relative to the 300-tick stall-detection cadence, and quest-completion
(a second natural XP source) is dormant corpus-wide unless specific flags are set. Remedy filed
separately: `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` (not implemented — this doc
documents the gap, it doesn't close it).

**Update 2026-08-08** (follow-up investigation, split into 3 tickets after user review — this
was originally one combined finding, corrected to reflect that the underlying causes are
genuinely distinct):

- `skill_unlocked`, `progression_conversion_applied`, and part of `attribute_changed`/
  `item_equipped` share one real, confirmed cause: `EvolutionSystem`'s entire level-up reward
  block is gated behind `levels_gained > 0`, and `level_up` itself rarely fires
  (`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`, unified with and superseding
  `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`). **Update 2026-08-09**: the chosen fix
  (raise `CombatRewardClassificationService.xp_multiplier` 4x, then 6x) was implemented and
  re-tested against real corpus data, and found insufficient even at 6x — zero *original*-population
  entities ever leveled up (max real XP gain 60 against a 100 XP threshold). Tracing deeper (per
  explicit user direction) found the real bottleneck is one level below XP magnitude entirely: real
  combat almost never lands a hit because `LegalityServiceV2.verify_attack_legality()` returns
  FALSE in 100% of a real 330-sample probe (`ReasonCode.FRIENDLY_FIRE_ILLEGAL` 45%,
  `ReasonCode.INSUFFICIENT_READINESS` 55%) — see the new dedicated section below, "Combat legality
  always false — the real bottleneck behind low kill rate." The multiplier change was reverted
  (no net `src/` change); the real fix is redirected to
  `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`.
- `item_equipped` has 2 *other*, independent real producers, both confirmed dormant for their own
  distinct reasons (`TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`): `ConversionIntentResolver`'s
  `EQUIP_ITEM` path is gated behind `ENABLE_PROGRESSION_EVOLUTION`, which defaults OFF and is
  never turned on in any real corpus profile; `EquipmentService.auto_equip()` is a real, complete,
  tested function with **zero real callers anywhere** — dead-but-correct code, never wired into
  the pipeline. Neither fixed here — both are real, actionable leads for a future ticket, not
  forced into an unscoped implementation.
- `trait_expressed`/`pillar_trait_unlocked` were found to have **no real producer at all**
  anywhere in `src/` — see the dedicated section below, the same class of finding as `IDENTITY`'s
  own hard ceiling.

## COMBAT — solid, but the real path is not the obvious one

**Real trigger events:** `combat_damage`, `combat_initiated`, `combat_kill`,
`hazard_drain_applied`, `near_death_survival`, `combat_hard_law_violation`,
`world_hard_law_violation`, `spawn_occupancy_violation`, `raid_party_spawned`.

**Status: solid, once you know which code path actually produces the volume.** The real dominant
kill mechanism corpus-wide is `movement.py`'s **opportunity-attack** path
(`CombatResolutionSystem.resolve_multi_attack()`), triggered when an entity disengages while
adjacent to a hostile — not the `ATTACK` action (`resolve_attack()`), which had **zero real calls**
in 2000-tick corpus runs (confirmed via direct instrumentation,
`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`). Rebirth/permadeath branching was
found to only exist in that unused function — a real, structural bug, now fixed by porting the
branch into the real dominant path.

**Important scoring nuance**: `entity_killed` (the `CONCLUSION_DEMOGRAPHIC`-bucket sibling of
`combat_kill`) scores **negatively** in the COMBAT pillar (`attrition: -1.0`,
`early_extinction: -10.0`) — by design, not a bug
(`TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`). A "successful" foundation-layer
combat loop is a *controlled*, non-extinction one, not a high-kill-count one — worth keeping in
mind when reasoning about what "COMBAT working well" should even mean for this simulation.

## Combat legality always false — the real bottleneck behind low kill rate

Found while tracing `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own combat-frequency
root cause, after 3 successive hypotheses were ruled out with real, instrumented probes against a
live `urban_political` kernel run (not assumed):

1. **Not hostile scarcity** — hostiles present within `radius=10.0` in 100% of 50 sampled ticks.
2. **Not goal-competition loss** — `GoalKind.COMBAT_ENGAGE` wins the goal competition in 325/330
   (98.5%) samples when available.
3. **Not a dead code path** — `tactical.py`'s real ATTACK branch routes through `ActionRouter` →
   `CombatActions.execute_attack()` → `CombatResolutionSystem.resolve_attack()` with a real,
   non-None `context` at the real pipeline call site — confirmed intact.

**The real, decisive cause**: `is_attack_legal` (`tactical.py:397`, via
`LegalityServiceV2.verify_attack_legality()`) was **FALSE in 100% of 330 real samples**, splitting
into `ReasonCode.FRIENDLY_FIRE_ILLEGAL` (150, 45%) and `ReasonCode.INSUFFICIENT_READINESS` (180,
55%). Because it's always false, `tactical.py`'s decision tree always falls through to the
`else: Pursuit` branch — entities perpetually chase hostiles via `MovementMode.PURSUE`, never
emitting a real ATTACK action. This is consistent with, and explains, the COMBAT section's own
earlier finding above that `resolve_attack()` had zero real calls in 2000-tick corpus runs — the
`ATTACK` action path isn't merely underused, it is **structurally unreachable** under current
legality conditions, leaving the opportunity-attack path (which requires a *retreating* entity, the
opposite of PURSUE) as the only real kill mechanism corpus-wide.

This is the real, deeper root cause underlying this whole document's own `GROWTH_PROGRESSION`
findings — low kill rate was treated as a given fact to design reward magnitude around; this
finding traces *why* it's low. Not fixed here — filed as
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` (the legality-gate bug/investigation)
and `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY` (a related but distinct feature idea:
personality/species-driven flee-vs-fight outcomes and pursuit-prevents-escape, raised by the user
during this same investigation).

**Update 2026-08-09** (`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`): the 2 sibling tickets
above raised the real, live `is_attack_legal` probe rate from 0% to 28.5%/36.6%, but a subsequent
full 2000-tick corpus re-verification found `combat_damage`/`combat_initiated`/`entity_killed`
still at **zero** in either `dungeon_crawl`/`urban_political`. Traced to a deeper, upstream cause:
`EntityIdentityResolver.resolve()`'s Path 1 (`clean_metadata`) required **both** `faction_id`
**and** `role_id` in `identity.properties`; `worldbuilding/compiler.py` (the real compile path for
these 2 worlds) sets `faction_id` but never `role_id`, so every entity fell through to Path 3
(`compatibility_projection`), which maps the raw *legacy* 4-value `Faction` enum
(`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`) to a string — silently collapsing any
content-driven faction outside those 4 buckets (confirmed: 100% of `dungeon_crawl`'s roster, 43%
of `urban_political`'s) to `faction_id="neutral"`, destroying real hostility detection for the
majority of the corpus. Fixed: Path 1 now trusts a real `faction_id` on its own, deriving `role_id`
from the existing legacy-role compat map only when absent (confirmed zero real consumers of
`role_id` itself). Real corpus re-verification confirmed the fix works — `is_attack_legal` now
gets checked for real hostile pairs that were never checked at all before (0 → 26+ real checks) —
but every one still fails on `ReasonCode.OUT_OF_RANGE` at real distances of 2-12 against a
`combat.range=1` melee attacker, revealing a **third, distinct bottleneck**: pursuit does not
appear to converge hostile pairs to melee range within a 2000-tick window. Filed as
`TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE`, not fixed in the same ticket.

**Correction, same update** (`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`): the "combat_damage/
entity_killed still at zero" claim above was incomplete — based on a filtered, `bandit_company`-
only sample, not a full event-count check. A full, unfiltered re-check on the identical
corpus-default `dungeon_crawl_seed42` run (post-fix) shows real, non-zero
`combat_damage=1`/`combat_initiated=1`/`entity_killed=1`/`combat_engagement_started=1` — a real
kill genuinely occurred. `urban_political_seed42` genuinely remains at zero in the same run. The
real, corrected question is why convergence is *rare* (1 kill / 2000 ticks / 32 entities in
`dungeon_crawl`, zero in `urban_political`), not why it is structurally impossible — reframed and
carried forward into `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`'s own investigation.

## STRATEGY_COGNITION (flag-free baseline)

**Real trigger events (baseline subset, no flags required):** `strategic_goal_changed`,
`project_started`, `project_completed`, `project_abandoned`, `StrategicBlockerAdded`.
(`belief_assimilated`/`belief_updated`/`lead_certainty_updated`/`self_model_updated` require
`ENABLE_BELIEF_ASSIMILATION`/`ENABLE_SELF_MODEL_COGNITION` and are out of this baseline audit's
scope.)

**Status: solid.** The goal-competition framework (`GoalRegistry`, multiple `GoalScorer`s per
`GoalKind` competing each tick) runs unconditionally for every entity — this is the real mechanism
behind "non-hardcoded, personality/RNG-biased exploration." One real gap was found and fixed this
session: `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` projects were winning the goal competition
correctly but silently never producing real navigation (`_resolve_target_position` returning
`(None, None, None)`) — the queue/blocking mechanism existed structurally but wasn't reaching
actual movement. Fixed.

## CONCLUSION_DEMOGRAPHIC

**Real trigger events:** `entity_killed`, `demographic_mortality`, `demographic_birth`.

**Status: solid, and recently strengthened.** One of the most reliably-touched buckets — nearly
every entity's life ends via one of these three. A real bug was found and fixed this session:
`entity_lifecycle_score.py` silently dropped metadata for entities born mid-run via
`demographic_birth` (a "None role" group, 21-48% of population per world before the fix, 0% after)
— `TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP`.

## `trait_expressed`/`pillar_trait_unlocked` — confirmed no producer, same class as IDENTITY

**Update 2026-08-08** (`TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`, split from this
audit's own `GROWTH_PROGRESSION` finding after user review): traced `IdentityUpdate.traits_add`/
`traits_remove`/`breakthroughs_add` (`src/core/updates.py:229,233-234`) and confirmed **zero real
production code anywhere in `src/` constructs either field** — the only real construction sites
are 3 test files (`tests/unit/progression/test_breakthroughs.py`,
`tests/unit/observability/test_event_shapers_progression.py`,
`tests/unit/core/test_domain_6_hardening.py`). The apply-path (consumer side,
`src/engine/patches.py`/`src/engine/apply.py`) is real, correct, and tested — the "Tough" trait's
own stat bonus (`max_hp` 100→142) genuinely works when the field is populated by hand. This is the
exact same class of finding as `IDENTITY`'s own confirmed hard ceiling below: a real, working,
tested mechanism with no real gameplay system that ever drives it. Unlike `GROWTH_PROGRESSION`'s
other zero-triggered events (which are blocked behind a real, fixable gate — see
`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`), there is no dormant gate to open here —
the gap is a missing mechanic entirely, not a blocked one. No fix landed; documented as a
confirmed, honest finding, not forced.

## IDENTITY — hard ceiling, not a foundation-layer bug

**Real trigger events:** `entity_role_changed`, `entity_faction_changed`. Both fields exist in
`IdentityUpdate` and are correctly consumed by the apply path — but **no code anywhere in `src/`
ever constructs an `IdentityUpdate` with either field set.** Confirmed directly
(`grep -rn "role_set=\|faction_set=" src/` returns zero real producers), including checking the
nearest real candidate (`PartyLifecycleService.check_defection()`, which only mutates notoriety,
not identity). This is not a foundation-layer defect to fix incidentally — it's a genuine missing
mechanic (promotion, defection-changes-faction, tamed-monster-joins-faction, etc. would all need
real design work), out of scope for "make the existing foundation solid."

---

## A related foundation-layer data-integrity risk (fixed: `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`)

**Monster-kind entities were frequently mistagged `role=CITIZEN` instead of `role=MONSTER`**
corpus-wide (found during `TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`). This mattered
for this audit because `entity.identity.role` is exactly the field the user's own design vision
depends on to separate "human, complex path" entities from "monster, patrol/attack-only" entities.

**Root cause, confirmed** (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`): `WorldCompiler.
compile()` has no `catalog_repo` of its own — it can only correctly resolve role/faction via a
pre-populated `CompileContext.legacy_roles`/`.legacy_factions` mapping, which `WorldAssemblyResolver.
assemble()` already computes and persists to `resolved/compile_context.json` alongside `world.
resolved.yaml` for every corpus world. `WorldRepository.load_world()` never surfaced this file,
so every real caller either duplicated the correct loading logic independently or silently
compiled without it — falling back to naive keyword matching that fails for almost every real
archetype role_id (e.g. "predator_hunter"/"raider"/"scout") and faction_id (e.g.
"goblin_warband"/"wild_beast_pack"), defaulting role to CITIZEN and faction to NEUTRAL. Not a
narrow content-authoring issue — a structural gap affecting every real monster-archetype entity
in every corpus world compiled through the affected call sites.

**Fixed**: `WorldRepository.load_world_with_context()` (new method) surfaces the real
`compile_context.json`; all 4 real, confirmed-buggy call sites (`src/cli/entry.py` — the general
simulation-run CLI; `tools/calibrate_simq.py`; `tools/balance_measure.py`;
`tools/personality_audit.py`) updated to use it. See `docs/parity_ledger/substrate.yaml` SUB-384
and `docs/parity_ledger/infrastructure.yaml` INFRA-330 for the full fix and real, measured impact
— including a large, positive COMBAT-pillar shift on `urban_political` (grade C → A) from
previously-invisible hostile-faction entities now being correctly detected.
`SpawnService.process_spawns()`'s own density check (`src/world/spawn.py`) reads
`EntityRole.MONSTER` for the same field, and is a real, disclosed downstream consumer whose
spawn-rate behavior shifted as a result (see SUB-384's own support_boundary).

## Recommendation

Hold `ECONOMY`/`SOCIAL`/`NARRATIVE_QUEST` expansion until
`TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` lands. The entities that would populate
richer economy/social content are the same entities whose `GROWTH_PROGRESSION` loop is currently
stalled — building richer higher-layer systems on top of a stalled growth loop would add surface
area without addressing the one real foundation-layer gap this audit found. Everything else in the
foundation (`VITALS`, `EXPLORATION`, `COMBAT`, baseline `STRATEGY_COGNITION`,
`CONCLUSION_DEMOGRAPHIC`) is confirmed solid and does not block higher-layer work on its own.

## Related Docs

- `docs/simulation_quality/entity_lifecycle_score.md`, `docs/guides/entity_lifecycle_score.md`
- `docs/simulation_quality/event_type_coverage.md` (the "wired to scorer" audit this document
  deliberately does not duplicate)
- `docs/simulation_quality/quality_scoring_contract.md` §7 (COMBAT), §7.6 (PROGRESSION life-arc)
- `docs/guidelines/intentional_divergences.md` §2.33 (opportunity-attack reward fix), §2.34
  (rebirth reachability fix)
- `tickets/done/TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC.md` (the epic this audit
  synthesizes)
