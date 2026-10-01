---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
phase: done
date: 2026-09-21
tags: [simulation-quality, progression]
---

# TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS

## Title
World-integrity bug living in the progression path: `stats_dirty` recalculation silently
converges every entity's species-specific base combat stats toward generic defaults, and has
been doing so throughout every prior balance measurement of this simulation

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**Read this as a world-integrity finding, not a progression-subsystem defect that happens to
live in progression's code path — per explicit peer review before this ticket was filed further:
this is the most consequential finding of the batch it came from.** Found incidentally while
building the value-differential calibration instrument for
`TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` (not deliberately hunted — a
zero-delta sanity check against a real compiled entity failed unexpectedly, which is what
surfaced this).

`src/engine/apply.py:616-624`'s `stats_dirty` call site invokes
`SkillScalingService.get_effective_stats(new_att, new_eq, wounds=..., scars=..., learned_skills=...,
traits=..., current_role=..., active_breakthroughs=..., class_id=...)` **without ever passing
`base_hp`/`base_atk`/`base_def`/`base_evasion`**. Both `get_effective_stats()`
(`src/engine/rpg_depth.py:342-356`) and the `recalculate_combat_stats()` it calls
(`src/progression/leveling.py:76-105`) default these to generic values (`base_hp=100,
base_atk=10, base_def=5, base_evasion=0.05`) when not supplied.

Confirmed directly: a `goblin_scout` from `data/worlds/mechanic_scenario_combat_judgement_
withdrawal/` spawns at `combat.max_hp=35` (a real, content/species-specific base). The moment
`stats_dirty` fires for ANY reason (an attribute change, an equipment change, a learned skill, a
trait add/remove, a wound, or `evolution_level` increasing — see `apply.py:595-608`'s own
`stats_dirty` condition), `max_hp` recalculates to `112` — the generic default (`100 + vitality*2 +
endurance*0.5` with `vitality=endurance=5`), silently discarding the entity's own spawned base
entirely, not just adjusting it by the delta. The same applies to `atk`/`def_stat`/`evasion`.

**Why this is world-integrity severity, not a progression-scoped defect**: `stats_dirty`'s own
trigger list is broad and routine — any attribute change, equipment change, learned skill, trait
add/remove, wound, or evolution-level increase fires it, for every entity, across every species,
role, and faction in the simulation. This means every entity's species/content-driven combat-stat
differentiation degrades toward one shared generic baseline (100/10/5/0.05) as soon as it takes
any of those ordinary actions, and keeps degrading further the more it acts. **This silently
invalidates every combat-balance observation anyone has ever measured against this simulation
before today, not just future ones** — any SimQ run, any manual balance pass, any tuning decision
made by watching real corpus play was watching species differentiation erode over the course of
that same run without anyone knowing it was happening. It is filed under `progression` because
the erosion is triggered by progression-adjacent events, but the actual defect and its blast
radius belong to the simulation's own world-model integrity, not to the progression subsystem's
own scope.

**Direct answer to this ticket's own open question, added 2026-09-21**
(`TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT`, a narrow, single-question follow-on
to the value-differential program): does entity identity actually matter to combat outcomes, or is
this erosion cosmetic? **Answer: it matters, exactly and measurably.** A real, dispatched fight
(`tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py`)
confirms that an entity's own `strength` attribute, run through the real
`LevelingService.recalculate_combat_stats()` derivation into `combat.atk`, has real,
formula-exact purchase on how much damage that entity deals in a real fight
(`CombatResolutionSystem.calculate_damage()`, also confirmed RNG-free and formula-exact via its own
differential). This `stats_dirty` bug is therefore severe for the worse of the two reasons this
ticket's own Request Summary named: it is not silently drifting something decorative, it is
silently destroying a real, demonstrated determinant of real combat outcomes every time it fires.

## Scope
**Superseded 2026-10-01 by the design resolution in Implementation Notes and
`staging_artifacts/TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS/plan.md`.** Steps 1-3
below are answered (see `investigation.md` §§2-6); step 4 is re-pointed. The original wording
("wire it through") is now known to be the wrong fix shape — see `investigation.md` §2.

**Narrowed 2026-10-01 by the rpg-feature-planning ruling (D + A) after the Step 0 measurement below: items 3 (trigger change) and 6 (re-measure) are WITHDRAWN; item 4 is re-pointed to dual-write.**

Resolved scope, in order:
1. Add a **typed durable per-entity base-stat home** (`base_hp`/`base_atk`/`base_def`/
   `base_evasion`), written once at spawn and immutable thereafter; plus a **separate typed
   permanent-grant accumulator**. Full Durable State Rule applies. Not in any free-form dict.
2. Write the base at spawn as the **residual** of the profile value minus that entity's own
   attribute contribution — NOT the raw profile value, which would inflate `goblin_scout` 35 -> 47.
3. Make the single derivation the sole writer of `max_hp`/`atk`/`def_stat`/`evasion`, fed the stored
   base plus the accumulator, and add the accumulator to the `stats_dirty` trigger set so
   near-death hardening keeps working.
4. Re-point near-death hardening (`hardening.py:84`) to increment the accumulator instead of
   `CombatUpdate.max_hp_delta`, preserving its trace keys and its observable `+5`.
5. Add a **new** `progression.yaml` parity entry (none covers base-stat preservation) and update the
   Bible 01 §2 neighbourhood.
6. **Re-measure** `stats_dirty` firings after the fix, with a positive control — step 3 makes the
   path reachable for the first time, so the 2026-09-30 zero is no longer the relevant number.

## Out of Scope
- **No `stats_dirty` trigger change; no activation of the full derivation.** Spawn and the derivation
  hold incompatible models of the whole derived-stat set (`move_cost` 10.0 -> 9.5 on every entity;
  `atk_range` 3 -> 1 on all five ranged archetypes), so the recalculation's dormancy is
  load-bearing. Owned by `TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS`.
- **`CoreActions.execute_allocate_ap`'s double-count (`core_actions.py:311-317`) — explicitly NOT in
  scope.** It is dormant by the recorded decision `DEV-004`
  (`docs/guidelines/intentional_divergences.md:2094`), which already owns the fix (porting
  PROG-015/069 aptitude-multiplier logic into that same function). See `investigation.md` §8.
- Re-authoring `stat_profiles.yaml` so profiles declare base terms rather than final stats — a
  content-semantics change belonging to the mechanics/rule owners. Recorded as a future option.
- Flipping `ENABLE_PROGRESSION_EVOLUTION`; deleting `CombatUpdate.max_hp_delta`; any SimQ
  re-baseline (the fix is value-neutral at spawn and under hardening).
- Fixing the value-differential instrument's own test suite — both new test files
  (`test_readiness_and_derived_stats_value_differential.py`,
  `test_evolution_xp_reward_value_differential.py`) already account for this by comparing
  arm-to-arm deltas (both arms undergo the identical default-base substitution), not absolute
  values against a raw spawn baseline — their own verdicts are unaffected by this bug and do not
  need to be revisited once this is fixed.

## Acceptance Criteria
1. A real decision + fix (or explicit documented divergence, if this turns out to be intended
   behavior) for whether `stats_dirty` recalculation should preserve an entity's spawned base
   stats.
2. If fixed: a real differential test confirming a `stats_dirty` trigger no longer silently
   inflates/deflates a species-specific entity's base stats toward the generic default.
3. Real corpus measurement (Scope item 4) recorded, even if the fix itself is deferred further.

## Related Tickets
- `TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` — where this was found
- `TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT` — direct answer to this ticket's
  own "does this matter" question: yes, exactly and measurably
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — prior investigation into
  the same `stats_dirty`/`recalculate_combat_stats` code path, from the reachability angle
- `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` — companion finding from
  the same program: this ticket shows species differentiation eroding after spawn, that one shows
  biological pressure was never differentiated by entity identity in the first place. Worth reading
  together for the roadmap session's own "how much does entity identity influence the simulation"
  question, per peer instruction — not merged, each stands on its own evidence.

## Related Docs
- `docs/world_rules/foundations/state-ownership.md` — OWN-01 (:23, ACCEPT), OWN-03
- `docs/guidelines/intentional_divergences.md:2094` — DEV-004 (ALLOCATE_AP dormancy)
- `docs/mechanics/01_entity_anatomy.md` §2 — the derivation formula of record
- `docs/architecture/rollout_flag_decisions_m1.md` — ENABLE_PROGRESSION_EVOLUTION trial

## Related Stored Artifacts
`staging_artifacts/TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS/`
(`investigation.md`, `plan.md`, `test_plan.md`) — created 2026-10-01.

## Related Code Areas
- `src/engine/apply.py:593-624` (`stats_dirty` trigger + call site)
- `src/engine/rpg_depth.py::SkillScalingService.get_effective_stats`
- `src/progression/leveling.py::LevelingService.recalculate_combat_stats`
- `src/core/builder.py` / `src/content/resolver.py` (spawn-time base-stat assignment, not yet read
  for this ticket)

## Assumptions / Open Questions
Whether a real, addressable per-entity "base" value exists anywhere in durable state today is
genuinely unknown — not assumed either way. That's Scope item 1's own first task.

## Implementation Notes

### 2026-09-30 — Premise re-verified against current code, and Scope 1 answered

Re-verified before scoping, per the standing rule that today's sample produced two false premises
and one duplicate. **The premise holds exactly, unchanged, at `01ac88f56`:**

- `src/engine/apply.py:616-623` calls `SkillScalingService.get_effective_stats(new_att, new_eq,
  wounds=…, scars=…, learned_skills=…, traits=…, current_role=…, active_breakthroughs=…,
  class_id=…)` — **no `base_hp`, `base_atk`, `base_def` or `base_evasion` argument.**
- `src/engine/rpg_depth.py:349-352` declares those four as keyword defaults
  `base_hp: int = 100, base_atk: int = 10, base_def: int = 5, base_evasion: float = 0.05`.
- So every `stats_dirty` recalculation rebuilds combat stats from the generic baseline and
  discards the entity's spawned species values. Confirmed by reading both sites, not inferred.

### Scope 1 — "does a recoverable per-entity base value exist?" — YES, with a caveat

**The base values exist as real content.** `data/content/entities/stat_profiles.yaml` defines
per-archetype profiles named `<archetype>_base` — e.g. `goblin_scout_base` at lines 55-59 with
`hp: 35, max_hp: 35, atk: 8, def: 2`, matching the ticket's observed spawn value of 35 exactly.
Others present: `hero_base`, `commoner_base`, `monster_base`, `wolf_predator_base`,
`goblin_raider_base`, `goblin_archer_base`, `cave_spider_base`. This is a first-class content
family, not ad-hoc data — `src/content/repository.py:117` registers it as
`ContentFamilySpec("entities.stat_profiles", …, StatsProfileDefinition, "stats_profiles")` and
`src/content/reference_graph.py:23` gives it the reference type `stat_profile`.

**The caveat, and the real design question: the entity does not carry a pointer back to its
profile.** Neither `EntityState` nor `IdentityComponent` has an `archetype_id`, `stat_profile_id`
or `species` field — verified by reading the full field list of both. So at `stats_dirty` time the
recalculation has no declared way to ask "which profile were these stats derived from?"

`EntityState.kind: str` **is** present and is in scope at the `apply.py` call site, which makes it
the obvious candidate link. **Whether `kind` actually resolves to a `stat_profiles.yaml` id has
NOT been confirmed** — that is the first thing to check, and it decides which of two fixes applies.

### Two fix shapes, and which one applies depends on that check

**A — lookup, if `entity.kind` resolves to a profile id.** Resolve the profile at recalc time and
pass its four values through. No new durable state. **Blocker to check first:** does the
`apply.py` path have access to a catalog/registry at all? There is direct precedent for it not
having one — `WorldCompiler.compile()` has no `catalog_repo` parameter and had to be handed
`context.legacy_roles`/`legacy_faction` for exactly this reason
(`src/worldbuilding/repository.py:89-114`'s docstring, `TCK-20260808-MONSTER-ROLE-MISTAGGING-
INVESTIGATION`). If `apply.py` is likewise catalog-free, A needs the same kind of context
threading and is not the cheap option it looks like.

**B — typed durable base-stat field, if no reliable link exists.** Store the resolved base values
(or the profile id) on the entity at spawn. This is **durable state** and the Durable State Rule
applies in full: typed model, stable location in entity state, defined lifecycle, inspection/debug
visibility, and tests. **Do not** put it in `identity.properties` — CLAUDE.md forbids durable
meaning in free-form metadata, and that dict is exactly that.

Either way this is **not** a parameter pass-through, which is how the ticket's Scope step 2 reads
("wire it through"). Both shapes need a real decision first, and B is an architecture change.

### 2026-09-30 — Re-rated P0 → P2 (user-authorised)

On the runtime evidence immediately below: the affected path fired **zero** times across three
corpus worlds and 40 deaths. The defect is real but latent. **Re-raise immediately** if any change
starts setting `update.attributes`, `update.equipment` or `wound_update` on a routine path — that
would make it live at once.

### 2026-09-30 — RUNTIME MEASUREMENT: the erosion never fires. Severity is wrong.

The ticket's central severity claim — that this "silently invalidates every combat-balance
observation anyone has ever measured" — was a reasoned inference from the code path. **Measured, it
is false.**

Probe: production loader (`WorldRepository.load_world_with_context`, the path real runs use — not
the content-catalog path, per `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`), real
`Kernel` ticks under `PROD_SMALL`, seed 42, counting every `SkillScalingService.
get_effective_stats` call.

| world | ticks | entities | **`stats_dirty` firings** | deaths | entities whose stats moved |
|---|---|---|---|---|---|
| `frontier_living_world` | 600 | 49 | **0** | 21 | 8 |
| `crowded_frontier` | 400 | 38 | **0** | 13 | 10 |
| `quest_dense_frontier` | 400 | 6 | **0** | 6 | 6 |

**Zero firings in all three worlds, across 40 deaths.** So the generic-baseline substitution at
`apply.py:616-623` is real in code but **unreached at ordinary corpus run lengths**. No entity's
species stats were eroded, because the recalc never ran.

**The zero is trustworthy** — a monkeypatch returning zero is meaningless without a positive
control, so the probe asserts one: it calls through `apply.py`'s own resolved name
(`apply_mod.SkillScalingService is rpg_depth.SkillScalingService`, then invokes it) and requires
the counter to increment by exactly 1 before the run starts. It did. Combat also genuinely
occurred (40 deaths), so this is not "nothing happened".

**Why stats still moved: there is a second, additive writer, and it is the one actually in use.**
`CombatUpdate.max_hp_delta` (`src/core/updates.py:111`, merged additively at `:145`) plus
`LevelingService`'s own `max_hp += …` at `leveling.py:123,147`. Observed increments were
`+5/+10/+15/+20` on `max_hp` only, with `atk`/`def` never moving — consistent with level-up HP
grants, not with a full recalc.

**This is the architecturally important finding.** The codebase already has a delta path for
combat stats that **preserves species bases by construction**, running alongside a full-recalc
path that **destroys them**. The live path is the safe one. So the question is less "how do we
feed the recalc a correct base" and more "should this recalc path exist at all, given a working
additive path already carries the load."

**Consequences for the decision:**
- **No SimQ re-baseline is implied** — not because the fix is conservative, but because the code
  being fixed does not execute. This resolves the open question raised in review; it was the right
  question and the answer is empirical, not assumed.
- **The `commoner_base` behaviour change does not arise in practice.** Village Workers keep
  `100/10/0` today because the recalc never runs on them. Worth declaring anyway, but it is not a
  live regression risk.
- **P0 is the wrong severity.** This is a latent defect in an unreached path — the same
  "unreachable mechanism" shape as the corpus this session has been working through all day. It
  should be re-rated and re-sequenced against defects that do execute.

**Bounds, stated plainly:** three worlds, one seed, 400–600 ticks. It does **not** prove the path
is unreachable in principle — only that nothing in an ordinary corpus run triggers it. A longer
run, an equipment-heavy scenario, or any future code that sets `update.attributes` /
`update.equipment` / `wound_update` would reach it immediately. The defect should still be fixed;
it should not be fixed *first*, and it should not be described as having corrupted past
measurements.

### 2026-10-01 — DESIGN RESOLUTION (planning session's call, with the rule owner consulted)

**Decision: Option B+ — "one base owner, one derivation." Option A is ruled out on code facts,
Option C is ruled out on coverage. B as the ticket words it is necessary but NOT sufficient.**

All code facts below were read at HEAD on 2026-10-01, not inferred from structure.

#### Option A (resolve the profile at recalc time) is dead — two independent blockers

1. **There is no entity→profile link.** `EntityState` (`src/core/state.py:879`) carries `kind: str`
   and no `archetype_id`, `species_id` or `stat_profile_id`; neither does `IdentityComponent`.
   `grep archetype_id src/core/` returns exactly one unrelated hit (`registries.py:517`). The base
   values are reached only via the required `ArchetypeDefinition.stat_profile` field
   (`src/content/schema.py:230`, resolved at `src/content/resolver.py:446`).
   `entity.kind` is **not** a usable substitute: on the archetype-native path it is set to
   `arch.species_id` (`src/entities/contract_builder.py:31`, whose own comment adds "may be
   overridden by spawn context"), and a species id is not a stat-profile id; on the legacy builder
   path it defaults to the literal `"hero"` (`src/core/builder.py:95`) and is freely settable
   (`:117`). This closes the ticket's own explicitly-unconfirmed caveat: **`kind` does not resolve
   to a profile id.**
2. **The apply path has no catalog.** `ApplyPath.apply_generation` (`src/engine/apply.py:189-198`)
   is a static method taking `prior_state`/`update`/`next_tick`/`next_world_time`/`cadence`/
   `audit_mode`/`audit_dirty_set`/`passive` — no catalog or repository parameter, and the file
   contains no `catalog`/`repo` reference at all. This is the precedent the ticket flagged
   (`WorldCompiler.compile()` having to be handed `context.legacy_roles`), confirmed to apply here.

**Note the asymmetry this exposes:** the resolved contract already computes `archetype_id` and
`species_id` (`contract_builder.py:28-29`) and `EntityState` then **discards both**. The base
identity is resolved at spawn and thrown away — which is precisely why B is a real durable-state
gap and not a convenience field.

#### Option C (retire the full-recalc path) is dead on the coverage test

`world-rule-catalog-design` supplied the governing rule and the test that decides between B and C:

- **OWN-01** (`docs/world_rules/foundations/state-ownership.md:23`, ACCEPT) — "Every durable
  authoritative state concept has an unambiguous canonical owner … must not independently establish
  conflicting authoritative truth for the same concept." Two writers producing 35 vs 112 for the
  same `max_hp` is a direct violation. **OWN-03** adds that stored `max_hp`/`atk`/`def` is a
  materialised derivation (Bible 01 §2: `base + VIT·2 + END·0.5 + gear`), so two derivations of it
  cannot both be authoritative. **The dual authority, not the wrong default, is the rule-level
  defect.**
- But OWN-01 requires *one* owner without saying which. The deciding question is **coverage**:
  retiring the recalc is legitimate only if the additive writers already emit a correct delta for
  **every** input of the §2 formula. **They do not.** The additive writers emit nothing for
  equipment, trait, learned-skill, breakthrough or class changes — all of which are `stats_dirty`
  triggers (`apply.py:595-608`) and all of which have real terms in the recalc
  (`leveling.py:110-150`). Retiring it would leave derived stats stale after those changes — an
  OWN-03 violation in the opposite direction. The rule owner also notes Bible 01 §5 breakthrough
  bonuses and Elder Attribute Modifiers depend on that propagation.

So exactly one writer must survive, and it has to be the full derivation.

#### Why B as worded is insufficient: the recalc cannot represent accumulated permanent grants

`recalculate_combat_stats` (`leveling.py:99-150`) computes `max_hp` **absolutely** —
`base_hp + vitality*2 + int(endurance*0.5)`, plus gear/trait terms. It has **no term for an
accumulated permanent grant.** But permanent grants exist and are written additively through
`CombatUpdate.max_hp_delta`, merged absolutely at `patches.py:321`
(`max_hp = new_combat.max_hp + u_com.max_hp_delta`):

- **`src/engine/pipeline_phases/hardening.py:84`** — `max_hp_delta=5`, declared in that phase's own
  LAW block as "a small **permanent** max-HP increase" for surviving a near-death hit.
- **`src/engine/domain/core_actions.py:317`** — `max_hp_delta=amount * 10` on vitality allocation,
  and **`:313`** `atk_delta=amount * 2` on strength allocation.

Therefore **fixing only the base still erases every accumulated hardening grant** the first time
`stats_dirty` fires. A correct base is necessary and not sufficient.

#### And a third finding: attribute allocation double-counts, at a divergent weight

`CoreActions.execute_allocate_ap` (`core_actions.py:311-317`) sets the attribute delta **and** a
hand-written combat delta for the same point:

| allocation | attribute delta | hand-written combat delta | the §2 formula's own term |
|---|---|---|---|
| vitality | `vitality_delta=amount` | `max_hp_delta=amount*10` | `vitality*2` |
| strength | `strength_delta=amount` | `atk_delta=amount*2` | `strength*0.5` |

Setting `update.attributes` **is** the primary `stats_dirty` trigger, so when this path runs the
same allocated point is counted twice — once at the hand-written weight, once by the recalc — at
**5× and 4× divergent weights** respectively, on top of the wrong-base rebuild. This is the
cleanest OWN-01 violation of the three.

**CORRECTED 2026-10-01, same day, before anyone acted on it — this path is dormant by a recorded,
verified decision, and my first write-up of it was wrong.** I originally wrote that "`ALLOCATE_AP`
is wired, not dead code: `action_router.py:55-56` dispatches it and `generator.py:79` generates
`ConversionKind.ALLOCATE_AP`", and concluded the ticket's own re-raise condition was already met in
committed code. **Both halves were wrong, and the error was name-matching two distinct
`ALLOCATE_AP` paths instead of tracing either one:**

- **The generator path never reaches `execute_allocate_ap`.** `ConversionKind.ALLOCATE_AP` resolves
  at `src/domains/progression/resolver.py:82-91` to `IdentityUpdate(unspent_ap_delta=-1)` — a
  decrement-only, **zero-attribute-gain** no-op returned directly as an `EntityUpdate`
  (`src/domains/progression/phase.py:73`), never through `ActionRouter`. It therefore never sets
  `update.attributes` and **cannot trigger `stats_dirty` at all**. Different path, same name.
- **No production code constructs the router payload.** The only `{"action": "ALLOCATE_AP", …}`
  constructors in the repo are two cases in `tests/unit/quest/test_progression_regression.py`
  (`:47`, `:68`). `execute_allocate_ap` has **zero `src/` payload producers**.

**This is `DEV-004`** (`docs/guidelines/intentional_divergences.md:2094`,
`TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`): "Keep `execute_allocate_ap` wired but dormant." It
ratifies `SUB-376` (`substrate.yaml`) and `ENTITY-008` (`docs/event_ledger/entity.yaml`), and its
2026-08-30 update records a **real 4-leg corpus trial** (`docs/architecture/
rollout_flag_decisions_m1.md` § "ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result") finding
the branch unreachable for **two independent** reasons, both of which I re-verified at HEAD today:

1. `ENABLE_PROGRESSION_EVOLUTION` is `FeatureMode.OFF` (`src/domains/optimization/
   feature_flags.py:48`), gating the whole `progression_conversion` phase (`pipeline.py:387`).
2. Its only trigger path (a ledger XP entry) has no live producer — `RewardLedgerService` appears
   only at its own definition (`src/domains/progression/ledger.py:13`), **zero callers**. The trial's
   diagnostic replay had 100% of sampled decisions converging on `SAVE_FOR_LATER`.

**Dormancy is test-guaranteed and passing at HEAD** (4 passed, run 2026-10-01):
`tests/integration/progression/test_allocate_ap_dormancy.py::
test_allocate_ap_unreachable_via_real_kernel_tick` and
`tests/unit/quest/test_progression_regression.py`.

**So the re-raise claim is WITHDRAWN.** The ticket's 2026-09-30 condition ("re-raise immediately if
any change starts setting `update.attributes`") is **not** met: nothing live sets it. The
double-count at `core_actions.py:311-317` is real in code and is still the cleanest OWN-01 violation
of the three *on the page*, but it has no live caller, it changes no observable behaviour today, and
its dormancy is a decided, documented, tested position rather than an oversight. **Do not re-raise
severity on it, and do not describe it as live.**

Two further notes for whoever implements:
- **This double-count should fold into DEV-004's own recommended-but-not-created follow-up**, not be
  filed fresh. DEV-004 already recommends "porting [`AllocateAttributeAction`'s] correct PROG-015/
  PROG-069 aptitude-multiplier logic into `core_actions.execute_allocate_ap` and correcting the
  resulting PROG-068/069/015 parity gap". Fixing the weights is the same edit to the same function;
  doing it twice from two tickets is how the weights diverged in the first place.
- **DEV-004's line citation has drifted.** It locates `execute_allocate_ap` at
  `core_actions.py:146-176` and its dispatch at `action_router.py:49-50`; today they are `:295-317`
  and `:55-56`. The decision is unchanged — only the line numbers moved.

#### Two corrections to this ticket's own earlier notes

1. **`leveling.py:123,147` are not a level-up writer.** The 2026-09-30 note cites them as
   "`LevelingService`'s own `max_hp += …`" constituting a second additive writer. Read directly,
   `:123` is `max_hp += defn.properties.get("hp_bonus", 0)` (equipment) and `:147` is
   `max_hp += 20` (the `Tough` trait) — **both are inside `recalculate_combat_stats` itself**, i.e.
   terms of the single derivation, not a competing writer. There is no additive level-up HP writer
   in `leveling.py`.
2. **The observed `+5/+10/+15/+20` movement was near-death hardening, not level-up HP grants.**
   The increments match `hardening.py`'s `max_hp_delta=5` applied repeatedly, and that phase fires
   on surviving near-death combat — consistent with the 40 deaths the probe recorded. The earlier
   note's "consistent with level-up HP grants" attribution is withdrawn.

   Neither correction changes the 2026-09-30 measurement itself (zero firings stands, with its
   positive control) or the P2 re-rating. They change what the second writer *is*, which is what
   the fix shape depends on.

#### One correction from the rule owner, affecting severity framing

The generic profiles do **not** fully coincide with the recalc defaults. `hero_base`,
`commoner_base` and `monster_base` are `100/10/`**`0`** (`data/content/entities/stat_profiles.yaml`),
while `rpg_depth.py:349-352` defaults `base_def=`**`5`**. So erosion is observable on
`commoner_base` too, as `def 0 → 5` — and `commoner_base` is live
(`entity_archetypes.yaml:98`). It is **not** confined to the `LEGACY-EXPORT` goblin/wolf/spider
profiles, as a first reading of the catalog suggests.

#### The resolved target shape

1. **A typed durable per-entity base-stat home** holds the declared spawn values —
   `base_hp`/`base_atk`/`base_def`/`base_evasion`, or the `stat_profile_id` plus a resolution step.
   Durable State Rule applies in full: typed model, stable location in entity state, defined
   lifecycle, inspection/debug visibility, tests. **Not** `identity.properties` — CLAUDE.md forbids
   durable meaning in free-form metadata. Written **once at spawn** from the already-resolved
   contract and **immutable afterwards**; its provenance is the stat profile.
2. **Permanent grants go in their own typed accumulator — do NOT fold them into the base.**
   Near-death hardening's `+5` accumulates in e.g. `permanent_max_hp_bonus`, with its grant events
   traceable, not by mutating `base_hp`.

   **This reverses an earlier draft of this resolution, on the rule owner's correction, and the
   reason is traceability rather than ownership.** My first shape folded grants into the base on the
   theory that the base had to be the single owner. That misreads OWN-01: OWN-01 governs who writes
   the **derived** stats, and one derivation writer satisfies it however many typed inputs it reads —
   a typed permanent-grant input is an *owned input*, not a second owner of `max_hp`. Folding
   destroys provenance: after a few grants the base can no longer say how much came from the declared
   species profile and how much was earned. **CAUSE-05** (causal history stays traceable within its
   declared reach) and **HP-02** (provenance needs a real causal ancestor) both cut against that, and
   so would any later question like "what is this entity's species base?" — including the de-hero
   inventory's "re-ground capability on real state". Base-mutation would not be an outright rule
   violation, but it would require explicitly recording the provenance loss; the accumulator shape
   costs nothing and loses nothing, so take it.
3. **The full derivation is the sole writer of `max_hp`/`atk`/`def_stat`/`evasion`**, reading
   **base + attributes + gear + permanent grants** — one writer of derived stats, every input with
   exactly one owner, nothing erased. `execute_allocate_ap` stops emitting `max_hp_delta`/`atk_delta` entirely — the attribute
   delta alone propagates through the derivation, which removes the double-count and the weight
   divergence in one move.
4. **Declare the weight change.** Today's hand-written weights (10 HP/point, 2 ATK/point) differ
   from the §2 formula's (2 HP/point, 0.5 ATK/point). Collapsing to one writer necessarily changes
   the per-point yield wherever that path fires. **This is a behaviour change, not a silent
   cleanup**, and it is the **mechanics owner's call, not the rule owner's** (so ruled by
   `world-rule-catalog-design`, which declined it as outside `docs/world_rules/`).

   **Default disposition, and the reasoning to hand the mechanics owner:** CLAUDE.md gives the
   Mechanics Bible precedence, so **§2 is the law and the hand-written 10/2 weights are the
   deviation** — not the reverse. Collapsing to §2 is therefore a **`Bug Fix`-class
   `intentional_divergences.md` entry that discloses the yield change**, *not* a §2 rewrite. It flips
   to an **`Intentional Gameplay Change`** with a real §2 edit only if the user wants the higher
   yields kept as a design choice. Either way it is disclosed and never silent.

   **The measurement this originally asked for has already been done, and it settles the stakes:
   near zero.** See the DEV-004 correction above — `execute_allocate_ap` has **no live payload
   producer**, the generator path never reaches it, and dormancy is verified by a 4-leg corpus trial
   plus a passing dormancy test. **So the yield change alters no observable behaviour today.** It
   still must be disclosed (a dormant branch can be woken, and DEV-004 explicitly contemplates a
   future producer), but it is a disclosure-on-a-dormant-path, **not** a live balance change, and it
   should not be escalated as one. Fold the disclosure into DEV-004's own recommended follow-up,
   which already owns the correctness of this function.

#### Consequences for scope, tier and sequencing

- **This is no longer a parameter pass-through, and the ticket's Scope step 2 ("wire it through")
  should be read as superseded.** It is a durable-state addition plus a writer-authority
  consolidation across three files, with a declared balance change. Tier stays `standard`; scope
  grows. It may warrant splitting (durable base field; then writer consolidation; then the declared
  weight reconciliation) — but the pieces are **ordered**, not independent.
- **P2 stands.** The erosion still does not fire at corpus run lengths. What changed is that two of
  the three OWN-01 violations are in committed, wired code rather than hypothetical.
- **Authority basis to cite:** OWN-01 and OWN-03 for the single-writer obligation; the
  user-accepted 2026-09-30 ruling on this ticket (species profile values are the entity's spawn
  stats and a recalc must not discard them) plus CLAUDE.md's Durable State Rule for the typed home.
  **There is no catalog Rule declaring species-derived base stats** — the rule owner checked
  `docs/world_rules/` and confirmed none exists; ID-02/STR-01 permit classification-driven
  properties without requiring them, and Bible 01 §3 declares *class* bases (NOVICE 100/10/5), not
  species. Do not cite a species-base Rule; it does not exist. The rule owner made **no catalog
  edit** and judged none warranted until the fix lands.
- A `progression.yaml` parity entry does not exist for base-stat preservation and will need to be
  **added**, not updated. (`#276` removed the rebirth/generation entries — re-read the ledger
  before assuming any neighbouring id.)

### Sequencing note

The ticket's own claim that this invalidates prior combat-balance observations is plausible and
important, but **do not restate it as established without a runtime measurement** — it is
currently a reasoned inference from the code path. If a before/after measurement is wanted, note
`TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` (the corpus runs at ~10 entities and
could not detect a real 58% combat-volume change), so SimQ may not be the right instrument for
demonstrating the improvement.
**Implementation, 2026-10-01 (rpg-implementer).**

Step 0 probe reproduced the trap: `goblin_scout` spawns 35/8/2/0.05; recalc with base 100 -> 112; with
base 35 -> 47; residual base 23 -> 35. A per-field probe over three worlds (seed 42) then showed the
plan's value-neutrality claim failed once the accumulator joined the `stats_dirty` trigger: `move_cost`
10.0 -> 9.5 on all entities (2/2, 49/49, 38/38), `atk_range` 3 -> 1 on scouts (and by the owner's widening
all five ranged archetypes), and a clamped `worker` def residual (def 0 vs int(5*0.3)). Stopped and handed
the design back; ruling **D + A**, no clamp.

Shape shipped:
- `CombatComponent` (host: base stats are combat stats, not identity) gains typed `base_hp/base_atk/
  base_def/base_evasion` (defaults 100/10/5/0.05 = the derivation's historical baseline) and
  `permanent_max_hp_bonus`. Canonical-dict fields; carried through `EntityState.to_readonly()`, which
  re-lists the component's fields by hand and would otherwise silently reset them.
- `src/core/derived_stats.py`: `attribute_stat_terms` (single definition, called by
  `recalculate_combat_stats`) and `residual_base_terms` (spawn residual). One helper, so the two cannot drift.
- The residual is written in `V2EntityBuilder.build()` (order-independent of `.combat()`/`.attributes()`),
  only for builders that opted in with `.spawn_combat_stats_are_final()`: the three profile-driven spawn
  paths (`archetype_factory`, `entity_spawner` legacy guard, `WorldCompiler.compile`) and all seven
  `EntityGenerator` paths (`src/systems/world_systems/generator.py`: hero, monster, offspring, demonic,
  humanoid offspring, goblin, stronghold), whose difficulty-scaled literals are final spawned stats too
  (the monster/boss population spawns through `spawn_monster`; found by rpg-feature-planning review). The opt-in is explicit
  because the builder cannot tell a profile's FINAL value from a test/scenario's base term
  (`test_leveling` declares `max_hp=100` as a base); undeclared builders keep the generic baseline, so
  default-built entities behave as before. The residual is UNCLAMPED and may be negative.
- `ApplyPath` passes the stored bases and accumulator into `get_effective_stats` ->
  `recalculate_combat_stats`; the accumulator is a linear additive `max_hp` term.
- Hardening keeps `max_hp_delta=5` (applied this tick, unchanged) AND adds
  `CombatUpdate.permanent_max_hp_bonus_delta=5` (applied in `CombatPatch`), same trace keys.
  `event_shapers.py:1829` stays correct because `max_hp_delta` is still written.

**Option A is a declared interim.** This ticket closes the CONFLICTING-VALUE defect (35 vs 112), not the
dual-path structure: max_hp is still maintained both incrementally (`max_hp_delta`) and by the derivation.
OWN-01/OWN-03 argument: stored max_hp is a materialised derivation; incrementally maintaining it from the
same definition is not an independent authority, and
`test_from_scratch_derivation_equals_incrementally_maintained_max_hp` makes agreement a checked invariant.
That holds only while the accumulator is a linear additive term (percentage/capped/attribute-dependent
hardening would break it). Expect the OWN-01 evidence to grade PARTIAL; full single-writer consolidation is
`TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS`.

**Dormancy is load-bearing.** `stats_dirty` never firing (zero firings, 3 worlds, positive control, 2026-09-30)
is the only thing preventing the move_cost/range drift; "latent defect" became "latent defect whose
dormancy is load-bearing". Step 3.3 (accumulator as a trigger) was withdrawn for that reason, so the
2026-09-30 count still stands and the planned post-fix re-measure (T12) does not apply: the trigger set is
byte-unchanged.

Known limitation: with no `stat_profile_id` stored, an entity's declared species stat is not recoverable
from the residual once its attributes move. Not new scope; the clean answer is a typed id at spawn.

No live profile clamps now (residual is unclamped); `worker` def residual is -1 and round-trips exactly.

## Test Summary
- `tests/unit/progression/test_species_base_stats_preserved.py`: 17 pass (spawn unchanged + residual 23/6/1;
  derivation inverts it; stats_dirty gives 35, excluding 112 and 47; vitality +2 -> 39; hardening +5, +10,
  grant survives an unrelated recalc; from-scratch == maintained max_hp after 0/1/2 grants; base immutable;
  negative residual round-trips; builder-order independence; shared-helper agreement; exact round trip for
  EVERY entity in frontier_living_world / crowded_frontier / quest_dense_frontier; canonical fields + stable
  hash; every CombatComponent field survives `to_readonly()`; hardening event max_hp matches actual;
  default builder keeps the generic baseline).
- Regression: unit/quest, unit/progression, unit/engine, integration/progression, mechanic_scenarios (483 pass);
  PROG-030's test_path, ALLOCATE_AP dormancy (4), unit/core, entities, worldassembly, worldbuilding,
  observability (1725 pass); determinism/canonical/replay/fingerprint/hash/checkpoint sweep (green).
  No recorded-hash fixture needed updating.

## Files Changed
src/core/derived_stats.py (new), src/core/state.py, src/core/updates.py, src/core/builder.py,
src/progression/leveling.py, src/engine/rpg_depth.py, src/engine/apply.py, src/engine/patches.py,
src/engine/pipeline_phases/hardening.py, src/entities/archetype_factory.py,
src/worldassembly/entity_spawner.py, src/worldbuilding/compiler.py, src/systems/world_systems/generator.py,
tests/unit/progression/test_species_base_stats_preserved.py (new), docs/mechanics/01_entity_anatomy.md,
docs/core/state.md, docs/parity_ledger/progression.yaml (PROG-127).

## Completion Summary
Species/profile base stats now survive a `stats_dirty` recalculation: `goblin_scout` recalculates to 35, not 112
(original bug) or 47 (profile-value-as-base trap), and a near-death hardening grant survives it. Shipped as
option A (declared interim, per rpg-feature-planning ruling): this closes the conflicting-value defect, not the
dual-path structure; consolidation is `TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS`.
The recalculation remains unreachable in corpus play (trigger set unchanged) and that dormancy is load-bearing.
Known base failure seen in the wide sweep, not caused by this change: `tests/integration/world/test_long_run_stability.py`.
Not done by design: planned post-fix `stats_dirty` re-measure (trigger unchanged), clamp (ruled out).
