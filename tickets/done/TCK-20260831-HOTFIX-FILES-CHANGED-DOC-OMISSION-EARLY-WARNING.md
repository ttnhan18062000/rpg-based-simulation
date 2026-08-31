---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING
phase: open
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING

## Title
Warn at Document-Update Time When a Ticket's `## Files Changed` Section Omits a Doc-Updater-Touched Path

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Filed from `agent-monitoring/retro/RETRO-2026-W35.md`'s "What to change?" item 1, confirmed
recurring across 4+ M1-batch tickets (`WOUND-THRESHOLD-DECISION`, `TACTICAL-WOUND-SCAR-WIRING`,
`REPUTATION-WITNESSED-EVENT-WIRING`, `AFFECTION-CONTRACT-GATE`): the ticket's own `## Files
Changed` section omitting a doc the Document-Update phase had legitimately touched, caught only
reactively at Verify (6+ phases later) via the `done-checker` agent's own judgment, always fixed
correctly but always late.

The data needed to catch this early already exists inside `.claude/workflows/implement-ticket.js`'s
Document-Update phase: `combinedFilesChanged` (`implement-ticket.js` around line 884-887) already
merges `implementation.files_changed` (the Implement phase's own self-report) with
`docUpdate.docs_updated`'s paths (the Document-Update phase's own real output) for the
doc-staleness gate's purposes — but this merged list is never cross-checked against the ticket
`.md` file's own literal `## Files Changed` prose section, which is what `done-checker` actually
reads at Verify.

## Scope
- Immediately after `combinedFilesChanged` is computed in `.claude/workflows/implement-ticket.js`'s
  Document-Update phase, read the ticket file's current `## Files Changed` section text and check
  whether every path in `docUpdate.docs_updated` appears in it.
- If any path is missing, emit a clear, non-blocking **warning** (into the phase's own event/log
  output, matching this codebase's established fail-open observability pattern — do not fail the
  gate or block the pipeline) naming the specific missing path(s), so whoever runs Finalize sees it
  immediately rather than only at Verify.
- Do NOT auto-edit the ticket file's `## Files Changed` prose programmatically — a warning is the
  right scope here (per the retro's own "warning/auto-fill" framing, choosing the lower-risk
  option); auto-mutating ticket markdown prose from a JS orchestration script is a separate,
  larger, more error-prone piece of scope not justified by this finding alone.
- Add a test exercising this new warning path (a case where `docs_updated` includes a path absent
  from a fixture ticket's `## Files Changed` text, and a case where it's present — no warning).

## Out of Scope
- Auto-filling/auto-editing the `## Files Changed` section itself.
- Making this check blocking/gate-failing — it must remain a warning, not a new hard gate.
- Any other `done-checker`/Verify-phase gate logic.

## Acceptance Criteria
- Running the Document-Update phase with a `docs_updated` path missing from the ticket's current
  `## Files Changed` section produces a visible warning at that point, not just at Verify.
- The pipeline does not fail or block on this warning alone.
- A regression test covers both the warning-fires and no-warning cases.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W35.md` (§ "What to change?" item 1, and item 2's precedent —
  two gate-checker false-positive tickets fixed the same week this finding was filed in)
- `docs/architecture/doc_updater_agent.md`

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (Document-Update phase, `combinedFilesChanged`)

## Assumptions / Open Questions
Exact warning format/placement (event message vs. a dedicated log line) left to implementation
judgment, matching existing patterns elsewhere in this same phase (e.g. the doc-staleness gate's
own ADVISORY-entry shape).

**Resolved during implementation**: `.claude/workflows/implement-ticket.js` is not executed as
real JS by an interpreter — per `.claude/skills/implement-ticket/SKILL.md`, it is read and
manually translated into tool calls by whichever agent is hand-orchestrating a ticket. Confirmed
via `grep -rn "require.*implement-ticket\|import.*implement-ticket"` across the whole repo (no
hits outside the one static "no forbidden calls" check) and via checking for a JS test runner
(`package.json`s found are all frontend-app configs, none reference this file). There is
genuinely no automated test surface for this file's internal logic — the Acceptance Criteria's
"regression test" bullet cannot be satisfied as originally scoped. Condition not met: verification
instead used a real-data manual trace (the new `awk` extraction command run directly against a
real closed ticket's `## Files Changed` section, confirmed to extract exactly the expected text)
plus a logical code review for placement/correctness.

## Implementation Notes
Added a deterministic, orchestrator-run check (no `agent()` call, mirroring the doc-staleness
gate's own shape immediately below it) right after `combinedFilesChanged` is computed in the
Document-Update phase: extracts the ticket file's current `## Files Changed` section text via
`awk`, checks each `docUpdate.docs_updated` path against it, and calls `log()` with a `⚠`-prefixed
warning naming any missing paths if the list is non-empty. Warning-only — never fails or blocks
the phase, and does not edit the ticket file. `docUpdate.docs_updated` empty (no docs touched this
ticket) correctly produces no warning, verified by tracing the logic (empty array → empty
`missingFromFilesChanged` → no `log()` call).

## Test Summary
No automated test surface exists for `.claude/workflows/implement-ticket.js`'s internal logic (see
"Resolved during implementation" above — this file is agent-interpreted, not code-executed).
Verified instead via: (1) running the new `awk` extraction command directly against a real closed
ticket file (`tickets/done/TCK-20260830-HOTFIX-EVENT-RECORDER-BATCH-FLUSH-VISIBILITY-REGRESSION.md`),
confirming it extracts exactly the section's real content; (2) manual logic trace for the
empty-`docs_updated` and all-paths-present cases (both correctly produce no warning).

## Files Changed
.claude/workflows/implement-ticket.js

## Completion Summary
Filed and fixed the same day, per `agent-monitoring/retro/RETRO-2026-W35.md` item 1. The
originally-scoped "regression test" AC bullet was found not satisfiable during implementation (no
automated test surface for this file exists) — disclosed above, not silently dropped, matching
this session's established Gate Integrity discipline.
