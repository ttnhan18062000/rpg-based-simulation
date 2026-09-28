---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE
phase: open
date: 2026-09-28
tags: [bug, lifecycle, engine, determinism]
---

# TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE

## Title
An entity that dies of natural aging is deactivated with no death cause and no succession, because
two systems write `lifecycle.active` one tick apart with no declared precedence

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
In an ordinary run, an entity that reaches `max_age_ticks` through normal per-tick aging goes
`active=False` with `death_reason=None` and **never recovers**. None of its lineage consequences
fire: no OLD_AGE record, no heir inventory/heirloom transfer, no nemesis-feud transfer, no
dying-wish seeding.

The cause is a dual-writer race on `entity.lifecycle.active`. Two independent writers disagree by
exactly one tick, and there is no declared precedence rule between them:

1. `ApplyPath._compute_entity_changes` (`src/engine/apply.py:94-109`) computes
   `new_age = life.age_ticks + 1` and commits
   `active=(new_hp > 0 and new_age < life.max_age_ticks)`. On the tick where `new_age` first
   reaches `max_age_ticks`, this **passive** branch sets `active=False` with no `death_reason` and
   no heir dispatch.
2. `LifecycleSystem.resolve_lifecycle`'s OLD_AGE branch
   (`src/systems/lifecycle_systems/lifecycle.py:193-195`) tests
   `entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks` against the value **persisted at
   the end of the prior tick** — one tick behind writer 1.
3. On the following tick, `resolve_lifecycle`'s own loop guard
   (`src/systems/lifecycle_systems/lifecycle.py:147-148`, `if not entity.lifecycle.active:
   continue`) finds the entity already inactive and skips it entirely. Its OLD_AGE branch can
   therefore never fire for a natural-aging death.

All three citations were re-verified against current `origin/main` source on 2026-09-28, not taken
from the source report alone.

This is the same **class** of defect as the regional-sovereignty dual-writer closed in
`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` (#247): two systems writing one durable
authoritative field with no declared resolution rule. It is a different field and a different pair
of writers.

## Scope
- Establish and document **one declared authority** for old-age deactivation, with an explicit
  resolution rule when the passive apply-path branch and `resolve_lifecycle` disagree.
- Make a natural-aging death produce an `OLD_AGE` `death_reason` and run its full lineage
  consequences, identically to the already-working staged case.
- Pin and document the tick on which a natural-aging death is recorded, including whether the fix
  shifts it relative to current behavior.
- Determine empirically whether the **starvation / sleep-debt** death path is silent in the same
  way — the passive branch at `apply.py:102-109` also computes `new_hp` from
  `bio.hunger >= 95.0` / `bio.sleep_debt >= 98.0`. Currently `UNKNOWN` from inspection only. If it
  is silent, fix it here or split it out with a written reason.
- Add regression coverage that fails against current code for a death reached through **ordinary
  per-tick progression**, not a staged starting state.
- Registry/parity follow-through: dated evidence notes on the `aging_death` and `succession`
  mechanism entries, and the matching parity-ledger entry.

## Out of Scope
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`. Related in class only. It is held on
  this session's track and must be sequenced against any fix here that touches world-dynamics /
  lifecycle **ordering** — see Assumptions.
- Any player-facing projection, observer contract, or presentation work. Not this ticket.
- The systemic-world first wave's own items J, B0 and C1. This ticket is Card R, scheduled ahead of
  them by explicit owner decision (see Assumptions).
- Combat- and hazard-triggered death paths, except where the fix's contract-level risk requires
  proving they are unchanged. The source report notes combat death is set by an earlier same-tick
  phase and, on a static read, does not appear to share this age-based race — **unverified**, so it
  is a risk to check, not a claim to rely on.

## Acceptance Criteria
1. An entity aging naturally to `max_age_ticks` through ordinary `Kernel.tick_once()` progression
   is recorded dead with `death_reason == "OLD_AGE"`.
2. That death dispatches its lineage consequences — heir inventory/heirloom transfer, nemesis-feud
   transfer, and dying-wish seeding — matching the behavior the staged-age case already produces.
3. No tick exists on which the entity is `active=False` with `death_reason=None` as a terminal
   state.
4. The tick on which a natural-aging death is recorded is pinned by an explicit test and documented.
   If the fix shifts that tick relative to current behavior, the shift is stated and justified, not
   absorbed silently — this is a determinism-visible change.
5. A single declared authority for old-age deactivation is documented, with the resolution rule when
   the two writers disagree.
6. A regression test reproduces the defect through ordinary per-tick progression and **fails against
   pre-fix code** — proven by running it against the unfixed tree, not asserted.
7. The starvation / sleep-debt path is answered at runtime as either affected or unaffected, with
   evidence. `UNKNOWN` is not an acceptable closing state for this item; `BLOCKED` with a named
   reason is.
8. Existing death, inheritance, passive-decay, group/clan-lifecycle and economy-vacancy tests pass
   **unmodified**, or any change to one is justified explicitly per the Gate Integrity rule.
9. `aging_death` and `succession` registry entries carry dated evidence notes, and the matching
   parity-ledger entry is updated.

## Related Tickets
- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` — same defect class (dual writer on a
  durable authoritative field), closed 2026-09-27 as #247.
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — held; sequencing constraint, see
  Out of Scope.
- `TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE` — an earlier **withdrawn** draft of this same
  defect, never in `tickets/`, surviving only in the `systemic-world-roadmap-proposal` branch
  history. Unreviewed and non-binding; superseded by this ticket.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card R (branch
  `systemic-world-roadmap-proposal` @ `5442a3d1a`, PR #249, unmerged).
- `docs/plans/systemic_world/first_wave_plan.md` §3 — the scheduling gate this ticket was moved
  ahead of.
- `docs/plans/systemic_world/roadmap.md` §7.1 — the diagnosis.
- `docs/mechanics/01_entity_anatomy.md` — biological pressures and XP/aging scaling.
- `docs/engine/authoritative_mutation_pipeline_contract.md` — apply-path law, the contract the
  passive branch is operating under.
- `docs/core/state.md` — authoritative vs non-authoritative state partitioning.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-lineage-composition-probe-findings.md` — the
  runtime reproduction and root-cause trace (on the unmerged branch above).

## Related Code Areas
- `src/engine/apply.py:94-109` — `ApplyPath._compute_entity_changes`, the passive writer.
- `src/systems/lifecycle_systems/lifecycle.py:147-148` — the already-inactive skip guard.
- `src/systems/lifecycle_systems/lifecycle.py:193-195` — the OLD_AGE branch that never fires.
- `src/engine/kernel.py:781`, `src/engine/kernel.py:835` — the commit calls the passive branch
  reaches via `apply.py:210`.
- `tests/simulation_quality/test_heir_inventory_transfer_corpus.py`,
  `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` — both pass
  today and both **stage age past the maximum**, which is exactly why they miss this.

## Assumptions / Open Questions
- **Scheduling: legitimate, and no longer an override.** This was filed on 2026-09-28 by direct
  owner instruction while `first_wave_plan.md` §3 (@ `5442a3d1a`) still gated the defect behind
  three triggers, none of which had fired — so it was originally recorded here as a deliberate
  override of that gate. **That is now superseded.** The package was updated the same day
  (@ `43db4a7fc`, verified against the remote) and §3 gained a fourth trigger, listed first:
  *"the owner scopes it directly as an independent ticket, which may land ahead of J, B0 and C1."*
  That is precisely what happened, so this ticket is trigger (i) firing, not a bypass. §3 also now
  states the fix's **correctness does not depend on owner memo decision 5**, and that this ticket
  sits **outside** the first wave rather than ahead of it in the same queue. No doc correction is
  owed any more.
- **The unreviewed prototype fix is explicitly not prescribed** (§3, `43db4a7fc`). This ticket
  treats it as optional evidence only — see the last bullet below.
- **Q1.** Which writer should be the declared authority — should the passive branch stop writing
  `active` entirely and only advance `age_ticks`, leaving deactivation solely to
  `resolve_lifecycle`? Not pre-decided here; it is the implementation's central design choice.
- **Q2.** Does the correction shift the recorded death tick? Likely yes, by one. Needs pinning.
- **Q3.** Are spawns created inactive relying on this same passive branch to become active?
  `UNKNOWN`, inspection only. **If answering requires deciding what an inactive spawn means in the
  world, do not pick a default — return it to the systemic-world roadmap.**
- **Q4.** Is the starvation / sleep-debt path silent in the same way? `UNKNOWN`, inspection only.
  See Acceptance Criterion 7.
- The local branch `natural-aging-old-age-dispatch-fix-unreviewed` holds an unreviewed prototype and
  a natural-aging scenario that failed 3/3 against current code. It is **optional evidence, never an
  approved fix**, was never run against the suite, and does not address Q3. Inspect or discard.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE/plan.md`'s
12 steps, in order. No architectural deviation from the approved plan.

**Q1 (declared authority) — resolved as planned.** `src/engine/apply.py:109`'s passive-branch
`active=` formula changed from `(new_hp > 0 and new_age < life.max_age_ticks)` to
`(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`.
`LifecycleSystem.resolve_lifecycle`'s OLD_AGE branch (`src/systems/lifecycle_systems/
lifecycle.py:193-195`) is now the sole declared authority for old-age deactivation; the passive
branch keeps only its immediate `new_hp > 0` HP-death gate. Proven via a pre-fix regression run
(Step 1's new test file failed 3/3 against unmodified `src/engine/apply.py`, for exactly the
described reason — `death_reason` stayed `None` — then passed 4/4 after the one-line fix landed).
No `src/engine/kernel.py` phase-ordering change was needed or made.

**Q3 (`initial_active=False` spawn reactivation) — pinned as unchanged, returned to the
systemic-world roadmap, not decided here.** The new formula reduces to the pre-fix expression
whenever `life.active` is already `False`, so the accidental reactivation side effect (a
construction-time-dormant spawn flips `active=True` the next `is_life_due` tick purely because age
is below max) is deliberately preserved bit-for-bit, not designed anew.
`tests/unit/entities/test_archetype_entity_factory.py::
test_initial_active_false_spawn_is_reactivated_by_ordinary_progression_post_fix` pins this current
behavior via a real `Kernel.tick_once()` run. Whether an `initial_active=False` spawn should
require an explicit, intentional activation path instead of this accidental one remains an open
design question for the systemic-world roadmap — zero production callers exist today
(`src/worldassembly/entity_spawner.py` hardcodes `initial_active=True`), so nothing live depends on
either answer.

**AC7 (starvation/sleep-debt silent death) — answered as EMPIRICALLY CONFIRMED AFFECTED, split
into a follow-up ticket, not fixed in this ticket.** Re-confirmed via
`tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`: an entity driven to `hp=0`
purely by passive hunger/sleep-debt decay still ends with `active=False, death_reason=None` after
this ticket's fix, because `resolve_lifecycle` has no HP/alive-based detection branch at all (only
OLD_AGE and COMBAT) — a distinct root cause (a missing detection branch) from the age dual-writer
race this ticket fixes (a timing race), so the writer-precedence fix cannot and does not touch it.
Filed `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` (`tickets/todos/`, standard tier) with
the drafted scope from `plan.md` Step 7, carrying the concrete fix (a new `resolve_lifecycle`
HP/alive-based death-detection branch, wired through the existing lineage-dispatch path).

**Vacancy-signal interaction (Step 4), a finding beyond the plan's own framing.**
`EconomicVacancyService.check_and_emit` is only ever invoked from `resolve_lifecycle`'s own
`recent_deaths` aggregate — an entity enters that list only on the tick `resolve_lifecycle` itself
detects `is_dead=True`. Pre-fix, an ordinary-progression old-age death was **never** added to
`recent_deaths` at all (the entity was skipped forever once the passive branch silently
deactivated it), so the vacancy signal did not merely fire one tick late for this path — it never
fired at all. Post-fix, it correctly fires on the tick the OLD_AGE death is recorded, one tick
after `age_ticks` first reaches `max_age_ticks`. Pinned by a new test in
`tests/integration/economy/test_economic_vacancy_signal.py`.

**Regression-surface finding (Step 12), pre-existing and unrelated — not touched.**
`tests/integration/world/test_long_run_stability.py::test_long_run_stability` and
`tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism` both fail with
`TimeoutError: Test execution exceeded the resource time limit.` (`tests/conftest.py:68`), tripped
by a `governance_ecology` phase-cost spike around tick 501 in this environment. Verified this is
**pre-existing and unrelated to this ticket's fix**, not a regression it caused: reverted
`src/engine/apply.py` to its pre-fix content, re-ran both tests, and got the byte-identical failure
(same tick 501 budget overrun, same phase-cost breakdown) before restoring the fix. This matches
the already-known, owner-parked "slow regression" class of issue (root-caused to `kernel.py`,
blocked pending engine re-architecture per prior session record) — reported here truthfully per the
Gate Integrity rule, not edited around. All other tests in every one of `test_plan.md`'s five
scoped command groups pass.

**AC-by-AC disposition:**
- AC1 (OLD_AGE death via ordinary progression) — MET. New regression test.
- AC2 (lineage consequences dispatch) — MET. Heir inventory transfer confirmed in the same test.
- AC3 (no silent terminal `active=False`/`death_reason=None` tick) — MET. Full-trace assertion.
- AC4 (death tick pinned and shift documented) — MET. Pinned by test; documented in
  `docs/guidelines/intentional_divergences.md` §2.59.
- AC5 (single declared authority documented) — MET. Source guard test +
  `docs/simulation/lifecycle_systems_contract.md` update.
- AC6 (regression test fails against pre-fix code, proven by running it) — MET. Ran before and
  after the fix; failure reason matched the described defect both times it was checked.
- AC7 (starvation/sleep-debt path answered) — MET as "affected, split out with a written reason"
  (not `UNKNOWN`, not fixed here). Follow-up: `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`.
- AC8 (existing tests pass unmodified) — MET for every test in scope, with one disclosed exception:
  the two long-run tests above fail for a confirmed pre-existing, unrelated reason (not modified,
  not silently excused — see finding above).
- AC9 (registry/parity dated evidence notes) — MET. `PROG-030` updated via
  `tools/parity_ledger_writer.py`; `aging_death`/`succession` entries in
  `registries/mechanisms.yaml` carry new 2026-09-28-dated addenda.

## Test Summary

All five `test_plan.md` "Scoped Pytest Commands" groups run, plus the new
`tests/unit/engine/test_apply.py` guard file (added by this ticket, postdating `test_plan.md`'s own
authoring) and the demographics/archetype-choice group, for extra confidence:

- Core lifecycle/progression + new mechanic-scenario regression: **87 passed**.
- Apply-path/apply-plan optimization parity: **21 passed**.
- Economy vacancy (unit + integration, includes the new tick-shift test): **12 passed**.
- Group/clan lifecycle: **25 passed**.
- Long-run integration: **4 passed, 2 failed** (`test_long_run_stability`,
  `test_1000_tick_determinism` — confirmed pre-existing/environmental, reproduces identically
  against pre-fix code, see Implementation Notes; not modified).
- New architecture-guard file, `tests/unit/engine/test_apply.py`: **2 passed**.
- Demographics/archetype-choice (bonus, not required by `test_plan.md`'s command list): **64
  passed**.

New tests added by this ticket, all passing post-fix and confirmed failing pre-fix where required:
- `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` — 4 tests (3 fail pre-fix per
  AC6, 1 — the AC7 starvation pin — passes both before and after, since it pins already-broken
  behavior this ticket does not fix).
- `tests/unit/engine/test_apply.py` — 2 tests (new file).
- `tests/integration/economy/test_economic_vacancy_signal.py` — 1 new test (existing 4 unmodified).
- `tests/unit/entities/test_archetype_entity_factory.py` — 1 new test (existing 16 unmodified).

## Files Changed
- `src/engine/apply.py` — the fix (Step 2).
- `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` — new (Steps 1, 6).
- `tests/unit/engine/test_apply.py` — new (Step 3).
- `tests/integration/economy/test_economic_vacancy_signal.py` — new test added (Step 4).
- `tests/unit/entities/test_archetype_entity_factory.py` — new test added (Step 5).
- `tickets/todos/TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP.md` — new follow-up ticket
  (Step 7).
- `docs/simulation/lifecycle_systems_contract.md` — declared-authority section, AC7
  forward-reference (Step 8).
- `docs/guidelines/intentional_divergences.md` — §2.59 added (Step 9).
- `docs/parity_ledger/progression.yaml` — `PROG-030` updated via `tools/parity_ledger_writer.py`
  (Step 10).
- `registries/mechanisms.yaml` — dated addenda on `aging_death` and `succession` (Step 11).
- `tickets/inprogress/TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE.md` — this file.
- `staging_artifacts/TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE/plan.md` — Deviations
  section added.

## Completion Summary
Fixed the dual-writer race on `entity.lifecycle.active`: `ApplyPath._compute_entity_changes`'s
passive branch no longer independently deactivates an entity for old age once it is already
active, making `LifecycleSystem.resolve_lifecycle`'s OLD_AGE branch the sole declared authority.
An ordinary-per-tick-progression old-age death now correctly records `death_reason="OLD_AGE"` and
dispatches its full succession/heirloom lineage consequences, one tick later than the prior (buggy,
silent) behavior — a documented, tested, determinism-visible shift. The starvation/sleep-debt
silent-death path was investigated, empirically confirmed still affected (a distinct, missing-
detection root cause, not this ticket's timing race), and split into follow-up ticket
`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` rather than fixed here. The `initial_active=
False` spawn reactivation side effect was pinned as unchanged and its underlying design question
returned to the systemic-world roadmap, per explicit prior instruction not to default it. All nine
acceptance criteria are met; the full scoped regression surface passes except two long-run tests
confirmed pre-existing and unrelated to this fix.
