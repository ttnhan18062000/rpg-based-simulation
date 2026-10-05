---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT
phase: done
date: 2026-10-05
tags: [engine, determinism, measurement]
---

# TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT

## Title
Outside `audit_mode` the tick-budget watchdog drops work on a **wall-clock** comparison, so any world slow
enough to trip it is nondeterministic as a function of machine load — and every measurement this project
takes outside `audit_mode` is therefore load-dependent

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**Two lanes measured the same world and got opposite answers about determinism. Both were right, and the
mechanism explains it.**

`rpg-implementer-2` found `frontier_living_world` **not reproducible run to run**: same code, same world,
seed 42, run alone — **8 deaths at tick 500 in one run, 10 in another**
(`probes/determinism_check_fl_2000_run1/2`). `generated_frontier_3_42` was identical across every run,
including paired capped/uncapped runs. It saw `Tick N exceeded budget` warnings on the diverging world and
named the kernel throttle as a candidate without investigating.

`rpg-implementer` reported, on the same world, **`run1 == run2` on all four worlds with identical
counters** — measured with `audit_mode=True` and `max_tick_budget_ms=1e9`.

**The mechanism, read by the planner at `src/engine/kernel.py:466-469`:**

```
hard_cap = self._profile.max_tick_budget_ms
if not self._audit_mode and self._state.tick > 5 and self._final_compute_ms > min(hard_cap, limit_ms):
    logger.warning(f"Tick {...} exceeded budget: {self._final_compute_ms:.2f}ms vs limit {...}. Aborting next tick if sustained.")
    self._status.record_dropped_work(9999)
```

> **CORRECTION (2026-10-06, perf review on PR #355; this ticket was filed with two errors, both the planner's):**
> 1. `kernel.py:466-469` does **not** drop work. It is the *end-of-tick* check; it only sets a telemetry counter (the `9999`
>    sentinel) that nothing reads to change behaviour. **The work is dropped by the mid-tick throttle at `kernel.py:618-626`**:
>    every 10 results it checks wall-clock time and, outside `audit_mode`, sheds the rest of the tick and forces `DEGRADED`.
>    The "Three facts" below describe the right symptom but cite the wrong lines for the work-dropping.
> 2. "Deterministic counter vs report-only" is **not** an open contract question. It was decided on 2026-10-03
>    (PERF-D1 inputs 2 and 3; `docs/engine/deterministic_execution.md`, "Canonical contract"): report-only is the answer under
>    both contracts today. Scope 3 below is therefore settled, not pending.
> The evidence stands and is kept: `frontier_living_world` 8 vs 10 deaths at tick 500, same seed; `generated_frontier_3_42` stable; and
> the `audit_mode` runs as the control arm, repeating exactly.

Three facts combine into the defect:
1. The guard is **skipped entirely in `audit_mode`** (`not self._audit_mode`).
2. `_final_compute_ms` is a **wall-clock measurement**, not a deterministic work counter.
3. Tripping it calls `record_dropped_work(9999)` — **work is actually discarded**, so outcomes change.

So outside `audit_mode`, a world whose ticks approach the budget will drop work on some runs and not
others, purely according to how loaded the machine was. `frontier_living_world` is slow enough to trip it;
`generated_frontier_3_42` is not. **This is wholly separate from the `id()`-keyed dirty-set defect fixed in
#344**, which was allocation-dependent and reproduced *inside* `audit_mode`. That one is fixed; this one was
never in scope and is still live.

**Aggravating context, worth stating:** this repository is routinely worked by ~8 concurrent interactive
sessions, several running simulations at once. A wall-clock-gated work-dropping guard is maximally
load-sensitive in exactly that environment, so measurements taken while another lane is running a
2000-tick probe are not comparable to measurements taken on a quiet machine.

## Consequences already incurred (not hypothetical)
Every single-run figure taken on `frontier_living_world` **outside `audit_mode`** is an indication, not a
measurement. Named explicitly so they are not cited as values:
- Lane B's unification figures: trauma crossings tick 5211 / 5317, `hometown` 7 -> 12, 275 deaths.
- Lane B's `bandit_road`/`goblin_camp` "~50 by tick 10,000" hazard figures (unpaired runs).
- ~~Lane A's opportunity-attack shift `38 -> 644` / `488 -> 283`.~~ **RETRACTED 2026-10-05 by the planner,
  on Lane A's correction. This ticket does NOT explain those figures and must not be cited as their cause.**
  Every run behind them (`combat_volume.py`, both arms, both trees) used `audit_mode=True` with
  `max_tick_budget_ms=1e9`, and `kernel.py:467` skips the watchdog when `audit_mode` is set. **The watchdog
  was off in both arms, so it cannot differ between them.** The planner generalised this mechanism to Lane
  A's figures without re-checking that its runs were in `audit_mode` — which Lane A had stated from its
  first report. The shifts remain **genuinely unexplained**, and that is how Lane A's PR states them.
  **The cheapest next step for those figures is unrelated to this ticket:** Lane A's fix-tree runs were
  shown identical across two runs, but each *control* figure is a single run, so the control arm's
  reproducibility is simply unmeasured. Repeat the control run before theorising about the mechanism — an
  unstable control would explain an opposite-signed pair without any new defect.

**What is NOT affected**, and must not be re-litigated: anything derived from **static geometry** (the
region bounds, areas, containment, the 15 overlapping pairs, the 24-world overlap census) — these never ran
a simulation. Decision 13's evidence base is geometric and survives intact. Likewise the trauma->panic
**units** argument, which is arithmetic about a mapping.

## Scope
1. **Confirm the mechanism with the cheap discriminator before anything else.** Re-run
   `frontier_living_world` seed 42 twice with `audit_mode=True` and an effectively unlimited
   `max_tick_budget_ms`, and twice with the default profile, on an otherwise quiet machine. Expected:
   identical under `audit_mode`, divergent under the default. If that does **not** reproduce, the cause is
   something else and the rest of this ticket is void — say so.
2. **Quantify the exposure.** Across the corpus, which worlds trip the guard at default profile, at what
   tick, and how often? A world that never trips it is safe to measure without `audit_mode`; one that does
   is not.
3. **Decide the correct behaviour, and bring the planner before implementing** — this is a contract
   question, not a free choice. Candidates: (a) gate work-dropping on a deterministic work counter rather
   than wall-clock; (b) keep the wall-clock guard for operational protection but make it **report-only**,
   never mutating simulation outcome; (c) make the guard deterministic by seeding it from the tick's own
   measured work. Note `docs/engine/performance_contract.md` and the watchdog architecture doc both bear on
   this, and CLAUDE.md's hard rule is "Do not break determinism."
4. **Record the measurement standard that follows**, wherever lanes will actually read it: any figure
   intended as a value, not an indication, is taken under `audit_mode` with the budget effectively
   disabled. Lane A already does this; it should be the documented default, not folklore.
5. Implement whichever option scope 3 settles, with a disabling-control test and a divergence entry if the
   guard's semantics change.

## Out of Scope
- #344's `id()`-keyed dirty-set defect. **Fixed, different mechanism, do not reopen.**
- Making `frontier_living_world` faster. Performance is a separate concern; this ticket is about
  determinism.
- Re-taking every historical figure. Re-take only those a live ticket actually cites as a value.
- The hazard cap and the region lookup. Both are separate tickets whose figures this ticket qualifies.

## Acceptance Criteria
- [ ] The audit-mode / default-profile discriminator run and its result stated, on a quiet machine.
- [ ] Per-world census of which corpus worlds trip the guard, at which tick.
- [ ] A planner-approved decision among (a)/(b)/(c) with the contract reasoning, before implementation.
- [ ] The measurement standard written where lanes read it (`docs/engine/` or the delivery guide), not only
      in this ticket.
- [ ] Disabling-control test; divergence recorded if guard semantics change.
- [ ] (REMOVED 2026-10-05: the `38 -> 644` / `488 -> 283` shift is **not** an instance of this defect —
      both arms ran under `audit_mode`, where the watchdog is disabled. Do not re-take it for this ticket.)

## Related Tickets
- `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK` (#344, done) — the other
  determinism defect; this is **not** a regression of it.
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (done) — characterised divergence
  that survived `audit_mode`, i.e. a different signature from this one.
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` and
  `TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION` — whose `frontier_living_world`
  figures this ticket downgrades to indications.
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` (#347) — cites this
  ticket as a **separate** source of non-`audit_mode` nondeterminism and states explicitly that it does not
  explain that ticket's own figures. Keep that distinction; do not collapse the two.

## Related Docs
- `docs/engine/performance_contract.md` — hardware classes and the budget this guard enforces.
- `docs/architecture/simulation_watchdog.md` — the watchdog whose alert this fires.
- `docs/engine/kernel.md` — the deterministic loop this guard sits inside.
- `docs/engine/deterministic_execution.md` — corrected by #344; needs this case added whichever way it is
  settled.

## Related Stored Artifacts
- Lane B's `probes/determinism_check_fl_2000_run1/2` — the 8-vs-10 divergence.
- Lane A's attack-path `probes/` — the `audit_mode` + `1e9` runs that are the natural control arm.

## Related Code Areas
- `src/engine/kernel.py:466-474` — the guard, the wall-clock comparison and `record_dropped_work(9999)`.
- `src/perf/profiles.py:45` — where `max_tick_budget_ms` is set per profile.
- `src/engine/scenario_runtime.py:409` (`200.0`), `src/domains/campaigns/runner.py:57` (`100.0`),
  `src/observability/readiness/harness.py:95` (`50.0`) — the budgets actually in force for different
  entry points; a probe's determinism depends on which of these it inherits.

## Assumptions / Open Questions
- **Lane.** Contested-adjacent: `kernel.py` is the deterministic loop. **Planner holds this pending the
  scope-3 decision**; do not grant a lane until the contract question is answered.
- Open: `record_dropped_work(9999)` — is 9999 a sentinel or a real quantity? If a sentinel, the dropped-work
  telemetry is also unreliable for any run that tripped the guard, which would affect the monitoring data.
- Open: does `limit_ms` differ from `hard_cap` in a way that makes the effective limit vary per run? The
  `min(hard_cap, limit_ms)` suggests two sources.
- Lane B did not investigate beyond naming the candidate, correctly. Nothing in its report should be read
  as a claim about cause.

## Implementation Notes
**Closed as superseded; no implementation under this ticket.** Perf took the work over: the owner adopted perf's plan on PR #355 (a
short perf `kernel.py` slice, PERF-M1-T03b, plus the tick-budget throttle made report-only, lands before the salience fix). Perf's own
report-only ticket was **not yet filed** when this closed, so the handover record is PR #355, comment `6000452921`. `src/engine/kernel.py`
is not edited by rpg until that slice merges.

Evidence kept (see the correction block in the Request Summary): `frontier_living_world` seed 42, 8 vs 10 deaths at tick 500 on
identical code; `generated_frontier_3_42` stable; the `audit_mode` + `max_tick_budget_ms=1e9` runs (this session's measurement standard)
repeat exactly and serve as the control arm. That measurement standard is already how every Lane A figure labelled a "value" in the
batch this closed under was taken. Not verified by this closure: the mid-tick throttle's behaviour at `kernel.py:618-626` was taken from
perf's review, not re-read or re-run here.

## Test Summary
No tests: nothing changed under this ticket.

## Files Changed
- none under this ticket (the ticket file moved to `done/`)

## Completion Summary
Superseded by perf's report-only ticket (handed over on PR #355, comment `6000452921`). Record corrected: the work is dropped by the
mid-tick throttle at `kernel.py:618-626`, not by `kernel.py:466-469` (a telemetry counter), and report-only was already decided on
2026-10-03. Acceptance criteria are left unchecked because the work moved to perf, not because it was done.
