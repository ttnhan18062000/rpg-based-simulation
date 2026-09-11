---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-GATE-CHECK-WIRING-DECISIONS
phase: done
date: 2026-07-20
tags: [workflows, process-improvement]
---

# TCK-20260720-GATE-CHECK-WIRING-DECISIONS

## Title
Wire doc_staleness_check.py into implement-ticket.js; document explicit deferral for the other 4 unwired gate checks

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
The same 2026-07-20 agent-orchestration audit that produced the 3 sibling hotfix batches found 5
gate-check modules under `tools/gate_checks/` that are shipped, tested, and self-documented as
intentionally unwired — "a future ticket decides where/whether to call it." This ticket is that
future ticket: for each of the 5, either wire it into a real call site with evidence-based
justification, or explicitly document why it stays unwired, rather than leaving the decision
implicit. Only 1 of the 5 (`doc_staleness_check.py`) turned out to be a genuinely mechanical,
low-risk wire-in; the other 4 each have a real structural reason not to be wired as a blocking
gate in this pass, investigated and recorded below rather than wired blindly.

## Scope
- **Wired: `tools/gate_checks/doc_staleness_check.py`** into `.claude/workflows/implement-ticket.js`,
  called immediately after the Implement phase's agent call returns (where `files_changed`/
  `behavior_changed` first become available) and before Architecture-Verify. A behavior-changing
  diff touching `src/` or `.claude/workflows/*.js` with zero `docs/` path in `files_changed` now
  returns a new terminal status, `DOC_STALENESS_BLOCKED`, instead of only surfacing 6+ phases
  later as a generic `DOD_BLOCKED` at Verify. This mirrors the exact precedent already set for
  `TAGS_NOT_REGISTERED` (pulled forward from Verify's `frontmatter_valid` condition to Scope, for
  the identical "catch it here instead of 6+ phases later" reason) — including that precedent's
  shape of folding the check's outcome into the same phase's own monitoring event rather than
  emitting a second one, and using the real `implementer` agent name rather than a synthetic
  pseudo-agent name outside `vocabulary.py`'s controlled `WORKFLOW_AGENTS` set.
- Documented `DOC_STALENESS_BLOCKED` in `docs/agent-monitoring/schema.md`'s `final_status` enum
  table, `docs/ai/workflows.md`'s Return-values table, and `docs/ai/ticket-lifecycle.md`'s
  flowchart and Implement step-by-step section — while in those tables, also added 4 other real,
  already-shipped terminal statuses that were separately found missing from the same tables
  (`SCOPE_AGENT_FAILED`, `EPIC_SCOPED`, `DATA_RUNS_CLEAN_FAILED`; `PARITY_INCOMPLETE`/
  `FINALIZE_INCOMPLETE` were already present in `workflows.md` but missing from `schema.md`) —
  fixing this adjacent staleness in the same pass rather than leaving it next to a fresh edit.
- **Deferred, with documented rationale (not wired):**
  - `tools/gate_checks/status_drift_check.py` — takes `done_dir`/`runs_path`, not a `ticket_id`;
    it scans the *entire* historical `tickets/done/` corpus and all of `runs.jsonl` on every call,
    with no way to scope to just the ticket being closed. Wiring it into every ticket's Finalize
    self-check as-is would mean any future reappearance of historical drift anywhere in the corpus
    hard-blocks an unrelated ticket's close. Confirmed live: the corpus is currently clean (0 FAIL
    across both its sub-checks), so this isn't an active problem today, but wiring it safely would
    require either scoping it down to just the closing ticket's own file + its own new `runs.jsonl`
    record, or accepting the corpus-wide blast radius deliberately — a real design decision, not a
    mechanical wire-in.
  - `tools/gate_checks/workflow_meta_conformance.py` — takes a `run_id` and reads that run's
    already-written `events.jsonl` rows. It can only meaningfully check a run whose events have
    already been flushed to disk, but the current run's own events aren't written until
    `writeMonitoring` executes near the very end of Finalize — so it cannot cleanly self-gate the
    very run it would be checking without restructuring the write order. Wiring it as a
    *retrospective* check over a *prior* run is a different, real design decision, not something
    this ticket decides unilaterally.
  - `tools/gate_checks/done_checker_audit.py` — its own module docstring explicitly states it is
    "read-only, disclose-don't-fix, warn-only (never blocking), no automated exit-code gate tied
    to findings" — it was designed from the start as a retrospective corpus-health report, not as
    a gate. There is no wiring decision to make here; it was never meant to be one.
  - `mechanics_auditor_static.py`'s weaker enforcement tier (no orchestrator-side call site,
    unlike the other 4 wired static checks) — investigated and found orthogonal to this ticket:
    `mechanics-auditor` is not invoked as a pipeline phase by any workflow at all (confirmed
    explicit, documented, intentional design in `docs/ai/agents.md`/`docs/ai/workflows.md`), so
    there is no orchestrator call site in any workflow to attach independent verification to.
    Closing this gap would require first deciding whether `mechanics-auditor` becomes a real
    pipeline phase — a materially larger, unrelated design change, not a gate-wiring decision.

## Out of Scope
- The live bugs, CLAUDE.md corrections, and docs/ai + schema accuracy fixes — tracked in the 3
  sibling tickets from the same audit (TCK-20260720-MONITORING-PIPELINE-BUGFIXES,
  TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES, TCK-20260720-DOCS-AI-SCHEMA-ACCURACY).
- Making `mechanics-auditor` a real pipeline phase — flagged as a prerequisite for closing its own
  enforcement gap, not decided or built here.
- Scoping `status_drift_check.py` down to a per-ticket check, or restructuring
  `workflow_meta_conformance.py`'s write-order dependency — both are real follow-up work, not
  built here; this ticket's job was to make the wiring *decision* explicit for each, not to design
  every deferred check's eventual wiring shape.
- The skills/docs orphan cleanup findings from the same audit (7 unwrapped simulation/lab
  workflows, 2 never-re-evaluated skills) — separate follow-up batch, not this ticket.

## Acceptance Criteria
- [x] `doc_staleness_check.py` is invoked in `implement-ticket.js` between the Implement agent
      call returning and the start of Architecture-Verify, verified by a static source-text
      regression test.
- [x] A `FAIL` from `doc_staleness_check.py` folds into the Implement phase's single existing
      monitoring event (not a second one), using the real `implementer` agent name, with no
      `reason_code` (the new status disambiguates 1:1) — all verified by dedicated tests.
- [x] The new `DOC_STALENESS_BLOCKED` terminal status writes a monitoring record before returning,
      verified by a dedicated test.
- [x] `DOC_STALENESS_BLOCKED` is documented in `docs/agent-monitoring/schema.md`'s `final_status`
      table, `docs/ai/workflows.md`'s Return-values table, and `docs/ai/ticket-lifecycle.md`'s
      flowchart and Implement section.
- [x] Each of the other 4 previously-unwired gate checks has an explicit, evidence-based
      deferral rationale recorded in this ticket (see Scope) — none left as a silent, undecided gap.
- [x] Live end-to-end verification: `doc_staleness_check.py` run directly via its CLI for all 4
      logical branches (behavior-changed+src+no-docs → FAIL; behavior-changed+src+docs → PASS;
      behavior-changed=false → PASS; docs/tests-only path → PASS) confirms exactly the intended
      gate behavior.
- [x] No regression: `tests/tools/test_doc_staleness_check.py` (10/10, pre-existing), new
      `tests/tools/test_doc_staleness_gate_wiring.py` (5/5), plus the broader monitoring/
      sidecar/tag-skill-mapping-scoped suite (57/57 total), all pass.

## Related Tickets
- TCK-20260711-DOC-STALENESS-GATE-CHECK (shipped `doc_staleness_check.py` unwired; this ticket
  completes the wiring that ticket's own docstring deferred)
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK (the exact precedent this ticket's wiring shape mirrors —
  pulling a Verify-phase check forward to catch it earlier)
- TCK-20260720-MONITORING-PIPELINE-BUGFIXES, TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES,
  TCK-20260720-DOCS-AI-SCHEMA-ACCURACY (sibling hotfix batches from the same audit)
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK (shipped `workflow_meta_conformance.py` unwired;
  deferral rationale recorded above)
- TCK-20260705-GATE-DET-DONE-CHECKER Part C (shipped `done_checker_audit.py`, by-design non-gating)
- TCK-20260718-STATUS-DRIFT-REPAIR (the original incident `status_drift_check.py` was built to
  detect; deferral rationale recorded above)

## Related Docs
- docs/agent-monitoring/schema.md
- docs/ai/workflows.md
- docs/ai/ticket-lifecycle.md
- docs/ai/agents.md (mechanics-auditor's documented non-pipeline status, referenced not modified)

## Related Stored Artifacts
None (hotfix — self-evident intent captured in this ticket).

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/gate_checks/doc_staleness_check.py
- tests/tools/test_doc_staleness_gate_wiring.py

## Assumptions / Open Questions
- The 4 deferred checks' rationale is recorded here as the authoritative decision record for
  this audit cycle — a future ticket revisiting any of them (e.g. scoping
  `status_drift_check.py` to a single ticket) should treat this ticket as prior context, not
  re-derive the reasoning from scratch.
- This ticket's own diff (touching `.claude/workflows/implement-ticket.js`, a behavior change)
  necessarily also touches `docs/` — a live, incidental proof that the new gate's own requirement
  is satisfiable in normal practice, not just in isolated unit tests.

## Implementation Notes
The wiring itself required correcting an initial mistake made during implementation: the first
draft created a second, synthetic-agent-named monitoring event for the check's failure case,
separate from the Implement phase's own event. Caught by re-reading the actual
`TAGS_NOT_REGISTERED` precedent code directly rather than assuming its shape — the real pattern
folds a deterministic check's outcome into the *same* phase event, computed via a ternary on the
check result, using the real agent name. Rewrote to match before writing any tests, so the tests
verify the corrected, precedent-consistent shape.

## Test Summary
- `tests/tools/test_doc_staleness_check.py`: 10/10 passing (pre-existing, unmodified — verifies
  the check module itself, not its wiring).
- `tests/tools/test_doc_staleness_gate_wiring.py`: 5/5 passing (new — static source-text
  regression tests verifying call-site position, event-folding shape, no stray `reason_code`,
  monitoring-before-return ordering, and correct argument passing).
- Broader scoped regression (`doc_staleness`, monitoring bypass, sidecar, step0, scope-orphan,
  tag-skill-mapping): 57/57 passing.
- Live CLI verification of all 4 logical branches of `doc_staleness_check.py`'s own gate logic,
  confirming exact expected PASS/FAIL behavior before trusting the wiring.
- `node --check .claude/workflows/implement-ticket.js`: syntax valid.

## Files Changed
- .claude/workflows/implement-ticket.js
- docs/agent-monitoring/schema.md
- docs/ai/workflows.md
- docs/ai/ticket-lifecycle.md
- tests/tools/test_doc_staleness_gate_wiring.py (new)

## Completion Summary
Wired `doc_staleness_check.py` into `implement-ticket.js`'s Implement phase, closing the exact gap
its own 2026-W28-retro-driven origin ticket identified (36% of first-attempt Verify failures
traced to undocumented behavior changes) — now caught immediately after Implement instead of 6+
phases later, mirroring the `TAGS_NOT_REGISTERED` precedent's proven shape. The other 4 previously
unwired gate checks each received an explicit, evidence-based deferral decision rather than being
wired blindly or left as a silent gap: 2 have structural scope problems (corpus-wide vs. per-ticket
for `status_drift_check.py`; write-order self-reference for `workflow_meta_conformance.py`), 1 was
never designed to be a gate at all (`done_checker_audit.py`), and 1 (`mechanics-auditor`'s
enforcement tier) has no pipeline call site to attach to until a separate, larger design decision
is made. Also fixed 4 other already-shipped terminal statuses found missing from the same
documentation tables while making this edit, rather than leaving fresh staleness beside a new fix.
