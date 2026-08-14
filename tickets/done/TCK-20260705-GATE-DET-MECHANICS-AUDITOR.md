---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-MECHANICS-AUDITOR
phase: done
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-MECHANICS-AUDITOR

## Title
Add a deterministic test_path existence-and-passing check backing mechanics-auditor's PARITY verdicts

## Status
DONE

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
Implemented all 5 steps of `staging_artifacts/TCK-20260705-GATE-DET-MECHANICS-AUDITOR/plan.md`
exactly as specified, no deviations.

- **Step 1** (`tools/gate_checks/mechanics_auditor_static.py`, new): six functions —
  `parse_test_path_citations`, `check_test_path`, `find_entry`, `verify_entry_test_path`,
  `verify_entries`, `candidate_ledger_files_for_module`. `CANONICAL_LEDGER_FILES` imported from
  `tools/parity_ledger_scan.py`; `candidate_ledger_files_for_module` is a direct pass-through of
  `parity_updater_static.expected_subsystems_for_files` (genuine reuse, not reimplementation).
  Multi-citation `test_path` values are checked in full — every citation's verdict is aggregated
  (`any FAIL -> overall FAIL`) and each citation's individual PASS/FAIL is visible in the joined
  evidence string, never collapsed. `tests_v2/` citations short-circuit to FAIL before any
  `subprocess.run` call (the directory doesn't exist in this repo). All `subprocess.run` invocations
  are wrapped in `try/except Exception` so a pytest invocation failure can never escape as an
  unhandled exception — it degrades to a FAIL result with the exception text in evidence.
- **Step 2** (`tests/tools/test_mechanics_auditor_static.py`, new): all 11 tests from `test_plan.md`,
  including the genuinely-failing-test fixture (test 2), the multi-citation "check ALL" lock-in
  (test 8, asserting overall FAIL plus both citations' individual verdicts visible), the
  `tests_v2/`-short-circuit guard (test 6, monkeypatches `subprocess.run` to raise if called), the
  scoped-invocation guard (test 9, asserts the exact citation is the pytest argv element, `"tests/"`
  is not), and the scoped-by-entry-ID guard (test 11, asserts sibling entries A-001/A-003 never
  appear when verifying A-002). Result: 11/11 passed.
- **Step 3** (`.claude/agents/mechanics-auditor.md`): added the `Step 0 — static pre-check` paragraph
  to the "Checking Parity" section per the plan's exact wording, including the explicit
  never-downgrade-Status rule and the enforcement-asymmetry disclosure sentence. Updated the
  `verified` bullet to reference Step 0. Added the `verified_by` field line to the `Output` section.
  No `Agent(subagent_type: "mechanics-auditor")` call site was added to
  `.claude/workflows/implement-ticket.js` (confirmed zero pre-existing call sites; adding one is
  explicitly out of scope per the plan and ticket).
- **Step 4** (`docs/ai/agents.md`): added the mirrored `Step 0 — static pre-check` paragraph and the
  `candidate_ledger_files_for_module` reuse note to the `mechanics-auditor` section, placed between
  the `Output classification` block and `When to invoke directly` (matching the plan's specified
  location, corrected after an initial mis-placement caught during self-review — see Verification
  below). Did not touch `docs/ai/skills.md`.
- **Step 5**: re-ran `grep -n -i "mechanics-auditor" docs/ai/workflows.md docs/ai/system_overview.md
  docs/ai/ticket-lifecycle.md` first — confirmed still zero mentions, matching investigation.md. Added
  exactly one cross-referencing sentence to each of the 3 files (no new phase-table row): a
  not-a-phase disclosure + pointer to `docs/ai/agents.md` in `workflows.md`; a static-pre-check note
  emphasizing agent-self-invocation (vs. orchestrator-run) in `system_overview.md`; and a
  not-a-phase + static-pre-check note near the Verify phase's own `done-checker` Step 0 description
  in `ticket-lifecycle.md`. Re-grepped all 3 post-edit to confirm exactly one single-sentence mention
  each, no table row added.

**Verification beyond the plan's own steps:** ran `graphify update .` (tests/tools/ and
tools/gate_checks/ files changed) and `make knowledge-index-update` (docs/ai/*.md files changed) to
keep the code graph and doc search index current, per this repo's own CLAUDE.md proactive-tool-use
rules.

## Test Summary
```
python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v
-> 11 passed

python3 -m pytest tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py tests/tools/test_mechanics_auditor_static.py -v
-> 52 passed
```
No pre-existing test was modified; `test_parity_updater_static.py` and `test_done_checker_static.py`
pass unmodified, confirming no regression to the sibling gate-check modules this ticket imports from.

## Files Changed
- `tools/gate_checks/mechanics_auditor_static.py` (new)
- `tests/tools/test_mechanics_auditor_static.py` (new)
- `.claude/agents/mechanics-auditor.md` (modified)
- `docs/ai/agents.md` (modified)
- `docs/ai/workflows.md` (modified)
- `docs/ai/system_overview.md` (modified)
- `docs/ai/ticket-lifecycle.md` (modified)

## Completion Summary
Added a scoped, per-entry deterministic backstop (`verify_entry_test_path`/`verify_entries`) that
answers whether a named parity-ledger entry's `test_path` citation exists and passes, without ever
overriding `mechanics-auditor`'s own independently-determined `Status`. Wired into the agent's own
prompt (no pipeline call site exists or was added) and documented in `docs/ai/agents.md` plus a
single cross-referencing sentence in each of the 3 other shared docs. All acceptance criteria met;
no deviations from the approved plan.
