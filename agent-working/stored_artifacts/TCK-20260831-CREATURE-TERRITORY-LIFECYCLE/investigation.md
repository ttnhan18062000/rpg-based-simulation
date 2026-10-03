---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-CREATURE-TERRITORY-LIFECYCLE
artifact_type: investigation
tags: [world, ecology]
---

# Investigation — TCK-20260831-CREATURE-TERRITORY-LIFECYCLE

## Context Search Note

Per Step 0c: `mcp__knowledge-search__search_docs` was called first with query "creature territory
life cycle camp maturity trauma monster spawn" (top hits: `docs/world/raid_boss_camp_contract.md`
— confirms `camp.py` growth/spawn/boss-spawn contract; `docs/mechanics/05_world_evolution.md` §6;
`stored_artifacts/TCK-20260425-WORLD-DYNAMICS`, `TCK-20260627-P2B-SPAWN-CADENCE`). Then
`graphify query "CampService BiologicalSystem monster kind life cycle territory"` (122 nodes,
BFS depth=2 — confirmed `CampState`, `CampUpdate`, `CampService`, `BiologicalUpdate`, `EntityState`,
`WorldDynamicsSystem` as primary code targets). Raw file reads/greps below are follow-up only, per
CLAUDE.md's Context Scan rule.

## Current Behavior

1. **`CampService.process_camps`** (`src/world/camp.py:21-84`) — the reuse precedent this ticket is
   explicitly asked to mirror. The trauma-multiplier shape is at **`src/world/camp.py:34-40`**:
   ```python
   m_delta = CampService.MATURITY_PER_TICK          # 0.05
   region = LegalityServiceV2.get_region_for_position(camp.position, state)
   if region and region.trauma_score > 50.0:
       m_delta *= 1.5
   camp_updates[c_id] = CampUpdate(id=c_id, maturity_delta=m_delta)
   ```
   Confirmed exact: `region.trauma_score > 50.0` → `m_delta *= 1.5`. This applies to `CampState`
   (per-camp, 0–100+ float), not to any per-entity concept. `CampService` also spawns monsters near
   the camp by **proximity** (10×10 box around `camp.position`, `camp.py:47-50`), not by any durable
   `camp_id` link stored on the spawned entity — there is no field anywhere on `EntityState` that
   records which camp an entity "belongs to." "Anchored to a camp/territory" (ticket Scope) is
   therefore not a pre-existing durable relationship; it would need to be either newly added or
   inferred by proximity the same way `camp.py` already does for its own spawn-cap check.
   `CampService.process_camps` is called from `src/engine/world_dynamics.py:166-168`, inside the
   `should_run(state.tick, None, cadence.world_dynamics)`-gated macro-dynamics block (§3), alongside
   `CalamityService`, `SpawnService`, `ResourceEcologyService`, `ThreatService`, `BossService`,
   `RaidService`, `DemographicCycleService`. This whole block runs via `pipeline.py:304`'s
   `run_phase("world_dynamics", ...)` call, which passes **no `feature_flag` argument** — the block
   is cadence-gated only, not `FeatureMode`-gated at all today. None of the individual services
   inside it (including `CampService`) carry their own flag check.

2. **`BiologicalSystem.update()`** (`src/systems/lifecycle_systems/biological.py:9-43`) — the class
   the ticket's Request Summary names as the "HERO/VILLAGER-only gate" (`entity.kind not in ["HERO",
   "VILLAGER"]: continue`, line 18). **This class is dead code in production.** `grep -rn
   "BiologicalSystem.update" src/ tests/` returns exactly one caller, and it is inside
   `tests/unit/core/test_biological.py` — its own unit test. `src/systems/biological_system.py` is
   only a re-export shim (`from src.systems.lifecycle_systems.biological import BiologicalSystem`)
   with no callers of its own either. **This is a significant finding that changes AC #3's scope**:
   the gate the ticket describes as "existing" is not the operative one — see Risks below.

3. **The real, live per-tick biological/aging path is `ApplyPath._compute_entity_changes`**
   (`src/engine/apply.py:70-127`), invoked every tick from `ApplyPath.apply_generation` (called from
   `kernel.py:757` and `kernel.py:811`, the main tick-advancement path, default `passive=True`). This
   function has **no `entity.kind` or `entity.identity.role` gate at all**:
   ```python
   if passive and (entity.lifecycle.active or is_life_due):
       if is_bio_due:
           bio = replace(bio, hunger=min(100.0, bio.hunger + 0.1*cadence.biological),
                               sleep_debt=min(100.0, bio.sleep_debt + 0.05*cadence.biological))
       if is_life_due:
           new_age = life.age_ticks + 1
           # starvation/exhaustion damage at hunger>=95 / sleep_debt>=98
           changes["lifecycle"] = replace(life, age_ticks=new_age,
               active=(new_hp > 0 and new_age < life.max_age_ticks))
   ```
   This applies to **every** active `EntityState`, MONSTER-kind included: hunger, sleep_debt, and
   `age_ticks` all accumulate for monsters today, unconditionally, whenever the `biological`/
   `lifecycle` cadence fires. `grep -rn "hunger_delta\s*=\s*-\|sleep_debt_delta\s*=\s*-"` shows the
   only places hunger/sleep_debt are ever *reduced* are town-visit actions — `src/town/inn.py:29`
   (`hunger_delta=-20.0`), `src/town/home.py:19` (sleep), `src/engine/domain/core_actions.py:31,41`
   (EAT/SLEEP intents), `src/engine/town_resolution.py:97,105` — all gated behind entering a town
   building, something monsters never do. This means monsters already accumulate hunger/sleep_debt/
   age with no relief mechanism, and `age_ticks >= max_age_ticks` (default 10000) or hunger≥95/
   sleep_debt≥98 passive damage would eventually kill a monster of old age or "starvation" today,
   independent of this ticket. This is **pre-existing behavior**, not introduced by this ticket —
   flagged as a risk to be aware of, not something in scope to fix here.

4. **Per-entity "maturity/age" concepts that already exist** (distinct from `CampState.maturity`):
   - `IdentityComponent.life_stage: LifeStage = LifeStage.ADULT` (`src/core/state.py:488`,
     `LifeStage(str, Enum)`: `CHILD`/`ADULT`/`ELDER`, `src/core/state.py:410-414`).
   - `LifecycleComponent.age_ticks: int = 0` / `max_age_ticks: int = 10000`
     (`src/core/state.py:145-146`), incremented +1 per `is_life_due` tick for every entity (see #3).
   - `LifeStageService.get_stage_for_age(age_ticks)` (`src/ai/life_stage.py:42-56`) maps age_ticks to
     `LifeStage` using **fixed global thresholds (3000/7000)**, shared numerically (but not by
     import — a deliberate cross-layer-avoidance decision, see Prior Work) with
     `src/domains/demographics/cohort.py::get_age_bracket()`. `LifecycleSystem.resolve_lifecycle()`
     (`src/systems/lifecycle_systems/lifecycle.py:53-70`) applies this transition monotonic-forward-
     only via a typed `EntityUpdate(identity=IdentityUpdate(life_stage_set=...))`.
   - **Critically, `LifeStageService`'s only consumer is `ScoreModifierSystem`/AI goal-utility
     multipliers** (`src/ai/score_modifiers.py:25`) — a strategic-cognition mechanism, not a
     spawn/growth mechanism, and its thresholds are a single global pair, not per-species. This is
     the wrong tool for "per-species pacing constants" (AC #4) — see Recommendation below.

5. **`CampState`** (`src/core/state.py:1093-1122`): `id, kind, position, maturity, active, faction,
   last_raid_tick`. `CampUpdate` (`src/core/updates.py:836-850`): `id, maturity_delta, active_set,
   last_raid_tick_set`. Applied via `src/engine/apply_plan.py:263-273`
   (`new_mat = camp.maturity + c_upd.maturity_delta`). **Confirmed zero other production consumer**:
   `grep -rln "CampState\b" src/` returns only `camp.py`, `apply_plan.py`, `apply.py` (type-only
   passthrough), and `state.py` (definition). `grep -rn "\.maturity\b" src/` outside those files
   turns up only `state.maturity` — a **separate, unrelated, world-level global int field**
   (`AuthoritativeState.maturity`, consumed by `src/world/calamity.py:31`, `src/world/raid.py:34`,
   `src/world/boss.py:91`, `src/systems/world_systems/generator.py:116-134` (boss stat scaling),
   `src/engine/checkpoint.py:73`, `src/api/presenters/state_presenter.py:21,31`,
   `src/replay/fingerprint.py:99,124`) that must not be confused with, renamed, or touched by this
   ticket. **This confirms the ticket's own caution (point 5 in the task brief) is correct: no
   hidden live consumer of `CampState.maturity` exists** — only the producer (`camp.py`) and the
   apply-path patcher (`apply_plan.py`) touch it.

6. **Monster-kind identification**: `CampService.process_camps` itself filters monsters via
   `e.identity.role == EntityRole.MONSTER` (`camp.py:48`), not `entity.kind` string matching.
   `entity.kind` for spawned monsters is a free-form string (`"goblin_warrior"`, `"orc_warrior"`,
   generic `"monster"` — see `EntityGenerator.spawn_monster`, `src/systems/world_systems/
   generator.py:59-83`), not a stable small enum — unsuitable for a `not in [...]` gate the way
   `BiologicalSystem.update()` uses it. `EntityRole.MONSTER` (`src/core/enums.py:9`, IntEnum) is the
   correct, already-precedented filter. Note: `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`
   (DONE, in `tickets/done/`) found and fixed a real corpus-wide bug where monster-kind entities were
   frequently mistagged `role=CITIZEN` via `WorldCompiler.compile()` missing catalog access — that
   fix is already landed, so `identity.role == EntityRole.MONSTER` should now be reliable for real
   corpus content, but it is worth re-confirming against a real compiled world during Plan/Test if
   any doubt remains.

7. **`FeatureFlagManager`** (`src/domains/optimization/feature_flags.py`): all recent new-gameplay
   flags follow `ENABLE_<SUBSYSTEM_NAME>` (screaming-snake, subsystem-descriptive, not a verb),
   default `FeatureMode.OFF` per the documented DEV-002 policy unless real corpus/SHADOW-validation
   evidence exists (none exists here — this is a brand-new mechanic). Two wiring patterns exist in
   the codebase depending on where the gated code lives:
   - **Pipeline-phase flags** (e.g. `ENABLE_WORLD_EMERGENCE`): gated via `pipeline.py`'s
     `run_phase(name, upd, fn, feature_flag="ENABLE_X")` closure (`pipeline.py:102-133`), which reads
     `FeatureFlagManager` in scope at that layer.
   - **Sub-phase / non-`run_phase` flags** (e.g. `ENABLE_GUILD_QUEST_GENERATION`, checked in
     `src/ai/goals/scorers.py:253-254`): read directly off `state.feature_flags`:
     `flags = getattr(state, "feature_flags", None) or {}; if flags.get("ENABLE_X", "OFF") == "ON":`.
     This is the same pattern `kernel.py:1028` uses for `ENABLE_PUSH_EVENT_SHAPERS`. **This ticket's
     new system falls into the second category** — it will live inside `world_dynamics.py`'s
     macro-dynamics block (called via a single un-flagged `run_phase("world_dynamics", ...)`, not its
     own phase), so it must use the direct `state.feature_flags` read pattern, not `FeatureFlagManager`
     injection (which isn't threaded down to `world_dynamics.py`/`camp.py` today).

## Mechanics / Engine Constraints

- **`docs/mechanics/05_world_evolution.md` §2** ("Regional Trauma & Hazards"): "If `Trauma Score >
  50.0`, the region enters an unstable state" — the exact threshold `CampService` already codes and
  this ticket must reuse verbatim (`> 50.0`, not `>= 50.0`).
- **`docs/mechanics/05_world_evolution.md` §5** ("Age Bracket Thresholds (Entity-Level)"): documents
  the existing 3000/7000 `age_ticks` boundaries for `young`/`adult`/`elder` — this is the
  cohort/strategic-cognition vocabulary (see Current Behavior #4), explicitly *not* meant to be
  reused for per-species monster pacing (their thresholds are global, not species-tunable).
- **`docs/mechanics/05_world_evolution.md` §6** ("Calamities & World Threats"): only mentions "Threat
  Evolution: Monsters in high-hazard regions evolve to higher Evolution Levels" — no existing
  documentation of any monster-side maturity/territory mechanic. This chapter is the natural home
  for the new mechanic (see Docs Requiring Update).
- **CLAUDE.md Architecture Rule / Durable State Rule**: "Decision logic reads state. It does not
  authoritatively mutate durable state. Durable changes must be represented through typed
  records/updates." A new per-entity maturity/territory field must follow the same
  `EntityState`-field + `EntityUpdate`-delta + apply-path-patch pattern already used by
  `CampState.maturity`/`CampUpdate.maturity_delta`/`apply_plan.py` — not a raw dict/`properties`
  bag (`IdentityComponent.properties: Dict[str, Any]` exists but is explicitly free-form and
  disallowed for durable meaning per the Hard Rules).
- **Determinism** (CLAUDE.md Hard Rules): the maturity delta and any life-stage-transition/spawn
  trigger must be a pure function of `(state.tick, region.trauma_score, entity fields)` — no RNG
  beyond the already-deterministic `DeterministicRNG` used elsewhere in `src/world/`, no wall-clock.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: needs a new subsection (e.g. under or adjacent to §6
  "Calamities & World Threats") documenting the new creature-territory maturity mechanic once
  implemented — the per-tick delta formula, the trauma>50.0→1.5x reuse, and the life-stage-
  transition/spawn threshold. Per CLAUDE.md's Authoritative Mechanics Rule, new logic must be
  documented in the Bible the same session it lands, not deferred.
- `docs/parity_ledger/world_dynamics.yaml`: needs two new entries (next available IDs `WORLD-118`,
  `WORLD-119`, following the existing pattern at WORLD-104/105/106/117 — "New mechanic added by
  TCK-..." in `divergence_note`) — one for the maturity-delta-with-trauma-multiplier mechanism
  (AC #1), one for the life-stage-transition/new-occupant-spawn mechanism (AC #2), each with a real
  `test_path` once tests exist.
- `docs/guidelines/intentional_divergences.md`: **conditionally required** — only if AC #3 is
  resolved by *superseding* the HERO/VILLAGER-only biological gate for monster-kind entities (rather
  than respecting it / leaving monsters outside generic hunger/sleep). This choice is not yet made
  at investigation time (see Risks below) — Plan must decide it. If the implementer confirms the
  gate is respected (monsters stay outside generic hunger/sleep — the more likely outcome, since the
  live gate that actually matters, `ApplyPath._compute_entity_changes`, is a separate, higher-risk
  hot path this ticket should not touch per the Anti-Drift Hazards below), whoever resolves this
  bullet should add "Resolved during implementation, condition not met" to this bullet's own text
  per the conditional-bullet convention (`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-
  BLOCKED`), and the doc itself need not be touched.

The `docs/mechanics/01_entity_anatomy.md` chapter (path: `docs/mechanics/01_entity_anatomy.md`) is
not required to change for this ticket: it covers biological pressures/XP scaling in general, but
this ticket's Out of Scope explicitly excludes "Generic hunger/sleep biological simulation expansion
beyond monster-kind entities" — the new mechanic is a maturity/territory concept, not a hunger/sleep
extension, so it does not belong in that chapter. The `docs/parity_ledger/combat_movement.yaml`
entry `COMB-095` (life-stage modifier law, `legacy_verified`, `test_path: null`) is not required to
change either: it describes the pre-existing `LifeStageService`/goal-multiplier mechanism, which
this ticket's Recommendation below explicitly avoids reusing/touching (see Anti-Drift Hazards).

## Parity Ledger Overlap

- **`WORLD-030`** (`docs/parity_ledger/world_dynamics.yaml`, text: "Camp reinforcements occur on
  schedule", status: `verified`, priority: **P0**, `test_path: null`) and **`WORLD-031`** ("Camp
  reinforcement level increases when camp is full", status: `verified`, priority: **P0**,
  `test_path: null`) — cited at the top of `camp.py` ("Compliance IDs: WORLD-030, WORLD-031"). Both
  are P0 with no `test_path`, a **pre-existing** gap (not introduced by this ticket). This ticket's
  Out of Scope explicitly excludes modifying `CampService`'s existing camp-maturity multiplier, so
  these entries are not touched, but flagged here since they're the closest existing precedent this
  ticket reuses the shape of.
- **`WORLD-023`** ("World maturity increases on schedule", P0, verified) — this is the unrelated
  **global** `AuthoritativeState.maturity` field (see Current Behavior #5), not `CampState.maturity`
  or any new per-entity field. Not touched; flagged only to avoid confusion during implementation.
- **`WORLD-DEMO-003`** (age-bracket thresholds 3000/7000, P1, verified) and **`WORLD-DEMO-004`**
  (elder attribute modifiers, P1, verified) — conceptually adjacent (age/maturity thresholds) but
  explicitly a different vocabulary for a different subsystem (cohort/demographics, not per-entity
  monster maturity) per `TCK-20260824-LIFE-STAGE-TRANSITIONS`'s own Design Decision 1. Not touched.
- **New entries needed**: `WORLD-118`, `WORLD-119` (see Docs Requiring Update above) — no existing
  entry describes a per-entity monster-territory maturity mechanism.

## Prior Work

- **`TCK-20260824-LIFE-STAGE-TRANSITIONS`** (`stored_artifacts/`, DONE) is the single most relevant
  prior ticket. It: (a) confirmed `age_ticks` increments unconditionally for every entity via the
  same `ApplyPath._compute_entity_changes` fused path this investigation re-confirms (finding #3
  above matches its finding #7 exactly); (b) explicitly decided **not** to reuse
  `LifeStageService`/`identity.life_stage` for anything beyond AI goal-scoring, keeping it separate
  from `cohort.py`'s aggregate demographics vocabulary (Design Decision 1) — the same reasoning
  applies here: this ticket's per-species monster maturity is a third, distinct vocabulary and
  should **not** be folded into `LifeStageService`; (c) documents two silent-drop traps in the
  `IdentityUpdate`/`IdentityPatch` typed-update path (`IdentityUpdate.is_noop()`/`.merge()` must
  enumerate any new field, and `IdentityPatch.apply()`'s `replace()` call must explicitly pass the
  new field as a kwarg or `dataclasses.replace()` silently drops it) — **directly applicable** if the
  new per-entity maturity field is added to `IdentityComponent`/`IdentityUpdate` (see Recommendation
  below); this is the single highest-risk implementation trap identified in this investigation.
- **`TCK-20260701-SIMQ-EMIT-CAMP`** (DONE) confirmed `CampState` has no dynamic-construction path
  (`StateUpdate` has no `camps_add`; camps are pre-placed at world generation, `CampService` only
  evolves existing camps). Not directly blocking (this ticket doesn't create new camps, only new
  monster maturity within existing ones), but confirms the camp count itself is out of this ticket's
  reach — territory anchoring must work against the existing, fixed set of camps.
- **`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`** (DONE) — fixed a real corpus-wide bug
  where monster entities were mistagged `role=CITIZEN`. Confirms `entity.identity.role ==
  EntityRole.MONSTER` should now be a reliable filter (see Current Behavior #6).
- No prior ticket implements anything resembling per-entity territory maturity or creature life
  stages — this is confirmed new subsystem work, matching the ticket's own Request Summary.

## Risks and Open Questions

- **Blocking for Plan — AC #3's premise needs reinterpretation.** The "HERO/VILLAGER-only biological
  gate" the ticket names is `BiologicalSystem.update()`, which is dead code (zero production
  callers). The actual live gate-equivalent — `ApplyPath._compute_entity_changes`'s hunger/sleep/age
  increments — has **no kind restriction at all** and already runs for monsters today (Current
  Behavior #3). Plan must explicitly decide what AC #3 means in light of this: (a) treat it as
  satisfied trivially since the named dead-code gate imposes no real constraint either way (monsters
  were never touched by it in the first place — "respecting" it costs nothing extra), and confirm the
  new maturity system does not touch `ApplyPath._compute_entity_changes` or extend generic hunger/
  sleep to monsters (Out of Scope already forbids this); or (b) reinterpret AC #3 against the live
  path and treat any future decision to give monsters hunger/sleep as the thing needing an
  `intentional_divergences.md` entry (not applicable to this ticket unless Plan chooses to add
  monster hunger/sleep, which Out of Scope already forbids). **Recommendation: (a)** — this ticket's
  Scope and Out of Scope already forbid extending generic hunger/sleep to monsters, so the practical
  answer is "respected" (monsters stay outside generic hunger/sleep, and the new maturity/territory
  concept is an entirely separate typed field, not a repurposing of `BiologicalComponent`). No
  `intentional_divergences.md` entry should be needed under this reading — see the conditional
  Format-1 bullet above.
- **Not yet resolved — durable state shape for per-entity maturity.** Two real options: (1) add a
  new typed field to `IdentityComponent`/`IdentityUpdate` (e.g. `territory_maturity: float = 0.0`,
  parallel to existing growth fields `evolution_level`/`veterancy_points`), following the
  `CampState.maturity`/`CampUpdate.maturity_delta` delta-based precedent exactly; or (2) reuse
  `lifecycle.age_ticks` as the underlying "clock" but drive the trauma-scaled *rate* through a new
  per-species multiplier applied only for MONSTER-role entities inside the new dedicated service
  (not inside the shared hot-path `_compute_entity_changes`). **Recommendation: option (1)** — it
  mirrors `CampState.maturity` most directly (the ticket's own explicit reuse target), keeps the new
  mechanic fully isolated from the performance-sensitive fused-apply hot path, and avoids overloading
  `age_ticks` (which already has its own unconditional +1/tick semantics for *all* entities, monsters
  included, that this ticket must not disturb). Plan should confirm the exact field name/location.
- **Not yet resolved — territory anchoring.** No existing durable link from an entity to "its" camp
  (Current Behavior #1). Recommendation: reuse `CampService`'s own proximity-based inference (recompute
  nearest active camp within a bounded radius each processing tick) rather than adding a new durable
  `camp_id` field — lower blast radius, no new typed-update surface, and matches the existing
  precedent exactly. Plan should confirm this is sufficient for "anchored to a camp/territory" or
  decide a durable link is actually required (e.g. if per-species pacing needs to persist across a
  monster wandering outside the 10×10 proximity box).
- **Per-species pacing constants have zero existing anchor** (ticket's own Assumptions section,
  confirmed true by this investigation — no monster-species-specific numeric table exists anywhere
  in `src/world/` or `data/content/`). This is intentionally open creative territory per the ticket;
  not a gap to close here.
- **Pre-existing monster starvation/old-age risk** (Current Behavior #3) is real but out of this
  ticket's scope to fix — flagged so the new maturity system's design doesn't accidentally compound
  it (e.g. a maturity-driven spawn that creates monsters destined to starve before ever mattering).

## Anti-Drift Hazards

- **Do not touch `ApplyPath._compute_entity_changes`** (`src/engine/apply.py`) — it is the shared,
  performance-sensitive ("sub-100ms targets") fused-apply hot path for every entity in the
  simulation. The new creature-territory system must live as its own service (parallel to
  `CampService`), called from `world_dynamics.py`'s already-cadence-gated §3 macro-dynamics block —
  not as a new branch inside the universal per-entity fused apply.
- **Do not reuse `LifeStageService`/`identity.life_stage`/`get_stage_for_age()`** for monster
  maturity — confirmed a different subsystem (AI goal-scoring, fixed global thresholds) by
  `TCK-20260824-LIFE-STAGE-TRANSITIONS`'s own explicit Design Decision 1. Reusing it would also fail
  AC #4's "per-species pacing constants" requirement, since its thresholds are a single global pair.
- **If a new field is added to `IdentityComponent`/`IdentityUpdate`, remember the two silent-drop
  traps** `TCK-20260824-LIFE-STAGE-TRANSITIONS` already documented: `IdentityUpdate.is_noop()`/
  `.merge()` must enumerate the new field, and `IdentityPatch.apply()`'s `replace(new_id, ...)` call
  (`src/engine/patches.py:221-226`) must explicitly pass it as a kwarg — omission is silently
  swallowed by `dataclasses.replace()`/`extract_patches()`'s noop filter, producing a looks-correct
  implementation that does nothing.
- **Do not filter monster-kind entities via `entity.kind` string matching** — `kind` is a free-form
  per-species string (`"goblin_warrior"`, `"orc_warrior"`, etc.), not a stable enum. Use
  `entity.identity.role == EntityRole.MONSTER`, matching `CampService`'s own existing convention.
- **Do not modify `CampState`/`CampUpdate`/`CampService.process_camps`'s existing trauma-multiplier
  logic** — explicitly Out of Scope; reuse the *shape* (`if region.trauma_score > 50.0: delta *=
  1.5`) in new code, do not refactor the existing camp code to share it.
- **Do not confuse `AuthoritativeState.maturity` (global, world-level) with `CampState.maturity`
  (per-camp) or the new per-entity field** — three genuinely distinct fields; a naming collision in
  code comments or variable names would be a real source of future confusion given the existing
  precedent of "maturity" already meaning two different things in this codebase.
- **The FeatureMode flag must gate the new service directly via `state.feature_flags`** (matching
  `ENABLE_GUILD_QUEST_GENERATION`'s pattern) — not assume `FeatureFlagManager` is available inside
  `world_dynamics.py`/`camp.py`, since it isn't threaded down to that layer today.
