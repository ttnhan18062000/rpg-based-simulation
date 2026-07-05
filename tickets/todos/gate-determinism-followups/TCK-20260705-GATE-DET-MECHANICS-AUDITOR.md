---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-MECHANICS-AUDITOR
phase: open
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-MECHANICS-AUDITOR

## Title
Add a deterministic test_path existence-and-passing check backing mechanics-auditor's PARITY verdicts

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Third of 4 gate-determinism tickets (see `tickets/todos/gate-determinism-followups/SEQUENCE.md` for
shared design decisions and full context). Per `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
table: "For any PARITY verdict, confirm the cited `test_path` exists **and is green in this run** — not
just present in the ledger." What stays LLM-judged: whether an `UNDOCUMENTED` implementation is actually
intended behavior.

## Scope
- `tools/gate_checks/mechanics_auditor_static.py`: given a parity-ledger entry ID (or a set of entries
  `mechanics-auditor` is about to render a `PARITY` verdict for), verify: (a) the entry's `test_path`
  field is non-null and points to a file:test that actually exists on disk, (b) running that specific
  test (scoped, not the full suite) exits 0 in the current working tree. Return PASS/FAIL with the
  actual pytest output on failure.
- Reuse `TCK-20260705-GATE-DET-PARITY-UPDATER`'s `src/`-to-subsystem mapping module if that ticket ships
  first and produces one generically reusable — do not derive a second, potentially-inconsistent mapping
  independently. Check that sibling ticket's `stored_artifacts/` before building anything new here.
- Investigate `mechanics-auditor.md`'s current invocation pattern (when/how it's actually invoked today —
  confirm whether it's called from `implement-ticket.js` at all, or only ad hoc via
  `Agent(subagent_type: "mechanics-auditor")` per `docs/ai/skills.md`'s "Choosing the Right Tool" table,
  since this affects where the static check's instruction gets wired in).
- Add a `verified_by` field to whatever schema/return-shape mechanics-auditor uses.
- At least one coverage-honesty test (a fixture entry with a `test_path` pointing to a real, passing
  test must PASS; a fixture entry with a `test_path` pointing to a nonexistent file, or to a real but
  failing test, must FAIL with the actual error surfaced, not just a generic "not found").

## Out of Scope
- The other 3 gates' static verifiers — see SEQUENCE.md.
- Re-deciding whether an `UNDOCUMENTED` implementation is intended behavior — remains LLM-judged.
- Running the full test suite to verify a `test_path` — must be scoped to exactly the cited test.
- Token/cost telemetry.

## Acceptance Criteria
- [ ] `tools/gate_checks/mechanics_auditor_static.py` exists, verifying both existence and pass/fail
      state of a cited `test_path`, reusing `GATE-DET-PARITY-UPDATER`'s mapping module if available.
- [ ] `mechanics-auditor`'s invocation path (wherever it actually is) instructs it to run this check
      before rendering any `PARITY` verdict.
- [ ] At least one coverage-honesty test per check function, including a genuinely-failing-test fixture
      case (not just a missing-file case).
- [ ] `docs/ai/agents.md`'s `mechanics-auditor` section and the other 3 shared docs updated.

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER, TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER (siblings)
- TCK-20260705-GATE-DET-PARITY-UPDATER (build after this one if possible, to reuse its mapping module)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- tickets/todos/gate-determinism-followups/SEQUENCE.md
- docs/ai/agents.md, docs/ai/skills.md (mechanics-auditor's "Choosing the Right Tool" entry),
  docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/mechanics-auditor.md
- .claude/workflows/implement-ticket.js (confirm whether mechanics-auditor is invoked here at all)
- docs/parity_ledger/*.yaml (read-only reference)

## Assumptions / Open Questions
- Whether `mechanics-auditor` is even invoked from within `implement-ticket.js`'s own pipeline today,
  or purely ad hoc — left for Investigate; this may mean the static check's wiring point is a standalone
  agent-invocation prompt rather than a workflow-file edit.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
