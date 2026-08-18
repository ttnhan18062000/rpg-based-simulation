---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE
phase: open
date: 2026-08-18
tags: [engine, determinism, bug, debugging, root-cause, testing]
---

# TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE

## Title
Root-cause and fix `test_long_run_stability`'s real hash-parity divergence (missing `audit_mode`
vs. the wall-clock tick-budget watchdog); rule out the spawn-collision RNG fix; precisely localize
(but do not guess-fix) a second, deeper divergence in `test_long_run_determinism_parity`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Two independent hash-parity tests failed on the "Slow regression" CI job's first-ever completed
run: `tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity` and
`tests/integration/world/test_long_run_stability.py::test_long_run_stability`, both asserting
`hash1 == hash2` across two same-seed runs and getting different hashes. A third test in the same
cert file, `test_long_run_pure_stability`, failed separately with a plain `TimeoutError`.

This session's own `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (commit
`0ecd2a83`, changed `WorldCompiler.compile()`'s entity-placement RNG consumption) was the prime
suspect given it directly touches deterministic RNG consumption during world compilation. **Ruled
out by real isolated-worktree bisection** (see investigation.md): the exact same divergence
reproduces identically on `db6335ad`, the commit immediately before the spawn-collision fix
landed. This is a pre-existing bug, unrelated to today's session's other work.

Root-caused instead to `src/engine/kernel.py`'s wall-clock tick-budget watchdog / mid-tick
emergency throttle (`time.perf_counter_ns()`-based work-shedding under simulated load) — a
**previously documented, already-tracked finding** (`docs/audits/D06_longrun_health.md` §F6,
`docs/parity_ledger/infrastructure.yaml` id `INFRA-273`, both discovered 2026-07-09,
status "documented, not fixed — intentional engine behavior"). The established, already-used
remedy for STRICT hash-equality tests (as distinct from F6's own tolerance-banded SimQ-anchor
remedy) is `audit_mode=True`, which the engine's own contract doc mandates
("`audit_mode` should be enabled in all CI runs that verify the determinism guarantee",
`docs/engine/deterministic_execution.md` Extension Rule 5) and which sibling tests/harnesses
already use (`src/certification/harness.py`, `tests/unit/kernel/test_replay_determinism.py`,
`LongRunStabilityHarness.verify_determinism_parity()` itself). `test_long_run_stability.py` simply
never adopted this already-established pattern — fixed here, verified with 3 independent
bit-identical repeated runs.

`test_long_run_determinism_parity` already uses `audit_mode=True` (via
`verify_determinism_parity()`) yet STILL diverges — a second, deeper, previously undocumented
mechanism, precisely localized to tick 30 of the `metropolis` scenario (a genuine
combat-engage-vs-combat-retreat strategic-goal divergence, not cosmetic reordering) but not traced
to the exact non-deterministic instruction within this ticket's time budget. Reported honestly,
not guess-fixed, per the parent task's explicit instruction; flagged as a required follow-up
(recorded as new finding F7 in `docs/audits/D06_longrun_health.md`).

`test_long_run_pure_stability`'s `TimeoutError` ruled unrelated to either mechanism (its code path
has no hash/replay/retry logic at all — single straight tick loop) — independently corroborated
by an already-closed sibling ticket from this same session
(`TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION`) that read-only-investigated the same
question and reached the same conclusion.

## Scope
- Root-cause all 3 CI failures with real evidence (bisection, direct reproduction, per-tick hash
  diffing) — not assumption.
- Fix `tests/integration/world/test_long_run_stability.py::test_long_run_stability`'s real
  non-determinism by adding the established `audit_mode=True` flag.
- Document the newly-precisely-localized second mechanism (Mechanism B) as a new finding in
  `docs/audits/D06_longrun_health.md` (F7), so a follow-up ticket does not have to rediscover it.
- Rule the TimeoutError in/out with evidence, cross-validated against the sibling ticket's own
  independent finding.

## Out of Scope
- `src/engine/kernel.py`'s watchdog/throttle/`ResourceGovernor` logic — documented, intentional,
  corpus-wide engine behavior (F6/INFRA-273); not touched, matching that finding's own explicit
  scope guard.
- Fixing Mechanism B (`test_long_run_determinism_parity`'s audit_mode-immune divergence) — reported
  and localized to tick 30 / specific entities / specific fields, but the exact non-deterministic
  instruction was not traced within this ticket's time budget. Guessing at a fix for a P0/P1
  architectural determinism bug without full certainty would violate CLAUDE.md's "Do not guess
  when uncertainty affects behavior or architecture." Left failing, `test_long_run_determinism_parity`
  and its `skipif(CI=="true")` guard untouched.
- `test_long_run_pure_stability`'s `TimeoutError` / `execute_run()`'s tick-budget calibration —
  ruled a separate, unrelated hardware/resource-budget issue; not this ticket's Related Code Areas.
  Its `skipif` also untouched.
- `src/perf/scenarios.py::build_metropolis_state()`'s entity-position-overlap bug (entities spaced
  100/200 apart in builder order land on identical tiles) — a real, separate, pre-existing,
  fully-deterministic defect found while tracing Mechanism B, likely a contributing trigger but not
  itself the non-determinism. Flagged in `docs/audits/D06_longrun_health.md`'s new F7 entry for a
  future ticket; not fixed here (would change the `metropolis` scenario's behavior for every other
  test that uses it, out of this ticket's blast radius).
- `tests/certification/test_cert_long_run_stability.py::test_long_run_runtime_stability` — not
  among the reported CI failures; not modified.

## Acceptance Criteria
- [x] Root cause of `test_long_run_stability`'s divergence identified with file:line evidence
      (`src/engine/kernel.py` lines ~431-453, ~585-612) and confirmed by direct reproduction.
- [x] Spawn-collision RNG fix (`0ecd2a83`) ruled out via real isolated-worktree bisection against
      the immediately-prior commit (`db6335ad`), not assumed.
- [x] `test_long_run_stability` fixed (`audit_mode=True` added) and verified deterministic across
      at least 3 independent repeated runs producing bit-identical hashes.
- [x] `test_long_run_determinism_parity`'s continuing divergence (despite already using
      `audit_mode=True`) investigated and precisely localized (first-diverging-tick + field-level
      diff), honestly reported as unresolved rather than guess-fixed.
- [x] `test_long_run_pure_stability`'s `TimeoutError` classified with evidence (not the same root
      cause), cross-validated against the independent sibling ticket's own finding.
- [x] No test assertion edited to force a pass — only `Kernel(...)`'s `flags` argument changed.
- [x] `docs/audits/D06_longrun_health.md` updated with the new F7 finding for traceability.
- [x] `data/runs/*`, `reports/release_proof/*` cleaned; `agent-monitoring/` staged; working log
      updated; frontmatter valid.

## Related Tickets
`tickets/done/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE.md` (ruled out as
cause, via bisection), `tickets/done/TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION.md`
(sibling ticket from this session; independently corroborates the TimeoutError ruling and
explicitly reserved these 2 files for this ticket), `tickets/done/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE.md`
(originated F6), `tickets/done/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY.md` and
`tickets/done/TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP.md` (F6 precedent extensions).
**Follow-up needed** (not created here): a new ticket to trace Mechanism B to its exact
non-deterministic instruction, starting from `docs/audits/D06_longrun_health.md`'s new F7 entry.

## Related Docs
`docs/engine/deterministic_execution.md` (determinism contract; Extension Rule 5 mandates
`audit_mode` for determinism-verification CI runs — this ticket's fix follows that rule),
`docs/audits/D06_longrun_health.md` (§F6, extended here with §F7),
`docs/parity_ledger/infrastructure.yaml` (`INFRA-273`, unmodified — already fully covers Mechanism
A; not a production behavior change here), `docs/engine/kernel.md` (§"Emergency Throttling", §"State
Hashing in Phase 7" — cited by F6 as the mechanism's own documentation).

## Related Stored Artifacts
`stored_artifacts/TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE/`

## Related Code Areas
`tests/integration/world/test_long_run_stability.py` (fixed), `src/engine/kernel.py` (read-only
reference — watchdog/throttle mechanism understood, not modified), `src/perf/long_run_harness.py`
(read-only reference — `verify_determinism_parity()`'s existing `audit_mode` usage is the fix
precedent), `docs/audits/D06_longrun_health.md` (F7 finding added).

## Assumptions / Open Questions
- Mechanism B's exact non-deterministic instruction (localized to tick 30 of the `metropolis`
  scenario, a combat-engage-vs-retreat strategic divergence) was not traced past the strategic
  state field-diff within this ticket's time budget. Working hypothesis (not proven): the
  `build_metropolis_state()` entity-position-overlap bug creates dense combat contention that
  some order-sensitive step in combat targeting or budget-constrained candidate selection resolves
  differently between runs. Left as an open question for the follow-up ticket.
- Why the `skipif(os.environ.get("CI") == "true")` guards did not prevent these tests from actually
  running on the real "Slow regression" CI job could not be conclusively determined (no direct
  access to the literal GitHub Actions execution logs) — same open question already recorded by
  the sibling ticket for its own 4 `skipif` guards. Not resolved here; both remaining `skipif`
  guards in this ticket's files (`test_long_run_determinism_parity`, `test_long_run_pure_stability`)
  are left in place since they still accurately describe real, unresolved issues.

## Implementation Notes
See `staging_artifacts/TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE/investigation.md`
for full evidence (bisection commands/output, log excerpts, per-tick hash-diff script and output,
field-level state diff). Summary:

1. Bisected via isolated `git worktree` (never touched the shared main tree) at `db6335ad` —
   identical divergence reproduces pre-spawn-collision-fix. Cause ruled out.
2. Direct reproduction on HEAD shows `src/engine/kernel.py`'s watchdog (`tick_once()` lines
   ~431-453) and mid-tick emergency throttle (`_phase_resolution()` lines ~585-612) tripping at
   different tick numbers between two same-seed runs — both gated `not self._audit_mode`. This is
   the already-documented F6/INFRA-273 finding, not a new one.
3. `docs/engine/deterministic_execution.md` Extension Rule 5 mandates `audit_mode` for
   determinism-verification runs; `test_long_run_stability.py` never adopted it. Fixed:
   `flags={"audit_mode": True}` added to both `Kernel(...)` calls in `run_sim()`.
4. Verified: 3 independent runs (2 same-process, 1 fresh-process) of the exact fixed scenario
   produce bit-identical hashes (`64d512de...`), 0 watchdog trips.
5. `test_long_run_determinism_parity` already uses `audit_mode=True` yet still diverges — isolated
   via per-tick state hashing to tick 30 exactly (tick 29 bit-identical, tick 30 diverges). Field
   diff shows a real combat_engage-vs-combat_retreat strategic decision split across multiple
   entities, plus an asymmetric `concern_low_hp`. Also found (separate, contributing, not the
   non-determinism itself): `build_metropolis_state()`'s entity-position formula causes ~35
   entity-pairs to spawn on identical tiles. Not traced to the exact non-deterministic instruction
   within budget — reported honestly per the parent task's explicit instruction, recorded as F7 in
   `docs/audits/D06_longrun_health.md` for a follow-up ticket.
6. TimeoutError (`test_long_run_pure_stability`) ruled unrelated — `execute_run()`'s `PURE` mode
   has no hash/replay/retry logic at all (single straight tick loop), cross-validated against the
   already-closed sibling ticket's independent, read-only finding.

## Test Summary
- `tests/integration/world/test_long_run_stability.py::test_long_run_stability` (real pytest
  invocation, `--resource-budget large`): PASSED post-fix; both hash values identical.
- Standalone 3x repeated-run verification of the exact fixed scenario (outside pytest, for cheap
  iteration): 3/3 bit-identical hashes, 0 watchdog trips.
- `test_long_run_determinism_parity`, `test_long_run_pure_stability`: left failing (unfixed, out
  of scope per above) — confirmed still exhibiting their pre-existing behavior, not made worse.

## Files Changed
- `tests/integration/world/test_long_run_stability.py` — added `flags={"audit_mode": True}` to
  both `Kernel(...)` constructions in `run_sim()`.
- `docs/audits/D06_longrun_health.md` — added F7 finding + Key Findings Summary row.
- `tickets/inprogress/TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE.md` — this file.
- `staging_artifacts/TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE/{investigation,plan,test_plan}.md`.

## Completion Summary
Ruled out `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` as the cause via real
isolated-worktree bisection (identical divergence reproduces on the commit before that fix
landed). Root-caused `test_long_run_stability`'s divergence to `src/engine/kernel.py`'s wall-clock
tick-budget watchdog/mid-tick emergency throttle — an already-documented, intentional engine
behavior (F6/INFRA-273, discovered 2026-07-09, explicitly not to be changed at the `kernel.py`
level). Fixed by adding the engine's own documented, already-precedented remedy for strict
hash-equality tests (`audit_mode=True`, mandated by `docs/engine/deterministic_execution.md`
Extension Rule 5), verified with 3 independent bit-identical repeated runs. Found and precisely
localized (to tick 30, specific entities, specific strategic-goal fields) a second, deeper,
previously-undocumented divergence in `test_long_run_determinism_parity` that persists even with
`audit_mode=True` — honestly reported as unresolved rather than guess-fixed, recorded as new
finding F7 in `docs/audits/D06_longrun_health.md` for a required follow-up ticket, along with a
separate contributing pre-existing bug found in `build_metropolis_state()`'s entity placement.
Ruled the `test_long_run_pure_stability` TimeoutError unrelated to either mechanism, cross-validated
against an independently-closed sibling ticket's own read-only finding from this same session.
