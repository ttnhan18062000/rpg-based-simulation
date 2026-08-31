---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE
phase: open
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE

## Title
Add an Explicit "Always the Bare Directory, Never Cherry-Picked Files" Rule to `test-scoper`

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Filed from `agent-monitoring/retro/RETRO-2026-W35.md`'s "What to change?" item 3, confirmed
recurring at least 8 times across the full week (5 in the M1 batch — `WIRE-ORPHANED-MECHANISMS`,
`OCCUPATION-CHANGE-TRIGGER`, `RELATIONSHIP-ROLE-FIELD`, others; at least 3 more in the follow-up
period, e.g. `HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES`'s Test-phase gate correctly
forcing a broadened `tests/tools/` scope): a scoped `pytest` command cherry-picks individual test
files instead of the bare containing test directory, caught by `test_scope_coverage_static`'s
structural backstop and always re-scoped correctly, but always after an initial failed attempt.

Read `.claude/agents/test-scoper.md` in full — it already has a **partial** version of this rule:
the "Scoping Rules" section (lines ~90-94) explicitly states "always include the **entire
`tests/tools/` directory**... never a subset" — but only for the `tools/*.py` (flat file) case.
The general rule — that once a `tests/unit/<x>/` (or any other mapped test) directory is
correctly identified as in-scope, the scoped command should pass the bare directory path and never
individual file names within it — is never stated as a standalone, always-true rule. The document's
"Scoping Rules" section conflates two genuinely separate questions: (a) *when* to expand beyond the
directly-mapped directory to cross-cutting tests (correctly scoped to shared infrastructure only),
and (b) whether to pass the *whole* mapped directory vs. a subset of files within it (should always
be the whole directory, unconditionally — this is the part currently under-stated).

## Scope
- Add an explicit, standalone bullet to `.claude/agents/test-scoper.md`'s "Scoping Rules" section:
  once any test directory is identified as in-scope (whether via the direct `src/`→`tests/unit/`
  mapping, the `tools/`→`tests/` map, or cross-cutting expansion), the scoped `pytest` command must
  pass the **bare directory path**, never individual file names within it — generalizing the
  existing `tools/*.py`-specific rule (lines ~90-94) into the general case, and citing the real
  recurrence evidence (this retro finding) as the "why".
- Keep the existing `tools/*.py` rule in place (it's still correct, just now a specific instance
  of the more general rule rather than the only stated case).

## Out of Scope
- Any change to the Test Directory Map itself, or the cross-cutting-expansion rule (Scoping Rules
  bullet 2) — those are correct and unaffected by this finding.
- `implement-ticket.js`'s own Test-phase orchestration logic — this is purely an agent-definition
  prompt-guidance fix.

## Acceptance Criteria
- `.claude/agents/test-scoper.md` states the bare-directory rule as a standalone, general rule, not
  only as a special case of the `tools/*.py` guidance.
- No existing correct guidance in the file is removed or weakened.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W35.md` (§ "What to change?" item 3)
- `.claude/agents/test-scoper.md`

## Related Code Areas
- `.claude/agents/test-scoper.md`

## Assumptions / Open Questions
None — this is a documentation-only fix to an agent definition, no code path changes.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented — no automated test surface for an agent-definition prompt file; verification
is re-reading the file for internal consistency.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
