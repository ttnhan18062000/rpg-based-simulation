---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS
phase: done
date: 2026-10-20
tags: [testing, workflows]
---

# TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS

## Title
The three Semgrep `use-defused-xml-parse` findings in `tools/ci_junit_merge.py` and `tools/ci_junit_summary.py` are accepted in code with a reason, the same way #667 handled testing's report tools.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
lead-planner-u24, 2026-10-20 (from platform's post-#668 scan, verified): code-scanning alerts #244, #245 and #246 are open on main f6c7bc795:
- `tools/ci_junit_merge.py:61`
- `tools/ci_junit_summary.py:94`
- `tools/ci_junit_summary.py:149`

These `ET.parse` calls read JUnit XML that pytest's `--junit-xml` wrote in this repo's own CI jobs: test.yml's summary steps, and the merge step over the same run's artifacts. That is the same input class #667 ruled on.

**testing-planner ruling, 2026-10-20: ACCEPT, do not fix.**
- defusedxml is not a dependency, and adding it is a pyproject/uv.lock change for lead-planner (ubuntu).
- The input is never untrusted.
- Mark each line `# nosemgrep: python.lang.security.use-defused-xml-parse.use-defused-xml-parse`, with the reason comment on the line above: "Parses this repo's own pytest junit XML; no untrusted input." This is the exact form at `tools/test_architecture/core_rpg_report.py:365-366`.
- Never dismiss in the Security tab.

**BLOCKED** until TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS lands, which puts `tools/ci_junit_*.py` in testing.owns. testing-planner already said yes; the dispatch waits on the user. Unblock check: `python3 -m tools.sessions.route tools/ci_junit_summary.py` names testing.

## Scope
1. Add the reason comment and the `nosemgrep` to the three lines. The parse calls stay unchanged otherwise.
2. If either file has another `ET.parse`/`fromstring` on main at unblock time, treat it the same way and list it.

## Out of Scope
- Adding defusedxml.
- Any behaviour change.

## Acceptance Criteria
- [x] AC1: each of the three lines carries the exact rule id and the reason. `tests/tools` and `tests/unit/tools` tests for ci_junit_merge and ci_junit_summary pass.
- [x] AC2 (read from the PR): CI on the PR is green.
- [ ] AC3 (post-merge, testing-planner): the first security-scan main run after merge shows 0 `use-defused-xml-parse` in these files, and alerts #244 to #246 close as fixed. Quote the run id.

## Related Tickets
- TCK-20261019-TEST-WORKFLOWS-GITHUB-CONTEXT-VIA-ENV-NOT-RUN (#667, the precedent)
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (ownership; the blocker)

## Related Docs
- (none)

## Related Stored Artifacts
- (none)

## Related Code Areas
- tools/ci_junit_merge.py, tools/ci_junit_summary.py

## Assumptions / Open Questions
- **UNBLOCKED 2026-10-21:** #701 merged as 7ae9a6ebc, and origin/main registries/session_roles.yaml:88 puts `tools/ci_junit_*.py` in testing.owns. Checked on main: the only parse sites are exactly the three lines in scope (ci_junit_merge.py:61; ci_junit_summary.py:94 and :149). There is no `fromstring`. Dispatched to testing-implementer.
- If the roles ticket instead routes these files elsewhere, this ticket moves to that owner with the ruling attached as a recommendation.

## Implementation Notes
- Unblock check: `python3 -m tools.sessions.route tools/ci_junit_summary.py` names testing (owned). #701 merged as 7ae9a6ebc.
- The three lines (tools/ci_junit_merge.py:61, tools/ci_junit_summary.py:94 and :149) each carry `# nosemgrep: python.lang.security.use-defused-xml-parse.use-defused-xml-parse`, and the line above carries "Parses this repo's own pytest junit XML; no untrusted input." This is the form at tools/test_architecture/core_rpg_report.py:365-366. No behaviour change; defusedxml is not added.
- Scope 2: `ET.parse` is the only XML parse in tools/ci_junit_*.py (no `fromstring`, no other call), so nothing else is listed.

## Test Summary
tests/tools/test_ci_junit_merge.py, test_ci_junit_summary.py and tests/unit/tools/test_junit_cost_report.py: 50 passed.

## Files Changed
- tools/ci_junit_merge.py
- tools/ci_junit_summary.py

## Completion Summary
The three ET.parse findings are accepted in code with the rule id and the reason; AC3 is testing-planner's post-merge check.
