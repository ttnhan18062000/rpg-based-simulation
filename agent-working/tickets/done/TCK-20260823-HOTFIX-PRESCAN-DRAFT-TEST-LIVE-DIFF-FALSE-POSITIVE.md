---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE
phase: done
date: 2026-08-23
tags: [testing]
---

# TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE

## Title
`test_draft_does_not_modify_claude_md_or_agent_md_files` false-positives on any unrelated uncommitted `.claude/agents/*.md` edit

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/tools/test_prescan_mandate_instruction_draft.py::test_draft_does_not_modify_claude_md_or_agent_md_files`
(actually located at `tests/docs/test_prescan_mandate_instruction_draft.py`) asserts:

```python
result = subprocess.run(
    ["git", "diff", "--stat", "HEAD", "--", "CLAUDE.md", ".claude/agents/*.md"],
    ...
)
assert result.stdout.strip() == "", (...)
```

This checks the **live, currently-uncommitted working-tree diff against HEAD** at the moment the
test runs — not the historical diff introduced specifically by the ticket the test's own docstring
says it exists to guard, `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` (confirmed shipped
and closed long ago: `tickets/done/TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT.md`,
committed at `59b4bede`). The test's docstring is explicit that its purpose was a one-time
"this specific ticket produced zero runtime change and didn't touch these files" assertion — but
implemented as a live `git diff HEAD` check, it instead functions as an ongoing, permanent
assertion that **no session may ever have an uncommitted edit to `CLAUDE.md` or any
`.claude/agents/*.md` file while this test suite runs**, regardless of which ticket is doing the
editing or why.

This is a structural test-isolation bug: `.claude/agents/*.md` files are legitimately edited by
many tickets over time (this very session edited `investigator.md` via a different, unrelated
hotfix ticket, `TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP`, and hit this
exact false positive during its own Test phase). The test will pass again once that unrelated
edit is committed (since `git diff HEAD` becomes empty relative to itself), which confirms the
check was never really scoped to `TCK-20260814`'s own diff — it is a live-working-tree assertion
masquerading as a historical one.

## Scope
- Rewrite `test_draft_does_not_modify_claude_md_or_agent_md_files` to check something that
  actually reflects the original intent — that `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`'s
  own historical commit(s) didn't touch `CLAUDE.md`/`.claude/agents/*.md` — rather than the live
  uncommitted working-tree state. Options to investigate: pin to that ticket's actual commit SHA(s)
  and diff those specifically (`git show <sha> --stat -- ...`), or determine whether this
  assertion even belongs as an ongoing regression test at all (a one-time historical fact about a
  closed ticket may not need a permanent CI-enforced guard, unlike a live invariant about current
  code).
- Do not weaken the underlying intent (verifying `TCK-20260814`'s own change was genuinely
  behavior-inert) — only fix the mechanism so it doesn't false-positive on unrelated, legitimate,
  uncommitted work elsewhere in the repo.

## Out of Scope
- Any other test in `tests/docs/test_prescan_mandate_instruction_draft.py` (tests 1-3 and any
  others) — only the one test using `git diff HEAD` (live working-tree state) is in scope.
- Re-opening or modifying `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` itself or its own
  draft doc (`docs/ai/claude_md_prescan_mandate_relaxation_draft.md`).

## Acceptance Criteria
- [x] The test no longer false-positives when an unrelated ticket has a legitimate, uncommitted
      edit to `.claude/agents/*.md` or `CLAUDE.md` in the working tree.
- [x] The test still meaningfully verifies (or explicitly documents why it no longer needs to)
      that `TCK-20260814`'s own historical change was behavior-inert with respect to those files.

## Related Tickets
- TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT (the ticket this test's docstring says it guards)
- TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP (discovered this during its own Test phase)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent per CLAUDE.md's hotfix convention.

## Related Code Areas
- tests/docs/test_prescan_mandate_instruction_draft.py

## Assumptions / Open Questions
- Whether a permanent regression test is even the right mechanism for "this one closed ticket
  didn't touch these files" (vs. e.g. a comment/note in that ticket's own working_log.csv entry) is
  itself an open design question this ticket's investigation should weigh in on, not assumed away
  here.

## Implementation Notes
Independently re-verified the orchestrator's root-cause SHAs before trusting them:
`git log --oneline --all --grep "TCK-20260814-KGMCP-PRESCAN"` shows `59b4bede` as
TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT's own commit, and
`git log --oneline -1 59b4bede^` confirms `12f773c8` (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE:
Record Phase 0 measurement baseline (INFRA-334)`) as its immediate parent. No discrepancy — both
SHAs used exactly as handed off.

Rewrote `test_draft_does_not_modify_claude_md_or_agent_md_files` in
`tests/docs/test_prescan_mandate_instruction_draft.py` to run
`git diff --stat 12f773c8..59b4bede -- CLAUDE.md .claude/agents/*.md` instead of
`git diff --stat HEAD -- ...`. This pins the check to TCK-20260814's own historical commit range
(an immutable fact once true) rather than the live working tree, so it can never false-positive
on an unrelated session's legitimate uncommitted edit to those files. Added an inline comment on
the test explaining the mechanism change and why, and expanded the module docstring with a
paragraph naming the pinned commit/parent SHAs and cross-referencing this ticket, since the
original docstring's "non-regression of the three live instruction surfaces" phrasing did not
make clear the check was meant to be a one-time historical assertion rather than an ongoing
live-diff invariant.

No deviation from the plan handed off in the ticket — implemented exactly the fix specified,
after independently confirming the SHAs.

## Test Summary
Ran `PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
tests/docs/test_prescan_mandate_instruction_draft.py -v`. All 5 tests pass, including the fixed
`test_draft_does_not_modify_claude_md_or_agent_md_files`. Verified via `git status`/`git diff`
that the fix mechanism (diffing two fixed historical SHAs) is structurally immune to any live
working-tree state — confirmed the working tree currently has no uncommitted edits to
`CLAUDE.md`/`.claude/agents/*.md` to begin with, so no artificial dirty-file scenario was needed
or manufactured, per the task's own guidance to prefer reasoning over fabricating test state.

## Files Changed
- `tests/docs/test_prescan_mandate_instruction_draft.py` — rewrote Test 4 to diff a pinned
  historical commit range instead of live `HEAD`; updated the test's inline comment and the
  module docstring.
- `tickets/inprogress/TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE.md` — this
  ticket file itself (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files
  Changed, Completion Summary).

No `staging_artifacts/{ticket_id}/` directory exists or was created for this ticket — hotfix tier
per `## Related Stored Artifacts` above, self-evident intent captured directly in the ticket per
CLAUDE.md's hotfix convention.

## Completion Summary
Fixed a test-isolation bug in `test_draft_does_not_modify_claude_md_or_agent_md_files`: it
previously diffed the live working tree against `HEAD`, which meant any unrelated session with an
uncommitted edit to `CLAUDE.md` or `.claude/agents/*.md` would fail it regardless of what that
session's own work touched. Rewrote it to diff the specific historical commit range
(`12f773c8..59b4bede`) that TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT's own commit
actually introduced, which is what the test's docstring always claimed to be checking. SHAs were
independently re-verified against `git log`/`git show` before use, and the docstring/inline
comments were updated to make the pinned-historical-diff mechanism explicit. All 5 tests in the
file pass; no forbidden files (`CLAUDE.md`, `.claude/agents/*.md`,
`docs/ai/claude_md_prescan_mandate_relaxation_draft.md`) were touched.
