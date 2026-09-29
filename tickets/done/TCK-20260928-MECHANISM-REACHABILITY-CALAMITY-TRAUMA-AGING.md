---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING
phase: done
date: 2026-09-28
tags: [simulation-quality, world, root-cause]
---

# TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING

## Title
Bounded reachability assessment for three mechanisms — `calamity_intensity`, `regional_trauma`, and
`aging_death`/`succession` — answering whether each is a condition, a defect, or a mislabel

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Three mechanisms carry registry `verified` blocks that corpus runs contradict or cannot confirm.
This ticket answers **why**, on four levels each, and ends each with **one exit claim**. It is a
bounded assessment, not an open-ended sweep and not a fix.

The four levels, per mechanism:
1. trigger reachability;
2. feasible run horizon;
3. actual state effects;
4. observer evidence (recorded, never required).

Implements Card J of `docs/plans/systemic_world/ticket_planner_handoff.md`
(branch `systemic-world-roadmap-proposal` @ `43db4a7fc`, PR #249, unmerged).

## Scope
- **J1 — `calamity_intensity`.** **Adopt** `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
  do not duplicate it. That ticket records `calamity_intensity` never leaving `0.0` in any region
  across a real 5000-tick run, producer and propagator both apparently inert.
- **J2 — `regional_trauma`.** **Adopt** `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, do not
  duplicate it. It already frames the problem correctly as **a region recording zero combat deaths**,
  not a wrong threshold — a trigger-reachability question that may be legitimately conditional.
- **J3 — `aging_death` / `succession`.** No ticket exists; **assess and classify only**. Fixing the
  known natural-aging defect is out of scope (see Related Tickets). Because that fix may land first,
  **every J3 finding must name the engine commit it was observed on.** The level-2 succession claim
  is limited to default settings and the current corpus.
- For each mechanism, state which of the four levels actually fails, and map the adopted ticket's
  existing scope onto those levels — explicitly naming where it does **not** fit.
- Correct any mechanism label through the registry process, with its evidence recorded in
  `registries/mechanisms.yaml`, not only in planning docs.

## Out of Scope
- **Any fix.** This ticket assesses and classifies. A confirmed defect is routed as separate work.
- A fourth mechanism. Exactly three, per Card J.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` and
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`. Both are in the same dormant-mechanism
  family and plausibly share J2's root symptom (regions recording zero combat deaths), but Card J
  fixes the count at three. **If the shared-root-cause hypothesis is confirmed, say so in the exit
  claim and stop** — do not absorb them.
- The `pressure-propagation-economy` epic folder, whose first ticket
  (`TCK-20260822-CALAMITY-AFTERMATH-SIGNAL`) touches the same calamity area. Excluded **whole**, per
  the project's epic all-or-nothing rule; do not cherry-pick from it.
- **Writing J1's `calamity_intensity` label into `registries/mechanisms.yaml`.** That entry's `state`
  reconciliation is already owned by `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`
  (open, `tickets/todos/`), whose Request Summary names `calamity_intensity` as its item 1 and whose
  Related Code Areas include the same registry file. J still assesses J1's reachability at all four
  levels and still states its exit claim in the ticket, but **a `registry label corrected` exit
  claim for J1 is recorded as a recommendation to that ticket, not applied to the registry here** —
  two tickets must not write the same mechanism entry. J2 and J3 are unaffected and may write their
  own labels normally. Surfaced by `tools/open_ticket_overlap.py` (top hit, score 40.0,
  `has_code_area_match` on `registries/mechanisms.yaml`).

## Acceptance Criteria
1. Each of the three mechanisms has an answer at all four levels, or a level explicitly recorded as
   `BLOCKED_WITH_REASON`. A harness limitation is never reported as "fine".
2. Each mechanism ends with exactly **one exit claim**, classifying it as a **condition**, a
   **defect**, or a **mislabel**.
3. For J1 and J2, the adopted ticket's existing scope is mapped onto the four levels, including a
   written statement of where it does not fit.
4. Level 2 (feasible horizon) is answered with **minimum evidence, not an open-ended long run** —
   the method is stated and justified. Note the arithmetic: default lifespan is 70 fantasy years,
   roughly 20M ticks (`src/core/state.py:165`), against corpus runs of 1k–5k ticks.
5. Every J3 finding names the engine commit it was observed on.
6. Any label correction is written through the registry process into `registries/mechanisms.yaml`
   with its evidence, not only into planning docs.
7. Findings are routed back to the systemic-world roadmap track (`world-rule-catalog-design`), which
   owns integration.

## Related Tickets
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — **adopted as J1.**
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — **adopted as J2.**
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — the natural-aging fix. **Merged 2026-09-29
  as `5d4e4a237` (PR #254); no longer in flight.** `src/engine/apply.py:109` now reads
  `active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`, making
  `LifecycleSystem.resolve_lifecycle` the sole declared authority for old-age deactivation. J3
  assesses against this landed state; it does not fix. This is why AC5 exists.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` — open, owns the `calamity_intensity`
  entry's `state` reconciliation in `registries/mechanisms.yaml`. See Out of Scope: J1 recommends,
  that ticket writes.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`,
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` — same family, deliberately out of scope.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card J (@ `43db4a7fc`).
- `docs/plans/systemic_world/first_wave_plan.md` §2 Epic J, §3.
- `docs/mechanics/05_world_evolution.md` — regional trauma, ecology, calamities.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-candidate-trajectory-search-findings.md` (on the
  unmerged branch above).

## Related Code Areas
- `src/core/state.py:165` — default lifespan constant behind J3's horizon arithmetic.
- `registries/mechanisms.yaml` — the `verified` blocks for all four mechanism entries; the first two
  were checked 2026-09-27 and are `contradicted` by corpus runs.

## Assumptions / Open Questions
- **Q1.** For J1 and J2, which of the four levels actually fails — and is the answer a condition, a
  defect, or a mislabel?
- **Q2.** How does each adopted ticket's existing scope map onto the four levels, and where does it
  not fit?
- **Q3.** What is the minimum evidence that answers level 2 without an open-ended long run?
- **Q4.** For J3, can levels 2 and 3 be recorded from existing evidence plus the reproduction,
  **without** fixing the defect?
- **Shared-root-cause hypothesis, flagged not assumed. — RESOLVED: checked, not confirmed.** J2's
  adopted ticket and the out-of-scope `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` both
  reduce, on the surface, to "a region recording zero combat deaths." Checking the second ticket
  directly (via `docs/plans/world_composition_precondition_gap_finding.md`, which already names it
  "instance 4, the exception") shows the two causes are, in fact, **opposite**:
  - **J2 (this ticket)**: `moon_cave` is spatially isolated — no hostile faction is ever composed
    within combat range of it. Entities are correctly *not* co-located there. Zero deaths occur
    because there is no one to fight.
  - **`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`**: entities *are* correctly co-located
    and deaths *do* genuinely occur in its sampled region (20/20 sampled real deaths were
    `outcome_kind == "DEFEAT"`, zero `"KILL"`). The zero-effect symptom there is a separate,
    single-cause classification divergence: `resolve_lifecycle()`'s own death-outcome filter only
    checks `outcome_kind in ("KILL", "PERMADEATH")` — it is missing `"DEFEAT"`, which real combat
    resolution also uses to mark `alive_set=False`.

  These are not the same defect wearing two names — one is a world-composition/geometry condition,
  the other is a code-level filter gap. **Stated here per this ticket's own instruction; not
  absorbed.** Zero edits were made to `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`'s own
  ticket file.
- **Contract-level risk.** Re-labelling a mechanism changes what other plans assume is live. Record
  every label change in the registry with evidence.
- None of the three mechanisms is SCP-mapped; **no SCP change is required.**

## Implementation Notes

This is an assessment/classification ticket. No `src/` production code was changed. Findings below
are transcribed from `staging_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/
investigation.md` (not re-derived), with the zero-callers and constant claims independently
re-confirmed during implementation via direct read/grep against current worktree HEAD (`702c3af83`).

### J1 — `calamity_intensity` (adopts `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`)

- **Level 1 (trigger reachability) — FAILS, structurally.** `grep -rn "apply_calamity_consequences"
  src/` re-run during implementation returns only the definition
  (`src/world/calamity.py:80`) and one unrelated comment (`src/world/displacement.py:27`) — zero
  real callers anywhere. `CalamityService.process_world_dynamics()`, the method actually invoked
  from `src/world/world_dynamics.py:133`, only *reads* `region.calamity_intensity`; it never calls
  `apply_calamity_consequences()`. This is a deeper finding than the adopted ticket's original
  2026-09-15 framing (a composition gap): the producer is never invoked at all, so its internal
  `hero`-kind/hazard-level check is never even evaluated.
- **Compounding, secondary finding (the adopted ticket's original scope)**: even if wired, the
  trigger condition is separately unreachable in the tested worlds — `frontier_living_world`
  composes zero `hero`-kind entities; `crowded_frontier`'s 3 heroes all spawn in `hometown`
  (`hazard_level: 0.0`) per `hero_adventurers.yaml`.
- **Level 2 (feasible run horizon) — moot.** Level 1 already fails as a structural, tick-count-
  independent fact (no call edge exists in the call graph). Method: static call-graph confirmation
  (`grep`), not a corpus run — this is AC4's "minimum evidence" answer for J1.
- **Level 3 (actual state effects) — none.** `region.calamity_intensity` stays `0.0` in every tested
  world across the full 5000-tick run length already observed by the adopted ticket. Its only real
  consumer (`process_world_dynamics()`'s boss-spawn region selection) always sees `0.0`.
- **Level 4 (observer evidence, recorded never required) — none.** Not investigated further, since
  the mechanism never produces a state change for an observer to encounter.
- **Exit claim: DEFECT** (recommendation only — see AC6/registry-write section below).
- **AC3 — where the adopted ticket's scope does not fit**: the adopted ticket's Scope/Acceptance
  Criteria were written before the 2026-09-20 zero-callers finding existed — they ask for "a
  proposed wiring fix... that would make `calamity_intensity` demonstrably nonzero," framed
  entirely around the composition gap (Level-1-if-wired). They do not cover the now-primary Level 1
  failure (the producer is never called at all), a different, more fundamental defect class. The
  adopted ticket's own Implementation Notes already flag this gap themselves; this assessment
  confirms that self-correction is still accurate.

### J2 — `regional_trauma` (adopts `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`)

- **Level 1 (trigger reachability) — FAILS, as a composition gap, not a wrong threshold.**
  `generated_frontier_3_42`'s `moon_cave` region (the corpus's only real LAIR-kind Place,
  `moon_cave_lair`) recorded `trauma_score == 0.0` after a real, freshly-run 5000-tick
  `Kernel.tick_once()` run performed during this implementation (see the new integration test
  below) — zero deaths were ever recorded there. Root cause: `moon_cave`'s `grid_bounds: [100, 70,
  130, 110]` sits ~30 units from the nearest populated region (`orc_stronghold`); `moon_cult_ruins`
  places only `moon_cult_apprentice_circle` there with no hostile faction ever composed within
  combat range.
- **Level 2 (feasible run horizon) — answered with the same 5000-tick run, no longer run needed.**
  Spatial isolation is a fixed geometric fact of the world's composition — running longer does not
  change `moon_cave`'s distance from any hostile faction. The freshly-observed 5000-tick
  zero-accumulation result (re-run during this implementation, not merely cited from the adopted
  ticket) confirms composition, not horizon, is the limiting factor.
- **Level 3 (actual state effects) — none for `moon_cave` specifically.** `moon_cave.trauma_score`
  stays `0.0`; `check_for_lair_spawn()`'s occupant-spawn gate can never open there. Elsewhere in the
  corpus, real trauma accumulation and decay do occur — the accrual/decay code itself
  (`src/engine/world_dynamics.py`'s "Death-triggered Trauma" block,
  `RegionalConsequenceService.process_recovery()`) is correct and wired; this is region-specific,
  not a general mechanism failure.
- **Level 4 (observer evidence) — not separately investigated.** Whether any entity ever paths into
  `moon_cave` for non-combat, quest-driven reasons remains an open question, flagged by the adopted
  ticket's own Implementation Notes and not resolved by this assessment.
- **Exit claim: CONDITION.** The current registry label (`state: done`, `verified.verdict:
  contradicted`, dated 2026-09-17) already states this accurately — no registry label correction is
  warranted.
- **AC3 — where the adopted ticket's scope does not fit**: the adopted ticket's Scope asks for "a
  proposed fix... bring findings + options to peer/user review" — a design decision, not a
  classification. It does not ask the trigger-reachability/horizon/state-effects/observer-evidence
  question this ticket asks explicitly as four separately-answered levels. The adopted ticket's own
  scope is otherwise a superset (it also asks whether the pattern generalizes to future LAIR
  places), which this assessment does not re-derive.

### J3 — `aging_death` / `succession` (no existing ticket; assessed fresh against commit
`702c3af83`, current worktree HEAD — the natural-aging fix landed as `5d4e4a237`/PR #254, already
merged into this ancestry)

- **Old-age check**: `LifecycleSystem.resolve_lifecycle()`
  (`src/systems/lifecycle_systems/lifecycle.py:193-195`) sets `death_reason = "OLD_AGE"` when
  `age_ticks >= max_age_ticks`, called every tick from `src/engine/pipeline.py:414`.
- **Level 1 (trigger reachability) — now real.** The prior dual-writer race that deactivated an
  entity one tick before `resolve_lifecycle`'s OLD_AGE check ever ran is closed
  (`src/engine/apply.py:109` now reads `active=(new_hp > 0 and (life.active or new_age <
  life.max_age_ticks))`, the post-fix formula, re-confirmed by direct read during this
  implementation). `resolve_lifecycle` is now the sole declared authority for old-age
  deactivation. `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` demonstrates the
  OLD_AGE branch fires correctly for an entity reaching `max_age_ticks` through ordinary per-tick
  progression.
- **Level 2 (feasible run horizon) — NOT reachable within any real corpus run at default settings;
  answered with arithmetic, not an open-ended long run, per AC4.** Re-confirmed directly during
  this implementation: `LifecycleComponent().max_age_ticks == 70 * TICKS_PER_FANTASY_YEAR ==
  20,160,000` (`src/core/state.py:165`; `TICKS_PER_FANTASY_YEAR = TICKS_PER_DAY * DAYS_PER_SEASON *
  SEASONS_PER_YEAR = 2400 * 30 * 4 = 288,000`, `src/core/calendar.py:10-13`). Against the
  1,000–5,000-tick corpus runs this repo's own evidence cites, that is ~4,032x–20,160x longer. No
  real corpus run has been observed to produce a natural old-age death through ordinary
  accumulation — stated as an open, unconfirmed-in-practice fact, not assumed either way. Pinned
  as a literal test assertion (see below).
- **Level 3 (actual state effects) — confirmed, via the merged fix's own regression evidence.**
  When triggered, the entity is recorded `active=False`, `death_reason_set="OLD_AGE"`,
  `is_permadeath_set=True`, `death_tick_set=state.tick`; the heir receives inherited feud, a dying
  wish, and inventory/heirloom transfer via a real `ResourceTransferIntent`. Confirmed passing in
  `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
  test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession`.
- **Level 4 (observer evidence, recorded never required) — real, non-combat-channel evidence
  found.** `src/observability/event_extractor.py:462-503` deliberately excludes OLD_AGE deaths from
  `CombatKillEvent` (only `death_reason == "COMBAT"` emits one). Instead: (a) `demographic_
  mortality` fires separately on later corpse removal, and (b) if the dead entity held a
  `SHOPKEEPER`/`WORKER` role, `EconomicVacancyService.check_and_emit()` emits a real
  `WorldEvent(category=PRODUCTION_ROLE_VACATED)` — already covered by
  `tests/integration/economy/test_economic_vacancy_signal.py::
  test_ordinary_progression_old_age_death_fires_vacancy_one_tick_after_age_reaches_max` (landed by
  the merged dual-writer-race fix). The `CombatKillEvent`-exclusion half was covered only
  generically (via `death_reason=None`) prior to this ticket — a narrow, real gap; closed by a new
  test naming `death_reason="OLD_AGE"` explicitly (see Test Summary). This is recorded evidence,
  not a claim that any situated observer can encounter it — that encounterability question is Card
  B0's scope, not this ticket's.
- **Exit claim: CONDITION.** Level 1 and Level 3 are both confirmed working (the dual-writer race
  is already fixed and merged, `5d4e4a237`). The remaining gap is purely a real-corpus-horizon
  reachability condition — not a defect (nothing is broken) and not a mislabel (the registry's
  `aging_death`/`succession` entries already carry accurate, dated 2026-09-28 evidence describing
  exactly this state, added by the now-closed dual-writer-race ticket itself).

### AC6 — registry-write confirmation: zero writes to `registries/mechanisms.yaml`, by design

This ticket performs **zero byte changes** to `registries/mechanisms.yaml`. Per mechanism:

- **J1**: exit claim is DEFECT, but the write is explicitly out of this ticket's scope (see Out of
  Scope) — routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` **as a
  recommendation only**, because that ticket already owns `calamity_intensity`'s registry `state`
  reconciliation and two tickets must not write the same entry.
- **J2**: exit claim is CONDITION; the current registry label (`state: done`,
  `verified.verdict: contradicted`, dated 2026-09-17) already states this accurately — no
  correction needed.
- **J3**: exit claim is CONDITION; the `aging_death`/`succession` registry entries already carry
  accurate, dated 2026-09-28 evidence added by the now-closed
  `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — no correction needed.

Since this ticket writes nothing to the file, there is no ordering/race/double-write risk. The
requirement satisfied here is that the "why no write" reasoning is stated explicitly in the ticket
body (this section) rather than left as a silent skip — AC6's own text ("any label correction is
written through the registry process... not only into planning docs") applies only when a
correction is made; none is made here.

### New/extended tests added

- `tests/architecture/test_calamity_intensity_producer_unwired.py` (new) — pins J1's zero-callers
  DEFECT finding via source-text scan, mirroring `tests/architecture/
  test_displacement_write_paths.py`'s technique.
- `tests/integration/world/test_lair_region_trauma_reachability.py` (new) — pins J2's CONDITION
  finding via a real 5000-tick `Kernel.tick_once()` run against `generated_frontier_3_42`, asserting
  `moon_cave.trauma_score == 0.0`. Marked `@pytest.mark.resource_budget_large` (not `slow`): a real
  timed run during implementation measured 5000 ticks at ~209s — over the default "medium" 60s
  budget but well under the 600s "large" budget the `resource_budget_large` marker forces
  regardless of CLI default (`tests/conftest.py`). Using `resource_budget_large` rather than `slow`
  keeps this test inside the `-m "not slow"` scoped command test_plan.md specifies, so it actually
  runs and is verified, rather than being silently excluded.
- `tests/unit/entities/test_lifecycle_horizon_constants.py` (new) — pins J3's Level-2 horizon
  arithmetic (`max_age_ticks == 20,160,000`, >=1000x the reference corpus run length).
- `tests/unit/observability/test_event_extractor_world.py` — extended with one new test,
  `test_combat_kill_not_emitted_for_old_age_death`, closing the narrow gap identified in Step 7:
  the existing `test_combat_kill_not_emitted_for_hazard_caused_death` already proves the
  `death_reason == "COMBAT"` gate excludes any non-COMBAT death generically (via
  `death_reason=None`), but no existing test named the `"OLD_AGE"` literal explicitly. The "does
  emit `PRODUCTION_ROLE_VACATED`" half was already fully covered by
  `tests/integration/economy/test_economic_vacancy_signal.py::
  test_ordinary_progression_old_age_death_fires_vacancy_one_tick_after_age_reaches_max` — no
  addition needed there.

## Test Summary

All four scoped pytest commands from `test_plan.md` were run against the current worktree HEAD
(`.venv/bin/python3 -m pytest ... -m "not slow"`). No test failures, no production code edits.

1. **Regression surface — unit calamity/trauma** (7 files): `71 passed`.
2. **Regression surface — unit lifecycle/aging** (5 files): `27 passed`.
3. **Regression surface — integration** (4 files): `28 passed, 5 deselected` (the 5 deselected are
   pre-existing `slow`-marked tests in those files, excluded by `-m "not slow"` as intended).
4. **New/extended tests** (`tests/architecture/test_calamity_intensity_producer_unwired.py`,
   `tests/integration/world/test_lair_region_trauma_reachability.py`,
   `tests/unit/entities/test_lifecycle_horizon_constants.py`): `4 passed in 188.03s`. Verified this
   passes using the *exact* command string from `test_plan.md` (no `--resource-budget large` CLI
   flag) — the `@pytest.mark.resource_budget_large` marker on the new integration test forces the
   large (600s) budget on its own, confirming it does not depend on an undocumented CLI flag to
   pass in CI's default invocation shape.
5. `tests/unit/tools/test_mechanism_registry.py` (AC6 registry-integrity check, per Step 3):
   `83 passed`, confirming `registries/mechanisms.yaml` remains valid and untouched.
6. `tests/unit/observability/test_event_extractor_world.py` (the extended file, Step 7 — **note**:
   not `test_event_extractor_world_dynamics.py`, the file test_plan.md item 5 named as one of two
   candidates; see plan.md Deviations for why the real pre-existing `CombatKillEvent`-exclusion
   coverage lives in this different, unlisted file, and is therefore not part of any of the four
   named scoped commands verbatim): run standalone, `21 passed in 0.43s` (20 pre-existing +
   the 1 new `test_combat_kill_not_emitted_for_old_age_death` — corrected during Verify after
   Architecture-Verify and the Test phase's own isolated run both independently counted 21, not
   the 24 this section originally, incorrectly, self-reported).

**Incidental side effect, reverted, not part of this ticket's diff**: running
`tests/unit/tools/test_mechanism_registry.py::test_make_target_generates_verification_view`
regenerates the real, committed `docs/brainstorm/mechanism_verification_view.md` from
`registries/mechanisms.yaml` as part of its own designed check (`make
mechanism-verification-view` then `--check`). That regeneration produced a 2-line diff purely
because the committed doc (`git log`: 2026-09-24) predates the registry's last real edit (`git
log`: 2026-09-29, the merged `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`) — pre-existing
drift unrelated to and not caused by this ticket, which never edits `registries/mechanisms.yaml`.
Reverted via `git checkout -- docs/brainstorm/mechanism_verification_view.md` to keep this
ticket's diff scoped; not this ticket's responsibility to regenerate/commit.

Never ran `pytest tests/` (full suite), per Scope Guards.

## Files Changed
- `tickets/inprogress/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING.md` — this file
  (Implementation Notes, Assumptions/Open Questions, Test Summary, Files Changed, Completion
  Summary, Status). `## Scope`, `## Out of Scope`, and `## Acceptance Criteria` were left
  untouched per plan Step 1 — this ticket's format states ACs as a numbered list, not `- [ ]`
  checkboxes; AC-by-AC satisfaction is instead stated explicitly in Completion Summary.
- `staging_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/plan.md` —
  Deviations section added (Steps 5 and 7).
- `staging_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/investigation.md` —
  pre-existing, created before this implementer run; not rewritten by this run.
- `staging_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/test_plan.md` —
  pre-existing, created before this implementer run; not rewritten by this run.
- `tests/architecture/test_calamity_intensity_producer_unwired.py` — new file (Step 4).
- `tests/integration/world/test_lair_region_trauma_reachability.py` — new file (Step 5).
- `tests/unit/entities/test_lifecycle_horizon_constants.py` — new file (Step 6).
- `tests/unit/observability/test_event_extractor_world.py` — extended with one new test (Step 7).
- `docs/plans/systemic_world/roadmap.md` — appended a new sub-bullet under §11 item 5 (Step 8).

No `src/` file, no `registries/mechanisms.yaml`, and no `docs/world_rules/` file was changed.

## Completion Summary

This ticket is an assessment closed by classification, not a code fix — no `src/` file was
changed. J1 (`calamity_intensity`) is classified **DEFECT** (recommendation only, routed to
`TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`); J2 (`regional_trauma`) and J3
(`aging_death`/`succession`) are both classified **CONDITION** (spatial isolation and
real-corpus-horizon reachability, respectively) with their existing registry labels already
accurate. `registries/mechanisms.yaml` was read but not written — see the "AC6" note in
Implementation Notes for the explicit per-mechanism reasoning. All four findings were re-verified
directly against current worktree HEAD (`702c3af83`) during implementation, not merely cited from
`investigation.md`: J1's zero-callers claim via `grep`, J2's spatial-isolation claim via a fresh,
real 5000-tick `Kernel.tick_once()` run (`moon_cave.trauma_score == 0.0` confirmed), and J3's
horizon arithmetic via direct reads of `src/core/state.py`/`src/core/calendar.py`.

Acceptance criteria: **AC1** — all three mechanisms answered at all four levels (Implementation
Notes), no level reported `BLOCKED_WITH_REASON` was needed (Level 1 evidence was directly
obtainable for all three). **AC2** — exactly one exit claim per mechanism (DEFECT / CONDITION /
CONDITION). **AC3** — each adopted ticket's (J1, J2) scope mapped onto the four levels with an
explicit "does not fit" statement (Implementation Notes). **AC4** — Level 2 answered with minimum
evidence per mechanism (J1: static call-graph grep, moot since Level 1 already fails structurally;
J2: the already-observed 5000-tick run, re-run fresh here rather than merely cited; J3: literal
horizon arithmetic, now pinned by `tests/unit/entities/test_lifecycle_horizon_constants.py`).
**AC5** — every J3 finding names the observed commit (`702c3af83`) and the merged fix commit
(`5d4e4a237`/PR #254). **AC6** — satisfied as "zero registry writes, by design," with explicit
per-mechanism reasoning recorded in Implementation Notes; `registries/mechanisms.yaml` itself was
never opened for writing (confirmed by `tests/unit/tools/test_mechanism_registry.py` passing
unmodified). **AC7** — findings routed to `docs/plans/systemic_world/roadmap.md` §11 item 5 (new
appended sub-bullet), mirroring item 3's own sibling-ticket precedent, not the frozen
`docs/world_rules/` Rule Catalog.

Four new/extended regression-pinning tests were added (Steps 4-7), one shared-root-cause finding
was checked and found **not confirmed** (J2's spatial isolation is the opposite cause from
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`'s death-outcome-kind filter gap — stated and
not absorbed, zero edits to that ticket's file). All four scoped pytest commands from
`test_plan.md` pass (130 total tests across the regression surface, all passing; 4 new/extended
tests, all passing), plus `tests/unit/tools/test_mechanism_registry.py` (83 passed). No fix was
made to any of the three mechanisms, no fourth mechanism was added, and no adjacent
out-of-scope ticket (`TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`,
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, the `pressure-propagation-economy` epic) was
absorbed.
