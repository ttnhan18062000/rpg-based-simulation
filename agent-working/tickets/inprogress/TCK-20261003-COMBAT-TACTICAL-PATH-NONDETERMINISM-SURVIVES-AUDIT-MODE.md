---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE
phase: open
date: 2026-10-03
tags: [engine, combat, determinism, root-cause]
---

# TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE

## Title

Run-to-run divergence on the combat/tactical path that `audit_mode=True` and a raised tick budget do
**not** suppress — a different mechanism from `INFRA-273`

## Status

INPROGRESS

## Tier

standard

## Type

bug

## Priority

P1

## Attribution

**The measurement in this ticket is `rpg-implementer`'s, not mine.** It was produced while implementing
`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (PR #291) and reported to
`rpg-feature-planning` on 2026-10-03. This ticket is filed by `rpg-feature-planning` because the finding
was at risk of living only in a cross-session thread and in a PR that may or may not land, and because
it blocks other work (see Blocks). **Full numbers and caveats are in that ticket's Implementation Notes,
"2026-10-03 re-measured", which is the citation of record.** Do not restate them from here if they
disagree — that file wins.

## Request Summary

Two identical runs of `frontier_living_world` seed 42, 2000 ticks, **with `audit_mode=True`,
`max_tick_budget_ms` raised, `LocalSequentialExecutor`, one run at a time on an idle machine**, produced
**different results: 780 vs 1609 opportunity attacks.** Unmodified `main` never diverges under the same
protocol. Not `PYTHONHASHSEED` (varies with `PYTHONHASHSEED=0` too), and intermittent — one 4-run
per-tick dump was identical through tick 24.

Bisecting with throwaway copies, **either half of that ticket's change alone reproduces it**
(hostility-only: 3 distinct trails in 5 runs; obj_kind-only: 2 in 5); `main` never does. Neither half
contains a wall-clock read or set iteration.

**This is not `INFRA-273`, and the distinction is the whole point of filing it separately.**
`INFRA-273` / `docs/audits/D06_longrun_health.md` §F6-F7 is the mid-tick emergency throttle at
`src/engine/kernel.py:612-620`, which drops authoritative result items when
`not self._audit_mode and elapsed > max_tick_budget_ms`. That mechanism is **suppressible** — an
independent probe by `rpg-feature-planning` confirmed it: `audit_mode=True` alone gave identical
canonical hashes at 200 ticks (4/4), and `audit_mode=True` plus a raised budget gave 3/3 identical at
2000 ticks. This finding **survives both**. Different signature, so treat it as a different mechanism
until something ties them.

**The working hypothesis, explicitly unproven:** nondeterminism already present on the
combat/tactical path, masked on `main` because that path rarely fires, and unmasked by any change that
makes entities reach tactical evaluation more often. That would explain why *either* half reproduces it
— two independent changes rarely both introduce nondeterminism, but both plausibly increase how often
an already-nondeterministic path executes. `rpg-implementer` did **not** locate the source and did not
claim one; neither does this ticket.

## Scope

- Confirm or refute the divergence independently, with a positive control, before any fix. A
  confirm-or-refute probe is the first step, not an implementation.
- If confirmed, isolate the source. Candidate starting point, offered as a lead and not a conclusion:
  `src/engine/tactical.py`, since it is on the path both halves feed and it already hosts three
  hardcoded-destination defects (see Related).
- Record whether the mechanism is distinct from `INFRA-273` or an unrecognised face of it.
- Determine whether `main` is genuinely clean or merely masked. "Main never diverges" is measured over
  the runs performed, which is not the same as proven deterministic.

## Out of Scope

- `INFRA-273` / the wall-clock throttle and its `audit_mode` remedy. Documented, deliberately deferred,
  and **not** this.
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`, whose root cause *is* the throttle family.
  Do not merge the two; conflating them would re-park this under a decision that does not cover it.
- Fixing `tactical.py`'s hardcoded `(0,0)` destinations — `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`
  owns that. Adjacent code, different defect.
- Deciding whether PR #291 lands. That is its own user's call.

## Acceptance Criteria

1. The divergence is independently reproduced or refuted, with a **positive control** proving the
   comparison instrument detects a difference when one exists (e.g. two different seeds). An
   uncontrolled "identical" result is not evidence.
2. Canonical state hashes are compared via `src/engine/checkpoint.py::CanonicalStateHasher.get_hash()`,
   not the lightweight `src/replay/fingerprint.py::StateFingerprinter` (whose own docstring defers to
   the canonical hasher).
3. Every run sets `audit_mode=True` and a raised `max_tick_budget_ms`, so a result cannot be an
   `INFRA-273` artifact. State the `dropped_work_total` and confirm it is 0.
4. The first divergent tick is identified, and the diverging field named, not just "the hashes differ".
5. A verdict is recorded on whether this is distinct from `INFRA-273`.
6. If confirmed, the row 7 classification is stated: a determinism break on a path that runs in
   ordinary corpus play is a **hard bug** (783 opportunity attacks on `main` is not a dormant path), so
   it is not parked as feature work.

## Blocks

- **`TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` AC-1** prescribes measuring the three
  retreat branches' firing rates with `audit_mode=True` and a raised budget — **the exact protocol this
  finding calls into question on the tactical path.** That measurement cannot be trusted until this is
  resolved, so this ticket should be settled first or that one's AC-1 needs a different instrument.
- Any future per-tick counter measurement on the combat/tactical path, for the same reason.

## Related Tickets

- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (inprogress, PR #291) — where
  this was found; its Implementation Notes are the citation of record. Its **AC6 (determinism holds) is
  contradicted, not merely undemonstrated**, which is why `rpg-feature-planning` recommended holding
  that PR.
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (active) — the throttle-family ticket.
  Cross-referenced **to disambiguate**, not to merge.
- `TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE` (done) — established the `audit_mode`
  remedy that this finding defeats.
- `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` (open) — adjacent code, and blocked by
  this.
- `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` (done) — nearest in spirit
  (combat event volume ceasing to reproduce) but cross-commit measurement staleness, **not** same-commit
  run-to-run divergence. Named so the two are not confused.

## Related Docs

- `docs/engine/deterministic_execution.md` — Extension Rule 5 mandates `audit_mode` for
  determinism-verifying runs; this finding shows that is necessary but **not sufficient**
- `docs/audits/D06_longrun_health.md` §F6-F7 — the throttle family this is **not**
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-273`
- `docs/engine/project_lawbook_m10.md:24-26` — Determinism is the **top** pillar under trade-off, which
  is why this is P1 rather than an annoyance

## Related Stored Artifacts

- None of its own. The evidence is in PR #291's ticket, deliberately not copied here to avoid two
  diverging records of one measurement.

## Related Code Areas

- `src/engine/tactical.py` — the suspected path, offered as a lead
- `src/engine/kernel.py:612-620` — the `INFRA-273` throttle, for contrast
- `src/engine/governor.py:78-105` — `tick_compute_ms` → `RuntimeMode`, a second wall-clock path that
  `audit_mode` does **not** disable and a raised budget defuses; worth eliminating explicitly
- `src/engine/checkpoint.py::CanonicalStateHasher` — the correct comparison instrument

## Assumptions / Open Questions

- Whether `main` is genuinely deterministic on this path or merely masked is **unverified**.
- Whether the governor's `RuntimeMode` transitions are implicated is unverified; a raised budget defuses
  them, and `rpg-implementer`'s runs had one, which weakens but does not eliminate that candidate.
- Whether this is reachable without either half of PR #291's change — i.e. whether any existing corpus
  scenario already triggers it — is unknown and would determine how urgent it is.

## Implementation Notes

**Status: re-measured and partly isolated by `rpg-implementer` on 2026-10-05; NOT closed.** Stopped at the
planner's guardrail (the upstream cause is unproven and the candidate fix is on the contested surface), with the
evidence below. Measured on branch `worktree-lane-a-tactical-path-batch` (`origin/main` `054b49146` plus the
retreat, entity-target and bravery-guard tickets); **not run on bare `origin/main`**, so "is main clean or
masked" (Scope, last bullet) is still open. None of the probes is in the repo (scratch scripts:
`det_probe.py`, `early_trials.py`).

**1. Reproduced, with a positive control (AC1-AC3).** `frontier_living_world`, 2000 ticks, `audit_mode=True`,
`max_tick_budget_ms=1e9`, `LocalSequentialExecutor`, canonical state hash (`CanonicalStateHasher.get_hash`)
every tick, `total_dropped_work == 0` and governor `RuntimeMode` 0 on every tick of every run. Four identical
seed-42 runs in four fresh processes: final hashes `cc17cd69…` (runs 1, 2, 4) and `a76fb7bf…` (run 3). Run 2
also differs from run 1 at tick 512 (entity 9) and **re-converges**, so a divergence can heal. Positive control:
seed 43 differs from every seed-42 run at tick 1 in every entity.

**2. First divergent tick and fields (AC4).** Run 3 vs run 1: tick 5 (index 4), entities 16 and 36. Differing
fields: `navigation.target`, `strategic.current_project_id`, `strategic.current_objective_id` and a whole
`strategic.projects[...]` entry. In one trace, entity 16 starts `project_stabilize_bandit_road_t4` and entity 36
`proj_guild_4` at tick 4; in the other neither does. Short 8-tick runs reproduce exactly this split and fall into
the same two traces.

**3. The proximate mechanism, measured.** At the first differing `StrategicWorkQueue.build` call (tick 4) the
budget (10), sweep interval (5), `dirty is None` and `force_full_scan` are identical. The candidate lists differ
(trace A has 16 and 36, trace B has 31). The only per-entity scheduling input that differs is **entity 16's
membership in `dirty.strategic_entities`: present in A, absent in B.** Entity 16 therefore sits in tier 6 in A
and in the tier-7 background sweep in B; the sweep's rotation then selects different entities under the budget.
The dirty set is not part of the canonical state hash, which is why hashes match until the project is created
at tick 5.

**4. Upstream cause: NOT established. A strong, specific lead.** `DirtySetBuilder.mark_from_update`
(`src/core/dirty.py:142-146`) de-duplicates entity updates with `id(e_upd)` in `_processed_upd_ids`. `id()` is
unique only among live objects, so an update allocated at a recycled address is silently skipped and its entity
never marked dirty. A shadow check (same `id`, different update content) found about **56 such skipped updates
per 8-tick trial in every trial, from tick 0**, with run-to-run variation (53 to 60), which is what an
allocation-dependent mechanism looks like. **Not shown:** that entity 16's update was among the skipped ones in a
diverging run; the diverging trace did not reproduce in the last two probe runs (it appeared in three of five
instrumented experiments, and in every experiment that showed it the switch came after trial 7, which is
unexplained). A second `id()`-keyed cache, `get_frozen` in `src/engine/executor.py:257` (frozen world views keyed
on `id(state.regions)` and similar), has the same reuse hazard and was **not tested**.

**5. Verdict on `INFRA-273` (AC5): distinct.** `audit_mode` was on, `dropped_work_total` was 0 and the governor
stayed in mode 0 on every tick, so neither the mid-tick throttle nor a mode transition can be involved; the
measured mechanism contains no wall-clock read. This contradicts `docs/engine/deterministic_execution.md`'s
statement that `audit_mode` is "the current way to get a deterministic run".

**6. Classification (AC6).** A determinism break on a path that runs in ordinary corpus play: a **hard bug**
(row 7), not parked.

**7. Ticket assumptions checked.** `tactical.py` is **not** the source: the divergence appears in strategic
scheduling at tick 4 before any tactical decision differs. `kernel.py:612-620` and `governor.py:78-105` are not
implicated on this evidence (nothing dropped, mode 0), so the exclusive hold on them was not used.

**Not done:** a fix (the candidate, `src/core/dirty.py`, is contested-surface and needs the planner); proof of
the entity-16 link; the `get_frozen` hazard; bare-`main` comparison; why the switch to the second trace came
after trial 7 in three experiments and never in two.

## Test Summary

No code changed; no test added. Evidence is probe output only (not in the repo).

## Files Changed

None (ticket only).

## Completion Summary

_Open. Re-measured, positively controlled, first divergent tick and fields named, verdict recorded; the
upstream cause is a strong lead (`id()`-keyed dedup in `src/core/dirty.py`), not a proven cause. Left in
`inprogress/` for the planner to split into a fix ticket._
