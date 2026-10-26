---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-CI-ASEPRITE-SKIP-LINE-ACCEPT-DEFUSED-XML-FINDING
phase: open
date: 2026-10-26
tags: [testing]
---

# TCK-20261026-CI-ASEPRITE-SKIP-LINE-ACCEPT-DEFUSED-XML-FINDING

## Title
Code-scanning alert #243 (Semgrep use-defused-xml-parse at tools/ci_aseprite_skip_line.py:23) is marked as trusted input at the line, in the same form as the ci_junit tools

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The owner's go is on #715 (issuecomment-6407266343, 2026-10-26): "fix the open code-scanning findings now … #243 `tools/ci_aseprite_skip_line.py` (use-defused-xml-parse) goes to testing-planner". lead-planner-u24 relayed it the same day.

Alert #243 is open on main: `python.lang.security.use-defused-xml-parse` at `tools/ci_aseprite_skip_line.py:23` (`ET.parse(path)` in `count_aseprite_skips`). The input is the merged pytest JUnit XML, `reports/junit/api-cli-engine.xml`, which this repo's own CI job writes. test.yml's "Note: needs_aseprite skips" step reads it. That is the input class TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS ruled on (alerts #244-246).

**testing-planner ruling (2026-10-26): ACCEPT at the line, the same as #244-246.**
- defusedxml is not a dependency, and the input is never untrusted.
- Don't add a dependency, don't disable the rule repo-wide, and never dismiss the alert in the Security tab.

**Ownership note:** `registries/session_roles.yaml` on main lists this file under **asset** (line 115), not testing. The owner's #715 note assigns the fix to testing-planner, and the asset seats are closed, so testing does it under that note. The registry is unchanged here; lead-planner-u24 has been told about the mismatch.

## Scope
1. At `tools/ci_aseprite_skip_line.py:23`:
   - add the reason comment on the line above: `# Parses this repo's own pytest junit XML; no untrusted input.`;
   - add `# nosemgrep: python.lang.security.use-defused-xml-parse.use-defused-xml-parse` on the parse line.
   This is the exact form at `tools/ci_junit_summary.py:94-95`. The parse call is otherwise unchanged.
2. If the file has any other `ET.parse` / `ET.fromstring` call, treat it the same way and list it here.

## Out of Scope
- The 14 src/** findings (rpg, TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE).
- Dependabot #143.
- Editing the ownership registry.

## Acceptance Criteria
- [ ] AC1: the marker and reason comment are on the parse line, in the same form as ci_junit_summary.py. No other code change.
- [ ] AC2: `pytest tests/visual_assets/test_ci_aseprite_skip_line.py` passes, and `semgrep --config p/python` (or the repo's semgrep job) reports no use-defused-xml-parse in the file. Record the command and output.
- [ ] AC3: after merge, the code-scanning run on main shows alert #243 as fixed, not dismissed. testing-planner checks this and records the run id.

## Related Tickets
- TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS (precedent; #244-246)
- TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE (rpg, src/**)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/ci_aseprite_skip_line.py
- tests/visual_assets/test_ci_aseprite_skip_line.py (run only)

## Assumptions / Open Questions
- none

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
