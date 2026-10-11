---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-PR-ATTRIBUTION-OFF-AT-SOURCE
phase: done
date: 2026-10-11
tags: [ai, governance, delivery]
---

# TCK-20261011-PR-ATTRIBUTION-OFF-AT-SOURCE

## Title
Turn off the Claude Code PR attribution line at its source, so pr-body-lint stops failing hand-opened PRs

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
GitHub issue #495 (finding from lead-planner). Sessions keep opening PRs whose body ends with
"🤖 Generated with [Claude Code](...)", and `pr-body-lint.yml` fails them (#482, #489).
`tools/delivery/pr_render.py` already omits the line. The sessions add it by hand because the harness's
attribution reminder tells them to; the repo rule lives only in `docs/guides/delivery_process.md`.
Confirmed on host u24desktop on 2026-10-11: agent-working-planner's own session context carries the
reminder "End pull request descriptions with: 🤖 Generated with [Claude Code]".

## Scope
- Add `"attribution": {"pr": ""}` to the project `.claude/settings.json` (Claude Code's attribution
  setting; an empty string turns the PR line off). Leave commit attribution unchanged.
- Verify the key is honoured: a session launched after the change no longer receives the PR
  attribution reminder. Record how this was checked in the Test Summary.
- Fallback, only if the key is not honoured by the installed Claude Code version: one line in
  CLAUDE.md's PR Lifecycle section: "PR bodies never carry an attribution line." Record which path was taken.

## Out of Scope
- Commit-message attribution (stays as is unless the owner decides otherwise).
- Any change to `pr-body-lint.yml` (it stays as the backstop) or to `pr_render.py`.
- Ownership of `pr-body-lint.yml` (TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED, same batch).

## Acceptance Criteria
1. `.claude/settings.json` carries `"attribution": {"pr": ""}` and is otherwise unchanged; it parses as JSON.
2. `python3 tools/sessions/settings_freshness.py .` reports the expected state after the change.
3. The Test Summary records whether a fresh session still gets the PR attribution reminder.
4. The owner confirms the literal `.claude/settings.json` diff in the batch PR (governing file).
   Approval of the approach: owner, 2026-10-11 ("proceed" on the triage of #495).

## Related Tickets
- TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED (added the CI check)
- TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED (same batch)
- GitHub issue #495

## Related Docs
- docs/guides/delivery_process.md ("PR Lifecycle")

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/settings.json
- .github/workflows/pr-body-lint.yml (read only)

## Assumptions / Open Questions
- Assumes the installed Claude Code supports the `attribution` settings key; the fallback covers the case it does not.

## Implementation Notes
Added top-level `"attribution": {"pr": ""}` to `.claude/settings.json`; nothing else changed; commit attribution untouched. Owner to confirm the literal diff (governing file). Path taken: the settings key, NOT the CLAUDE.md fallback.

## Test Summary
JSON parses. Evidence the key is honoured: in THIS running session, the attribution reminder the harness re-sent after the edit lists only the commit line (`Co-Authored-By: ...`); before the edit it also said to end PR descriptions with the Generated-with line. This is in-session evidence, NOT a fresh launch: I did not launch a new session (the `claude` binary is not run from here), so a fresh-launch check is still open. `settings_freshness.py .` reports only the expected 'differs from origin/main' for changed cards/settings.

## Files Changed
`.claude/settings.json`.

## Completion Summary
PR attribution is turned off at its source via the settings key; fresh-launch confirmation remains.
