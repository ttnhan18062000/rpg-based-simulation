---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260803-BRAINSTORM-SKILL-STALE-PATH
phase: done
date: 2026-08-03
tags: [skills, documentation]
---

# TCK-20260803-BRAINSTORM-SKILL-STALE-PATH

## Title
Fix stale `docs/superpowers/specs/` path reference in the brainstorming skill file

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`.claude/skills/brainstorming/SKILL.md` instructs writing design docs to
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` in two places (line 29 of the
numbered Checklist, and line 114 of the "After the Design" section prose). The
`docs/superpowers/` directory does not exist anywhere in this repo and never has —
confirmed by the prior structural audit `TCK-20260803-DOCS-STRUCTURE-AUDIT`, which
enumerated all 26 real top-level `docs/` subfolders and found no `superpowers` entry.
This project's own `CLAUDE.md` documents `docs/architecture/` as the real destination
for "ADR-shaped design docs." A near-identical Codex-facing mirror,
`.agents/skills/brainstorming/SKILL.md` (real file, not a symlink — content diverges
only in the frontmatter `description` field), was found during scoping to carry the
exact same stale reference at the same two line numbers. Scope was expanded during
review to cover both files rather than leave one stale copy behind.

## Scope
- In `.claude/skills/brainstorming/SKILL.md`:
  - Line 29 (Checklist item 6): replace
    `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` with
    `docs/architecture/YYYY-MM-DD-<topic>-design.md`.
  - Line 114 ("After the Design" → Documentation): replace
    `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` with
    `docs/architecture/YYYY-MM-DD-<topic>-design.md`.
- In `.agents/skills/brainstorming/SKILL.md`:
  - Same two path substitutions, at the same two line numbers (29, 114) — the file's
    structure mirrors `.claude/skills/brainstorming/SKILL.md` exactly aside from its
    own frontmatter `description` field, which is untouched.
- No other text in either file changes.

## Out of Scope
- Any change to the brainstorming skill's actual process/checklist logic, ordering,
  or wording beyond the two literal path substitutions.
- Creating any new file under `docs/architecture/` — this ticket only corrects the
  destination reference text; it does not author a design doc itself.
- Re-auditing the rest of `docs/` for other stale `docs/superpowers/` references —
  already done at the folder-structure level by `TCK-20260803-DOCS-STRUCTURE-AUDIT`;
  this ticket is scoped to the one specific file/reference already identified.
- Fixing the dead `"superpowers"`/`"specs"` branches in
  `tools/validate_frontmatter.py`'s `detect_content_type()` — explicitly out of scope
  per `TCK-20260803-DOCS-STRUCTURE-AUDIT`'s own plan, tracked separately.
- The `docs/superpowers/specs/*.md` glob entry found in `docs/REGISTRY.yaml` (line
  16683) — that is a generated/derived artifact entry, not a hand-authored
  instruction, and regenerates automatically per this repo's Finalize workflow.

## Acceptance Criteria
- `grep -rn "docs/superpowers" .claude/skills/brainstorming/SKILL.md .agents/skills/brainstorming/SKILL.md`
  returns no matches in either file.
- `grep -n "docs/architecture/YYYY-MM-DD-<topic>-design.md" .claude/skills/brainstorming/SKILL.md`
  returns exactly two matches, at the Checklist item 6 line and the "After the
  Design" → Documentation line.
- `grep -n "docs/architecture/YYYY-MM-DD-<topic>-design.md" .agents/skills/brainstorming/SKILL.md`
  returns exactly two matches, at the same two line positions.
- No other line in either file differs from its pre-change version (each file's diff
  is exactly its own two path substitutions — `.agents/`'s frontmatter `description`
  field, already divergent from `.claude/`'s before this ticket, must remain
  unchanged by this ticket).

## Related Tickets
- `TCK-20260803-DOCS-STRUCTURE-AUDIT` (done) — confirmed `docs/superpowers/` does not
  exist as a top-level `docs/` subfolder; this ticket's premise depends on that
  finding.
- `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS` (done) — previously found and removed a
  *different* stale `docs/superpowers/` reference, in `docs/guidelines/frontmatter_schema.md`;
  did not search for or fix the one in this skill file.
- `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` (done) — removed dead `superpowers`/`specs`
  entries from `tools/generate_registry.py`'s `_SKIP_DOC_SUBDIRS`; same underlying
  stale-directory family, different file, does not overlap this ticket's scope.

## Related Docs
- `CLAUDE.md` (this repo's project instructions) — documents `docs/architecture/` as
  "ADR-shaped design docs" destination; cited as the correct replacement target,
  no re-derivation needed.
- `docs/guidelines/frontmatter_schema.md` — the file where the sibling stale
  reference was already fixed by `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS`.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-DOCS-STRUCTURE-AUDIT/investigation.md` and
  `plan.md` — source of the confirmed "no `docs/superpowers/` on disk" finding this
  ticket relies on.
- None found specifically investigating `.claude/skills/brainstorming/SKILL.md` or
  its `.agents/` duplicate.

## Related Code Areas
- `.claude/skills/brainstorming/SKILL.md` (lines 29, 114 — two edits)
- `.agents/skills/brainstorming/SKILL.md` (lines 29, 114 — two edits, same fix)

## Assumptions / Open Questions
- Assumes `docs/architecture/` remains the correct, current destination for design
  docs per `CLAUDE.md`'s own documented convention; if that convention changes before
  this ticket is implemented, the replacement target would need to change too.
- Scope was expanded during review (after the initial scoping pass flagged
  `.agents/skills/brainstorming/SKILL.md` as an out-of-scope duplicate carrying the
  identical stale reference) to fix both files together, rather than leave one stale
  copy behind — see Request Summary.
- `layer: guidelines` was chosen following the direct precedent of prior skill-file
  text-fix tickets (`TCK-20260704-SKILL-TRIGGER-COVERAGE`, `TCK-20260705-SIX-SKILLS-INVESTIGATION`,
  `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`, `TCK-20260803-DOCS-STRUCTURE-AUDIT`), all of
  which used `layer: guidelines` for `.claude/skills/` and doc-path correctness work.

## Implementation Notes
Replaced the literal string `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` with
`docs/architecture/YYYY-MM-DD-<topic>-design.md` at exactly two locations in each file:
Checklist item 6 (line 29) and the "After the Design" → Documentation bullet (line 114).
Applied via targeted `Edit` calls (not `replace_all`) so each occurrence was matched and
substituted individually, confirming there were exactly two matches per file. No other
text, including `.agents/skills/brainstorming/SKILL.md`'s divergent frontmatter
`description` field, was touched. Implementation matched the plan exactly — no
deviations.

## Test Summary
No automated test suite applies to skill instruction text. Verified via the ticket's own
Acceptance Criteria, run directly after the edits:
- `grep -rn "docs/superpowers" .claude/skills/brainstorming/SKILL.md .agents/skills/brainstorming/SKILL.md` — no matches (exit 1) in either file.
- `grep -n "docs/architecture/YYYY-MM-DD-<topic>-design.md" .claude/skills/brainstorming/SKILL.md` — exactly two matches, at lines 29 and 114.
- `grep -n "docs/architecture/YYYY-MM-DD-<topic>-design.md" .agents/skills/brainstorming/SKILL.md` — exactly two matches, at lines 29 and 114.
- `git diff` on both files — confirmed the diff is exactly the two path substitutions per
  file, nothing else changed.

## Files Changed
- `.claude/skills/brainstorming/SKILL.md` (lines 29, 114)
- `.agents/skills/brainstorming/SKILL.md` (lines 29, 114)

## Completion Summary
Fixed the stale `docs/superpowers/specs/` path reference in both the Claude-facing and
Codex-facing brainstorming skill files, redirecting future `/brainstorming`-driven design
docs to the real `docs/architecture/` destination documented in this repo's `CLAUDE.md`.
Both files now point design-doc writes at a directory that actually exists, closing the
gap identified by `TCK-20260803-DOCS-STRUCTURE-AUDIT`. Change is a minimal two-line
text substitution per file with no logic, ordering, or frontmatter changes; verified
against all four acceptance criteria via grep and git diff. No new files were created
under `docs/architecture/`, per the ticket's explicit out-of-scope note.
