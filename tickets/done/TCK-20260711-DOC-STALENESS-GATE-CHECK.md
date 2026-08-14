---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260711-DOC-STALENESS-GATE-CHECK
phase: done
date: 2026-07-11
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260711-DOC-STALENESS-GATE-CHECK

## Title
Static gate check: flag behavior-changing diffs with no docs/ touch

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
This week's agent-monitoring retro (`agent-monitoring/retro/RETRO-2026-W28.md`) found that
`done-checker` (the Verify phase agent) failed its first attempt on 22 of 61 calls (36%) this week,
every single failure tagged `reason_code=dod_condition_failed`. The retro's Notes section (item 1
and item 3) traces this to one recurring root cause: a behavior-changing Implement phase not
updating a `docs/` file describing the changed behavior, caught only reactively by done-checker's
Verify pass. This happened twice in the immediately preceding session alone
(`TCK-20260711-EPIC-SCOPE-ORPHAN-FIX`, `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`), both needing a
second Verify pass after a manual `docs/` fix. It was always caught and fixed before Finalize
(never silently shipped), but it is expensive.

The retro's own recommended action (Notes item 3): add a static check mirroring
`tools/gate_checks/workflow_meta_conformance.py`'s shape — a standalone function with a
`MARKER:`-prefixed CLI, not wired into the pipeline — but for "behavior changed with no docs
touch" instead of "declared phase with no matching event."

This ticket scopes and ships that check only. It does not wire it into any workflow.

## Scope
- Add a new module, `tools/gate_checks/doc_staleness_check.py`, exporting a single aggregate
  check function (mirrors `workflow_meta_conformance.py`'s one-function, list-of-dicts shape,
  not `parity_updater_static.py`'s two-call split — there is no agent-prompt injection point
  this check needs to feed).
- The function takes a `files_changed` list and a `behavior_changed` boolean (the same two
  fields `implement-ticket.js` already collects from the Implement phase's return schema — see
  `.claude/workflows/implement-ticket.js` lines ~547-548, `580`) and flags `FAIL` when:
  - `behavior_changed` is `true`, AND
  - at least one path in `files_changed` starts with `src/` or matches `.claude/workflows/*.js`,
    AND
  - no path in `files_changed` starts with `docs/`.
  Otherwise returns `PASS` (mirrors `workflow_meta_conformance.py`'s status vocabulary).
- Return shape: a list of dicts (or equivalent `(status, evidence)` result) consistent with the
  existing `tools/gate_checks/*.py` precedent — at minimum `status` (`PASS`/`FAIL`) and
  `evidence` (a short string explaining which files triggered the flag).
- Include a `MARKER:`-prefixed JSON CLI entrypoint (`if __name__ == "__main__":` block) matching
  the contract every other `gate_checks` script uses.
- Add tests under `tests/tools/test_doc_staleness_check.py` covering at minimum:
  - A false-positive guard: a ticket that changed behavior but genuinely needed no docs update
    (e.g. a pure test-only change, or a `src/` change with `behavior_changed=false`) — must
    return `PASS`.
  - A true-positive guard: reproducing the actual `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX` /
    `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK` incident shape (a `src/` and/or
    `.claude/workflows/*.js` change, `behavior_changed=true`, zero `docs/` paths in
    `files_changed`) — must return `FAIL`.

## Out of Scope
- Wiring this check into `implement-ticket.js`'s pipeline (Parity or pre-Verify) or into
  `done_checker_static.py`'s own DoD checklist — a separate future ticket decides where/whether
  to call it, exactly as `workflow_meta_conformance.py` itself remains unwired today.
- Any change to done-checker's own agent prompt or its DoD checklist wording.
- Retroactively re-checking already-closed tickets for this pattern.
- Any change to `implement-ticket.js`'s `behavior_changed` / `files_changed` return schema
  itself (it already exists and is reused as-is).
- Adding a `docs/parity_ledger/infrastructure.yaml` entry (see Assumptions — this follows the
  no-wiring, no-ledger-entry precedent `workflow_meta_conformance.py` itself set; to be
  confirmed, not decided, during this ticket's own Parity phase).

## Acceptance Criteria
- `tools/gate_checks/doc_staleness_check.py` exists, exporting an aggregate check function with
  the `files_changed` + `behavior_changed` -> list-of-dicts (or `(status, evidence)`) shape
  described in Scope.
- Running the module's CLI entrypoint directly prints a single `MARKER:`-prefixed JSON line.
- `tests/tools/test_doc_staleness_check.py` exists and passes, with at least one false-positive
  guard test (pure test-only / no-behavior-change diff returns `PASS`) and at least one
  true-positive guard test reproducing the `EPIC-SCOPE-ORPHAN-FIX`/`EPIC-STALENESS-DEDUPE-CHECK`
  incident shape (returns `FAIL`).
- The check is NOT called from `.claude/workflows/implement-ticket.js` or
  `tools/gate_checks/done_checker_static.py` — confirmed by grep/diff review at Verify.
- `pytest tests/tools/test_doc_staleness_check.py` passes locally.

## Related Tickets
- `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` (done) — the precedent shape this ticket
  mirrors (standalone `tools/gate_checks/` static check, `MARKER:`-prefixed CLI, deliberately
  not wired into the pipeline).
- `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX` (done) — one of the two incidents this check is meant to
  catch going forward (behavior-changing Implement phase, no `docs/` update, caught reactively by
  done-checker's first Verify pass).
- `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK` (done) — the second incident of the identical
  failure shape, same session.
- `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` (done) — a DIFFERENT, narrower kind of doc
  staleness (`docs/ai/workflows.md`'s phase-count lists drifting from the actual `.claude/workflows/*.js`
  file contents). Confirmed NOT a duplicate of this ticket: that ticket repaired one specific
  stale doc's phase-count lists; this ticket is a general "behavior changed, no docs/ path
  touched at all" diff-level check, independent of any specific doc's content.
- `TCK-20260705-GATE-DET-DONE-CHECKER` (done) — established `done_checker_static.py`'s existing
  DoD static-check shape this new module sits adjacent to (same `tools/gate_checks/` directory,
  same repo, different concern).

## Related Docs
- None in `docs/mechanics/` or `docs/engine/` apply — confirmed by scan; this is agent-
  infrastructure tooling (a static repo-diff check), not a simulation-mechanics or engine-
  contract change.
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` — background context
  for the "near-horizon static check" pattern this ticket continues (same pattern
  `workflow_meta_conformance.py` and `tools/agent-monitoring/epic_scope_orphan_check.py` used).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK/` — the precedent shape
  (investigation.md, plan.md, test_plan.md) to mirror for module structure and CLI contract.
- `stored_artifacts/TCK-20260711-EPIC-SCOPE-ORPHAN-FIX/` — one of the two concrete incidents
  this check targets.
- `stored_artifacts/TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK/` — the second concrete incident.

## Related Code Areas
- `tools/gate_checks/workflow_meta_conformance.py` — precedent shape to mirror (function
  signature style, `MARKER:`-prefixed CLI, non-wiring stance, docstring convention).
- `tools/gate_checks/done_checker_static.py` — existing adjacent DoD static-check module; new
  module lives alongside it in the same directory but is a separate, standalone concern.
- `.claude/workflows/implement-ticket.js` — source of the `behavior_changed` (line ~548) and
  `files_changed` (line ~547) fields the Implement phase already returns; also where a future
  wiring call site would go (Parity, ~line 779-809, or a new pre-Verify step) — reading only, no
  edit in this hotfix.
- `tools/gate_checks/parity_updater_static.py` — reference for the two-call split shape this
  ticket's module deliberately does NOT need (no agent-prompt injection point to feed).

## Assumptions / Open Questions
- Assumes no `docs/parity_ledger/infrastructure.yaml` entry is needed for this hotfix, following
  `workflow_meta_conformance.py`'s own precedent (that ticket also shipped an unwired static
  check with no ledger entry). This differs from `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX`, which DID
  get `INFRA-265` because it had a real orchestrator wiring call site into
  `implement-ticket.js` — this ticket has no such call site. To be confirmed (not decided here)
  during this ticket's own Parity phase.
- Assumes `layer: ai` is correct (agent-orchestration tooling, matching this repo's convention
  that `layer:ai` means the Claude agent system, not gameplay AI/cognition).
- Assumes the exact match rule for `.claude/workflows/*.js` should be a glob/suffix check
  (`.endswith('.js')` under that directory prefix), not a regex requiring the literal `*` — to be
  confirmed by whoever implements, consistent with how `workflow_meta_conformance.py` resolves
  workflow source paths.
- If a future ticket wires this check in and it turns out the false-positive rate is high (e.g.
  many behavior changes legitimately need no doc update), that would invalidate the "flag every
  such diff" scope as currently written — but resolving that tradeoff is explicitly out of scope
  for this hotfix, which ships the check unwired.

## Implementation Notes
Added `tools/gate_checks/doc_staleness_check.py`, exporting a single aggregate function
`check_doc_staleness(files_changed, behavior_changed) -> List[dict]`, mirroring
`workflow_meta_conformance.py`'s one-function, list-of-dicts shape. FAIL fires only when all
three hold: `behavior_changed` is `True`, at least one path in `files_changed` starts with
`src/` or matches `.claude/workflows/*.js` (prefix + `.endswith('.js')` check, per the
Assumptions section's glob/suffix resolution), and zero paths in `files_changed` start with
`docs/`. Otherwise `PASS`. Each result dict carries `status` and `evidence` (lists the flagged
paths on FAIL, or a short counts summary on PASS).

Included a `MARKER:`-prefixed JSON CLI entrypoint matching `workflow_meta_conformance.py`'s
contract: `sys.argv[1]` is the `behavior_changed` flag (`"true"`/`"false"`, case-insensitive),
and all remaining argv elements are `files_changed`.

Added `tests/tools/test_doc_staleness_check.py` (10 tests, all passing): false-positive guards
(behavior_changed=False with src/ paths; test-only change with behavior_changed=True), a
true-positive guard reproducing the EPIC-SCOPE-ORPHAN-FIX/EPIC-STALENESS-DEDUPE-CHECK incident
shape for both `src/` and `.claude/workflows/*.js` paths, a happy-path guard confirming the same
true-positive shape PASSes once a `docs/` path is present, plus edge cases (empty
`files_changed`, non-`.js` file under `.claude/workflows/`) and two CLI subprocess tests
confirming the `MARKER:` JSON contract.

Confirmed via grep: the check is not referenced anywhere in
`.claude/workflows/implement-ticket.js` or `tools/gate_checks/done_checker_static.py` — ships
unwired per scope. No `docs/parity_ledger/` entry added (per ticket's Out of Scope /
Assumptions — left for confirmation at this ticket's own Parity phase). No deviations from the
ticket's Scope.

## Test Summary
`pytest tests/tools/test_doc_staleness_check.py -q` — 10 passed, 0 failed.

## Files Changed
- `tools/gate_checks/doc_staleness_check.py` (new)
- `tests/tools/test_doc_staleness_check.py` (new)

## Completion Summary
Shipped `check_doc_staleness` as a standalone, unwired static gate check plus its test suite,
per hotfix scope. Ready for Parity/Verify/Finalize.
