---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE

## Title
Epic C ungated parts 1–4: proof fields in test_plan.md, advisory test-quality checklist, epic coordination note, unified failure-triage procedure

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implements parts 1–4 of `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (roadmap §4.4–4.6). Epic D's start condition needs the test-plan fields and the triage procedure.

## Scope
1. `investigator.md`: `test_plan.md` gains a per-acceptance-criterion proof plan. Mandatory: level, proof kind, oracle source (Bible/contract section + parity-ledger id), expected effect, selected commands. Optional: negative cases, fixtures, non-functional risk.
2. `architecture-reviewer.md`: advisory, diff-scoped test-quality checklist at Architecture-Verify. No verdict change; a clean review is valid.
3. Epic coordination note: the `implement-epic` epic-creation prompt seeds a `### Shared test fixtures and patterns` subsection in the epic ticket; the investigator reads it.
4. `docs/testing/regression_policy.md` §13: evidence record, failure classes, prohibitions, defects handed to the feature team. `delivery_process.md` CI triage links to it.

## Out of Scope
- Oracle-review / approval step (part 5, HOLD D-M2). The oracle field only cites.
- Quarantine policy and tooling (part 6, HOLD D-MF). §6 is untouched except a pending-decision pointer.
- `CLAUDE.md` and `settings.json` (need the user's direct confirmation; the CLAUDE.md gate-integrity link to §13 is left for the user).
- New phase or test-writing agent.
- Enforcement of the Proof Plan fields (a done-checker condition or static function): new gate tooling, not in the epic. Proposed to agent-working-design only if the pilot shows fields going missing.

## Acceptance Criteria
1. `investigator.md` lists the mandatory and optional fields; the oracle field cites only.
2. The checklist is advisory and adds no `NEEDS_CHANGES` trigger.
3. The epic-creation prompt seeds the coordination subsection and the investigator reads it; no control-flow change.
4. `regression_policy.md` §13 is the single triage document; `delivery_process.md` links to it; §6's rule is unchanged.
5. Tests pin the above; scoped pytest passes.

## Related Tickets
- `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (parent epic)

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3, §4.4–4.6
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §5, §7
- `docs/testing/regression_policy.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
`.claude/agents/investigator.md`, `.claude/agents/architecture-reviewer.md`, `.claude/workflows/implement-epic.js`, `docs/testing/regression_policy.md`.

## Assumptions / Open Questions
- Agent-definition files are shared with agent-working-design; the intended edits were sent to them and they replied before the edits (cleared investigator.md, architecture-reviewer.md, implement-epic.js prose).
- The proof fields are advisory during the pilot (roadmap principle 8).

## Implementation Notes
- §13 appended to `regression_policy.md` (no renumbering). The drill is recorded in the staging investigation, now in `stored_artifacts/`.
- Advisory throughout (roadmap principle 8): the Proof Plan and the checklist never block.
- Reviewer removed the planned done-checker WARN and static function (not in epic scope); neither was added. `done_checker_static.py`, `done-checker.md` and `ticket-scoper.md` belong to another unpushed batch and are untouched.
- Coordination note lives in the epic ticket's Implementation Notes, seeded by the `implement-epic` request-mode prompt and read by `investigator.md`. Epics created before this change have no subsection; the investigator reads it only if present.
- No test-quality findings to act on: the checklist ran on the one changed test file (`test_test_workflow_agent_prose.py`), which asserts on file text, not on mocks. Clean review.
- CLAUDE.md's gate-integrity rule has no pointer to §13 yet; it needs the user's direct confirmation.

## Test Summary
`pytest tests/tools/test_test_workflow_agent_prose.py tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_delivery_ci_triage_classifier.py tests/tools/test_skill_investigate_search_before_grep.py`: 81 passed.

## Files Changed
- `.claude/agents/investigator.md`, `.claude/agents/architecture-reviewer.md`
- `.claude/workflows/implement-epic.js` (one line in the epic-creation prompt)
- `docs/testing/regression_policy.md`, `docs/guides/delivery_process.md`
- `tests/tools/test_test_workflow_agent_prose.py`

Parts 1–4 landed as advisory process changes plus one triage document. Proof Plan enforcement is deliberately out of scope.
