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

OPEN

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

_To be completed by the implementer. Start with a confirm-or-refute probe, not a fix._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
