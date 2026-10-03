---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-READINESS-SPEED-FORMULA
artifact_type: plan
tags: [combat, progression]
---

# Implementation Plan — TCK-20260831-READINESS-SPEED-FORMULA

## Summary
Add `readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)` to
`LevelingService.recalculate_combat_stats()`'s Step 1 block, wire the new dict key through the two
places that would otherwise silently drop it (`get_effective_stats()`'s pass-through, already
safe by construction, and `ApplyPath`'s PH8 `replace(new_com, ...)` call, which is not), add three
unit/regression tests plus one hand-orchestrated pre-change-vs-post-change corpus validation script
that isolates the one real population segment whose agility actually diverges from the dataclass
default in production data (entities that have aged into `LifeStage.ELDER`), and update the two
stale docs plus a new parity ledger entry (`COMB-318`). The `k=1.0` coefficient, the corpus
validation's exact metric/window/variant design, and the floor are all resolved below — see Open
Questions for the explicit confirmation that nothing is left for Review to decide.

## Steps

### Step 1 — Add the `readiness_speed` formula to `recalculate_combat_stats()`
**Files:** `src/progression/leveling.py`
**Change:** In `LevelingService.recalculate_combat_stats()`'s Step 1 block (`src/progression/leveling.py:99-104`,
confirmed by direct read: `max_hp`/`atk`/`def_stat`/`evasion` are all computed here as flat
`base_X + attribute_term`, no `readiness_speed` key exists anywhere in the function today, confirmed
by reading the full function body lines 76-184 and its final returned dict at lines 176-184), add
one new line immediately after the `evasion` line (line 103):
```python
readiness_speed = max(1.0, 10.0 + (attributes.agility - 5) * 1.0)
```
Add `"readiness_speed": readiness_speed` to the returned dict (lines 176-184), following the
existing 1:1 key-name-matches-`CombatComponent`-field convention already used for every other key
in that dict (`CombatComponent.readiness_speed` confirmed at `src/core/state.py:311`,
`readiness_speed: float = 10.0`).

**Formula and `k=1.0` — reasoning (do not re-derive, this is decided):**
- Reference point: `AttributeComponent.agility` defaults to `5` (`src/core/state.py:442`,
  confirmed by direct read of the dataclass). The `(agility - 5)` term is required, not
  `agility * k` alone, to satisfy backward compatibility (AC #2) — this matches every existing
  hardcoded test fixture that never sets agility explicitly and therefore gets the `5` default.
- Precedent coefficients read directly in this session: `evasion = base_evasion + (agility * 0.001)`
  (`leveling.py:103`) and `move_cost = 10.0 + (total_weight/5.0) - (agility*0.1)`
  (`leveling.py:154`, with an inline floor `move_cost = max(5.0, move_cost)` at `leveling.py:155`).
- Real corpus agility range, traced through every writer of `AttributeComponent.agility` in `src/`
  (not inferred from content — `data/content/entities/stat_profiles.yaml`'s `attribute_bias:
  agility: "medium"/"high"` tags are confirmed non-numeric and unconsumed by any `src/` mapping,
  same as investigation's finding for `races.yaml`):
  - `execute_allocate_ap()` (`src/engine/domain/core_actions.py:294-324`) has branches only for
    `"strength"` and `"vitality"` — **no `"agility"` branch exists**, so players/AI can never
    allocate points into agility via level-up.
  - `evolution.py`'s non-hero level-up path (`src/engine/evolution.py:125-132`) sets
    `vitality_delta`/`strength_delta`/`endurance_delta` only — agility untouched.
  - The only durable, non-default agility value ever written in `src/` is a **one-time** elder
    life-stage decay: `compute_elder_attribute_update()` (`src/domains/demographics/cohort.py:
    107-109`) sets `agility_delta=-int(attrs.agility*0.3)` (= `-1` at the default `agility=5`,
    integer truncation), applied exactly once per entity, gated by
    `LifeStageService.is_forward_transition(...)` at `src/systems/lifecycle_systems/lifecycle.py:
    57-68` (forward-only, fires once when an entity crosses into `LifeStage.ELDER`).
  - The only other agility modifier in `src/`, `fleet_foot`'s `attribute_bonuses: {"agility": 3}`
    (`src/progression/breakthroughs.py:18-22`), is confirmed **transient** (applied live inside
    `get_effective_stats()` via `BreakthroughService.apply_bonuses()`, never written to durable
    `AttributeComponent` state) **and confirmed never granted in real gameplay**:
    `docs/mechanics/attribute_progression_contract.md:237-240` states "nothing in
    production/gameplay code constructs `IdentityUpdate(breakthroughs_add=[...])` ... never
    invoked outside tests." No class tier in `CLASS_TIER_REGISTRY`
    (`src/core/classes.py:59-72`) touches agility either (WARRIOR/MAGE tiers bonus
    strength/vitality/intelligence/spirit/wisdom/endurance only; ROGUE has no tier options
    registered at all).
  - **Conclusion: the only real, durable, population-scale agility divergence from `5` that exists
    in actual corpus runs today is `4` (elder-decayed entities), not any higher value.** The
    formula's upward direction (tested at the unit level, e.g. `agility=15`) currently has zero
    real corpus population expressing it.
- Given that real range, `move_cost`'s magnitude (`k=0.1`) would produce only a ±0.1 swing on the
  only real non-default population (`agility=4` → `readiness_speed=9.9`), a <1% cadence change —
  this is exactly the "hollow metric" failure mode `METAMORPHIC-LAB-PILOT` already hit once
  (investigation.md, Prior Work). `evasion`'s magnitude (`k=0.001`) is deliberately flavor-scale
  for a `[0, 0.95]` probability stat and is the wrong precedent for a stat this ticket's own title
  frames as needing "a real...formula" with actual behavioral consequence. `k=1.0` is chosen
  instead: at the only real non-default population (`agility=4`), it yields `readiness_speed=9.0`
  — a 10% slower passive regen (≈11.1 ticks to refill from 0 instead of 10), proportionate to the
  already-implemented, already-felt scale of other elder penalties in the same subsystem (elder
  `strength`/`vitality`/`endurance` deltas at `cohort.py:107-114` are similarly ~20-30% cuts on
  their respective base values), large enough to be a real, detectable signal for Step 6's corpus
  validation rather than sub-noise, and still nowhere near the `readiness_speed <= 0` "regen
  disabled" failure mode documented in `apply.py:127` (even a hypothetical `agility=0` entity,
  which cannot occur via any current writer, yields `readiness_speed=6.0` under this formula, well
  clear of zero).
- **Symmetric, not one-sided**: below-reference agility reduces `readiness_speed`, matching the
  ticket's own AC #1 wording ("higher agility... faster regen" implies the converse for lower
  agility) and thematically consistent with the elder cohort's already-documented "combat
  effectiveness" decline (`cohort.py:91` docstring).
- **Floor at `1.0`, inline, mirroring `move_cost`'s own inline-floor pattern** (`leveling.py:155`,
  not `evasion`'s deferred-to-`get_effective_stats()` clamp pattern) rather than deferring — because
  `AttributeComponent` is a plain frozen dataclass constructible directly with any `agility` value
  including `0` or negative (`src/core/state.py:438-450`; only `AttributePatch.apply()` at
  `src/engine/patches.py:583-593` clamps to an upper bound of `100`, and even that has **no lower
  bound** — so a directly-constructed low-agility entity, e.g. in a future content/test path, is a
  real, not merely theoretical, way to hit a very negative `(agility-5)` term). Floor prevents ever
  reaching the `readiness_speed <= 0` "readiness permanently locked" state flagged in
  investigation.md's Risks section (`apply.py:127`: `if comb.readiness < 100.0 and
  comb.readiness_speed > 0`).
**Do NOT touch:** `move_cost`'s existing agility term (`leveling.py:154`) — same attribute, opposite
sign convention (higher agility *lowers* move_cost, higher agility *raises* readiness_speed); do
not consolidate or share code between the two formulas. Do not touch Steps 2-5 of the same function
(equipment bonuses, passive skills, traits, tactical role derivation).
**Verify:** `test_readiness_speed_reference_agility_backward_compatible` and
`test_readiness_speed_derives_from_agility_two_values` (Step 4).

### Step 2 — Fix the PH8 silent-drop point in `ApplyPath`
**Files:** `src/engine/apply.py`
**Change:** In `ApplyPath._apply_entity_update_to_dict()`'s PH8 block, the `replace(new_com, ...)`
call (`src/engine/apply.py:507-515`, confirmed by direct read — currently an explicit kwarg list:
`max_hp`, `atk`, `def_stat`, `evasion`, `move_cost=derived.get(...)`, `range=derived.get(...)`,
`tactical_role=derived.get(...)`, with **no `readiness_speed` kwarg**), add one line following the
exact `.get(...)`-with-fallback pattern already used by `move_cost`/`range`/`tactical_role` in the
same call:
```python
readiness_speed=derived.get("readiness_speed", new_com.readiness_speed),
```
Insert it anywhere in the kwarg list (after `evasion=derived["evasion"],` is a natural spot,
matching the dict's own key order from Step 1). `derived` here is the dict returned by
`SkillScalingService.get_effective_stats()` (called at lines 497-505), which is a plain pass-through
of whatever `recalculate_combat_stats()` returns (`src/engine/rpg_depth.py:369-392`, confirmed by
direct read — no allowlist/filtering logic between `recalculate_combat_stats()`'s return and
`get_effective_stats()`'s return; the only mutations in between are wound/scar penalty subtraction
on `atk`/`def_stat`/`max_hp` and an evasion clamp, none of which touch `readiness_speed`).

**Every other writer of `CombatComponent` at this call site, and how this change interacts with
each:**
- This `replace(new_com, ...)` call (`apply.py:507-515`) is the only writer of `readiness_speed`
  being modified in this step. It does not run unconditionally — it is gated by the `stats_dirty`
  check (`apply.py:476-489`), which is `True` only when `update.attributes`, `update.equipment`,
  or specific `identity`/`wound_update` fields changed. When `stats_dirty` is `False`,
  `readiness_speed` is untouched by this block entirely (the field simply carries over from
  `entity.combat` via whatever earlier patch step populated `new_com`).
- **`EntityState.to_readonly()`** (`src/core/state.py:905`, per investigation.md, already fixed by
  COMB-298 to include `readiness_speed`) is a *different* writer, on a *different* path
  (readonly-view reconstruction, not the PH8 apply-path dict). Not touched by this step; already
  correct.
- **`ApplyPath._fast_replace_identity()`** (`src/engine/apply.py:529-549+`, per investigation.md,
  already fixed by `CREATURE-TERRITORY-LIFECYCLE`) is a third writer, used on a distinct fast-path
  identity-only update route that does not recompute derived stats at all — it does not call
  `recalculate_combat_stats()`/`get_effective_stats()`, so it never had a `readiness_speed`
  derivation to drop in the first place; not touched by this step.
- **Passive regen** (`apply.py:122-130`, `if comb.readiness < 100.0 and comb.readiness_speed > 0:
  readiness += readiness_speed`) *reads* `readiness_speed` every tick but never writes it — no
  ordering conflict with this step's write, since PH8 (this block) and the passive-regen block
  operate on different fields of the same `CombatComponent` within the same
  `_apply_entity_update_to_dict()` call and are not both stats_dirty-gated the same way; confirm no
  regression via Step 4's Test 3 and via `test_readiness_regenerates_passively_per_tick`
  (unaffected — it never triggers `stats_dirty`, only passes an explicit override at entity
  construction).
- **`V2EntityBuilder.combat(readiness_speed=...)`** (`src/core/builder.py:253,272`) is a fourth,
  construction-time-only writer (raw kwarg pass-through, no derivation) — used by test fixtures to
  set an initial value before any `ApplyPath` run; not touched, and not in conflict since it only
  ever runs before the entity enters the pipeline this step modifies.
**Do NOT touch:** the `class_id`/breakthrough-related lines in the same PH8 block, or the
hp-clamp/stamina-refill logic immediately following the `replace(new_com, ...)` call
(`apply.py:517-525`) — copy-paste risk flagged explicitly in investigation.md and test_plan.md as
the highest-risk single line in this ticket.
**Verify:** `test_readiness_speed_survives_apply_path_replace` (Step 4), plus the existing
`test_class_tiers.py`/`test_breakthroughs.py` suites (regression guard that this kwarg addition
doesn't disturb unrelated fields the same call sets).

### Step 3 — No change needed to `get_effective_stats()` itself
**Files:** none (documentation-only note, no code change in this step)
**Change:** `SkillScalingService.get_effective_stats()` (`src/engine/rpg_depth.py:342-392`,
confirmed by direct read) has no allowlist on the dict it returns — it mutates specific keys
(`atk`, `def_stat`, `max_hp` for wound/scar penalties; `evasion` for the clamp) and returns the
same dict object otherwise unchanged (line 392: `return base_stats`). Once Step 1 adds
`"readiness_speed"` to `recalculate_combat_stats()`'s returned dict, it flows through this function
automatically with zero changes required here.
**Do NOT touch:** do not add a wound/scar penalty branch for `readiness_speed` in this function.
`docs/mechanics/02_combat_laws.md` §5 documents wound `speed_penalty` as "computed and stored on
the wound... `speed_penalty` is computed" but confirmed **not yet read by
`SkillScalingService.get_effective_stats()`** (`docs/mechanics/02_combat_laws.md:79-82`, and
`get_effective_stats()`'s wound-penalty block at `rpg_depth.py:377-381` only reads
`wound_pen["atk_penalty"]`/`["def_penalty"]`/`["max_hp_penalty"]` — no `speed_penalty` key
accessed). This is a known, separate, un-scoped gap per investigation.md's Anti-Drift Hazards —
this ticket's `readiness_speed` derivation must not start silently reading it as a side effect of
touching this file.
**Do NOT touch:** the evasion clamp (`rpg_depth.py:390`) or wound/scar penalty blocks
(`rpg_depth.py:377-387`).
**Verify:** `tests/unit/core/test_rpg_depth.py`'s existing `TestEffectiveStats` suite (lines
471-526) must keep passing unchanged — confirms adding a new dict key doesn't perturb existing
`atk`/`max_hp`/etc. assertions.

### Step 4 — New tests
**Files:** `tests/unit/core/test_rpg_depth.py`, `tests/unit/combat/test_readiness_regen.py`
**Change:**
1. `test_readiness_speed_derives_from_agility_two_values` (new method on `TestEffectiveStats` in
   `tests/unit/core/test_rpg_depth.py`, following the file's existing per-derived-stat-concern
   organization): build two `AttributeComponent`s differing only in `agility` — `agility=5` and
   `agility=15` — call `SkillScalingService.get_effective_stats(attrs)` for each, assert
   `stats_15["readiness_speed"] > stats_5["readiness_speed"]` (direction check, not just
   inequality — guards the exact sign-confusion hazard flagged in test_plan.md against
   `move_cost`'s inverted sign), and assert the exact values: `stats_5["readiness_speed"] == 10.0`,
   `stats_15["readiness_speed"] == 20.0` (per Step 1's formula: `10.0 + (15-5)*1.0 = 20.0`).
2. `test_readiness_speed_reference_agility_backward_compatible` (same file/class): build an entity
   via `AttributeComponent()` (no explicit agility, gets the dataclass default `5`), call
   `get_effective_stats()`, assert `stats["readiness_speed"] == 10.0` exactly. This is the direct
   regression guard for AC #2.
3. `test_readiness_speed_survives_apply_path_replace` (new test in
   `tests/unit/combat/test_readiness_regen.py`, co-located with the sibling silent-drop regression
   test `test_readiness_speed_survives_to_readonly_reconstruction` per test_plan.md's
   discoverability rationale): build an entity with `agility != 5` (e.g. `agility=15` via
   `.attributes(agility=15)` on `V2EntityBuilder`, confirmed builder supports an `.attributes(...)`
   call per investigation.md's citation of `_build()`'s pattern in the same file), trigger a
   `stats_dirty` update via `ApplyPath.apply_generation(state, StateUpdate(entity_updates={eid:
   EntityUpdate(entity_id=eid, attributes=AttributeUpdate(agility_delta=0))}), ...)` — an
   attributes-non-`None` update is sufficient to flip `stats_dirty` True per `apply.py:477`
   regardless of the delta's numeric value — and assert
   `next_state.entities[eid].combat.readiness_speed == 20.0` (the derived value, not the stale
   `10.0` default). This is the direct regression guard for Step 2's fix — the single highest-risk
   line in this ticket per investigation.md and test_plan.md.
**Do NOT touch:** any of the 4 existing tests in `test_readiness_regen.py` (all pass an explicit
`readiness_speed=` override at construction, bypassing derivation entirely — must keep passing
unmodified) or the existing `TestEffectiveStats` methods.
**Verify:** run
`pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_readiness_regen.py -v` — all new
and existing tests pass.

### Step 5 — Full regression suite for the progression/apply-path domain
**Files:** none (test execution only)
**Change:** Run the two scoped pytest commands from test_plan.md:
```
pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_readiness_regen.py \
       tests/unit/progression/ tests/unit/core/test_rpg_math.py \
       tests/unit/core/test_domain_6_hardening.py tests/unit/quest/test_progression_lifecycle.py \
       tests/unit/resource/test_durability_repair.py -m "not slow"
```
```
pytest tests/integration/pipeline/test_recovery_gaps.py \
       tests/integration/combat/test_class_tier_win_rate.py -m "not slow"
```
```
pytest tests/arena/test_arena_regional_control.py -m "not slow"
```
**Do NOT touch:** any file under these test suites unless a genuine new failure surfaces that
traces directly to Steps 1-2 (in which case fix the *implementation*, not the test's assertion —
per the project's Gate Integrity rule).
**Verify:** all listed suites pass.

### Step 6 — Corpus validation (mandatory per ticket Scope, not a bare unit-test swap)
**Files:** a throwaway script under `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/`
(e.g. `corpus_validation.py`), not a permanent `tests/` file — matching both same-batch precedents
(`METAMORPHIC-LAB-PILOT`, `RACE-RELATIONS-MATRIX`) treating their pre/post-code corpus runs as
throwaway, since a pre-change/post-change code split cannot be a permanent CI-running test.
**Change — design resolution (this was investigation's flagged open question, now resolved):**

*Why not "vary agility between two entities in the same run" (option (a) from the initial framing)
as the sole design:* the only real, durable, population-scale agility divergence in production data
is the elder cohort (`agility=4` vs default `5` — see Step 1's citation trail). But
`LifeStageService.get_goal_multipliers()` (`src/ai/life_stage.py:32-37`) already gives
`LifeStage.ELDER` a `"combat": 0.5` goal-multiplier — elders are already, independently, half as
likely to pursue combat goals. An intra-run elder-vs-non-elder comparison would conflate this
pre-existing behavioral confound with the new `readiness_speed` effect; a difference could not be
attributed cleanly to the formula.

*Why not a pure whole-run pre/post-code aggregate either (investigation's literal suggestion, taken
unmodified):* the non-elder majority of any corpus population has `agility=5` in both the baseline
(pre-change) and compared (post-change) runs — bit-identical `readiness_speed=10.0` either way,
since neither `execute_allocate_ap()` nor any class tier nor (in practice) any breakthrough ever
moves a real entity's agility. A whole-run aggregate `combat_damage`-rate would dilute the one real
signal source (entities that crossed into `ELDER` during the run) into a population where 90%+ of
attackers are unaffected either way — high risk of a degenerate, hollow `baseline == compared`
result, the exact trap `METAMORPHIC-LAB-PILOT` already hit once.

**Resolved design — pre/post-code variant axis (isolates the formula's effect by holding all AI
behavior/goal-multipliers identical across both runs — the elder-combat-avoidance confound cancels
out because it is present equally in baseline and compared), restricted to a late-run metric
window (isolates the signal by counting only the period where the one real affected population
segment — entities that aged into ELDER — actually exists):**
1. Confirmed thresholds: `LifeStageService.get_stage_for_age()` (`src/ai/life_stage.py:41-55`)
   returns `ELDER` at `age_ticks >= 7000`. `age_ticks` increments by exactly `1` per simulation
   tick for every entity, unconditionally (`src/engine/apply.py:96`: `new_age = life.age_ticks +
   1`), and every world-generated entity starts at `age_ticks=0` (`lifecycle.py:54` comment,
   confirmed). `LifecycleComponent.max_age_ticks` defaults to `10000` (`src/core/state.py:146`).
   So for an entity present since world start, `age_ticks ≈ tick`, and it is eligible to be
   `ELDER` for the tick window `[7000, 10000)` before natural old-age death.
2. Pick a real corpus world with a population that plausibly survives past tick 7000 while still
   fighting in that window — reuse `unit_faction_tension` (`data/worlds/unit_faction_tension/`,
   confirmed on disk by `RACE-RELATIONS-MATRIX`'s plan, "already proven population-stable to 2000
   ticks") if a longer stability check at 9000+ ticks holds, else Implementer selects the closest
   equivalent long-running stable world from `data/worlds/` and records the substitution reason.
   Run length: **9500 ticks** (leaves a 2500-tick elder-eligible window: `[7000, 9500]`). Seeds:
   **3** (matching `RACE-RELATIONS-MATRIX`'s precedent seed count).
3. **Baseline variant** = current code before Steps 1-2 (`git stash` the diff, or run against the
   pre-ticket commit). **Compared variant** = code after Steps 1-2 land. Run the identical
   world/scenario/experiment (`ScenarioLabOrchestrator(...).run_lab(...)`, matching
   `RACE-RELATIONS-MATRIX`'s exact hand-orchestration pattern, bypassing `MutationLabOrchestrator`
   since a `src/` code formula is not `WorldSpec`-addressable per investigation.md's Prior Work
   citation) with the same seeds for both.

   **Observability mode must be pinned explicitly to `"STANDARD"` — do not leave it unset or set
   it to `"LONG_RUN"`.** `ExperimentObservabilitySpec.mode` (`src/lab/schema.py:106`, confirmed by
   direct read: `mode: str = Field(..., description="Observability detail mode, e.g. 'LONG_RUN'")`)
   is a required free-string field with **no schema-enforced safe default**. It is resolved by
   `ScenarioLabOrchestrator._resolve_obs_mode()` (`src/lab/orchestrator.py:50-63`, confirmed by
   direct read of the mapping): `"STANDARD"` → `ObservabilityMode.NORMAL` (line 60); any
   unrecognized or missing string — including an empty/omitted `mode` — falls back to
   `ObservabilityMode.LIGHT` (line 63, `mapping.get(mode_str, ObservabilityMode.LIGHT)`); and the
   label `"LONG_RUN"`, which an implementer would naturally reach for on a 9500-tick corpus run,
   maps to `ObservabilityMode.LONG_RUN` — the *other* gated mode, not a safe choice either. This
   matters specifically because `combat_damage` — the exact event this step's metric filters on
   (point 4 below) — is silently suppressed for non-lethal hits whenever the resolved mode is
   `LIGHT` or `LONG_RUN`: the gate in `_shape_combat_events()` (confirmed by direct read at
   `src/observability/event_shapers.py:224`) reads
   `if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):` — a
   non-lethal hit only produces a `combat_damage` event when the resolved mode is *not* LIGHT or
   LONG_RUN. The elder-window metric (point 4) is built on routine, non-lethal damage ticks, not
   just kills. Running under the silent `LIGHT` default, or under the intuitively-but-wrongly-named
   `"LONG_RUN"` label, would silently drop most or all of the signal in **both** baseline and
   compared runs — producing either a hollow `baseline == compared` PASSED (via
   `monotonic_non_increasing`'s `compared_val <= baseline_val` trivially holding at zero-vs-zero
   events) or a lethal-only sample that looks like real evidence but isn't measuring what this
   ticket claims. `"STANDARD"` resolves to `ObservabilityMode.NORMAL`, which is not in the gated
   `(LIGHT, LONG_RUN)` tuple, so it is the correct, safe choice. Construct the throwaway spec with
   `observability=ExperimentObservabilitySpec(mode="STANDARD", record_events=True, ...)` explicitly
   in the script — never omit `mode` and never pass `"LONG_RUN"`.
4. For each seed's `simulation_events.jsonl`, filter to `event_type == "combat_damage"`
   (`src/observability/event_shapers.py:230-234`, confirmed payload includes `attacker_id`) **and**
   `tick >= 7000`. Compute `elder_window_damage_rate = filtered_event_count / 2500` (the window
   width), averaged across the 3 seeds, for each variant.
5. Build `variant_metrics = {"baseline": {"elder_window_damage_rate": <baseline_avg>, "run_count":
   3}, "compared": {"elder_window_damage_rate": <compared_avg>, "run_count": 3}}` and call
   `MetamorphicRuleEngine.evaluate_rules()` (`src/lab/metamorphic.py:164-176`, same signature
   confirmed by `RACE-RELATIONS-MATRIX`'s plan) with:
   ```python
   spec = ExpectedRelationshipSpec(
       id="readiness_speed_elder_window_check",
       type="monotonic_non_increasing",
       metric="elder_window_damage_rate",
       baseline_variant="baseline",
       compared_variant="compared",
   )
   ```
   **`monotonic_non_increasing`, not `monotonic_non_decreasing`** — this is a deliberate,
   non-obvious choice: the formula itself is symmetric (Step 1), but the *only real corpus
   population* it currently affects moves agility **down** (elder decay, `5→4`), never up (no real
   writer ever raises agility above `5` — see Step 1's citation trail). So the real, expected
   corpus-observable direction for this specific check is a *decrease* from baseline to compared,
   not an increase. This does not contradict the formula's tested increase-direction (Step 4, Test
   1, `agility=15`) — that is a synthetic unit-test value with no real population instance today.
6. Assert `results[0].status == "PASSED"`. If the initial 9500-tick/3-seed run produces a
   degenerate `baseline == compared` result (plausible — the elder-window population may still be
   small), follow the precedent empirical escalation (`METAMORPHIC-LAB-PILOT`,
   `RACE-RELATIONS-MATRIX`): first widen the window/run length (e.g. 12000 ticks, window
   `[7000, 12000]`) before adding seeds, since a wider elder-eligible window increases the elder
   attacker sample size directly; do not accept a hollow `PASSED` from a zero-difference result
   without first trying this.
**Do NOT touch:** `data/worlds/`, `data/content/`, or any `WorldSpec`/`ScenarioSpec` file
permanently — any world/scenario/experiment spec authored for this validation is throwaway,
created and torn down inside the script, matching `RACE-RELATIONS-MATRIX` Step 12's teardown
discipline. Do not leave `data/lab_runs/` output on disk — clean up per the project's Definition of
Done (`rm -rf data/runs/*` equivalent for lab runs). Do not leave `observability.mode` unset and do
not set it to `"LONG_RUN"` — both silently gate off the exact `combat_damage` signal this step
measures (see point 3's rationale, `event_shapers.py:224`).
**Verify:** the script's own printed `results[0].status == "PASSED"` output, captured in this
ticket's Implementation Notes / Completion Summary as the real evidence artifact (not re-run in
CI); additionally, before trusting a `PASSED` result, confirm the script's constructed
`ExperimentObservabilitySpec.mode == "STANDARD"` literally appears in the throwaway spec (grep the
script, or assert it inline) — a silent fallback to `LIGHT` would still print `PASSED` on a hollow
zero-events result, so the mode pin itself must be checked, not just the final status string.

### Step 7 — Update `docs/mechanics/02_combat_laws.md` §7
**Files:** `docs/mechanics/02_combat_laws.md`
**Change:** In the "Passive Regeneration" bullet (`docs/mechanics/02_combat_laws.md:135-141`,
confirmed by direct read: currently states "an entity below 100.0 readiness regenerates by its own
`readiness_speed` stat (`CombatComponent.readiness_speed`, default **10.0/tick**), capped at
100.0"), replace "default **10.0/tick**" framing with the derivation: state that
`readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)`, computed in
`LevelingService.recalculate_combat_stats()`, so `10.0/tick` is the value **at reference/baseline
agility (`5`)**, not a universal flat default; cite the new parity entry `COMB-318` (Step 9).
**Do NOT touch:** the readiness gate's numeric thresholds (`>= 100.0`, `-100.0` reset) or any other
bullet in §7 — out of scope per the ticket's Out of Scope section (no rebalancing of gate pacing).
**Verify:** manual doc review; no automated test covers doc prose, but `COMB-318`'s `v2_evidence`
(Step 9) must match this doc's stated formula exactly (parity requirement).

### Step 8 — Update `docs/mechanics/attribute_progression_contract.md`
**Files:** `docs/mechanics/attribute_progression_contract.md`
**Change:** In the "Derived Stat Recalculation Order" section's Step 1 code block
(`docs/mechanics/attribute_progression_contract.md:135-142`, confirmed by direct read — currently
lists `max_hp`/`atk`/`def_stat`/`evasion`/`atk_range` only), add the new
`readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)` line to that same code block (Step 1 of
the enumerated order, matching where it's actually computed in `leveling.py`). Also update the
"RPG Meaning"/summary paragraph's enumerated derived-stat list (which currently reads "All derived
stats (HP, ATK, DEF, evasion, move cost, tactical role)... recalculated deterministically") to
include `readiness_speed`. Add a pointer to Step 4's new tests in the Regression Tests table if one
exists in this doc's existing structure (Implementer confirms exact table format before editing).
**Do NOT touch:** Steps 2-6 of the same enumerated order (equipment, passive skills, traits, move
cost scaling, tactical role) — only Step 1 changes.
**Verify:** manual doc review; cross-check against Step 1's actual code.

### Step 9 — New parity ledger entry `COMB-318`
**Files:** `docs/parity_ledger/combat_movement.yaml`
**Change:** Confirmed highest existing `COMB-*` id in this file is `COMB-317`
(`docs/parity_ledger/combat_movement.yaml:4115-4136`, confirmed by direct read of the last entry in
the file) — next free id is `COMB-318`. Append a new entry (do not edit `COMB-298` — see reasoning
below) following the exact schema shape of the `COMB-316`/`COMB-317` entries read directly above:
```yaml
- id: COMB-318
  text: readiness_speed is derived from agility (readiness_speed = max(1.0, 10.0 + (agility - 5)
    * 1.0)) inside LevelingService.recalculate_combat_stats(), rather than always the flat 10.0
    dataclass default. Reference/baseline agility (5) preserves readiness_speed == 10.0 exactly,
    keeping every existing test fixture that never sets agility valid. The derived value flows
    through SkillScalingService.get_effective_stats() and ApplyPath's PH8 replace(new_com, ...)
    call to reach the live CombatComponent.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: "src/progression/leveling.py Step 1 block (readiness_speed formula, new line);
    src/engine/apply.py:507-515 (replace(new_com, ...) now includes
    readiness_speed=derived.get('readiness_speed', new_com.readiness_speed)). Corpus-validated
    via hand-orchestrated pre/post-code MetamorphicRuleEngine.evaluate_rules() check
    (staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/corpus_validation.py),
    monotonic_non_increasing on elder_window_damage_rate, PASSED. Landed in
    TCK-20260831-READINESS-SPEED-FORMULA."
  proof_type: regression
  test_path: tests/unit/core/test_rpg_depth.py::TestEffectiveStats::test_readiness_speed_derives_from_agility_two_values,
    tests/unit/core/test_rpg_depth.py::TestEffectiveStats::test_readiness_speed_reference_agility_backward_compatible,
    tests/unit/combat/test_readiness_regen.py::test_readiness_speed_survives_apply_path_replace
  divergence_note: null
  support_boundary: null
```
**Reasoning for a new entry instead of editing `COMB-298`:** `COMB-298`
(`docs/parity_ledger/combat_movement.yaml:3301-3341`) describes the passive-regen *mechanism's
existence* (field exists, defaults to 10.0, applied every tick) — it makes no claim about
derivation and remains fully true after this ticket. Editing it to also claim agility-derivation
would misrepresent what its own `v2_evidence`/`test_path` actually verified (its two tests,
`test_readiness_regenerates_passively_per_tick` and
`test_readiness_speed_survives_to_readonly_reconstruction`, both pass an explicit
`readiness_speed=` override and never exercise the new derivation path). Per the ticket's own "or a
new entry" alternative and investigation.md's Parity Ledger Overlap section.
**Do NOT touch:** `COMB-298`'s text, status, or `v2_evidence` fields. Do NOT touch `COMB-300` (same
readiness subsystem, orthogonal — movement no longer costs readiness at all, unaffected by how fast
readiness regenerates).
**Verify:** `python3 tools/parity_ledger_writer.py` schema validation (or equivalent lint used by
this repo for parity YAML), if one exists; otherwise manual YAML validity check
(`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/combat_movement.yaml'))"`).

## Scope Guards
- No code in this ticket reads or references `AptitudeComponent.agi_apt`
  (`src/core/state.py:522`, default `1.0`) anywhere. Confirmed unread by `recalculate_combat_stats()`
  or `get_effective_stats()` today (investigation.md). The agi_apt-modulated multiplier half of the
  formula is deferred to idea 1/Genetics — do not implement any part of it, do not add a
  placeholder/stub for it, and do not add a code comment implying it is "coming soon" in a way that
  couples this ticket's landing to that future ticket.
- Do not touch `move_cost`'s existing agility term (`leveling.py:154`) or its sign convention.
- Do not add a wound/scar `readiness_speed` penalty path in `get_effective_stats()` — `speed_penalty`
  stays computed-but-unread, unchanged from today (Step 3).
- Do not edit `COMB-298`'s text/status/evidence (Step 9).
- Do not rebalance the readiness gate's numeric thresholds (`>= 100.0`, `-100.0` reset, 100.0 cap)
  — `TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK` already ruled out rebalancing the *default*
  without corpus evidence; this ticket reframes the source as a derivation (not a default-value
  rebalance) and satisfies that ruling's spirit via Step 6's corpus validation, but the gate itself
  is untouched.
- Do not leave any throwaway `WorldSpec`/`ScenarioSpec`/`data/lab_runs/` artifacts from Step 6 on
  disk after the ticket closes.
- Do not touch `EntityState.to_readonly()` or `ApplyPath._fast_replace_identity()` — both already
  correctly handle `readiness_speed` from prior tickets (investigation.md, confirmed).

## Dependency Map
- Step 1 (formula) has no dependencies — implement first.
- Step 2 (PH8 fix) is independent of Step 1's exact `k` value but depends on Step 1 existing (the
  `derived` dict must contain a `"readiness_speed"` key for Step 2's `.get(...)` to have anything
  meaningful to read) — implement second.
- Step 3 is a no-op verification step, can run any time after Step 1.
- Step 4 (tests) depends on Steps 1 and 2 both landing (Test 3 specifically exercises Step 2's fix).
- Step 5 (regression suite) depends on Steps 1, 2, 4.
- Step 6 (corpus validation) depends on Steps 1 and 2 landing in the "compared" code state; the
  "baseline" state is the pre-Step-1 commit — can be prepared in parallel but must run its compared
  variant after Steps 1-2 land.
- Steps 7, 8 (docs) depend on Step 1's final formula text being settled (they cite it verbatim) —
  implement after Step 1, can run in parallel with Steps 2-6.
- Step 9 (parity entry) depends on Steps 1, 2, 4, and 6 all having concrete evidence to cite
  (`v2_evidence`/`test_path`) — implement last.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: `recalculate_combat_stats()` derives `readiness_speed` from agility; two entities with different agility produce different `readiness_speed` | Step 1 | `test_readiness_speed_derives_from_agility_two_values` |
| AC #2: backward-compatible — reference/baseline agility still yields `readiness_speed == 10.0` | Step 1 | `test_readiness_speed_reference_agility_backward_compatible` |
| AC #3: new regression test asserts formula output for >=2 distinct agility values | Step 4 | `test_readiness_speed_derives_from_agility_two_values` (agility=5 and agility=15) |
| AC #4: `docs/mechanics/02_combat_laws.md` §7 and parity entry (COMB-298 or new) updated in the same session | Steps 7, 9 | manual doc/YAML review |
| AC #5: ticket scope explicitly states base formula ships now, agi_apt deferred | Already satisfied in the ticket body's own Scope/Out-of-Scope sections (no plan step needed — this AC is about the ticket text itself, already present) | N/A |

## Anti-Drift Notes
- **The `apply.py:507-515` silent-drop is the single highest-risk line in this ticket.** It is the
  same class of bug already hit twice in this subsystem (COMB-298's `to_readonly()` fix,
  `CREATURE-TERRITORY-LIFECYCLE`'s `_fast_replace_identity` fix) — Step 2's fix and Step 4's Test 3
  are the direct guard against a fourth recurrence.
- **Do not confuse `move_cost`'s sign with `readiness_speed`'s sign.** Both read
  `attributes.agility` in the same function; `move_cost` *decreases* with agility, `readiness_speed`
  *increases* with agility. Step 4's Test 1 explicitly asserts the direction, not just inequality,
  to guard against a copy-paste sign inversion.
- **The real corpus population currently only ever expresses the decrease direction** (elder decay,
  `agility 5→4`) — no real writer raises agility above `5` today (`fleet_foot` breakthrough is
  wired but never granted in production; no allocate_ap/class-tier path touches agility). Step 6's
  corpus validation is deliberately designed around this fact (`monotonic_non_increasing`, elder-
  window metric) rather than the more intuitive but currently-unrealizable "higher agility → higher
  corpus-wide combat rate" framing.
- **`LifeStage.ELDER`'s pre-existing `"combat": 0.5` goal-multiplier** (`src/ai/life_stage.py:34`)
  is a real behavioral confound for any elder-vs-non-elder *intra-run* comparison — Step 6's design
  avoids it by using pre/post-code as the variant axis (holds behavior constant) rather than
  cohort-split within one run.
- **`combat_damage` is silently suppressed for non-lethal hits under `ObservabilityMode.LIGHT` and
  `ObservabilityMode.LONG_RUN`** (`event_shapers.py:224`). Step 6's metric depends on routine,
  non-lethal damage events, so the throwaway `ExperimentSpec` must explicitly pin
  `observability.mode="STANDARD"` (→ `ObservabilityMode.NORMAL`, confirmed at
  `orchestrator.py:57-63`). Leaving `mode` unset silently resolves to `LIGHT`
  (`orchestrator.py:63`'s default), and reaching for the plausible-sounding `"LONG_RUN"` label
  resolves to the *other* gated mode — both would produce a hollow, non-representative result that
  still prints `PASSED`. This was an architecture-review finding on this plan; do not regress it in
  implementation.
- **`speed_penalty` on wounds stays computed-but-unread.** Do not let Step 3's review of
  `get_effective_stats()` turn into an implicit expansion of scope that starts reading it.
- **Corpus validation is not optional** — a plan/implementation that only does Steps 1, 2, 4, 5, 7,
  8, 9 and skips Step 6 does not satisfy the ticket's own Scope wording ("Corpus-validate the
  change... rather than shipping as a bare unit-tested formula swap").

## Open Questions
None remaining — every design decision investigation.md flagged as open is resolved above:
1. **Formula and `k`**: `readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)`, `k=1.0`, resolved
   in Step 1 with full reasoning and real-corpus-range citations.
2. **Symmetric vs floored**: symmetric direction, floored at `1.0`, resolved in Step 1.
3. **PH8 silent-drop fix**: exact kwarg and insertion point specified in Step 2.
4. **COMB-298 vs new entry**: new entry `COMB-318`, resolved in Step 9 with reasoning.
5. **Corpus validation design**: pre/post-code variant axis + elder-window-restricted
   `combat_damage` metric + `monotonic_non_increasing` relationship, fully specified in Step 6,
   including why the naive intra-run cohort-split and naive whole-run aggregate were both rejected.
6. **Docs**: both `02_combat_laws.md` §7 and `attribute_progression_contract.md`'s Derived Stat
   Recalculation Order section, specified in Steps 7-8.
7. **agi_apt scope boundary**: confirmed zero references anywhere in this plan, restated explicitly
   in Scope Guards.

## Deviations (recorded during Implementation)

- **Step 6's exact escalation path (widen ticks/window on `unit_faction_tension`) did not apply —
  the actual root cause was structural, not sample-size.** The initial 9500-tick/3-seed run on
  `unit_faction_tension` produced a degenerate `baseline=0.0`/`compared=0.0` result, as the plan
  anticipated was possible. Per Step 6 point 6's own instruction, before accepting a hollow
  `PASSED`, three single-seed 9500-tick diagnostic runs were done (not the literal "widen
  ticks/window on the same world" escalation, which the evidence below shows would not have
  helped) across `unit_faction_tension`, `crowded_frontier`, and `lifecycle_full_coverage_world`
  (the last chosen specifically because it is authored to exercise the full lifecycle including
  `ELDER`, with active hostile modules). All three showed the identical root cause: every
  `combat_damage` event in the entire 9500-tick run occurs before tick 1000 (106-196 events per
  world), and zero occur at `tick >= 1000` in any of them — real combat activity structurally
  ceases early and does not resume, in every tested world. Since `LifeStageService.get_stage_for_age()`
  requires `age_ticks >= 7000` for `ELDER` eligibility, the elder-eligible window and the
  active-combat window never overlap in any tested world's current content. This is a corpus-content
  fact, not a tick-count or seed-count artifact, so the plan's literal "widen ticks/seeds on the
  same world" escalation would not have changed the outcome — confirmed empirically via world
  substitution instead (still within Step 6's own authorized substitution clause: "else Implementer
  selects the closest equivalent long-running stable world... and records the substitution
  reason").
- **Consequence for `COMB-318`'s evidence claim**: the plan's literal Step 9 template (a directional
  `monotonic_non_increasing` `PASSED` with real signal) was not achievable honestly. `COMB-318` was
  written instead with the true finding: code-level correctness remains fully verified by the three
  unit/regression tests (Step 4), and the corpus-validation attempt is documented as a genuine null
  result with its structural root cause, plus a `support_boundary` field explaining exactly what
  real-corpus validation can and cannot currently support for this change. This was a deliberate
  choice not to fabricate a stronger claim than the evidence supports, per the project's Gate
  Integrity rule ("never edit an artifact to make a gate pass instead of fixing the underlying
  substance" / "stop and report truthfully").
- No code, formula, or scope changes resulted from this finding — Steps 1, 2, 4, 5, 7, 8 all
  landed exactly as planned. Only Step 6's evidence-quality outcome and Step 9's `v2_evidence`
  wording differ from the plan's literal template.
