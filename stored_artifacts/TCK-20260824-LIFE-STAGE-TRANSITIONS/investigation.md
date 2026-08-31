---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LIFE-STAGE-TRANSITIONS
artifact_type: investigation
tags: [cognition]
---

# Investigation — TCK-20260824-LIFE-STAGE-TRANSITIONS

## Context Search Note

`mcp__knowledge-search__search_docs` was called first, as required, with query "Implement Life
Stage Transitions LifeStageService identity.life_stage" and returned `{"error": "index not found",
"action": "run make knowledge-index"}` — this matches the pre-confirmed, documented environment gap
for this session (the fallback `python3 tools/knowledge_search.py` was already confirmed unavailable
the same way earlier in this session). Proceeded to `graphify query "LifeStageService life stage
transitions IdentityUpdate IdentityPatch"` (641 nodes, BFS depth=2 — confirmed `IdentityComponent`,
`IdentityUpdate`, `ApplyPath`, `LifecycleComponent`, `AuthoritativeState` as the primary code
targets), then to the file reads and greps below.

## Current Behavior

1. **`LifeStage` enum and `IdentityComponent.life_stage`** — `src/core/state.py:410-414`
   (`LifeStage(str, Enum)`: `CHILD`/`ADULT`/`ELDER`), `src/core/state.py:488`
   (`IdentityComponent.life_stage: LifeStage = LifeStage.ADULT`), `src/core/state.py:509`
   (included in `to_canonical_dict()` via `str(self.life_stage)`).

2. **`IdentityUpdate` has no `life_stage_set` field** — `src/core/updates.py:220-263`. `is_noop()`
   (237-243) and `merge()` (245-263) enumerate every other field (`role_set`, `faction_set`,
   `evolution_level_set`, etc.) but never mention `life_stage`.

3. **`LifeStageService.get_goal_multipliers()`** — `src/ai/life_stage.py:5-33`, a pure static
   method mapping `LifeStage` → per-`GoalKind` multiplier dict (CHILD: exploration 1.5/social
   1.2/harvesting 0.5/combat 0.2/fatigue 0.8; ADULT: neutral `{}`; ELDER: fatigue 1.5/combat
   0.5/social 1.3/harvesting 0.7).

4. **`ScoreModifierSystem.apply_modifiers()`** — `src/ai/score_modifiers.py:12-74` calls
   `LifeStageService.get_goal_multipliers(entity.identity.life_stage)` (line 25) and multiplies
   every `GoalScore.utility` by the result (lines 38-40). This runs on **every** goal-score
   evaluation, unflagged and live — confirmed by the parity ledger's own divergence note on
   COMB-095/SOC-078 ("`src/ai/score_modifiers.py` is live code (imported by intelligence.py) — not
   a V1 orphan"). Because nothing ever writes `identity.life_stage` away from its `ADULT` default,
   this multiplier stage is a permanent, universal 1.0 no-op in production today — the exact "dead
   field" the ticket's Request Summary describes.

5. **`IdentityPatch.apply()`** — `src/engine/patches.py:170-226`. Reads current component values
   from `new_id` into locals (`rl`, `fac`, `rec`, `tgt`, `lvl`, ...; lines 176-188, no `life_stage`
   local), applies the incoming `IdentityUpdate`'s `*_set`/`*_delta` fields onto those locals
   (190-207), then builds the final `IdentityComponent` via one of two branches:
   - `_fast_replace_identity` (line 219) — only when `not self.identity and self.group_id_set is
     None and not self.property_updates and self.intent_results` (line 218). This branch can
     **never** fire when `life_stage_set` is populated, because `life_stage_set` lives inside
     `self.identity` (the `IdentityUpdate`), which makes `self.identity` truthy and forces the
     `else` branch below. So `_fast_replace_identity`'s existing `life_stage=id_comp.life_stage`
     passthrough (`src/engine/apply.py:529`) is safe by construction — it is only ever reached when
     there is genuinely no `IdentityUpdate` to apply, so preserving the unchanged value is correct.
   - `replace(new_id, role=rl, faction=fac, known_recipes=..., craft_target=tgt,
     evolution_level=lvl, evolution_points=ep, veterancy_points=vp, veterancy_rank=vrank,
     unspent_ap=ap, learned_skills=..., traits=..., active_breakthroughs=..., cooldowns=...,
     group_id=gid, properties=..., latest_intent_results=intents)` (lines 221-226) — **this is the
     branch that actually needs to change.** It never passes `life_stage=...`, so
     `dataclasses.replace()` silently preserves `new_id.life_stage` unchanged even once
     `life_stage_set` exists on `IdentityUpdate` and even once `IdentityUpdate.is_noop()`/`merge()`
     are fixed. The AC's "verify `_fast_replace_identity` does not silently drop it" is
     technically satisfied already (that path is unreachable for this field), but the *real* silent
     drop risk is in this `replace()` call, which needs a `life_stage=ls` kwarg computed the same
     way `rl`/`fac`/etc. are.

6. **A second, independent silent-drop trap**: `IdentityPatch.is_noop()` (`src/engine/patches.py:
   154-156`) delegates to `self.identity.is_noop()`. `extract_patches()`
   (`src/engine/patches.py:681-700`, specifically line 698-700) only constructs an `IdentityPatch`
   when `update.identity is not None or ...`, but then immediately drops it again if
   `p.is_noop()` returns `True`. **If `IdentityUpdate.is_noop()` is not updated to also check
   `life_stage_set is not None`, an `IdentityUpdate(life_stage_set=...)` with no other field set
   will report `is_noop() == True` and the whole patch — including the life_stage change — is
   silently discarded before `apply()` ever runs.** This is arguably the single easiest way to
   ship this ticket with a passing-looking but functionally inert implementation, since
   `apply()` itself would look correct in isolation.

7. **Age tracking**: `LifecycleComponent.age_ticks` (`src/core/state.py:143-154`, default
   `max_age_ticks=10000`) is the only per-entity age signal. It is advanced deterministically,
   authoritatively, +1 per `is_life_due` tick (gated by `cadence.lifecycle` via `should_run()`)
   directly inside `ApplyPath._compute_entity_changes` (`src/engine/apply.py:94-110`) — this is
   the passive/A-section of the fused per-entity apply function, which also drives passive hunger,
   sleep debt, and old-age deactivation (`active=(new_hp > 0 and new_age < life.max_age_ticks)`,
   line 109).

8. **Existing age-driven typed-update precedent**: `LifecycleSystem.resolve_lifecycle()`
   (`src/systems/lifecycle_systems/lifecycle.py:34-137`) reads `entity.lifecycle.age_ticks >=
   entity.lifecycle.max_age_ticks` (line 54, durable state) and returns a `StateUpdate` containing
   an `EntityUpdate(active=False, lifecycle=LifecycleUpdate(...))` — it never mutates
   `AuthoritativeState` directly. This is the established, already-reviewed pattern for "age
   crosses a threshold → typed update," most recently touched by
   `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`. It only processes entities where
   `entity.lifecycle.active` is `True` (line 45) — any new age-based trigger reusing this call site
   should respect the same guard.

9. **Cohort-level age brackets** (`src/domains/demographics/cohort.py`, Out of Scope for direct
   edits): `get_age_bracket(age_ticks)` (lines 50-65) is a pure function returning
   `"young"`/`"adult"`/`"elder"` strings for **`PopulationCohort.bracket`** — an abstract,
   region-level aggregate count, never tied to a real `EntityState`. Thresholds: `age_ticks < 3000`
   → young, `< 7000` → adult, `>= 7000` → elder. `compute_elder_attribute_update()` (lines 68-106)
   is a pure function producing an `EntityUpdate(AttributeUpdate(...))` (STR/AGI ×0.7, VIT/END
   ×0.5-equivalent deltas, WIS/CHA ×1.3) for an elder-bracket entity — **confirmed orphaned**: `grep
   -rn "compute_elder_attribute_update"` across `src/` and `tests/` returns exactly one production
   definition (`cohort.py:68`) and zero production call sites; every other hit is inside
   `tests/unit/world/test_demographics.py` (6 direct unit-test calls, all passing in isolation).

10. **No production path spawns an entity below `ADULT`/age-zero-as-child today.** `grep -rn
    "age_ticks="` across `src/` (excluding `state.py`/`cohort.py`/`patches.py`/`apply.py`
    definitions) and a scan of `src/entities/archetype_factory.py` and
    `src/systems/world_systems/generator.py` show no entity-generation path ever sets a non-default
    `age_ticks`. Every generated entity (hero, NPC, etc.) starts at `LifecycleComponent.age_ticks =
    0` as a construction-time bookkeeping default, **not** a literal "just born" fact — and
    `IdentityComponent.life_stage` correctly starts at `ADULT` for these entities via its own
    default. `DemographicCycleService.process_demographics()` only ever mutates abstract
    `PopulationCohort.count` integers (`src/domains/demographics/cohort.py:315-410`); it never
    creates a real per-entity `EntityState` "newborn." **This is a load-bearing finding for the
    trigger's design** (see Risks/Open Questions below): a transition rule that unconditionally
    recomputes `life_stage` from `age_ticks` every tick would misclassify every world-generated
    adult entity as `CHILD` at tick 1 (`age_ticks=0` falls in the `<3000` bracket), a severe,
    silent, world-wide behavior regression. The transition must be **monotonic forward-only**
    (never move an entity to a stage with a lower ordinal than its current one).

11. **Builder support**: `V2EntityBuilder.identity(..., life_stage: Optional[LifeStage] = None,
    ...)` (`src/core/builder.py:164-214`) already lets tests construct an entity with an explicit
    starting `life_stage` (e.g. `tests/unit/strategic/test_personality_goal_modifiers.py:82-110`'s
    `test_life_stage_multipliers`, and `tests/helpers/entities.py:83/126/143`). No runtime system
    calls this after construction — it's a test-only entry point today.

## Mechanics / Engine Constraints

- **Architecture Rule** (`CLAUDE.md`, Core Boundaries): "Decision logic reads state. It does not
  authoritatively mutate durable state. Durable changes must be represented through typed
  records/updates. Authoritative application is the only place durable state should be committed."
  This constrains where the new age-based trigger may live: it must produce an
  `EntityUpdate(identity=IdentityUpdate(life_stage_set=...))`, not an in-place mutation. Finding 8
  above (`LifecycleSystem.resolve_lifecycle`) is the established, already-reviewed precedent for
  exactly this shape and is the natural place to extend, rather than adding a new special case
  directly into `ApplyPath._compute_entity_changes`'s performance-sensitive passive-tick section.
- **Determinism** (`CLAUDE.md` Hard Rules: "Do not break determinism"): the trigger must be a pure
  function of `age_ticks` (and, if cadence-gated, `tick`) — no RNG, no wall-clock reads.
- `docs/mechanics/04_strategic_cognition.md` documents the goal-scoring formula (§ "score =
  urgency + benefit + personality_bias + ...") in detail but has **zero mention** of the
  post-formula `ScoreModifierSystem` multiplier stage (personality/life-stage/boredom/blocker) at
  all — this is a pre-existing documentation gap that predates this ticket (see Docs Requiring
  Update below for the decision on whether to close it here).
- `docs/mechanics/01_entity_anatomy.md` (biological pressures, XP scaling) has **zero mention** of
  `age_ticks`/`max_age_ticks`/old-age death at all — the entire aging/lifecycle mechanic, including
  the older, already-implemented-and-tested `OLD_AGE` death path, has never been documented in the
  Bible. This ticket does not newly create that gap.

## Docs Requiring Update

- `docs/parity_ledger/combat_movement.yaml`: no existing entry describes the mechanism that *sets*
  `IdentityComponent.life_stage` (only entries describing the multiplier *consuming* it —
  COMB-095, `legacy_verified`, `test_path: null` — already exist). Add a new entry documenting the
  age-based transition trigger, its numeric thresholds, and a real `test_path` pointing at the new
  test asserting `identity.life_stage` flips at the defined boundary. This file is the established
  home for `LifecycleSystem`-driven age transitions (see COMB-309/COMB-311, the
  `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX` entries for `resolve_lifecycle`'s combat-death
  check) and already hosts the "life-stage modifier law" naming convention (COMB-095).
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`: lines 284-287 ("One possible duplicate
  system, not yet reconciled... Whoever scopes idea 20 should settle this first") explicitly name
  this exact open question and explicitly assign its resolution to whoever scopes idea 20 (this
  ticket). This investigation resolves it (see Design Decisions below) — the roadmap's "Known open
  items" entry must be updated to record the resolution so it stops presenting the question as
  open. This doc is already listed in the ticket's own "Related Docs."

The `docs/mechanics/04_strategic_cognition.md` chapter (path:
`docs/mechanics/04_strategic_cognition.md`) is not required to change for this ticket, despite
documenting the goal-scoring pipeline that `ScoreModifierSystem` feeds into: it already has zero
coverage of the entire post-formula modifier stage (personality bias, boredom, blockers, and
life-stage alike), a pre-existing gap this ticket did not create and whose life-stage slice alone
would be an inconsistent partial fix. The `docs/mechanics/01_entity_anatomy.md` chapter (path:
`docs/mechanics/01_entity_anatomy.md`) is likewise not required to change: it has zero coverage of
`age_ticks`/`max_age_ticks`/old-age death today, including the older, already-shipped `OLD_AGE`
death path in `LifecycleSystem.resolve_lifecycle()` — adding only the new life-stage-transition
slice of the aging mechanic while the death slice stays undocumented would fragment the same gap
rather than close it. Both are flagged as a single future "Aging & Lifecycle" Bible section,
covering age progression, old-age death, and life-stage transitions together, rather than three
separate partial edits across three tickets. `docs/guidelines/intentional_divergences.md` (path:
`docs/guidelines/intentional_divergences.md`) is not required to change either: this ticket does
not diverge from any documented Mechanics Bible law — no chapter currently makes any claim about
`identity.life_stage` that this ticket's implementation would contradict; it is making a
previously-inert, already-declared field reachable, not changing declared behavior.

## Parity Ledger Overlap

- `WORLD-DEMO-003` (`docs/parity_ledger/world_dynamics.yaml`, `status: verified`, `priority: P1`)
  — `get_age_bracket()`'s cohort-level bracket thresholds. Overlaps conceptually (same numeric
  boundaries, 3000/7000) but is explicitly Out of Scope for direct modification; not touched.
- `WORLD-DEMO-004` (`docs/parity_ledger/world_dynamics.yaml`, `status: verified`, `priority: P1`)
  — `compute_elder_attribute_update()`, the orphaned attribute-penalty mechanism. Decision below:
  not wired in this ticket; entry is not touched.
- `COMB-095` (`docs/parity_ledger/combat_movement.yaml`, `status: legacy_verified`, `priority:
  P0`), `SOC-078` (`docs/parity_ledger/social_narrative.yaml`, `status: legacy_verified`,
  `priority: P0`), `TOWN-071` (`docs/parity_ledger/town_resource.yaml`, `status: verified`,
  `priority: P0`) — all three describe the "life-stage modifier law" / "life stage priority shift"
  (i.e. `ScoreModifierSystem`/`LifeStageService.get_goal_multipliers()`), all three carry
  `test_path: null` despite being `P0` (a **pre-existing** violation of the "P0 entries require a
  passing `test_path`" rule — not introduced by this ticket). This ticket does not fix that gap
  (it would require adding dedicated `ScoreModifierSystem` tests beyond this ticket's AC), but
  flags it as a good, low-risk follow-up now that the underlying field is finally reachable
  end-to-end and a real multiplier-difference assertion (like
  `test_life_stage_multipliers`, already passing) could plausibly backfill one of these
  `test_path`s.
- New entry needed in `docs/parity_ledger/combat_movement.yaml` for the new age-based trigger (see
  Docs Requiring Update).

## Prior Work

- `tests/integration/optimization/test_component_patch_apply_parity.py` already exercises the
  exact end-to-end shape this ticket needs to add a test for:
  `EntityUpdate(entity_id=4, identity=IdentityUpdate(role_set="PALADIN"))` run through
  `apply_generation` and asserted via `new_state.entities[4].identity.role == "PALADIN"` — this is
  the template to replicate for `life_stage_set`, since it exercises the full pipeline (not just
  `IdentityPatch.apply()` in isolation), catching exactly the `replace()`-kwarg-omission bug
  described in Current Behavior #5.
- `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`) is the
  directly reusable precedent for "read `age_ticks`, emit a typed `IdentityUpdate`/`EntityUpdate`"
  — most recently modified by `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`
  (`tickets/done/TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX.md`), which shows the accepted
  pattern for a small, targeted addition to this exact function plus its matching
  `combat_movement.yaml` parity entries (COMB-309, COMB-311).
- `TCK-20260619-E52A-COHORT-MODEL`, `TCK-20260619-E52C-AGE-ADVANCEMENT`,
  `TCK-20260619-E52-DEMOGRAPHICS` (`stored_artifacts/`) are the prior work that built
  `get_age_bracket()`/`compute_elder_attribute_update()`/`PopulationCohort` — confirms these were
  always scoped as cohort/region-aggregate mechanisms, never as per-entity `IdentityComponent`
  drivers, consistent with Design Decision 1 below.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M9 section, line 147) flags that "the
  long-run observation tool's default 5000-tick run would never even reach the real 7000-tick
  elder-attribute threshold idea 20 needs" — a real-simulation-observability timing gap, not a unit
  test concern (unit tests construct `LifecycleComponent(age_ticks=7000)` directly), but worth
  carrying into the test plan's Anti-Drift section so a future SimQ/observability check on this
  ticket's feature doesn't repeat the same false-negative.

## Design Decisions (both ticket-charged open questions, resolved here)

### Decision 1 — Representation alignment (LifeStage enum vs. `get_age_bracket()` string tiers)

**Resolved: keep the two vocabularies (and their consumers) separate; align only the underlying
numeric age boundaries.**

- `get_age_bracket()` (`young`/`adult`/`elder`) operates on `PopulationCohort.bracket` — an
  abstract, region-level aggregate count with no tie to any real `EntityState`. `LifeStage`
  (`CHILD`/`ADULT`/`ELDER`) operates on `IdentityComponent.life_stage` — a concrete per-entity
  field consumed by `LifeStageService.get_goal_multipliers()` inside strategic cognition. These are
  genuinely different subsystems, at different aggregation levels (region-cohort-count vs.
  single-entity), with different consumers (demographic simulation vs. AI goal scoring). Nothing
  today reads both for the same logical individual — duplication between them is not incidental,
  it reflects that they were built for different jobs (confirmed by Prior Work: `E52A`/`E52C` were
  scoped purely as cohort/demographics work).
- However, correctness *does* require the same **numeric** tick boundaries, even with different
  string vocabularies: an entity's real age should not report as "child" by one representation and
  "adult" by the other if a future system ever cross-references them (this is exactly the
  ambiguity the roadmap's M9 finding flags). The new per-entity trigger therefore reuses
  `get_age_bracket()`'s exact numeric law — `age_ticks < 3000` → CHILD, `3000 ≤ age_ticks < 7000` →
  ADULT, `age_ticks ≥ 7000` → ELDER — as literal constants in a new pure function (recommended:
  `LifeStageService.get_stage_for_age(age_ticks: int) -> LifeStage` in `src/ai/life_stage.py`,
  symmetric with `get_age_bracket()`), rather than importing `cohort.py`'s function directly.
  Duplicating the two integer literals (not the logic style, just the boundary values) is a
  deliberate, explicitly-recorded tradeoff, not an oversight, for two reasons: (a) the ticket's Out
  of Scope forbids modifying `cohort.py`/`test_demographics.py`, so a shared helper would need to
  live somewhere new anyway; (b) `src/ai/` (strategy/cognition layer) importing
  `src/domains/demographics/` (world/economy layer) would be a backwards cross-layer dependency
  this codebase doesn't otherwise have. A code comment in the new function should cross-reference
  `WORLD-DEMO-003` so a future reconciliation effort (if one is ever chartered) has a clear paper
  trail back to this decision.
- **This does not require touching `cohort.py` or `test_demographics.py`** — satisfies the Out of
  Scope constraint exactly as required.

### Decision 2 — `compute_elder_attribute_update()` wiring

**Resolved: do not wire it in this ticket; it remains a deliberately separate, still-orphaned
mechanism.**

Rationale:
- **Scope discipline.** `compute_elder_attribute_update()` mutates `AttributeComponent` (STR/AGI/
  VIT/END/WIS/CHA deltas) — a different component and mechanic entirely from this ticket's
  `IdentityComponent.life_stage`/goal-multiplier concern. None of this ticket's acceptance criteria
  mention attribute stat changes.
- **No idempotency guard exists.** The function has no "already applied" tracking. Naively calling
  it once per tick for every elder-bracket entity (the natural place to wire it, mirroring the new
  life-stage trigger's own per-tick check) would re-subtract the same deltas every tick forever —
  runaway, unbounded stat decay. Making it safe to wire would require its own one-shot/idempotent
  design (e.g. a new durable "elder modifier applied" flag), which is a real, separate technical
  problem, not a one-line wiring change.
- **Genuine architectural independence.** Attribute stat penalties (physical capability) and
  goal-utility multipliers (behavioral bias) are different mechanic categories. Both are legitimate
  "elder effects," but there is no requirement they share a single trigger — `LifeStageService`'s
  ELDER goal multipliers and `compute_elder_attribute_update()`'s stat penalties can coexist as
  independent systems, each triggered by (but not coupled through) the same underlying
  `age_ticks` fact.
- **No regression from leaving it unwired.** It is already fully covered by its own passing unit
  tests in isolation (`tests/unit/world/test_demographics.py`, 6 tests), confirmed still orphaned
  (zero production callers) by grep. Leaving it as-is changes nothing about current behavior.
- Flagged as a legitimate candidate for its own future, separately-scoped ticket, whose primary
  technical challenge would be designing the idempotency/one-shot-transition guard — not something
  to improvise as a side effect of this ticket.

## Risks and Open Questions

- **Critical implementation risk (not an open question — a hard constraint):** the age-based
  trigger must be **monotonic forward-only** (never assign a `LifeStage` with a lower ordinal than
  the entity's current one: CHILD(0) < ADULT(1) < ELDER(2)). See Current Behavior #10 — every
  world-generated entity starts at `age_ticks=0` (a construction-time bookkeeping default, not a
  literal "just born" fact) while `life_stage` correctly defaults to `ADULT`. A naive
  "recompute `get_stage_for_age(age_ticks)` and always overwrite" trigger would misclassify every
  entity in the simulation as `CHILD` at tick 1 — a severe, silent, world-wide regression. The
  correct check is `if ordinal(target_stage) > ordinal(current_stage): set life_stage = target`.
- **`IdentityUpdate.is_noop()` and `.merge()` must both be updated**, not just `.apply()` (Current
  Behavior #6). An `IdentityUpdate(life_stage_set=...)` with no other field populated will be
  silently discarded by `extract_patches()`'s `is_noop()` filter before `apply()` is ever reached
  if `is_noop()` isn't taught about the new field — this is the single easiest way to ship a
  looks-correct-in-isolation but functionally inert implementation.
- **The `replace()` kwargs in `IdentityPatch.apply()` (patches.py:221-226) must explicitly compute
  and pass `life_stage=ls`** — not the `_fast_replace_identity` path, which is provably unreachable
  for this field (Current Behavior #5). Mislabeling this as "the fast path drops it" (per the
  ticket text's phrasing) would lead an implementer to inspect and "fix" the wrong function.
- **Trigger call-site choice is left to Plan**, not fixed here: `LifecycleSystem.resolve_lifecycle()`
  is the recommended, precedent-matched, lowest-blast-radius site (Prior Work), but Investigation
  does not mandate it — Plan should confirm no cadence/ordering conflict exists between
  `resolve_lifecycle`'s per-tick death check and where age is incremented in
  `ApplyPath._compute_entity_changes` before finalizing.
- **Both ticket-charged design questions are resolved above, not deferred** — see Design Decisions.
  No blocking open question remains for Plan to resolve; Plan should proceed directly to
  implementation-shape decisions (exact call site, exact new-function name/location) using the
  constraints established here.

## Anti-Drift Hazards

- Do not touch `src/domains/demographics/cohort.py` or `tests/unit/world/test_demographics.py` —
  explicitly Out of Scope. The new age→stage mapping duplicates numeric literals rather than
  importing from that module (Decision 1).
- Do not wire `compute_elder_attribute_update()` into anything as a side effect of adding the
  life-stage trigger — explicitly decided against in this ticket (Decision 2). Adding an
  idempotency guard and wiring it is real, separate scope.
- Do not implement the trigger as an unconditional "recompute and overwrite `life_stage` every
  tick" — must be monotonic forward-only (Risks, first bullet). This is the single highest-risk
  place for a silent, world-wide regression in this ticket.
- Do not forget `IdentityUpdate.is_noop()`/`.merge()` — a correct `.apply()` alone is not
  sufficient; the patch can be filtered out before `apply()` runs (Risks, second bullet).
- Do not add `life_stage` to the `stats_dirty` recompute block in
  `ApplyPath._apply_entity_update_to_dict` (apply.py:460-509) — `life_stage` does not feed
  `SkillScalingService.get_effective_stats`; its only consumer is
  `ScoreModifierSystem`/`LifeStageService`, downstream of derived-stat recalculation. Adding it
  there would be unnecessary scope creep with no behavioral basis.
- Keep the new pure age→stage function's numeric constants (3000, 7000) commented as intentionally
  mirroring `get_age_bracket()` (`WORLD-DEMO-003`) — a future maintainer changing one set of
  thresholds without noticing the other exists is the exact failure mode Decision 1 anticipates.
- The M9 roadmap finding (5000-tick default observation runs never reach the 7000-tick elder
  threshold) is a simulation-observability concern, not a unit-test one — do not let it justify
  skipping a direct unit-level assertion (construct `LifecycleComponent(age_ticks=7000)` /
  `age_ticks=6999` directly; no real multi-thousand-tick simulation run is needed to test this
  ticket's AC).
