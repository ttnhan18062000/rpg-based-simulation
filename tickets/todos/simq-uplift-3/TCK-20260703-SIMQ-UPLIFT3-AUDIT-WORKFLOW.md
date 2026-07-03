---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW
phase: open
date: 2026-07-03
tags: [simulation_quality, workflow, tooling, audit, process]
---

# TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW

## Title
Formalize a repeatable "SimQ full audit" workflow that can be triggered consistently across sessions

## Status
OPEN

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
(to be filled during implementation)

## Test Summary
(to be filled during implementation — a successful dry-run against current state is the primary
verification)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
