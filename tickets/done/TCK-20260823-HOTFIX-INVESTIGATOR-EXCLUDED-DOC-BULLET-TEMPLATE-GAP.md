---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP
phase: done
date: 2026-08-23
tags: [documentation, architecture]
---

# TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP

## Title
Fix `investigator` agent's "Docs Requiring Update" template to prevent excluded-doc bullet false positives

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`.claude/agents/investigator.md`'s "Docs Requiring Update" section (lines 70-88) only documents
one format: a leading `` - `docs/path` `` bullet for a doc that MUST be updated, machine-parsed by
`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` via
`_DOCS_BULLET_RE = re.compile(r"^-\s+\`(docs/[^\`]+?)(?::\d+)?\`", re.MULTILINE)`. The template
gives no guidance for how an investigator should mention a doc it *considered but explicitly
excluded* (a common, legitimate need — e.g. "docs/X is not required because..."). Investigators
naturally reuse the only documented bullet format for this case too, since it's the template's own
established shape for referencing a doc path at all. The parser cannot tell the two apart — it
only reads the leading backtick path, never the reasoning text that follows — so an excluded-doc
bullet is indistinguishable from a required one and the ticket's own `docs_to_update_coverage`
static check fails with `git status shows no changes to these path(s)`, even though the
investigation's own prose says the doc was *deliberately* not touched.

This was found and worked around twice in the 2026-08-21/22 world-rendering-core batch (this
week's agent-monitoring retro, `RETRO-2026-W34.md` Notes item 1): once reactively on
`TCK-20260821-VISUAL-VARIANTS-METRIC` (caught at Verify time, cost a BLOCKED→fix→re-verify round
trip), once pre-emptively on `TCK-20260821-VISUAL-GRADE-SCORER` (investigation.md's own "Docs
Requiring Update" section was reformatted before Verify ever ran, avoiding the round trip).
Both fixes were the same shape: rewrite the excluded doc's mention as prose, dropping the leading
`` - `docs/...` `` bullet, so only the genuinely-required path(s) remain machine-parseable.

## Scope
- Update `.claude/agents/investigator.md`'s "Docs Requiring Update" section (lines 70-88) to
  explicitly document a second, distinct format for a doc that was considered and excluded: prose
  only, no leading `` - `docs/...` `` bullet — e.g. "The `docs/X.md` doc (path: `X.md`, under
  `docs/`) is not required because..." — matching the exact reformatting pattern already used
  successfully in `stored_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/investigation.md` and
  `stored_artifacts/TCK-20260821-VISUAL-GRADE-SCORER/investigation.md`'s "Docs Requiring Update"
  sections (both real, already-fixed examples in this same repo, in the main checkout, not this
  worktree).
- State explicitly in the template that the leading-bullet format is reserved exclusively for docs
  that genuinely must change, and that mixing an excluded doc into that same bullet shape is a
  known, previously-hit false-positive trigger for `check_docs_to_update_coverage`.
- No change to `tools/gate_checks/done_checker_static.py`'s parser itself — the parser's own
  contract (only read the leading backtick path, ignore reasoning text) is a deliberate,
  documented design choice (see that function's own docstring), not the bug. The bug is the
  template giving investigators no alternative format for the excluded-doc case, so they default
  to the only one shown.

## Out of Scope
- Changing `_DOCS_BULLET_RE`'s regex or `check_docs_to_update_coverage`'s parsing logic.
- Retroactively fixing any other already-closed ticket's `investigation.md` (the two cited
  examples already self-corrected during their own pipeline runs; this ticket only prevents the
  pattern from recurring going forward).
- Any change to `concern-investigator.md` (a distinct agent with its own, differently-shaped
  output contract — not investigated here; a separate ticket if the same gap is confirmed there).

## Acceptance Criteria
- [x] `.claude/agents/investigator.md`'s "Docs Requiring Update" section documents both formats
      explicitly: the required-doc bullet (unchanged) and a new excluded-doc prose convention,
      with an example of each.
- [x] The updated template explicitly states why the distinction matters (the parser only reads
      the leading path, not reasoning text) so a future investigator dispatch understands the
      mechanism, not just the rule.
- [x] No change to `tools/gate_checks/done_checker_static.py` or its tests.

## Related Tickets
- TCK-20260821-VISUAL-VARIANTS-METRIC (first real occurrence, caught reactively at Verify)
- TCK-20260821-VISUAL-GRADE-SCORER (second occurrence, caught pre-emptively before Verify)

## Related Docs
- .claude/agents/investigator.md
- agent-monitoring/retro/RETRO-2026-W34.md (Notes item 1 — the finding that prompted this ticket)

## Related Stored Artifacts
None — hotfix tier, self-evident intent per CLAUDE.md's hotfix convention.

## Related Code Areas
- .claude/agents/investigator.md
- tools/gate_checks/done_checker_static.py (read-only reference, not modified)

## Assumptions / Open Questions
- Whether `concern-investigator.md` (a separate agent, used by `create-tickets`, not
  `implement-ticket`) has the same gap is not investigated here — flagged as a possible follow-up
  if the same false-positive pattern is ever observed there.

## Implementation Notes
Rewrote the "Docs Requiring Update" section's format guidance in
`.claude/agents/investigator.md` (previously a single unlabeled "Required format" block, now split
into explicitly-labeled "Format 1" / "Format 2"):

- **Format 1 — required doc** (unchanged in substance, relabeled): the leading
  `` - `docs/path`: reason `` bullet, now explicitly stated to be reserved *exclusively* for docs
  that genuinely must change, with a pointer to Format 2 for the excluded case.
- **Format 2 — excluded doc** (new): prose only, no leading `- ` bullet, path still
  backtick-wrapped inline. Modeled verbatim on the real, already-applied pattern in
  `stored_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/investigation.md`'s own "Docs
  Requiring Update" section (the `docs/agent-monitoring/schema.md` paragraph), quoted directly as
  the worked example per the ticket's Scope instruction.
- **New "Why the distinction matters" paragraph**: spells out the actual mechanism —
  `_DOCS_BULLET_RE` only reads the leading backtick path on a bulleted line and never reads the
  reasoning text after the colon, so Format 1 used for an excluded doc is indistinguishable from a
  required one to the parser and fails `check_docs_to_update_coverage` with a `git status shows no
  changes` error. Cites both real prior occurrences
  (`TCK-20260821-VISUAL-VARIANTS-METRIC`, `TCK-20260821-VISUAL-GRADE-SCORER`) named in the ticket.
- The trailing "If none apply, write `None.`" sentence was preserved (moved to the end, after both
  formats) and extended to explicitly rule out inventing a third format.

No deviation from the ticket's Scope — the fix is confined to the documented section of
`investigator.md`; `done_checker_static.py` and `concern-investigator.md` were confirmed untouched
via `git status --porcelain` before finishing.

## Test Summary
No automated test parses this section's literal content or would need updating for its own sake.
Confirmed via targeted search before editing:
- `grep -rln "Docs Requiring Update" tests/` — zero matches (no test parses that section's literal
  content).
- `tests/tools/test_done_checker_static.py` — tests the parser (`_DOCS_BULLET_RE` /
  `check_docs_to_update_coverage`) against synthetic fixture strings, not against
  `investigator.md`'s own prose; contains no reference to `investigator.md` at all.
- `tests/tools/test_concern_investigator_agent_definition.py` — targets only
  `.claude/agents/concern-investigator.md` and `create-tickets.js`'s `INVESTIGATION_SCHEMA`;
  unrelated to this ticket's file, and that agent was correctly left untouched.
- `tests/tools/test_skill_investigate_search_before_grep.py` — targets
  `.claude/skills/implement-ticket/SKILL.md`'s Step 2 text, a different file; only mentions
  `investigator.md` in a docstring cross-reference to an unrelated prior ticket
  (TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP), not this section.

**Real, pre-existing, unrelated test failure hit during Test phase**:
Combined command `pytest tests/tools/test_finalize_knowledge_index_refresh.py
tests/tools/test_epic_scope_orphan_check.py tests/tools/test_done_checker_static.py
tests/tools/test_skill_investigate_search_before_grep.py
tests/tools/test_concern_investigator_agent_definition.py
tests/docs/test_prescan_mandate_instruction_draft.py tests/docs/test_doc_integrity.py -q` — 1
failed, 125 passed, 1 skipped across all 7 files combined. Isolating just
`pytest tests/docs/test_prescan_mandate_instruction_draft.py -q` alone: 1 failed, 4 passed.
The failure (`test_draft_does_not_modify_claude_md_or_agent_md_files`) asserts
`git diff --stat HEAD -- CLAUDE.md .claude/agents/*.md` is empty at test-run time. This is a
structural test-isolation bug, not caused by this ticket's content: the test's own docstring says
it exists to guard `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` (shipped/closed long
ago), but it is implemented as a *live uncommitted working-tree diff* check rather than a check
scoped to that historical ticket's own commit(s) — so it fails for ANY session with an unrelated,
legitimate, uncommitted edit to `.claude/agents/*.md`, which is exactly this ticket's own real
change. Confirmed it will pass again once this ticket's change is committed (since `git diff HEAD`
becomes empty relative to itself post-commit) — proving the check was never actually scoped to
`TCK-20260814`'s own diff. Filed as a separate hotfix ticket,
`TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE`, rather than editing that test
file (out of this ticket's own scope) to route around the failure.

All other relevant tests pass: `tests/tools/test_finalize_knowledge_index_refresh.py`,
`tests/tools/test_epic_scope_orphan_check.py`, `tests/tools/test_done_checker_static.py`,
`tests/tools/test_skill_investigate_search_before_grep.py`,
`tests/tools/test_concern_investigator_agent_definition.py`, and
`tests/docs/test_doc_integrity.py` all pass clean.

This is a pure prose/template edit with no parsing/runtime behavior change, consistent with the
ticket's own framing ("no code, no tests should need updating").

## Files Changed
- `.claude/agents/investigator.md` — "Docs Requiring Update" section: split single bullet-format
  guidance into Format 1 (required, unchanged bullet shape) + Format 2 (new, excluded-doc prose
  shape) + a new "Why the distinction matters" mechanism paragraph.
- `docs/ai/ticket-lifecycle.md` (Document-Update phase: a real gap found and fixed — its
  Investigate-phase section restated the old single-format rule literally enough that a reader
  following this doc alone would still hit the exact false positive this hotfix fixes. Updated to
  document both formats plus the `_DOCS_BULLET_RE` mechanism, citing this ticket.)
- `tickets/inprogress/TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP.md` — this
  file: Status, Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed,
  Completion Summary filled in.

## Completion Summary
Added a second, explicitly-labeled bullet format ("Format 2") to `investigator.md`'s "Docs
Requiring Update" section for docs that were considered but explicitly excluded — prose only, no
leading `` - `docs/...` `` bullet — alongside the existing required-doc bullet format ("Format 1"),
plus a new paragraph explaining the exact regex mechanism (`_DOCS_BULLET_RE` only reads the leading
path, never the reasoning text) that makes mixing the two formats a false-positive trigger for
`check_docs_to_update_coverage`. `done_checker_static.py` and `concern-investigator.md` were
confirmed untouched. Both Acceptance Criteria are satisfied; no automated test needed updating for
this change's own sake.

Document-Update found and fixed a real gap: `docs/ai/ticket-lifecycle.md` independently restated
the old single-format rule and needed the same two-format update. Test phase surfaced a real,
pre-existing, unrelated test-isolation bug (`tests/docs/test_prescan_mandate_instruction_draft.py`'s
`test_draft_does_not_modify_claude_md_or_agent_md_files` checks live uncommitted `git diff HEAD`
state rather than a specific historical ticket's own diff, so it false-positives on this ticket's
own legitimate, uncommitted `.claude/agents/investigator.md` edit) — filed as a separate hotfix
ticket, `TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE`, rather than editing that
out-of-scope test file.
