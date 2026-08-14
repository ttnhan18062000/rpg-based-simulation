---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW
phase: done
date: 2026-07-03
tags: [simulation-quality, workflow, tooling, audit, process]
---

# TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW

## Title
Formalize a repeatable "SimQ full audit" workflow that can be triggered consistently across sessions

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Across SimQ Uplift Batches 1-3, the same manual sequence has been repeated by hand each time:
re-run the calibration corpus, diff grade movement against `grade_anchors.json`, update
`docs/simulation_quality/eval_matrix_results.md`, update `docs/audits/D20_simq_integration.md`'s
grade distribution table and open-follow-up list, run `make evaluate --dry-run`, and check parity
ledger entries for staleness. This process depends entirely on whoever is doing the work
remembering every step and every file to touch — there is no single command or documented runbook
that guarantees the same steps happen the same way in a future session.

Per 2026-07-03 user direction: build this into a proper, repeatable workflow (in the same spirit as
this repo's existing `.claude/workflows/implement-ticket.js` / `implement-epic.js` pattern, or at
minimum a documented runbook + a `make` target that chains the mechanical steps) so a future agent
session — or a future engineer — can trigger "audit SimQ state" and get the same complete,
consistent result without re-deriving the process from scratch or missing a step.

## Scope
1. Enumerate every step performed manually across the SimQ Uplift Batch 1-3 doc-sync passes (this
   session's own `git log` on `simulation_quality` branch is the primary source): which
   calibration commands run, which files get updated (`grade_anchors.json`,
   `eval_matrix_results.md`, `D20_simq_integration.md`, `event_type_coverage.md`, relevant parity
   ledger files), and in what order.
2. Design the workflow: decide whether this should be (a) a new `.claude/workflows/simq-audit.js`
   following the existing `implement-ticket.js`/`implement-epic.js` JS-phase pattern (agent-driven,
   consistent with how this repo already automates multi-step ticket work), (b) a `make
   simq-full-audit` target that scripts the mechanical parts (calibration runs, diffing) and
   leaves doc-writing to a human/agent, or (c) both — a make target for the mechanical parts, a
   documented runbook for the judgment-requiring parts (which findings go in which doc section).
3. Implement the chosen design.
4. Dry-run it against the current (post-Batch-3) state to confirm it produces the same kind of
   output this session produced by hand, without missing a step.
5. Document the workflow's usage in an appropriate `docs/` location (likely alongside
   `docs/simulation_quality/quality_scoring_contract.md` or a new `docs/simulation_quality/audit_workflow.md`).

## Out of Scope
- Re-running the audit itself as part of this ticket (that's what the workflow enables future
  sessions to do — this ticket builds the tool, doesn't necessarily execute a full audit pass with
  it, though a dry-run/smoke-test is required per Scope item 4)
- Changing any SimQ scoring logic, calibration harness internals, or grade thresholds
- Building a fully autonomous/unattended audit (some steps — deciding whether a grade movement is
  expected vs. a regression, writing narrative doc updates — plausibly still need human/agent
  judgment; this ticket should make the mechanical parts repeatable, not eliminate judgment calls)

## Acceptance Criteria
- [ ] Every manual step from the Batch 1-3 doc-sync process is enumerated with its exact commands/
      files
- [ ] A design decision is made and documented for how the workflow is implemented (new `.claude/workflows/`
      file, `make` target, or both) with reasoning for the choice
- [ ] The workflow is implemented and dry-run successfully against current repo state
- [ ] Usage is documented in a discoverable `docs/` location
- [ ] A future session invoking this workflow does NOT need to re-read this ticket, the SimQ
      uplift batch tickets, or this session's transcript to know what steps to run

## Related Tickets
- TCK-20260702-SIMQ-EVAL-MATRIX (done) — established part of the corpus-refresh pattern this
  workflow should encode
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — this workflow is most useful once run against the
  expanded corpus that ticket produces
- TCK-20260702-SIMQ-UPLIFT2-FACTION, -INFORMATION, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER —
  source of the manual process being formalized

## Related Docs
- `.claude/workflows/implement-ticket.js`, `.claude/workflows/implement-epic.js` — existing
  workflow pattern to potentially follow
- `docs/audits/D20_simq_integration.md` — one of the docs the workflow should keep in sync
- `docs/simulation_quality/eval_matrix_results.md`, `docs/simulation_quality/event_type_coverage.md`
- `docs/simulation_quality/quality_scoring_contract.md`

## Related Stored Artifacts
- None yet — this is new process/tooling work

## Related Code Areas
- `tools/calibrate_simq.py`, `tools/evaluate_simq.py`
- `.claude/workflows/` — existing workflow definitions, for pattern reference
- `Makefile` — existing `evaluate`/`evaluate-full` targets, for pattern reference

## Assumptions / Open Questions
- UQ-1: Should this be a Claude Code workflow (agent-orchestrated, like `implement-ticket.js`) or a
  plain shell/Python script invoked via `make`? The former fits this repo's existing pattern for
  multi-step agent work; the latter is simpler and doesn't require an agent session to run. This is
  a real design decision the ticket owner should make during planning, not default to without
  consideration — flag for architecture review either way.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW/plan.md` (APPROVED,
one fix-and-reverify cycle), steps 1-7 in order:

1. `tools/simq_audit_gaps.py` — read-only, always-exit-0 anchor-coverage scanner (imports
   `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` from `tests.simulation_quality.test_grade_regression`, diffs
   against `grade_anchors.json` keys) + parity-ledger candidate scan (entry-level match on
   `text`/`divergence_note`/`v2_evidence` for `simq`/`calibrat`/`qualityhub`/pillar names). No write
   paths anywhere in the file.
2. `tests/unit/tools/test_simq_audit_gaps.py` (+ `tests/unit/tools/__init__.py`, new package) — 4 tests:
   synthetic uncovered-key detection, real-fixture zero-false-positive regression guard, real-ledger
   candidate scan finding the four known IDs (`SOC-237`, `SOC-238`, `INFRA-251`, `INFRA-258`), and
   exit-code-always-0 with an injected uncovered key.
3. `Makefile` — `simq-full-audit` / `-full` / `-slow` targets (added to `.PHONY`), using the corrected
   shell logic: no leading dash on the pytest line, `test_status=$$?` captured explicitly, final `exit
   $$test_status` so a regression-test failure still fails the target even though
   `simq_audit_gaps.py` always exits 0.
4. `.claude/workflows/simq-audit.js` (new) — 7-phase workflow (Recalibrate → Classify Drift → Update
   Anchors → Sync Docs → Parity Check → Verify → Report) mirroring `implement-ticket.js`'s
   `phase()`/`agent()`/`pushEvent()`/`writeMonitoring()` conventions exactly. Recalibrate is a
   schema-less `agent()` call (no `Step 0b` — `runId` doesn't exist yet, same reason
   `implement-ticket.js`'s Scope phase has none). Update Anchors is schema-validated
   (`UPDATE_ANCHORS_SCHEMA` with `targeted_test_passed: boolean`) since the orchestrator branches on
   it. Report is a deterministic JS `if` on `classifyResult.verdict` — `no_regression` returns
   `DONE_NO_TICKET` with a suggested chore-commit message and touches no ticket; `regression`/
   `needs_da_decision` spawns one ticket via `ticket-scoper` (same `TICKET_SCHEMA` shape as
   `implement-ticket.js`'s Scope phase) pre-seeded from Classify Drift's non-`EXPECTED_DRIFT` items,
   returning `NEEDS_TICKET` with a `/implement-ticket` hand-off instruction. `writeMonitoring` uses
   `workflow: "simq-audit"` and a synthetic `run_id` (`SIMQ-AUDIT-<timestamp>`), called at every exit.
5. `.claude/skills/simq-audit/SKILL.md` (new) — mirrors `implement-ticket/SKILL.md`'s structure
   (Usage, Input, Action translation table, Pipeline, Notes).
6. Smoke test (Step 6): ran `make simq-full-audit` and the new pytest file against current repo state
   only — did not invoke the workflow's agent phases (Classify Drift onward), per explicit ticket
   scope. Confirmed the baseline the plan predicted: 40 real anchor keys, 29 `FAST_ANCHOR_KEYS`, 11
   `SLOW_ANCHOR_KEYS`, 0 uncovered.
7. `docs/simulation_quality/audit_workflow.md` (new) — usage doc: what the workflow replaces, the
   7-phase pipeline, the governance decision (no_regression → chore commit, no ticket;
   regression/needs_da_decision → ticket hand-off), usage examples, mechanical-only path, and a
   "Do not" list.

No changes to `src/simulation_quality/*` scoring logic, `calibrate_simq.py`/`evaluate_simq.py`
internals, or grade thresholds. The workflow's agent phases (Classify Drift onward) were not executed
as part of this ticket — only designed, code-reviewed, and syntax-checked (`node --check`).

`plan.md`'s Deviations section documents three minor implementation-time notes (parity-candidate list
breadth vs. the plan's "short and useful" framing — same approved design, not changed; the exit-code
test calling `main()` directly per the plan's own fallback clause; confirming the new
`tests/unit/tools/` package needed creating).

## Test Summary
- `python3 -m pytest tests/unit/tools/test_simq_audit_gaps.py -q` → 4 passed.
- `make simq-full-audit` → exit 0. Diff step (`evaluate_simq.py --dry-run`) ran against existing
  `data/calibration/` (one `MISSING` scenario, `urban_political_seed42_200t` — non-fatal, pre-existing,
  unrelated to this ticket). Regression tests: 29 passed, 1 skipped, 11 deselected. Coverage scan: 0
  uncovered anchor keys of 40; parity-candidate scan surfaced entries across all 9 ledger files
  including the four expected IDs.
- `node --check .claude/workflows/simq-audit.js` and `node --check .claude/workflows/implement-ticket.js`
  → both exit 0 (syntax-valid ES module).
- Per ticket scope, the workflow's agent-orchestrated phases (Classify Drift → Report) were not
  executed — first real exercise happens the next time a SimQ batch needs auditing.

## Files Changed
- `tools/simq_audit_gaps.py` (new)
- `tests/unit/tools/__init__.py` (new)
- `tests/unit/tools/test_simq_audit_gaps.py` (new)
- `Makefile` (added `simq-full-audit`, `simq-full-audit-full`, `simq-full-audit-slow` targets + `.PHONY` update)
- `.claude/workflows/simq-audit.js` (new)
- `.claude/skills/simq-audit/SKILL.md` (new)
- `docs/simulation_quality/audit_workflow.md` (new)
- `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW/plan.md` (Deviations section added)

## Completion Summary
Built a repeatable, two-tier SimQ audit system: `tools/simq_audit_gaps.py` (anchor-coverage +
parity-ledger candidate scanner, informational, always exits 0) and `make simq-full-audit`/`-full`/
`-slow` Makefile targets for the mechanical steps (calibration diff, regression tests, coverage
scan) with a correctly-propagating exit code, plus a full 7-phase `.claude/workflows/simq-audit.js`
+ `.claude/skills/simq-audit/SKILL.md` agent-orchestrated workflow mirroring `implement-ticket.js`'s
conventions, with a governance-encoded Report phase (no_regression → lightweight chore commit, no
ticket; regression/needs_da_decision → ticket hand-off via the existing ticket-scoper). Went
through 2 architecture-review cycles (3 violations found and fixed: an unattested bare-Bash
Recalibrate pattern, a missing schema on Update Anchors, and a Makefile leading-dash bug that would
have silently defeated the pytest gate's exit code). Documented in
`docs/simulation_quality/audit_workflow.md`. Smoke-tested successfully against current repo state
(29 tests passing, 0 uncovered anchor keys of 40) without invoking the workflow's own agent phases.
